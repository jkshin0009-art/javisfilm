"""Voice: per-character, per-emotion reference voices for dots.tts, and a
cancellable speaking queue.

dots.tts has no emotion parameter; it copies the delivery of the reference clip.
So emotion is chosen by choosing the clip, the same routing little-gemma-tools
does with `clausecat --route-emotion` feeding piper's set_voice:

    voices/<character>/neutral.wav + neutral.txt   (txt = what is said in the wav)
    voices/<character>/happy.wav   + happy.txt
    ...

A missing emotion falls back to neutral, then to any clip of that character.

The engine is pluggable. DotsTtsEngine loads dots.tts directly; CallableEngine
wraps the function the project already uses to call dots.tts, so the existing
TTS lane is reused instead of loading a second copy of the model.
"""
from __future__ import annotations

import os
import queue
import threading
import time
import wave
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Iterator, List, Optional

from chatup.shaper import Clause

AUDIO_EXT = (".wav", ".flac", ".mp3", ".ogg")


@dataclass(frozen=True)
class VoiceRef:
    wav: str
    text: str
    emotion: str


class VoiceBank:
    def __init__(self, root: str, default_emotion: str = "neutral") -> None:
        self.root = root
        self.default_emotion = default_emotion

    def _dir(self, persona: str) -> str:
        return os.path.join(self.root, persona)

    def emotions(self, persona: str) -> List[str]:
        d = self._dir(persona)
        if not os.path.isdir(d):
            return []
        out = []
        for f in sorted(os.listdir(d)):
            stem, ext = os.path.splitext(f)
            if ext.lower() in AUDIO_EXT:
                out.append(stem)
        return out

    def _ref(self, persona: str, emotion: str) -> Optional[VoiceRef]:
        d = self._dir(persona)
        for ext in AUDIO_EXT:
            wav = os.path.join(d, emotion + ext)
            if os.path.isfile(wav):
                txt = os.path.join(d, emotion + ".txt")
                text = ""
                if os.path.isfile(txt):
                    with open(txt, encoding="utf-8-sig") as f:
                        text = f.read().strip()
                return VoiceRef(wav, text, emotion)
        return None

    def pick(self, persona: str, emotion: str) -> Optional[VoiceRef]:
        for emo in (emotion, self.default_emotion):
            ref = self._ref(persona, emo)
            if ref is not None:
                return ref
        rest = self.emotions(persona)
        return self._ref(persona, rest[0]) if rest else None

    def check(self, personas: Iterable[str]) -> List[str]:
        """Problems worth fixing before a session: no clip, no neutral, no transcript."""
        problems = []
        for p in personas:
            emos = self.emotions(p)
            if not emos:
                problems.append(f"{p}: no reference audio in {self._dir(p)}")
                continue
            if self.default_emotion not in emos:
                problems.append(f"{p}: no {self.default_emotion} clip (fallback uses {emos[0]})")
            for e in emos:
                ref = self._ref(p, e)
                if ref is not None and not ref.text:
                    problems.append(f"{p}/{e}: no transcript .txt (dots.tts clones better with prompt_text)")
        return problems


# ---------------------------------------------------------------- engines
class DotsTtsEngine:
    """Loads dots.tts in this process. Use CallableEngine instead when the project
    already has the model loaded."""

    def __init__(self, model: str = "dots-studio/dots.tts-soar", precision: str = "bfloat16",
                 optimize: bool = True, language: Optional[str] = "ko", num_steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None, runtime=None) -> None:
        if runtime is None:
            from dots_tts.runtime import DotsTtsRuntime     # heavy import, only when used
            runtime = DotsTtsRuntime.from_pretrained(model, precision=precision, optimize=optimize)
        self.runtime = runtime
        self.language = language
        self.num_steps = num_steps
        self.guidance_scale = guidance_scale
        self.sample_rate = int(runtime.sample_rate)

    def stream(self, text: str, ref: Optional[VoiceRef]) -> Iterator:
        kw = dict(text=text, language=self.language, num_steps=self.num_steps,
                  guidance_scale=self.guidance_scale)
        if ref is not None:
            kw["prompt_audio_path"] = ref.wav
            kw["prompt_text"] = ref.text or None
        for chunk in self.runtime.generate_stream(**kw):
            yield chunk.float().cpu().squeeze(0).numpy()


class CallableEngine:
    """fn(text, wav_path_or_None, prompt_text) -> samples, or an iterator of chunks."""

    def __init__(self, fn: Callable, sample_rate: int) -> None:
        self.fn = fn
        self.sample_rate = int(sample_rate)

    def stream(self, text: str, ref: Optional[VoiceRef]) -> Iterator:
        out = self.fn(text, ref.wav if ref else None, ref.text if ref else "")
        if out is None:
            return
        if isinstance(out, (list, tuple)) or hasattr(out, "shape"):
            yield out
        else:
            yield from out


# ---------------------------------------------------------------- players
class NullPlayer:
    """Plays nothing. realtime=True sleeps for the audio's length (for timing tests)."""

    def __init__(self, realtime: bool = False) -> None:
        self.realtime = realtime
        self._stop = threading.Event()

    def play(self, samples, sample_rate: int) -> bool:
        if self.realtime:
            end = time.monotonic() + len(samples) / float(sample_rate)
            while time.monotonic() < end:
                if self._stop.wait(0.01):
                    return False
        return not self._stop.is_set()

    def stop(self) -> None:
        self._stop.set()

    def reset(self) -> None:
        self._stop.clear()


class SoundDevicePlayer:
    """Speaker output through the sounddevice package (pip install sounddevice)."""

    def __init__(self, device=None, block: int = 2048) -> None:
        import sounddevice   # noqa: F401  (fail early if missing)
        self.device = device
        self.block = block
        self._stop = threading.Event()
        self._stream = None
        self._rate = None

    def _open(self, rate: int):
        import sounddevice as sd
        if self._stream is None or self._rate != rate:
            if self._stream is not None:
                self._stream.close()
            self._stream = sd.OutputStream(samplerate=rate, channels=1, dtype="float32", device=self.device)
            self._stream.start()
            self._rate = rate
        return self._stream

    def play(self, samples, sample_rate: int) -> bool:
        import numpy as np
        data = np.asarray(samples, dtype="float32").reshape(-1, 1)
        st = self._open(sample_rate)
        for i in range(0, len(data), self.block):
            if self._stop.is_set():
                return False
            st.write(data[i:i + self.block])
        return not self._stop.is_set()

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.abort()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def reset(self) -> None:
        self._stop.clear()


class WavWriter:
    """Writes each clause to <out_dir>/<n>_<persona>_<emotion>.wav (for checking voices)."""

    def __init__(self, out_dir: str) -> None:
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self._buf: List = []
        self._n = 0

    def play(self, samples, sample_rate: int) -> bool:
        self._buf.append((samples, sample_rate))
        return True

    def finish(self, name: str) -> Optional[str]:
        if not self._buf:
            return None
        import numpy as np
        rate = self._buf[0][1]
        audio = np.concatenate([np.asarray(s, dtype="float32").reshape(-1) for s, _ in self._buf])
        self._buf = []
        self._n += 1
        path = os.path.join(self.out_dir, f"{self._n:03d}_{name}.wav")
        pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        return path

    def stop(self) -> None:
        self._buf = []

    def reset(self) -> None:
        pass


# ---------------------------------------------------------------- worker
@dataclass
class SpeakJob:
    turn: int
    persona: str
    clause: Clause


class VoiceWorker:
    """Speaks clauses in order on a background thread while the LLM keeps generating.

    cancel() is barge-in: it drops the queue and cuts the current clause. What was
    fully spoken is kept per turn in spoken(turn), so the history can record the
    part the listener actually heard."""

    def __init__(self, engine, bank: Optional[VoiceBank], player,
                 on_event: Optional[Callable[[str, SpeakJob], None]] = None) -> None:
        self.engine = engine
        self.bank = bank
        self.player = player
        self.on_event = on_event
        self._q: "queue.Queue[Optional[SpeakJob]]" = queue.Queue()
        self._gen = 0
        self._lock = threading.Lock()
        self._pending = 0          # queued + playing
        self._spoken: Dict[int, List[str]] = {}
        self._thread = threading.Thread(target=self._run, name="voice", daemon=True)
        self._thread.start()

    def say(self, turn: int, persona: str, clause: Clause) -> None:
        with self._lock:
            self._pending += 1
        self._q.put(SpeakJob(turn, persona, clause))

    def spoken(self, turn: int) -> List[str]:
        with self._lock:
            return list(self._spoken.get(turn, []))

    def cancel(self) -> None:
        with self._lock:
            self._gen += 1
        try:
            while True:
                job = self._q.get_nowait()
                if job is not None:
                    with self._lock:
                        self._pending -= 1
        except queue.Empty:
            pass
        self.player.stop()

    def wait_idle(self, timeout: Optional[float] = None) -> bool:
        end = None if timeout is None else time.monotonic() + timeout
        while True:
            if not self.busy:
                return True
            if end is not None and time.monotonic() > end:
                return False
            time.sleep(0.02)

    @property
    def busy(self) -> bool:
        with self._lock:
            return self._pending > 0

    def close(self) -> None:
        self.cancel()
        self._q.put(None)

    def _emit(self, kind: str, job: SpeakJob) -> None:
        if self.on_event:
            try:
                self.on_event(kind, job)
            except Exception:
                pass

    def _run(self) -> None:
        while True:
            job = self._q.get()
            if job is None:
                return
            with self._lock:
                gen = self._gen
            if gen == self._gen and hasattr(self.player, "reset"):
                self.player.reset()
            ref = self.bank.pick(job.persona, job.clause.emotion) if self.bank else None
            self._emit("start", job)
            completed = True
            try:
                for chunk in self.engine.stream(job.clause.text, ref):
                    with self._lock:
                        stale = gen != self._gen
                    if stale or not self.player.play(chunk, self.engine.sample_rate):
                        completed = False
                        break
            except Exception:
                completed = False
                self._emit("error", job)
            with self._lock:
                if completed and gen == self._gen:
                    self._spoken.setdefault(job.turn, []).append(job.clause.text)
            if hasattr(self.player, "finish") and completed:
                self.player.finish(f"{job.persona}_{job.clause.emotion}")
            with self._lock:
                self._pending -= 1
            self._emit("done" if completed else "cut", job)

"""ConversationLoop: a reference multi-party loop with autonomous speech.

It shows how the pieces fit, and it runs on its own (demo.py chat), but the
project's chatbot already has a loop; the intended use is to take the parts it
lacks: the judge for who speaks / whether to speak / what to do, the shaper and
policy for turn endings, and the voice worker for barge-in.

One cycle:
  user line   -> barge-in (cut the speaker, note what was heard) -> wants_stop?
              -> addressed? / next_speaker? -> that character answers
  user silent -> caps (turns, time) -> should_speak? -> stuck? (director note)
              -> next_speaker? -> that character speaks -> route? (image / scenario / ask)
Every judge call has a rule to fall back on when its answer is not confident.
"""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

from chatup.judge import ConversationJudge, Line, Verdict
from chatup.llm import Cancelled, CancelToken, LLMError, StallError
from chatup.policy import TurnPolicy, loop_score
from chatup.shaper import Clause, ReplyShaper

RULES = (
    "여러 사람이 함께 대화하는 자리다. 너는 {name}의 대사만 말한다. 다른 사람의 대사, 지문, 이름표를 쓰지 않는다. "
    "소리 내어 말하는 짧은 구어체 문장 한두 개로 말한다. 목록이나 마크다운을 쓰지 않는다. "
    "감정이 분명하면 문장 앞에 {tags} 중 하나를 붙일 수 있다(소리 내어 읽지 않는다)."
)


@dataclass
class Persona:
    name: str
    system: str
    voice: str = ""                 # folder in the voice bank; defaults to name

    @property
    def voice_id(self) -> str:
        return self.voice or self.name


@dataclass
class LoopConfig:
    idle_seconds: float = 8.0         # user silence before autonomous speech is considered
    gap_seconds: float = 1.0          # pause between autonomous turns
    max_auto_turns: int = 12          # autonomous turns in a row without the user
    max_session_seconds: float = 1800.0   # autonomous talk stops after this long without the user
    followups: int = 1                # extra characters that may chime in right after a reply
    stall_timeout: float = 60.0
    max_failures: int = 3
    max_tokens: int = 300
    temperature: float = 0.8
    history_lines: int = 30
    stuck_every: int = 4              # autonomous turns between stuck checks
    stuck_pre: float = 0.25           # loop_score above which the judge is asked
    route_every: int = 3              # turns between route decisions; 0 = off
    judge_emotion: bool = False       # ask the judge for an emotion when the reply has no tag
    emotions: Sequence[str] = ("neutral", "happy", "sad", "angry")
    barge_note: str = "끼어듦"
    stuck_note: str = "(연출 메모: 대화가 제자리를 돌고 있다. 새 화제나 새 사건을 꺼내라.)"
    rules: str = RULES


class Hooks:
    """Override what the project needs. All calls come from the loop thread."""

    def on_clause(self, persona: str, clause: Clause) -> None: ...
    def on_line(self, line: Line) -> None: ...
    def on_image(self, persona: str, prompt: str) -> None: ...
    def on_route(self, action: str, verdict: Verdict, lines: List[Line]) -> None: ...
    def on_decision(self, name: str, verdict: Verdict) -> None: ...
    def on_state(self, state: str, detail: str = "") -> None: ...


@dataclass
class TurnResult:
    persona: str
    text: str
    clauses: List[Clause] = field(default_factory=list)
    interrupted: bool = False
    error: str = ""


class ConversationLoop:
    def __init__(self, llm, personas: Sequence[Persona], *, judge: Optional[ConversationJudge] = None,
                 voice=None, policy: Optional[TurnPolicy] = None, config: Optional[LoopConfig] = None,
                 hooks: Optional[Hooks] = None, user_name: str = "사용자",
                 clock: Callable[[], float] = time.monotonic) -> None:
        if not personas:
            raise ValueError("at least one persona")
        self.llm = llm
        self.personas = {p.name: p for p in personas}
        self.names = [p.name for p in personas]
        self.judge = judge
        self.voice = voice
        self.policy = policy or TurnPolicy()
        self.cfg = config or LoopConfig()
        self.hooks = hooks or Hooks()
        self.user_name = user_name
        self.clock = clock
        self.lines: List[Line] = []
        self._inbox: "queue.Queue[str]" = queue.Queue()
        self._cancel: Optional[CancelToken] = None
        self._lock = threading.Lock()
        self._turn = 0
        self._last_activity = clock()
        self._auto_turns = 0
        self._auto_since = clock()
        self._turns_since_route = 0
        self._failures = 0
        self._paused = False
        self._director_note = ""
        self._last_spoken: Optional[tuple] = None     # (turn, line index, clause count) of the last voiced turn

    # ------------------------------------------------------------ input (any thread)
    def user_says(self, text: str) -> None:
        """Queue a user line and cut whoever is speaking (barge-in)."""
        text = text.strip()
        if not text:
            return
        self._inbox.put(text)
        with self._lock:
            tok = self._cancel
        if tok is not None:
            tok.cancel()
        if self.voice is not None:
            self.voice.cancel()

    # ------------------------------------------------------------ main loop
    def run(self, stop: threading.Event, poll: float = 0.05) -> None:
        while not stop.is_set():
            self.step(poll)

    def step(self, wait: float = 0.0) -> Optional[TurnResult]:
        """One cycle: handle a user line if there is one, else maybe speak on our own."""
        try:
            text = self._inbox.get(timeout=wait) if wait > 0 else self._inbox.get_nowait()
        except queue.Empty:
            text = None
        if text is not None:
            return self._on_user(text)
        return self._maybe_autonomous()

    # ------------------------------------------------------------ user turn
    def _on_user(self, text: str) -> Optional[TurnResult]:
        self._trim_unheard()
        self.lines.append(Line(self.user_name, text))
        self.hooks.on_line(self.lines[-1])
        self._touch()
        self._auto_turns = 0
        self._auto_since = self.clock()
        self._failures = 0
        self._paused = False

        if self.judge is not None:
            v = self._ask("wants_stop", lambda: self.judge.wants_stop(self.lines))
            if v is not None and v.value == "Yes":
                self._paused = True
                self.hooks.on_state("paused", "user asked to stop")
                return None

        responder = self._pick_responder(text)
        result = self._speak(responder)
        for _ in range(self.cfg.followups):
            if not self._inbox.empty() or result.interrupted:
                break
            nxt = self._pick_followup(exclude=responder)
            if nxt is None:
                break
            self._pause(self.cfg.gap_seconds)
            if not self._inbox.empty():
                break
            result = self._speak(nxt)
            responder = nxt
        return result

    def _pick_responder(self, text: str) -> str:
        if len(self.names) == 1:
            return self.names[0]
        if self.judge is not None:
            v = self._ask("addressed", lambda: self.judge.addressed(self.lines, self.names))
            if v is not None and v.value in self.personas:
                return v.value
            v = self._ask("next_speaker", lambda: self.judge.next_speaker(self.lines, self.names))
            if v is not None and v.value in self.personas:
                return v.value
        mentioned = [n for n in self.names if n in text]
        if len(mentioned) == 1:
            return mentioned[0]
        return self._least_recent(exclude=None)

    def _pick_followup(self, exclude: str) -> Optional[str]:
        if self.judge is None or len(self.names) < 2:
            return None
        cands = [n for n in self.names if n != exclude]
        v = self._ask("next_speaker", lambda: self.judge.next_speaker(self.lines, cands, allow_silence=True))
        if v is not None and v.value in cands:
            return v.value
        return None          # silence, or not sure: leave the floor to the user

    # ------------------------------------------------------------ autonomous turn
    def _idle_for(self) -> float:
        if self.voice is not None and self.voice.busy:
            self._touch()
            return 0.0
        return self.clock() - self._last_activity

    def _maybe_autonomous(self) -> Optional[TurnResult]:
        if self._paused or self._failures >= self.cfg.max_failures:
            return None
        idle = self._idle_for()
        need = self.cfg.idle_seconds if self._auto_turns == 0 else self.cfg.gap_seconds
        if idle < need:
            return None
        if self._auto_turns >= self.cfg.max_auto_turns:
            self._pause_autonomy(f"{self._auto_turns} turns without the user")
            return None
        if self.clock() - self._auto_since > self.cfg.max_session_seconds:
            self._pause_autonomy("session time limit")
            return None
        if self.judge is not None and self._auto_turns == 0:
            v = self._ask("should_speak", lambda: self.judge.should_speak(self.lines, idle))
            if v is not None and v.value == "No":
                self._touch()             # wait another idle period before asking again
                return None
        if self.judge is not None and self._auto_turns and self._auto_turns % max(1, self.cfg.stuck_every) == 0:
            if loop_score([l.text for l in self.lines]) >= self.cfg.stuck_pre:
                v = self._ask("stuck", lambda: self.judge.stuck(self.lines))
                if v is not None and v.value == "Yes":
                    self._director_note = self.cfg.stuck_note
        speaker = self._pick_autonomous()
        self._auto_turns += 1
        result = self._speak(speaker)
        self._maybe_route()
        return result

    def _pick_autonomous(self) -> str:
        last = self._last_speaker()
        cands = [n for n in self.names if n != last] or list(self.names)
        if self.judge is not None and len(cands) > 1:
            v = self._ask("next_speaker", lambda: self.judge.next_speaker(self.lines, cands))
            if v is not None and v.value in cands:
                return v.value
        return self._least_recent(exclude=last)

    def _maybe_route(self) -> None:
        self._turns_since_route += 1
        if self.judge is None or self.cfg.route_every <= 0 or self._turns_since_route < self.cfg.route_every:
            return
        self._turns_since_route = 0
        v = self._ask("route", lambda: self.judge.route(self.lines))
        if v is not None and v.value and v.value != self.judge.actions[0]:
            self.hooks.on_route(v.value, v, list(self.lines))

    def _pause_autonomy(self, why: str) -> None:
        self._paused = True
        self.hooks.on_state("autonomy_paused", why)

    # ------------------------------------------------------------ speaking
    def build_messages(self, persona: Persona) -> List[Dict]:
        tags = " ".join(f"[{e}]" for e in self.cfg.emotions)
        others = ", ".join(n for n in self.names if n != persona.name)
        system = persona.system.strip() + "\n\n" + self.cfg.rules.format(name=persona.name, tags=tags)
        if others:
            system += f"\n함께 있는 사람: {others}, {self.user_name}."
        msgs: List[Dict] = [{"role": "system", "content": system}]
        for line in self.lines[-self.cfg.history_lines:]:
            if line.speaker == persona.name:
                role, content = "assistant", line.text
            else:
                role, content = "user", line.render()
            if msgs[-1]["role"] == role and role != "system":
                msgs[-1]["content"] += "\n" + content
            else:
                msgs.append({"role": role, "content": content})
        nudge = self._director_note or f"({persona.name}의 차례다. {persona.name}로서 말하라.)"
        if msgs[-1]["role"] == "user":
            msgs[-1]["content"] += "\n" + nudge
        else:
            msgs.append({"role": "user", "content": nudge})
        return msgs

    def _speak(self, name: str) -> TurnResult:
        persona = self.personas[name]
        self._turn += 1
        turn = self._turn
        messages = self.build_messages(persona)
        self._director_note = ""
        shaper = ReplyShaper(name, [n for n in self.names if n != name] + [self.user_name])
        tok = CancelToken()
        with self._lock:
            self._cancel = tok
        spoken: List[Clause] = []
        recent = [l.text for l in self.lines]
        result = TurnResult(name, "")
        ended = False
        judged_emotion = False

        def handle(events) -> bool:
            nonlocal judged_emotion
            for ev in events:
                if ev.kind == "image":
                    self.hooks.on_image(name, ev.value)
                    continue
                if ev.kind == "stop":
                    return True
                clause = ev.clause
                verdict = self.policy.check(clause, [c.text for c in spoken], recent)
                if verdict in ("drop",):
                    continue
                if verdict == "stop":
                    return True
                if self.cfg.judge_emotion and self.judge is not None and not spoken and not judged_emotion \
                        and shaper.emotion == "neutral":
                    judged_emotion = True
                    v = self._ask("emotion", lambda: self.judge.emotion(name, clause.text, self.cfg.emotions,
                                                                        self.lines))
                    if v is not None and v.value:
                        shaper.emotion = v.value
                        clause.emotion = v.value
                spoken.append(clause)
                if self.voice is not None:
                    self.voice.say(turn, persona.voice_id, clause)
                self.hooks.on_clause(name, clause)
                if verdict == "speak_last":
                    return True
            return False

        try:
            for piece in self.llm.stream_chat(messages, max_tokens=self.cfg.max_tokens,
                                              temperature=self.cfg.temperature, cancel=tok,
                                              stall_timeout=self.cfg.stall_timeout):
                if handle(shaper.feed(piece)):
                    ended = True
                    tok.cancel()
                    break
            if not ended:
                handle(shaper.flush())
        except Cancelled:
            if not ended:
                result.interrupted = True
        except StallError as e:
            result.error = f"stall: {e}"
        except LLMError as e:
            result.error = str(e)
        finally:
            with self._lock:
                self._cancel = None

        if result.interrupted and self.voice is not None:
            heard = self.voice.spoken(turn)
        else:
            heard = [c.text for c in spoken]
        result.clauses = spoken
        result.text = " ".join(heard)
        if result.error or not spoken:
            self._failures += 1
            self.hooks.on_state("turn_failed", result.error or "empty reply")
        else:
            self._failures = 0
        if result.text or result.interrupted:
            note = self.cfg.barge_note if result.interrupted else ""
            self.lines.append(Line(name, result.text or "…", note))
            self.hooks.on_line(self.lines[-1])
            if self.voice is not None and not result.interrupted:
                self._last_spoken = (turn, len(self.lines) - 1, len(spoken))
        self._touch()
        return result

    # ------------------------------------------------------------ helpers
    def _trim_unheard(self) -> None:
        """The reply finished generating but its audio was cut by the user: keep
        only the clauses that were actually heard, and mark the line."""
        info, self._last_spoken = self._last_spoken, None
        if info is None or self.voice is None:
            return
        turn, idx, count = info
        self.voice.wait_idle(1.0)                  # let the cut clause settle
        heard = self.voice.spoken(turn)
        if len(heard) < count and idx < len(self.lines):
            old = self.lines[idx]
            self.lines[idx] = Line(old.speaker, " ".join(heard) or "…", self.cfg.barge_note)

    def _ask(self, name: str, fn) -> Optional[Verdict]:
        try:
            v = fn()
        except LLMError as e:
            self.hooks.on_state("judge_error", f"{name}: {e}")
            return None
        self.hooks.on_decision(name, v)
        return v

    def _touch(self) -> None:
        self._last_activity = self.clock()

    def _pause(self, seconds: float) -> None:
        end = self.clock() + seconds
        while self.clock() < end and self._inbox.empty():
            time.sleep(0.01)

    def _last_speaker(self) -> Optional[str]:
        for line in reversed(self.lines):
            if line.speaker in self.personas:
                return line.speaker
        return None

    def _least_recent(self, exclude: Optional[str]) -> str:
        last_seen = {n: -1 for n in self.names}
        for i, line in enumerate(self.lines):
            if line.speaker in last_seen:
                last_seen[line.speaker] = i
        cands = [n for n in self.names if n != exclude] or list(self.names)
        return min(cands, key=lambda n: (last_seen[n], self.names.index(n)))

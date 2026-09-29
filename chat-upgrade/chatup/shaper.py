"""ReplyShaper: raw token stream in, speakable clauses out.

Port of little-gemma-tools' clausecat policy to Python, with Korean added:
  * drops <think>...</think> (also when the tags are split across chunks) and
    chat special tokens such as <|im_end|> or <end_of_turn>;
  * reads inline tags, which are never spoken:
      [happy] [sad] [angry] [neutral] ... or [[emotion:happy]]   -> emotion for the next clauses
      [nod] [shake] [quiet] ...                                 -> gesture on the next clause
      [[image: a prompt]]                                       -> an image request event
  * drops a leading "Name:" the model adds in front of its own line, and stops
    the turn when the model starts writing another character's line;
  * cuts clauses at the model's own punctuation (. ! ? … and the Korean
    full stop 。) so TTS can start on the first clause, merges clauses that are
    too short to say on their own, and splits over-long ones at a comma or space.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

DEFAULT_EMOTIONS: Dict[str, str] = {
    "neutral": "neutral", "happy": "happy", "sad": "sad", "angry": "angry",
    "surprised": "surprised", "calm": "calm", "excited": "excited", "fear": "fear",
    "평온": "neutral", "기쁨": "happy", "슬픔": "sad", "화남": "angry", "놀람": "surprised",
    "차분": "calm", "신남": "excited", "두려움": "fear",
}
DEFAULT_GESTURES = ("nod", "shake", "quiet", "laugh", "sigh", "끄덕", "고개젓기", "웃음", "한숨")

_SPECIAL = re.compile(r"<\|[^|>]{1,40}\|>|<(?:start|end)_of_turn>|</?s>|<eos>|<bos>")
_TAG = re.compile(r"\[\[\s*(emotion|emo|image|img)\s*:\s*([^\]]*?)\s*\]\]|\[([^\[\]\n]{1,24})\]", re.I)
_ENDERS = ".!?…。！？"
_MARK_BASE, _MARK_SPAN = 0xE000, 0x1900       # Unicode private use area
_CLOSERS = "\"'”’)）」』]"
_QUESTION_END = re.compile(r"[?？]\s*[\"'”’)）」』]*\s*$")


@dataclass
class Clause:
    text: str
    emotion: str = "neutral"
    gestures: List[str] = field(default_factory=list)
    is_question: bool = False
    index: int = 0


@dataclass
class ShaperEvent:
    kind: str            # "clause" | "image" | "stop"
    clause: Optional[Clause] = None
    value: str = ""


class ReplyShaper:
    """One instance per spoken turn.

    speaker: the name the model speaks as (its "Name:" prefix is removed).
    others:  names of the other participants; a new line starting with one of
             them ends the turn (the model tried to write their line too)."""

    def __init__(self, speaker: str = "", others: Sequence[str] = (), *,
                 emotions: Optional[Dict[str, str]] = None, gestures: Iterable[str] = DEFAULT_GESTURES,
                 default_emotion: str = "neutral", min_chars: int = 6, soft_max: int = 60,  # min_chars: see _weight
                 hard_max: int = 140) -> None:
        self.speaker = speaker
        self.others = [o for o in others if o and o != speaker]
        self.emotions = {k.lower(): v for k, v in (emotions or DEFAULT_EMOTIONS).items()}
        self.gestures = {g.lower() for g in gestures}
        self.emotion = default_emotion
        self.min_chars = min_chars
        self.soft_max = soft_max
        self.hard_max = hard_max
        self._raw = ""            # undecided raw tail (may hold a partial tag or <think>)
        self._text = ""           # cleaned text not yet emitted
        self._pending_gestures: List[str] = []
        self._actions: Dict[str, tuple] = {}
        self._mark_seq = 0
        self._in_think = False
        self._started = False     # leading speaker prefix handled
        self._stopped = False
        self._index = 0
        self.spoken: List[str] = []
        names = [re.escape(n) for n in [speaker] + self.others if n]
        self._prefix_re = (re.compile(r"^\s*(?:\*\*)?(?:" + "|".join(names) + r")(?:\*\*)?\s*[:：]\s*")
                           if names else None)
        self._other_re = (re.compile(r"\n\s*(?:\*\*)?(?:" + "|".join(re.escape(o) for o in self.others)
                                     + r")(?:\*\*)?\s*[:：]") if self.others else None)

    # ------------------------------------------------------------ public
    @property
    def stopped(self) -> bool:
        return self._stopped

    def feed(self, chunk: str) -> List[ShaperEvent]:
        if self._stopped or not chunk:
            return []
        self._raw += chunk
        events = self._consume(final=False)
        events += self._split(final=False)
        return events

    def flush(self) -> List[ShaperEvent]:
        if self._stopped:
            return []
        events = self._consume(final=True)
        events += self._split(final=True)
        return events

    # ------------------------------------------------------------ raw -> clean text
    def _consume(self, final: bool) -> List[ShaperEvent]:
        events: List[ShaperEvent] = []
        while self._raw:
            if self._in_think:
                end = self._raw.find("</think>")
                if end < 0:
                    # keep a possible partial "</think>" at the tail
                    keep = _partial_suffix(self._raw, "</think>")
                    self._raw = self._raw[len(self._raw) - keep:] if keep else ""
                    return events
                self._raw = self._raw[end + len("</think>"):]
                self._in_think = False
                continue
            start = self._raw.find("<think>")
            if start >= 0:
                self._append(self._raw[:start], events)
                self._raw = self._raw[start + len("<think>"):]
                self._in_think = True
                continue
            # hold back anything that may be the start of a tag or token
            hold = 0 if final else _holdback(self._raw)
            ready, self._raw = (self._raw[: len(self._raw) - hold], self._raw[len(self._raw) - hold:]) if hold \
                else (self._raw, "")
            self._append(ready, events)
            break
        return events

    def _append(self, text: str, events: List[ShaperEvent]) -> None:
        """Clean `text` and add it to the clause buffer. A tag becomes a private-use
        marker at its place in the text, so it takes effect on the clause it sits in,
        not on whatever clause happens to be drained next."""
        if not text:
            return
        text = _SPECIAL.sub("", text).replace("</think>", "")
        out = []
        pos = 0
        for m in _TAG.finditer(text):
            out.append(text[pos:m.start()])
            pos = m.end()
            if m.group(1):
                key, val = m.group(1).lower(), m.group(2).strip()
                if key in ("emotion", "emo"):
                    out.append(self._marker("emotion", val))
                elif val:
                    out.append(self._marker("image", val))
            else:
                word = m.group(3).strip()
                low = word.lower()
                if low in self.emotions:
                    out.append(self._marker("emotion", low))
                elif low in self.gestures:
                    out.append(self._marker("gesture", low))
                else:
                    out.append(m.group(0))       # ordinary bracketed text: keep it
        out.append(text[pos:])
        self._text += "".join(out)

    def _marker(self, kind: str, value: str) -> str:
        ch = chr(_MARK_BASE + (self._mark_seq % _MARK_SPAN))
        self._mark_seq += 1
        self._actions[ch] = (kind, value)
        return ch

    def _set_emotion(self, word: str) -> None:
        w = word.strip().lower()
        self.emotion = self.emotions.get(w, self.emotion)

    # ------------------------------------------------------------ clean text -> clauses
    def _split(self, final: bool, force: bool = False) -> List[ShaperEvent]:
        events: List[ShaperEvent] = []
        if not self._started:
            if self._prefix_re is None:
                self._started = True
            else:
                stripped = self._text.lstrip()
                if not stripped:
                    return events
                m = self._prefix_re.match(self._text)
                if m:
                    self._text = self._text[m.end():]
                    self._started = True
                else:
                    longest = max(len(n) for n in [self.speaker] + self.others if n) + 6
                    if len(stripped) >= longest or final or force or any(c in stripped for c in ":：\n"):
                        self._started = True
                    else:
                        return events
        if self._other_re is not None:
            m = self._other_re.search(self._text)
            if m:
                self._text = self._text[: m.start()]
                events += self._drain(final=True)
                self._stopped = True
                events.append(ShaperEvent("stop", value="other speaker"))
                return events
        events += self._drain(final=final or force)
        return events

    def _drain(self, final: bool) -> List[ShaperEvent]:
        events: List[ShaperEvent] = []
        while True:
            cut = _find_cut(self._text, self.min_chars, self.soft_max, self.hard_max, final)
            if cut is None:
                break
            piece, self._text = self._text[:cut], self._text[cut:]
            events += self._emit(piece)
        if final and self._text:
            events += self._emit(self._text)
            self._text = ""
        return events

    def _emit(self, piece: str) -> List[ShaperEvent]:
        """Markers before the first spoken character act before the clause
        (emotion, gesture, image); markers after it attach gestures to the clause
        and change the emotion from the next clause on."""
        before: List[tuple] = []
        after: List[tuple] = []
        chars: List[str] = []
        seen_text = False
        for ch in piece:
            act = self._actions.pop(ch, None)
            if act is not None:
                (after if seen_text else before).append(act)
                continue
            if ch.isalnum():
                seen_text = True
            chars.append(ch)
        events: List[ShaperEvent] = []
        for kind, value in before:
            if kind == "emotion":
                self._set_emotion(value)
            elif kind == "gesture":
                self._pending_gestures.append(value)
            else:
                events.append(ShaperEvent("image", value=value))
        text = " ".join("".join(chars).split()).strip("*_ ")
        late_images = []
        for kind, value in after:
            if kind == "gesture":
                self._pending_gestures.append(value)
            elif kind == "image":
                late_images.append(value)
        if text and any(c.isalnum() for c in text):
            clause = Clause(text=text, emotion=self.emotion, gestures=self._pending_gestures,
                            is_question=bool(_QUESTION_END.search(text)), index=self._index)
            self._pending_gestures = []
            self._index += 1
            self.spoken.append(text)
            events.append(ShaperEvent("clause", clause=clause))
        for kind, value in after:
            if kind == "emotion":
                self._set_emotion(value)
        events += [ShaperEvent("image", value=v) for v in late_images]
        return events

    def pending_gestures(self) -> List[str]:
        """Gestures that came after the last clause (for example a closing [nod])."""
        out, self._pending_gestures = self._pending_gestures, []
        return out


# ---------------------------------------------------------------- helpers
def _partial_suffix(s: str, token: str) -> int:
    """Length of the longest suffix of s that is a proper prefix of token."""
    for n in range(min(len(token) - 1, len(s)), 0, -1):
        if s.endswith(token[:n]):
            return n
    return 0


def _holdback(s: str) -> int:
    """How many trailing characters might still become a tag, <think> or special token."""
    hold = 0
    dbl = s.rfind("[[")
    if dbl >= 0 and "]]" not in s[dbl:] and len(s) - dbl <= 200:
        hold = len(s) - dbl
    lb = s.rfind("[")
    if lb >= 0 and "]" not in s[lb:] and len(s) - lb <= 40:
        hold = max(hold, len(s) - lb)
    la = s.rfind("<")
    if la >= 0 and ">" not in s[la:] and len(s) - la <= 20:
        hold = max(hold, len(s) - la)
    return hold


def _weight(text: str) -> int:
    """Spoken length for the minimum-clause rule: a Hangul syllable counts as two
    letters, so "좋아요." (3 syllables) is long enough to say on its own and "네." is not."""
    return sum(2 if "\uac00" <= ch <= "\ud7a3" else 1 for ch in text if ch.isalnum())


def _find_cut(text: str, min_chars: int, soft_max: int, hard_max: int, final: bool) -> Optional[int]:
    """Index just past a clause boundary, or None to wait for more text."""
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch in _ENDERS or ch == "\n":
            j = i + 1
            while j < n and (text[j] in _ENDERS or text[j] in _CLOSERS):
                j += 1
            # a boundary needs the next character (so "3.5" and "..." are not cut) unless final
            if j >= n and not final and ch != "\n":
                return None
            if ch == "." and j < n and text[j].isdigit() and i > 0 and text[i - 1].isdigit():
                i = j
                continue
            if j < n and not text[j].isspace() and ch != "\n" and text[j] not in _CLOSERS:
                i = j
                continue
            if _weight(text[:j]) >= min_chars:
                return j
            i = j
            continue
        i += 1
    if n > soft_max:
        for sep in (", ", "，", "、", "; "):
            k = text.rfind(sep, min_chars, soft_max)
            if k > 0:
                return k + len(sep)
    if n > hard_max:
        k = text.rfind(" ", min_chars, hard_max)
        return (k + 1) if k > 0 else hard_max
    return None

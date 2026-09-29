"""TurnPolicy: when a spoken turn ends, and whether a reply repeats what was said.

From little-gemma: a turn ends when the speaker asks a question (-end-on-question),
so the floor passes instead of the model answering itself, and every turn has a
hard cap (SERVE_GEN) so a runaway reply cannot hold the floor. The repetition
guard is new: autonomous multi-party loops drift into characters echoing each
other, and the cheapest fix is to notice it and stop the clause from being spoken.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from chatup.shaper import Clause


def _grams(text: str, n: int = 3) -> set:
    t = "".join(ch for ch in text.lower() if ch.isalnum())
    if len(t) <= n:
        return {t} if t else set()
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def similarity(a: str, b: str, n: int = 3) -> float:
    """Character n-gram Jaccard: script-agnostic, works for Korean without a tokenizer.
    Trigrams (default) for "is this the same sentence"; bigrams for short chatter."""
    ga, gb = _grams(a, n), _grams(b, n)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def max_similarity(text: str, others: Iterable[str]) -> float:
    return max((similarity(text, o) for o in others), default=0.0)


@dataclass
class TurnPolicy:
    end_on_question: bool = True
    max_clauses: int = 4
    max_chars: int = 220
    repeat_threshold: float = 0.6     # clause vs recent lines: drop it above this
    min_repeat_chars: int = 8         # short clauses ("네.", "그래요?") are allowed to repeat
    recent_window: int = 8            # how many past lines the guard compares against

    def check(self, clause: Clause, spoken: Sequence[str], recent: Sequence[str]) -> str:
        """Decide what to do with a clause before it is spoken.

        spoken: clauses already spoken in this turn. recent: past lines of the conversation.
        Returns "speak", "speak_last" (speak it, then end the turn), "drop" (skip it,
        the turn continues) or "stop" (skip it and end the turn)."""
        text = clause.text
        if len(text) >= self.min_repeat_chars:
            if max_similarity(text, spoken) >= self.repeat_threshold:
                return "stop"                   # looping inside its own turn
            if max_similarity(text, list(recent)[-self.recent_window:]) >= self.repeat_threshold:
                return "drop"
        chars = sum(len(s) for s in spoken) + len(text)
        if len(spoken) >= self.max_clauses or chars > self.max_chars + 40:
            return "stop"
        if self.end_on_question and clause.is_question:
            return "speak_last"
        if len(spoken) + 1 >= self.max_clauses or chars >= self.max_chars:
            return "speak_last"
        return "speak"

    def is_repeat_turn(self, text: str, recent: Sequence[str]) -> bool:
        """Whole-turn check, for replies produced without streaming."""
        return len(text) >= self.min_repeat_chars and \
            max_similarity(text, list(recent)[-self.recent_window:]) >= self.repeat_threshold


def loop_score(lines: List[str], window: int = 6) -> float:
    """Mean pairwise similarity of the last `window` lines: near 0 for a moving
    conversation, rising as characters paraphrase each other. A cheap pre-check;
    the judge's stuck question decides."""
    tail = [l for l in lines[-window:] if l]
    if len(tail) < 3:
        return 0.0
    pairs = [(i, j) for i in range(len(tail)) for j in range(i + 1, len(tail))]
    return sum(similarity(tail[i], tail[j], n=2) for i, j in pairs) / len(pairs)

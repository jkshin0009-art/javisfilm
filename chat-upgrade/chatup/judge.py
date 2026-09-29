"""ConversationJudge: the decisions a looping multi-party chatbot makes between
turns, asked as Jev-style typed questions to the chatbot's own LLM.

Each method returns a Decision (answer, probability, level). The loop acts on it
only above a threshold and otherwise falls back to a plain rule, the Jev pattern
of "typed question -> typed answer with confidence -> accept / fall back". The
questions are Korean because the conversation is; the answer scaffold stays in
English (A/B/C, Yes/No) because that is what the readout reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from chatup.decide import Decider, Decision, Question

SILENCE = "아무도 말하지 않는다 (잠시 조용히)"
EVERYONE = "모두에게 / 특정한 사람 없음"

# should_speak asks what state the conversation is in, which the model can read off
# the last lines, instead of "is it natural to speak", which it could not (probe:
# p 0.51 / 0.52 on both test cases). Each state maps to speak or wait.
STATE_WAITING = "등장인물이 사용자에게 묻거나 말을 걸었고, 사용자의 대답을 기다리는 중이다"
STATE_ONGOING = "등장인물들이 이야기하던 중이고, 이어서 할 말이 남아 있다"
STATE_WRAPPED = "한 이야기가 마무리되어, 새 화제를 꺼낼 때다"
STATE_RESTING = "사용자가 쉬자고 하거나, 조용히 해 달라고 했다"
CONVERSATION_STATES = (STATE_WAITING, STATE_ONGOING, STATE_WRAPPED, STATE_RESTING)
SPEAK_STATES = (STATE_ONGOING, STATE_WRAPPED)

DEFAULT_ACTIONS = (
    "대화를 그대로 이어간다",
    "지금 이야기하는 장면을 이미지로 만든다",
    "지금 나온 아이디어를 시나리오 메모로 남긴다",
    "사용자에게 의견을 묻는다",
)

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "next_speaker": 0.55,
    "should_speak": 0.6,
    "addressed": 0.6,
    "route": 0.7,
    "emotion": 0.5,
    "stuck": 0.7,
    "wants_stop": 0.8,
    "wants_image": 0.8,
    "reply_bad": 0.8,
}


@dataclass
class Line:
    speaker: str
    text: str
    note: str = ""          # e.g. "끼어듦" when the line was cut off by the user

    def render(self) -> str:
        return f"{self.speaker}: {self.text}" + (f" ({self.note})" if self.note else "")


def format_state(lines: Sequence[Line], roster: str = "", max_lines: int = 12,
                 max_chars: int = 2400, extra: str = "") -> str:
    """The state a decision sees: who is present, then the last lines."""
    body = [l.render() for l in lines[-max_lines:]]
    text = "\n".join(body)
    if len(text) > max_chars:
        text = text[-max_chars:]
        text = text[text.find("\n") + 1:] if "\n" in text else text
    parts = []
    if roster:
        parts.append("등장인물:\n" + roster.strip())
    parts.append("최근 대화:\n" + (text if text else "(아직 없음)"))
    if extra:
        parts.append(extra.strip())
    return "\n\n".join(parts)


@dataclass
class Verdict:
    """What the loop needs: the value to act on (None = fall back) and the evidence."""
    value: Optional[str]
    decision: Decision

    @property
    def acted(self) -> bool:
        return self.value is not None


class ConversationJudge:
    def __init__(self, decider: Decider, *, roster: str = "", user_name: str = "사용자",
                 thresholds: Optional[Dict[str, float]] = None, actions: Sequence[str] = DEFAULT_ACTIONS,
                 max_lines: int = 12) -> None:
        self.decider = decider
        self.roster = roster
        self.user_name = user_name
        self.th = dict(DEFAULT_THRESHOLDS)
        self.th.update(thresholds or {})
        self.actions = tuple(actions)
        self.max_lines = max_lines

    def _state(self, lines: Sequence[Line], extra: str = "") -> str:
        return format_state(lines, self.roster, self.max_lines, extra=extra)

    # ------------------------------------------------------------ floor
    def next_speaker(self, lines: Sequence[Line], candidates: Sequence[str],
                     allow_silence: bool = False) -> Verdict:
        """Who should talk next. None = not sure (use the rotation rule)."""
        opts = list(candidates) + ([SILENCE] if allow_silence else [])
        q = Question.choice("대화의 흐름으로 볼 때, 다음에 말하는 것이 가장 자연스러운 사람은 누구인가? "
                            "질문을 받은 사람, 이름이 불린 사람, 할 말이 가장 분명한 사람을 우선한다.",
                            opts, name="next_speaker")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(d.accept(self.th["next_speaker"]), d)

    def should_speak(self, lines: Sequence[Line], idle_seconds: float = 0.0) -> Verdict:
        """Autonomous speech gate. value "Yes"/"No" (None = not sure); the state the
        judge read is decision.answer, so a caller can add a new-topic note when it
        is STATE_WRAPPED."""
        q = Question.choice("최근 대화를 보고, 지금 대화가 어떤 상태인지 고른다. 마지막 줄이 누구의 말이고 "
                            "무엇으로 끝났는지를 가장 중요하게 본다.", CONVERSATION_STATES, name="conversation_state")
        extra = f"({self.user_name}는 {idle_seconds:.0f}초째 말이 없다.)" if idle_seconds else ""
        d = self.decider.decide(self._state(lines, extra=extra), q)
        return Verdict(_group_verdict(d, SPEAK_STATES, self.th["should_speak"]), d)

    def addressed(self, lines: Sequence[Line], candidates: Sequence[str]) -> Verdict:
        """Whom the user's last line was meant for. EVERYONE counts as an answer."""
        q = Question.choice(f"{self.user_name}의 마지막 말은 누구에게 한 말인가?",
                            list(candidates) + [EVERYONE], name="addressed")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(d.accept(self.th["addressed"]), d)

    # ------------------------------------------------------------ what to do
    def route(self, lines: Sequence[Line]) -> Verdict:
        """Talk on, or hand the moment to another lane (image, scenario note, ask the user)."""
        q = Question.choice("지금 시점에 이 대화 프로그램이 할 일로 가장 알맞은 것은?", self.actions, name="route")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(d.accept(self.th["route"]), d)

    def wants_image(self, lines: Sequence[Line]) -> Verdict:
        """Image gate for a keyword trigger: does the user's last line ask for a new
        picture? "장면" or "보여" alone do not make it a picture request."""
        q = Question.noul(f"{self.user_name}의 마지막 말이 그림(이미지)을 새로 그려서 보여 달라는 요청인가? "
                          "'장면', '보여' 같은 말이 들어 있어도 그림을 원하는 것이 아니면 아니다.",
                          name="wants_image")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(_noul_verdict(d, self.th["wants_image"]), d)

    def stuck(self, lines: Sequence[Line]) -> Verdict:
        q = Question.noul("최근 대화가 같은 말을 되풀이하거나, 새로운 내용 없이 제자리를 맴돌고 있는가?",
                          name="stuck")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(_noul_verdict(d, self.th["stuck"]), d)

    def wants_stop(self, lines: Sequence[Line]) -> Verdict:
        q = Question.noul(f"{self.user_name}가 마지막 말에서 대화를 멈추거나, 조용히 하거나, 그만하라고 요청하는가?",
                          name="wants_stop")
        d = self.decider.decide(self._state(lines), q)
        return Verdict(_noul_verdict(d, self.th["wants_stop"]), d)

    # ------------------------------------------------------------ the reply itself
    def emotion(self, speaker: str, text: str, emotions: Sequence[str], lines: Sequence[Line] = ()) -> Verdict:
        """Emotion for the voice when the model gave no tag."""
        q = Question.choice(f"{speaker}가 방금 한 말(마지막 줄)을 소리 내어 말할 때 가장 알맞은 감정은?",
                            list(emotions), name="emotion")
        state_lines = list(lines[-4:]) + [Line(speaker, text)]
        d = self.decider.decide(self._state(state_lines), q)
        return Verdict(d.accept(self.th["emotion"]), d)

    def reply_bad(self, lines: Sequence[Line], speaker: str, reply: str) -> Verdict:
        """Quality gate before a non-streamed reply is spoken: Yes = regenerate."""
        q = Question.noul(f"마지막 줄의 {speaker}의 대답이 앞에서 이미 한 말을 되풀이하거나, 다른 사람의 대사까지 "
                          "대신 말하거나, 흐름과 상관없는 말인가?", name="reply_bad")
        d = self.decider.decide(self._state(list(lines) + [Line(speaker, reply)]), q)
        return Verdict(_noul_verdict(d, self.th["reply_bad"]), d)

    def ask(self, lines: Sequence[Line], q: Question, threshold: float) -> Verdict:
        """Any other typed question the project wants to add."""
        d = self.decider.decide(self._state(lines), q)
        if q.kind == "noul":
            return Verdict(_noul_verdict(d, threshold), d)
        return Verdict(d.accept(threshold), d)


def _group_verdict(d: Decision, yes_options: Sequence[str], threshold: float) -> Optional[str]:
    """"Yes" when the options in yes_options together reach threshold, "No" when
    the others do, else None."""
    if d.answer is None or d.confidence is None:
        return None
    p_yes = sum(d.p(o) for o in yes_options)
    if p_yes >= threshold:
        return "Yes"
    if 1.0 - p_yes >= threshold:
        return "No"
    return None


def _noul_verdict(d: Decision, threshold: float) -> Optional[str]:
    """"Yes" when P(Yes) >= threshold, "No" when P(No) >= threshold, else None."""
    if d.answer is None:
        return None
    if d.confidence is None:
        return None
    if d.yes >= threshold:
        return "Yes"
    if d.p("No") >= threshold:
        return "No"
    return None

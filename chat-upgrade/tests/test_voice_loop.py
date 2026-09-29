import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatup.decide import Decision  # noqa: E402
from chatup.judge import EVERYONE, SILENCE, Line, Verdict  # noqa: E402
from chatup.llm import Cancelled  # noqa: E402
from chatup.loop import ConversationLoop, Hooks, LoopConfig, Persona  # noqa: E402
from chatup.shaper import Clause  # noqa: E402
from chatup.voice import NullPlayer, VoiceBank, VoiceWorker  # noqa: E402


# ---------------------------------------------------------------- voice
def _touch(path, text=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").close()
    if text is not None:
        with open(os.path.splitext(path)[0] + ".txt", "w", encoding="utf-8") as f:
            f.write(text)


def test_voice_bank_pick_and_check(tmp_path):
    root = str(tmp_path)
    _touch(os.path.join(root, "hana", "neutral.wav"), "안녕하세요")
    _touch(os.path.join(root, "hana", "happy.wav"), "와 신난다")
    _touch(os.path.join(root, "doyun", "sad.wav"))
    bank = VoiceBank(root)
    assert bank.pick("hana", "happy").wav.endswith("happy.wav")
    assert bank.pick("hana", "happy").text == "와 신난다"
    assert bank.pick("hana", "angry").emotion == "neutral"          # falls back to neutral
    assert bank.pick("doyun", "happy").emotion == "sad"             # then to any clip
    assert bank.pick("nobody", "happy") is None
    problems = bank.check(["hana", "doyun", "mirae"])
    assert any("mirae: no reference audio" in p for p in problems)
    assert any("doyun: no neutral clip" in p for p in problems)
    assert any("doyun/sad: no transcript" in p for p in problems)
    assert not any(p.startswith("hana") for p in problems)


class FakeEngine:
    sample_rate = 1000

    def __init__(self):
        self.calls = []

    def stream(self, text, ref):
        self.calls.append((text, ref.emotion if ref else None))
        for _ in range(5):
            yield [0.0] * 20          # 5 x 20 ms


def test_voice_worker_speaks_in_order_and_cancels(tmp_path):
    root = str(tmp_path)
    _touch(os.path.join(root, "hana", "neutral.wav"), "x")
    _touch(os.path.join(root, "hana", "happy.wav"), "y")
    eng = FakeEngine()
    events = []
    w = VoiceWorker(eng, VoiceBank(root), NullPlayer(realtime=True), on_event=lambda k, j: events.append(k))
    w.say(1, "hana", Clause("하나", emotion="happy"))
    w.say(1, "hana", Clause("둘"))
    assert w.wait_idle(3)
    assert w.spoken(1) == ["하나", "둘"]
    assert eng.calls == [("하나", "happy"), ("둘", "neutral")]
    for i in range(5):
        w.say(2, "hana", Clause(f"문장 {i}"))
    time.sleep(0.15)
    w.cancel()
    assert w.wait_idle(2)
    assert len(w.spoken(2)) < 5
    assert "cut" in events
    w.say(3, "hana", Clause("다시"))                 # works again after a cancel
    assert w.wait_idle(2) and w.spoken(3) == ["다시"]
    w.close()


# ---------------------------------------------------------------- loop
class FakeLLM:
    """Replies from a script keyed by persona (read from the system prompt)."""

    def __init__(self, replies, delay=0.0):
        self.replies = replies
        self.delay = delay
        self.messages = []

    def stream_chat(self, messages, cancel=None, **kw):
        self.messages.append(messages)
        name = next(n for n in self.replies if messages[0]["content"].startswith(f"너는 {n}"))
        queue = self.replies[name]
        text = queue.pop(0) if len(queue) > 1 else queue[0]
        for ch in text:
            if cancel is not None and cancel.cancelled:
                raise Cancelled("cancelled")
            if self.delay:
                time.sleep(self.delay)
            yield ch


def V(value, name="x", p=0.9):
    d = Decision(name, "choice", [], {}, value, p, 0.5, "L0", 0.9, 0.0, 2, 1.0)
    return Verdict(value, d)


class FakeJudge:
    actions = ("대화를 그대로 이어간다", "지금 이야기하는 장면을 이미지로 만든다")

    def __init__(self, **answers):
        self.answers = answers
        self.asked = []

    def _a(self, name):
        self.asked.append(name)
        return V(self.answers.get(name), name)

    def next_speaker(self, lines, candidates, allow_silence=False):
        v = self._a("next_speaker")
        return v if v.value in list(candidates) + [SILENCE, None] else V(None)

    def addressed(self, lines, candidates):
        return self._a("addressed")

    def should_speak(self, lines, idle):
        return self._a("should_speak")

    def wants_stop(self, lines):
        return self._a("wants_stop")

    def stuck(self, lines):
        return self._a("stuck")

    def route(self, lines):
        return self._a("route")

    def emotion(self, speaker, text, emotions, lines=()):
        return self._a("emotion")


PERSONAS = [Persona("하나", "너는 하나다."), Persona("도윤", "너는 도윤이다."), Persona("미래", "너는 미래다.")]


class Rec(Hooks):
    def __init__(self):
        self.clauses, self.states, self.routes, self.images = [], [], [], []

    def on_clause(self, persona, clause):
        self.clauses.append((persona, clause.text))

    def on_state(self, state, detail=""):
        self.states.append(state)

    def on_route(self, action, verdict, lines):
        self.routes.append(action)

    def on_image(self, persona, prompt):
        self.images.append((persona, prompt))


def make(replies=None, judge=None, cfg=None, delay=0.0, voice=None):
    replies = replies or {"하나": ["조명은 다 챙겼어요."], "도윤": ["대본은 거의 끝났어요."],
                          "미래": ["장소는 강릉이 좋겠어요."]}
    hooks = Rec()
    cfg = cfg or LoopConfig(idle_seconds=0.0, gap_seconds=0.0, followups=0)
    loop = ConversationLoop(FakeLLM(replies, delay), PERSONAS, judge=judge, config=cfg, hooks=hooks, voice=voice)
    return loop, hooks


def test_user_line_goes_to_the_named_character_without_judge():
    loop, hooks = make()
    loop.user_says("미래 씨, 장소는 어디가 좋아요?")
    r = loop.step()
    assert r.persona == "미래" and hooks.clauses == [("미래", "장소는 강릉이 좋겠어요.")]
    assert [l.speaker for l in loop.lines] == ["사용자", "미래"]


def test_messages_put_own_lines_as_assistant_and_others_as_user():
    loop, _ = make()
    loop.lines = [Line("사용자", "안녕"), Line("하나", "안녕하세요"), Line("도윤", "반가워요")]
    msgs = loop.build_messages(loop.personas["하나"])
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert msgs[1]["content"] == "사용자: 안녕"
    assert msgs[3]["content"].startswith("도윤: 반가워요") and "하나의 차례" in msgs[3]["content"]
    assert "함께 있는 사람: 도윤, 미래, 사용자." in msgs[0]["content"]


def test_judge_picks_responder_and_falls_back_when_unsure():
    loop, _ = make(judge=FakeJudge(addressed="도윤", wants_stop="No"))
    loop.user_says("이번 장면 어떻게 할까?")
    assert loop.step().persona == "도윤"
    loop2, _ = make(judge=FakeJudge(addressed=EVERYONE, next_speaker=None, wants_stop="No"))
    loop2.user_says("이번 장면 어떻게 할까?")
    assert loop2.step().persona == "하나"            # least recent, first in order


def test_wants_stop_pauses_without_reply():
    loop, hooks = make(judge=FakeJudge(wants_stop="Yes"))
    loop.user_says("다들 조용히 해 줘")
    assert loop.step() is None
    assert "paused" in hooks.states
    assert loop.step() is None                      # stays quiet on its own


def test_autonomous_turns_rotate_and_stop_at_cap():
    cfg = LoopConfig(idle_seconds=0.0, gap_seconds=0.0, max_auto_turns=4, followups=0, route_every=0)
    loop, hooks = make(cfg=cfg)
    speakers = [loop.step().persona for _ in range(4)]
    assert speakers == ["하나", "도윤", "미래", "하나"]
    assert loop.step() is None and "autonomy_paused" in hooks.states
    loop.user_says("하나야")
    assert loop.step().persona == "하나"             # the user brings it back


def test_should_speak_no_waits():
    loop, _ = make(judge=FakeJudge(should_speak="No"))
    assert loop.step() is None


def test_stuck_adds_director_note_and_route_calls_hook():
    judge = FakeJudge(should_speak="Yes", stuck="Yes", route="지금 이야기하는 장면을 이미지로 만든다")
    cfg = LoopConfig(idle_seconds=0.0, gap_seconds=0.0, stuck_every=2, stuck_pre=0.0, route_every=3,
                     followups=0)
    replies = {"하나": ["그래 맞아."], "도윤": ["응 맞아."], "미래": ["맞아 그래."]}
    loop, hooks = make(replies=replies, judge=judge, cfg=cfg)
    for _ in range(3):
        loop.step()
    assert "연출 메모" in loop.llm.messages[2][-1]["content"]
    assert hooks.routes == ["지금 이야기하는 장면을 이미지로 만든다"]


def test_end_on_question_and_image_tag():
    replies = {"하나": ["[[image: 새벽 바닷가]]이 장면 어때요? 그리고 더 할 말이 있어요."],
               "도윤": ["x"], "미래": ["y"]}
    loop, hooks = make(replies=replies)
    loop.user_says("하나야")
    r = loop.step()
    assert [c.text for c in r.clauses] == ["이 장면 어때요?"]
    assert hooks.images == [("하나", "새벽 바닷가")]


def test_barge_in_records_what_was_heard():
    replies = {"하나": ["첫 문장은 여기까지입니다. 두 번째 문장은 아주 길게 이어지고 있습니다 계속 계속 계속."],
               "도윤": ["네, 말씀하세요."], "미래": ["y"]}
    loop, hooks = make(replies=replies, delay=0.01)
    loop.user_says("하나야")
    threading.Timer(0.45, lambda: loop.user_says("도윤 씨, 잠깐만요")).start()
    r = loop.step()
    assert r.interrupted
    assert loop.lines[-1].speaker == "하나" and loop.lines[-1].note == "끼어듦"
    assert loop.lines[-1].text == "첫 문장은 여기까지입니다."
    r2 = loop.step(0.5)
    assert r2.persona == "도윤"
    msgs = loop.llm.messages[-1]
    assert any("(끼어듦)" in m["content"] for m in msgs)


def test_followup_character_chimes_in():
    cfg = LoopConfig(idle_seconds=100, gap_seconds=0.0, followups=1)
    loop, hooks = make(judge=FakeJudge(addressed="하나", next_speaker="미래", wants_stop="No"), cfg=cfg)
    loop.user_says("하나야, 조명은?")
    loop.step()
    assert [p for p, _ in hooks.clauses] == ["하나", "미래"]


def test_empty_replies_stop_autonomy_after_failures():
    cfg = LoopConfig(idle_seconds=0.0, gap_seconds=0.0, max_failures=2, followups=0)
    loop, hooks = make(replies={"하나": ["<think>...</think>"], "도윤": ["[nod]"], "미래": ["  "]}, cfg=cfg)
    loop.step()
    loop.step()
    assert loop.step() is None
    assert hooks.states.count("turn_failed") == 2


def test_barge_in_during_playback_trims_to_what_was_heard(tmp_path):
    root = str(tmp_path)
    _touch(os.path.join(root, "하나", "neutral.wav"), "x")
    voice = VoiceWorker(FakeEngine(), VoiceBank(root), NullPlayer(realtime=True))   # 100 ms per clause
    replies = {"하나": ["첫 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."], "도윤": ["네."], "미래": ["y"]}
    cfg = LoopConfig(idle_seconds=100, gap_seconds=0.0, followups=0)
    loop, _ = make(replies=replies, cfg=cfg, voice=voice)
    loop.user_says("하나야")
    r = loop.step()                                  # generation ends at once; audio keeps playing
    assert not r.interrupted and loop.lines[-1].note == ""
    time.sleep(0.15)                                 # first clause heard, second playing
    loop.user_says("잠깐")
    loop.step()
    hana = [l for l in loop.lines if l.speaker == "하나"][0]
    assert hana.note == "끼어듦" and hana.text == "첫 문장입니다."
    voice.close()

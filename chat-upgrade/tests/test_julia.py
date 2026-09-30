import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatup.__main__ import main  # noqa: E402
from chatup.bridge import JudgeBridge  # noqa: E402
from chatup.decide import Question  # noqa: E402
from chatup.julia import (NOUL_TEXT, CascadeDecider, JuliaClient, JuliaDecider, JuliaError,  # noqa: E402
                          make_decider)
from chatup.llm import LLMError  # noqa: E402
from mockserver import MockJulia  # noqa: E402
from test_bridge import FakeClient  # noqa: E402


def pick(word, first_bonus=0.0):
    """Scores: the option containing `word` gets 9, others 1; the first listed gets a bonus."""
    def scores(body):
        s = [9.0 if word in o else 1.0 for o in body["options"]]
        s[0] += first_bonus
        return s
    return scores


@pytest.fixture
def julia():
    m = MockJulia().start()
    yield m
    m.stop()


def test_client_sends_state_question_options(julia):
    julia.scores = pick("b")
    p = JuliaClient(julia.url + "/predict").probabilities("st", "q?", ["a", "b"])
    assert julia.requests[-1] == {"state": "st", "question": "q?", "options": ["a", "b"]}
    assert p == pytest.approx([0.1, 0.9])


def test_client_errors_are_llm_errors(julia):
    c = JuliaClient(julia.url)
    julia.status = 500
    with pytest.raises(JuliaError):
        c.probabilities("s", "q", ["a", "b"])
    julia.status = 200
    julia.raw = {"probabilities": [1.0]}
    with pytest.raises(JuliaError):
        c.probabilities("s", "q", ["a", "b"])
    with pytest.raises(LLMError):
        JuliaClient("http://127.0.0.1:9", timeout=1).probabilities("s", "q", ["a", "b"])


def test_choice_reads_both_orders_and_cancels_position_bias(julia):
    julia.scores = pick("도윤", first_bonus=12.0)       # strong pull toward whatever is listed first
    d = JuliaDecider(JuliaClient(julia.url)).decide("state", Question.choice("누구?", ["하나", "도윤", "미래"]))
    assert d.answer == "도윤" and d.level == "julia" and d.calls == 2
    assert [r["options"] for r in julia.requests] == [["하나", "도윤", "미래"], ["미래", "도윤", "하나"]]
    assert d.confidence == pytest.approx(d.p("도윤")) and abs(sum(d.distribution.values()) - 1) < 1e-4


def test_noul_keeps_yes_no_names(julia):
    julia.scores = pick("Yes")
    d = JuliaDecider(JuliaClient(julia.url), orders=1).decide("s", Question.noul("그런가?"))
    assert julia.requests[-1]["options"] == [NOUL_TEXT["Yes"], NOUL_TEXT["No"]]
    assert d.answer == "Yes" and d.yes == pytest.approx(0.9) and d.calls == 1


def test_score_value_is_expected_level(julia):
    julia.scores = lambda body: [1.0, 1.0, 8.0]
    d = JuliaDecider(JuliaClient(julia.url), orders=1).decide("s", Question.score("얼마나?", ["낮음", "중간", "높음"]))
    assert d.answer == "높음" and d.value == pytest.approx(0.1 * 1 + 0.8 * 2)


def test_images_are_not_for_julia(julia):
    d = JuliaDecider(JuliaClient(julia.url)).decide("s", Question.noul("q"), images=["x.png"])
    assert d.level == "none" and d.answer is None and not julia.requests


def test_decisions_log(julia, tmp_path):
    log = tmp_path / "d.jsonl"
    JuliaDecider(JuliaClient(julia.url), log_path=str(log)).decide("state text", Question.noul("q"))
    rec = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert rec["level"] == "julia" and rec["state"] == "state text"


class CountingLLM:
    def __init__(self, inner):
        self.inner, self.n = inner, 0

    def decide(self, state, q, images=()):
        self.n += 1
        return self.inner.decide(state, q, images)


def test_cascade_asks_llm_only_when_julia_is_unsure(julia):
    from chatup.decide import Decider
    llm = CountingLLM(Decider(FakeClient(want="미래", p=0.95)))
    c = CascadeDecider(JuliaDecider(JuliaClient(julia.url)), llm, trust=0.8)
    q = Question.choice("누구?", ["하나", "도윤", "미래"])
    julia.scores = pick("도윤")                          # 9/11 = 0.82: sure enough
    d = c.decide("s", q)
    assert d.answer == "도윤" and d.level == "julia" and llm.n == 0
    julia.scores = lambda body: [1.0, 1.0, 1.0]         # unsure
    d = c.decide("s", q)
    assert d.answer == "미래" and d.level == "L0" and llm.n == 1 and "asked llm" in d.note
    assert d.calls >= 3                                  # julia's two orders + the llm's


def test_cascade_when_julia_is_down_or_llm_fails(julia):
    from chatup.decide import Decider
    q = Question.noul("q")
    down = JuliaDecider(JuliaClient("http://127.0.0.1:9", timeout=1))
    d = CascadeDecider(down, Decider(FakeClient(want="Yes")), trust=0.9).decide("s", q)
    assert d.answer == "Yes" and "julia failed" in d.note
    julia.scores = lambda body: [6.0 if "Yes" in o else 4.0 for o in body["options"]]
    d = CascadeDecider(JuliaDecider(JuliaClient(julia.url)), Decider(FakeClient(fail=True))).decide("s", q)
    assert d.level == "julia" and d.answer == "Yes"     # llm down: julia's own answer comes back
    with pytest.raises(LLMError):
        CascadeDecider(down, Decider(FakeClient(fail=True))).decide("s", q)


def test_make_decider_names():
    with pytest.raises(ValueError):
        make_decider("gpt")
    with pytest.raises(ValueError):
        make_decider("cascade")
    assert isinstance(make_decider("julia"), JuliaDecider)


def test_bridge_backend_from_env(julia, tmp_path):
    julia.scores = pick("도윤")
    env = {"FJ_JUDGE": "act", "FJ_JUDGE_BACKEND": "julia", "FJ_JULIA_URL": julia.url,
           "FJ_JUDGE_LOG": str(tmp_path)}
    llm = FakeClient(want="하나")
    b = JudgeBridge.from_env("http://unused", env=env, client=llm)
    assert b.speaker([("사용자", "누가 말할래?")], ["하나", "도윤"], baseline="하나") == "도윤"
    assert llm.calls == 0
    rec = json.loads((tmp_path / "hooks.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert rec["backend"] == "julia" and rec["level"] == "julia" and rec["final"] == "도윤"


def test_bridge_cascade_falls_back_to_llm(julia, tmp_path):
    julia.scores = lambda body: [1.0] * len(body["options"])
    b = JudgeBridge("http://unused", "act", client=FakeClient(want="하나"), backend="cascade",
                    julia_url=julia.url, log_dir=str(tmp_path))
    assert b.speaker([("사용자", "누가 말할래?")], ["하나", "도윤"], baseline="도윤") == "하나"


def test_probe_with_julia_backend(julia, capsys):
    julia.scores = lambda body: [3.0] + [1.0] * (len(body["options"]) - 1)
    assert main(["probe", "--backend", "julia", "--julia-url", julia.url, "--url", "http://127.0.0.1:9"]) == 0
    out = capsys.readouterr().out
    assert "RESULT backend: julia" in out and "julia x19" in out

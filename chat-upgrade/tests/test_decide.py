import json
import math
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatup.decide import (Decider, Question, QuestionError, build_user, cyclic_shifts,  # noqa: E402
                           read_labels, spread_order)
from chatup.llm import FirstToken  # noqa: E402


class BiasedModel:
    """Fake LLM: logit(label at position j) = preference(option shown there) + bias[j].
    That is the additive position bias the rotations are meant to cancel."""

    def __init__(self, prefs, bias=(), noul_yes=0.0, noul_first_bias=0.0, mass=0.95, logprobs=True,
                 text="A", extra=()):
        self.prefs = prefs
        self.bias = list(bias)
        self.noul_yes = noul_yes
        self.noul_first_bias = noul_first_bias
        self.mass = mass
        self.logprobs = logprobs
        self.text = text
        self.extra = list(extra)
        self.calls = []

    def first_token_logprobs(self, messages, top_n=20):
        user = messages[-1]["content"]
        self.calls.append(user)
        if not self.logprobs:
            return FirstToken(self.text, [])
        m = re.search(r"Answer (Yes|No) or (Yes|No)\.", user)
        if m:
            first = m.group(1)
            z = {"Yes": self.noul_yes, "No": 0.0}
            z[first] += self.noul_first_bias
            labels = ["Yes", "No"]
            logits = [z["Yes"], z["No"]]
        else:
            opts = re.findall(r"^([A-Z]|\d+)\. (.*)$", user, re.M)
            labels = [l for l, _ in opts]
            logits = [self.prefs.get(text, 0.0) + (self.bias[j] if j < len(self.bias) else 0.0)
                      for j, (_, text) in enumerate(opts)]
        mx = max(logits)
        ex = [math.exp(x - mx) for x in logits]
        s = sum(ex)
        top = [(lab, math.log(self.mass * e / s)) for lab, e in zip(labels, ex)]
        top += [("<think>", math.log(max(1e-6, 1 - self.mass)))] + self.extra
        top.sort(key=lambda t: t[1], reverse=True)
        return FirstToken(top[0][0], top[:top_n])


def test_question_validation():
    with pytest.raises(QuestionError):
        Question.choice("q", ["one"])
    with pytest.raises(QuestionError):
        Question.choice("q", ["a", "a"])
    with pytest.raises(QuestionError):
        Question.score("q", ["x"])
    q = Question.choice("q", ["x", "y", "z"], name="n")
    assert q.labels() == ["A", "B", "C"] and q.id == "n"
    assert Question.noul("q").labels() == ["Yes", "No"]
    assert Question.score("q", ["lo", "mid", "hi"]).labels() == ["1", "2", "3"]
    assert Question.choice("q", ["x", "y"]).id.startswith("q_")


def test_orders():
    assert cyclic_shifts(3) == [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
    for k in range(1, 12):
        assert sorted(spread_order(k)) == list(range(k))
    assert spread_order(4)[:2] == [0, 2]


def test_build_user_layout():
    q = Question.choice("누가?", ["하나", "도윤"])
    u = build_user("하나: 안녕", q, [1, 0])
    assert "A. 도윤" in u and "B. 하나" in u and u.endswith("Answer with the letter only.")
    assert "(empty)" in build_user("", Question.noul("q"), [1, 0])
    assert "Answer No or Yes." in build_user("s", Question.noul("q"), [1, 0])


def test_read_labels_merges_spellings_and_floors_missing():
    q = Question.choice("q", ["x", "y", "z"])
    top = [("A", math.log(0.5)), (" A", math.log(0.2)), ("B", math.log(0.1)), ("hello", math.log(0.05))]
    lps, mass, found = read_labels(top, q)
    assert found == 2
    assert math.isclose(math.exp(lps[0]), 0.7, rel_tol=1e-9)
    assert math.isclose(mass, 0.8, rel_tol=1e-9)
    assert math.exp(lps[2]) == pytest.approx(0.025)        # half of the smallest listed


def test_read_labels_korean_yes_no():
    q = Question.noul("q")
    lps, mass, _ = read_labels([("네", math.log(0.6)), ("아니요", math.log(0.3))], q)
    assert math.exp(lps[0]) == pytest.approx(0.6) and math.exp(lps[1]) == pytest.approx(0.3)


def test_rotation_cancels_position_bias():
    prefs = {"하나": 0.0, "도윤": 1.0, "미래": 0.0}
    q = Question.choice("다음은?", ["하나", "도윤", "미래"], name="ns")
    raw = Decider(BiasedModel(prefs, bias=[2.5, 0, 0]), rotations=1, prior_correction=False)
    d_raw = raw.decide("s", q)
    assert d_raw.answer == "하나" and d_raw.level == "raw"           # fooled by position A
    full = Decider(BiasedModel(prefs, bias=[2.5, 0, 0]), rotations="full", prior_correction=False)
    d = full.decide("s", q)
    assert d.answer == "도윤" and d.level == "L0" and d.calls == 3
    assert d.flips > 0                                                # the orders disagreed
    assert sum(d.distribution.values()) == pytest.approx(1.0, abs=1e-4)


def test_adaptive_stops_early_on_clear_case():
    prefs = {"a": 6.0, "b": 0.0, "c": 0.0, "d": 0.0, "e": 0.0}
    model = BiasedModel(prefs)
    d = Decider(model).decide("s", Question.choice("q", list(prefs)))
    assert d.answer == "a" and d.calls == 2 and d.confidence > 0.9


def test_noul_reads_both_phrasings():
    model = BiasedModel({}, noul_yes=2.0, noul_first_bias=1.0)
    d = Decider(model).decide("s", Question.noul("q", name="stop"))
    assert d.answer == "Yes" and d.calls == 2 and d.yes > 0.8
    assert d.accept(0.8) == "Yes" and d.accept(0.99) is None
    one = Decider(BiasedModel({}, noul_yes=-2.0), rotations=1).decide("s", Question.noul("q"))
    assert one.calls == 1 and one.answer == "No"


def test_score_expected_value():
    prefs = {"낮음": 0.0, "보통": 2.0, "높음": 0.0}
    d = Decider(BiasedModel(prefs)).decide("s", Question.score("q", ["낮음", "보통", "높음"]))
    assert d.answer == "보통" and d.calls == 1 and d.value == pytest.approx(1.0, abs=1e-6)


def test_no_logprobs_falls_back_to_parsing():
    q = Question.choice("q", ["x", "y"])
    d = Decider(BiasedModel({}, logprobs=False, text="B")).decide("s", q)
    assert d.level == "parsed" and d.answer == "y" and d.confidence is None
    assert d.accept(0.5) is None and d.accept(0.5, allow_parsed=True) == "y"
    d2 = Decider(BiasedModel({}, logprobs=False, text="음... 글쎄요")).decide("s", q)
    assert d2.level == "none" and d2.answer is None


def test_low_label_mass_means_no_decision():
    q = Question.choice("q", ["x", "y"])
    d = Decider(BiasedModel({"x": 3.0}, mass=0.05)).decide("s", q)
    assert d.level == "none" and d.answer is None and "thinking" in d.note


class StateModel(BiasedModel):
    """Preference comes from the state ("fav=y"), so a batch of states has varied answers."""

    def first_token_logprobs(self, messages, top_n=20):
        fav = re.search(r"fav=(\w)", messages[-1]["content"]).group(1)
        self.prefs = {k: (0.4 if k == fav else 0.0) for k in "xyz"}
        return super().first_token_logprobs(messages, top_n)


def test_prior_correction_after_enough_decisions():
    # the same strong preference for position A in every state; the batch prior learns it
    dec = Decider(StateModel({}, bias=[3.0, 0, 0]), rotations=1, min_prior_n=6)
    q = Question.choice("q", ["x", "y", "z"], name="p")
    assert dec.decide("fav=y", q).answer == "x"          # raw readout follows position A
    for fav in "xyzxyz":
        dec.decide(f"fav={fav}", q)
    assert dec.decide("fav=y", q).answer == "y"
    assert dec.decide("fav=z", q).answer == "z"
    # noul is left alone: its prior is the answer's base rate, not a position habit
    assert Decider(BiasedModel({}, noul_yes=-2.0))._prior_for(Question.noul("q")) is None


def test_decision_log(tmp_path):
    path = tmp_path / "logs" / "d.jsonl"
    dec = Decider(BiasedModel({"x": 2.0, "y": 0.0}), log_path=str(path))
    dec.decide("state text", Question.choice("q", ["x", "y"], name="logged"))
    rec = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert rec["name"] == "logged" and rec["answer"] == "x" and rec["state"] == "state text"

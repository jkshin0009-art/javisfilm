import json
import math
import os
import re
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatup.__main__ import main  # noqa: E402
from chatup.bridge import JudgeBridge, summarize, to_lines  # noqa: E402
from chatup.judge import STATE_WAITING, STATE_WRAPPED, Line  # noqa: E402
from chatup.llm import FirstToken, LLMError  # noqa: E402
from chatup.shaper import ThinkFilter  # noqa: E402


class FakeClient:
    """Picks the option whose text contains `want` (or Yes/No) with probability p."""

    def __init__(self, want="Yes", p=0.95, delay=0.0, fail=False):
        self.want, self.p, self.delay, self.fail = want, p, delay, fail
        self.calls = 0
        self.lock = threading.Lock()

    def first_token_logprobs(self, messages, top_n=20):
        with self.lock:
            self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise LLMError("cannot reach server")
        user = messages[-1]["content"]
        if re.search(r"Answer (Yes|No) or (Yes|No)\.", user):
            other = "No" if self.want == "Yes" else "Yes"
            return FirstToken(self.want, [(self.want, math.log(self.p)), (other, math.log(1 - self.p))])
        opts = re.findall(r"^([A-Z])\. (.*)$", user, re.M)
        rest = (1 - self.p) / max(1, len(opts) - 1)
        top = [(lab, math.log(self.p if self.want in text else rest)) for lab, text in opts]
        top.sort(key=lambda t: t[1], reverse=True)
        return FirstToken(top[0][0], top)


H = [("사용자", "3번 장면에서 도윤이는 왜 화를 냈어?"), ("하나", "그건요...")]


def bridge(client, modes, tmp_path=None, **kw):
    return JudgeBridge("http://unused", modes, client=client,
                       log_dir=str(tmp_path) if tmp_path else None, **kw)


def records(tmp_path):
    with open(os.path.join(str(tmp_path), "hooks.jsonl"), encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def test_to_lines_accepts_common_shapes():
    lines = to_lines([Line("하나", "a"), ("도윤", "b"), {"role": "user", "content": "c"},
                      {"name": "미래", "text": "d"}, {"role": "assistant", "content": "  "}])
    assert [(l.speaker, l.text) for l in lines] == [("하나", "a"), ("도윤", "b"), ("사용자", "c"), ("미래", "d")]


def test_off_asks_nothing():
    c = FakeClient()
    b = bridge(c, "off")
    assert b.image(H, baseline=True) is True
    assert b.speaker(H, ["하나", "도윤"], baseline="하나") == "하나"
    assert c.calls == 0


def test_act_uses_confident_answer_and_logs(tmp_path):
    b = bridge(FakeClient(want="No"), "act", tmp_path)
    assert b.image(H, baseline=True) is False             # the keyword matched, the judge says no
    r = records(tmp_path)[-1]
    assert r["hook"] == "image" and r["baseline"] is True and r["final"] is False and r["changed"]
    assert r["level"] == "L0" and r["calls"] == 2 and "state" not in r


def test_act_keeps_baseline_when_unsure(tmp_path):
    b = bridge(FakeClient(want="No", p=0.6), "act", tmp_path)
    assert b.image(H, baseline=True) is True
    assert records(tmp_path)[-1]["value"] is None


def test_speaker_only_returns_a_candidate(tmp_path):
    b = bridge(FakeClient(want="도윤"), {"default": "off", "speaker": "act"}, tmp_path)
    assert b.speaker(H, ["하나", "도윤", "미래"], baseline="미래") == "도윤"
    assert b.speaker(H, ["하나"], baseline="하나") == "하나"          # nothing to choose
    b2 = bridge(FakeClient(want="없는 사람"), "act")
    assert b2.speaker(H, ["하나", "도윤"], baseline="하나") == "하나"


def test_addressed_everyone_keeps_baseline():
    b = bridge(FakeClient(want="모두에게"), "act")
    assert b.addressed(H, ["하나", "도윤"], baseline=None) is None
    b2 = bridge(FakeClient(want="하나"), "act")
    assert b2.addressed(H, ["하나", "도윤"], baseline=None) == "하나"


def test_autonomy_reads_conversation_state(tmp_path):
    b = bridge(FakeClient(want=STATE_WAITING), "act", tmp_path)
    assert b.autonomy(H, baseline=True) is False
    assert records(tmp_path)[-1]["judge"] == STATE_WAITING
    b2 = bridge(FakeClient(want=STATE_WRAPPED), "act")
    assert b2.autonomy(H, baseline=True) is True


def test_errors_and_timeouts_fall_back(tmp_path):
    b = bridge(FakeClient(fail=True), "act", tmp_path)
    assert b.stuck(H, baseline=False) is False
    assert records(tmp_path)[-1]["error"].startswith("LLMError")
    b2 = bridge(FakeClient(want="Yes", delay=0.5), "act", tmp_path, timeout=0.1)
    t0 = time.monotonic()
    assert b2.stuck(H, baseline=False) is False
    assert time.monotonic() - t0 < 0.4
    assert records(tmp_path)[-1]["error"] == "timeout"


def test_observe_returns_baseline_at_once_and_logs_later(tmp_path):
    c = FakeClient(want="No", delay=0.2)
    b = bridge(c, "observe", tmp_path, max_pending=2)
    t0 = time.monotonic()
    assert b.image(H, baseline=True) is True
    assert time.monotonic() - t0 < 0.1
    b.image(H, baseline=True)
    b.image(H, baseline=True)                               # third one: queue full, skipped
    assert b.wait_observers(5)
    rs = records(tmp_path)
    assert sum(1 for r in rs if r.get("error") == "skipped: busy") == 1
    done = [r for r in rs if not r.get("error")]
    assert len(done) == 2 and all(r["value"] is False and r["final"] is True and not r["changed"] for r in done)


def test_modes_from_env_and_file(tmp_path):
    env = {"FJ_JUDGE": "observe", "FJ_JUDGE_IMAGE": "act", "FJ_JUDGE_LOG": str(tmp_path)}
    b = JudgeBridge.from_env("http://unused", env=env, client=FakeClient())
    assert b.mode("image") == "act" and b.mode("stuck") == "observe" and b.log_path.endswith("hooks.jsonl")
    f = tmp_path / "judge_modes.json"
    f.write_text(json.dumps({"default": "off", "speaker": "act", "stuck": "bogus"}), encoding="utf-8")
    b2 = JudgeBridge("http://unused", "observe", modes_file=str(f), client=FakeClient())
    assert b2.mode("speaker") == "act" and b2.mode("stuck") == "off"      # bogus value ignored
    assert JudgeBridge("http://unused", None, client=FakeClient()).mode("image") == "off"


def test_summary_has_no_text(tmp_path, capsys):
    b = bridge(FakeClient(want="No"), {"default": "act"}, tmp_path)
    b.image(H, baseline=True)
    b.image(H, baseline=False)
    b3 = bridge(FakeClient(fail=True), "act", tmp_path)
    b3.stuck(H, baseline=False)
    text = summarize(os.path.join(str(tmp_path), "hooks.jsonl"))
    assert "| image | act | 2 | 2 | 1/2 (50%) | 0 | 1 | 0 |" in text
    assert "LLMError x1" in text
    assert "도윤" not in text and "장면" not in text
    out = tmp_path / "SUMMARY.md"
    assert main(["report", "--log", os.path.join(str(tmp_path), "hooks.jsonl"), "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == text


def test_think_filter_streaming():
    f = ThinkFilter()
    out = "".join(f.feed(c) for c in ["안녕<th", "ink>비밀</thi", "nk>하세요<|im_", "end|>"]) + f.flush()
    assert out == "안녕하세요"
    f = ThinkFilter(assume_open=True)
    assert ("".join(f.feed(c) for c in ["생각...</th", "ink>대답"]) + f.flush()) == "대답"
    f = ThinkFilter()
    assert ("".join(f.feed(c) for c in ["a < b 이고 ", "c > d"]) + f.flush()) == "a < b 이고 c > d"
    f = ThinkFilter()
    assert f.feed("<think>끝나지 않음") == "" and f.flush() == ""

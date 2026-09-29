import math
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatup.__main__ import main, probe_cases  # noqa: E402
from mockserver import MockLLM  # noqa: E402


def oracle(body):
    """Answers the probe like a good model would: finds the expected option in the
    prompt by a keyword and puts 80% on its label, whatever its position."""
    user = body["messages"][-1]["content"]
    m = re.search(r"Answer (Yes|No) or (Yes|No)\.", user)
    if m:
        if "그만하라고" in user:                       # wants_stop
            yes = "조용히 좀" in user
        elif "제자리를 맴돌고" in user:                 # stuck
            yes = "그래, 맞아." in user
        elif "대신 말하거나" in user:                   # reply_bad
            yes = user.count("강릉과 태안이에요.") >= 2
        else:                                          # wants_image
            yes = "그림으로 한번 그려" in user
        p = 0.8 if yes else 0.2
        return [("Yes", math.log(p)), ("No", math.log(1 - p))]
    opts = re.findall(r"^([A-Z])\. (.*)$", user, re.M)
    want = None
    for key, opt in (("결말은", "대답을 기다리는"), ("후보지가 두 군데", "이어서 할 말"), ("도윤아", "도윤"), ("미래 씨가", "미래"), ("하나야, 조명", "하나"), ("다들", "모두에게"),
                     ("그림으로", "이미지로"), ("점심", "그대로"), ("본선", "happy"), ("허전", "sad")):
        if key in user:
            want = opt
            break
    top = []
    for lab, text in opts:
        p = 0.8 if want and want in text else 0.2 / max(1, len(opts) - 1)
        top.append((lab, math.log(p)))
    return sorted(top, key=lambda t: t[1], reverse=True)


@pytest.fixture
def mock():
    m = MockLLM().start()
    m.logprobs = oracle
    yield m
    m.stop()


def test_probe_end_to_end(mock, tmp_path, capsys):
    report = tmp_path / "PROBE.md"
    assert main(["probe", "--url", mock.url, "--report", str(report)]) == 0
    out = capsys.readouterr().out
    assert f"RESULT accuracy: {len(probe_cases())}/{len(probe_cases())}" in out
    assert "levels: L0" in out
    text = report.read_text(encoding="utf-8")
    assert "| next_speaker: 이름을 불러 물음 | 도윤 | 도윤 |" in text
    assert all(r["chat_template_kwargs"] == {"enable_thinking": False} for r in mock.requests)


def test_probe_without_logprobs_reports_parsed(mock, capsys):
    mock.logprobs = None
    mock.reply_pieces = ["A"]
    assert main(["probe", "--url", mock.url]) == 0
    out = capsys.readouterr().out
    assert "label mass: n/a" in out and "parsed" in out


def test_voices_check(tmp_path, capsys):
    d = tmp_path / "bank" / "hana"
    d.mkdir(parents=True)
    (d / "neutral.wav").write_bytes(b"")
    assert main(["voices", "--bank", str(tmp_path / "bank"), "--strict"]) == 1
    out = capsys.readouterr().out
    assert "hana: neutral" in out and "no transcript" in out

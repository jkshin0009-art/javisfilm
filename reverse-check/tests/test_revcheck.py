import json
import math
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "chat-upgrade", "tests"))

import revcheck  # noqa: E402
from mockserver import MockLLM  # noqa: E402

try:
    FF = revcheck.find_ffmpeg()
except SystemExit:
    FF = None
needs_ff = pytest.mark.skipif(FF is None, reason="ffmpeg not available")


def make_video(path):
    """Three 2 s colour blocks with a moving box, 320x240, cuts at 2.0 and 4.0 s."""
    parts = []
    for c in ("darkred", "white", "navy"):          # different brightness, so each change is a cut
        parts += ["-f", "lavfi", "-i", f"color=c={c}:s=320x240:d=2:r=25"]
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *parts, "-filter_complex",
                    "[0][1][2]concat=n=3:v=1:a=0,drawbox=x='t*40':y=100:w=40:h=40:c=white:t=fill",
                    "-c:v", "mpeg4", "-q:v", "3", path], check=True)


def user_text(body):
    c = body["messages"][-1]["content"]
    return c[-1]["text"] if isinstance(c, list) else c


def oracle(body):
    text = user_text(body)
    if re.search(r"Answer (Yes|No) or (Yes|No)\.", text):
        p = 0.2 if "없는 중요한" in text else (0.7 if "A (실제로 쓴" in text else 0.9)
        return [("Yes", math.log(p)), ("No", math.log(1 - p))]
    opts = re.findall(r"^([A-Z])\. (.*)$", text, re.M)
    top = [(lab, math.log(0.8 if "AI로 만든" in t else 0.05)) for lab, t in opts]
    return sorted(top, key=lambda x: x[1], reverse=True)


@pytest.fixture
def mock():
    m = MockLLM().start()
    m.logprobs = oracle
    m.reply_pieces = ["A red square scene, static camera, flat studio light."]
    yield m
    m.stop()


def test_time_helpers():
    assert revcheck.parse_time("8:51") == 531
    assert revcheck.parse_time("1:02:03.5") == 3723.5
    assert revcheck.parse_time(12) == 12.0
    assert revcheck.fmt_time(531) == "8:51.0"


@needs_ff
def test_full_pipeline(tmp_path, mock, capsys):
    video = str(tmp_path / "src.mp4")
    make_video(video)
    work = str(tmp_path / "work")
    assert revcheck.main(["shots", video, "--work", work, "--start", "0:00.5", "--end", "6",
                          "--max-side", "160"]) == 0
    data = json.load(open(os.path.join(work, "shots.json"), encoding="utf-8"))
    spans = [(round(s["start"], 1), round(s["end"], 1)) for s in data["shots"]]
    assert spans == [(0.5, 2.0), (2.0, 4.0), (4.0, 6.0)]
    for s in data["shots"]:
        assert all(os.path.getsize(os.path.join(work, f)) > 0 for f in s["frames"])
        assert os.path.getsize(os.path.join(work, s["clip"])) > 0
    assert "s002" in open(os.path.join(work, "index.html"), encoding="utf-8").read()

    assert revcheck.main(["classify", "--work", work, "--url", mock.url]) == 0
    data = json.load(open(os.path.join(work, "shots.json"), encoding="utf-8"))
    assert {s["kind"] for s in data["shots"]} == {"showcase"}
    sent = mock.requests[-1]["messages"][-1]["content"]
    assert sent[0]["type"] == "image_url" and sent[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    # the project's logic stands in as a command that reads the frame paths it is given
    cmd = (f'"{sys.executable}" -c "import sys,os; fs=sys.argv[1:]; '
           f'print(\'shot with\', len(fs), \'frames\', all(os.path.exists(f) for f in fs))" {{frames}}')
    assert revcheck.main(["prompt", "--work", work, "--cmd", cmd, "--only", "showcase"]) == 0
    assert open(os.path.join(work, "prompts", "project", "s001.txt"), encoding="utf-8").read().strip() \
        == "shot with 3 frames True"
    assert revcheck.main(["prompt", "--work", work, "--vlm", "--url", mock.url]) == 0
    assert "red square" in open(os.path.join(work, "prompts", "vlm", "s002.txt"), encoding="utf-8").read()

    with open(os.path.join(work, "truth.csv"), "w", encoding="utf-8") as f:
        f.write("shot,prompt\ns001,\"A red screen, locked-off camera\"\n")
    assert revcheck.main(["score", "--work", work, "--url", mock.url]) == 0
    scores = json.load(open(os.path.join(work, "scores.json"), encoding="utf-8"))
    r = scores["project"]["s001"]
    assert r["mean"] == pytest.approx(0.9, abs=0.01) and r["invented"] == pytest.approx(0.2, abs=0.01)
    assert r["truth_mean"] == pytest.approx(0.7, abs=0.01)
    assert "truth" not in scores["vlm"]["s002"]
    calls = len(mock.requests)
    assert revcheck.main(["score", "--work", work, "--url", mock.url]) == 0     # already scored: no calls
    assert len(mock.requests) == calls

    out = str(tmp_path / "REPORT.md")
    assert revcheck.main(["report", "--work", work, "--offset", "8:00", "--with-prompts", "--out", out]) == 0
    rep = open(out, encoding="utf-8").read()
    assert "| s001 | 8:00.5 | showcase | 0.90 | 0.20 | 0.70 | 0.90 | 0.20 | 0.70 |" in rep
    assert "| s002 | 8:02.0 | showcase | 0.90 | 0.20 | - | 0.90 | 0.20 | - |" in rep
    assert "| project | 3 | 0.90 | 0.20 | 0.70 (1) |" in rep
    assert "**s002 [vlm]** A red square scene" in rep


@needs_ff
def test_crop_and_empty_range(tmp_path):
    video = str(tmp_path / "src.mp4")
    make_video(video)
    work = str(tmp_path / "w")
    assert revcheck.main(["shots", video, "--work", work, "--crop", "160:120:0:0", "--no-clips",
                          "--max-side", "100"]) == 0
    data = json.load(open(os.path.join(work, "shots.json"), encoding="utf-8"))
    assert len(data["shots"]) == 3 and "clip" not in data["shots"][0]
    with pytest.raises(SystemExit):
        revcheck.main(["shots", video, "--work", work, "--start", "5", "--end", "4"])


def test_command_failure_is_reported(tmp_path, capsys):
    work = tmp_path / "w"
    (work / "frames").mkdir(parents=True)
    for t in "abc":
        (work / "frames" / f"s001_{t}.jpg").write_bytes(b"x")
    data = {"video": "v", "start": 0, "end": 1, "shots": [{"id": "s001", "start": 0, "end": 1,
            "frames": [f"frames/s001_{t}.jpg" for t in "abc"]}]}
    (work / "shots.json").write_text(json.dumps(data), encoding="utf-8")
    cmd = f'"{sys.executable}" -c "import sys; sys.exit(3)"'
    assert revcheck.main(["prompt", "--work", str(work), "--cmd", cmd]) == 0
    out = capsys.readouterr().out
    assert "s001 FAILED (3)" in out and "0 written" in out

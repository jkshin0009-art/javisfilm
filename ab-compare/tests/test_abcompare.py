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

pytest.importorskip("PIL")
import abcompare as ab  # noqa: E402
from mockserver import MockLLM  # noqa: E402

try:
    FF = ab.ffmpeg_bin()
except SystemExit:
    FF = None
pytestmark = pytest.mark.skipif(FF is None, reason="ffmpeg not available")


def clip(path, colour, box):
    """2 s grey clip; `box` draws a bright square (a stand-in for a light leak)."""
    vf = f"drawbox=x=40:y=40:w=160:h=120:c={box}:t=fill" if box else "null"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c={colour}:s=320x240:d=2:r=25", "-vf", vf, "-c:v", "mpeg4", "-q:v", "2", path], check=True)


def test_light_metrics(tmp_path):
    from PIL import Image
    im = Image.new("L", (100, 100), 100)
    im.paste(255, (0, 0, 50, 20))          # 10 % blown
    im.paste(220, (0, 20, 50, 40))         # 10 % glow
    p = tmp_path / "m.png"
    im.save(p)
    m = ab.light_metrics(p)
    assert m["blown"] == pytest.approx(0.1) and m["glow"] == pytest.approx(0.1)


def test_frames_blind_and_reveal(tmp_path, capsys):
    a, b = str(tmp_path / "a.mp4"), str(tmp_path / "b.mp4")
    clip(a, "gray", None)
    clip(b, "gray", "white")
    mock = MockLLM().start()
    mock.logprobs = lambda body: [("Yes", math.log(0.3)), ("No", math.log(0.7))]
    try:
        out = tmp_path / "ab"
        assert ab.main(["frames", "--out", str(out), "--arm", f"base={a}", "--arm", f"leak={b}",
                        "--count", "3", "--width", "160", "--vlm", mock.url, "--seed", "1",
                        "--note", "LoRA off vs on"]) == 0
    finally:
        mock.stop()
    data = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert data["arms"]["leak"]["blown"] > 0.15 > data["arms"]["base"]["blown"]
    assert data["arms"]["base"]["leak_p"] == pytest.approx(0.3, abs=0.01)
    key = json.loads((out / "key.json").read_text(encoding="utf-8"))
    page = (out / "blind.html").read_text(encoding="utf-8")
    assert "base" not in re.sub(r'src="[^"]*"', "", page) and "leak" not in re.sub(r'src="[^"]*"', "", page)
    inv = {v: k for k, v in key.items()}
    votes = tmp_path / "votes.csv"
    votes.write_text(f"row,choice\nr0,{inv['base']}\nr1,{inv['base']}\nr2,{inv['leak']}\n"
                     f"best,{inv['base']}\nworst,{inv['leak']}\n", encoding="utf-8")
    assert ab.main(["reveal", "--out", str(out), "--votes", str(votes)]) == 0
    res = (out / "RESULT.md").read_text(encoding="utf-8")
    assert "overall best: base   worst: leak" in res and "| base | 2/3 |" in res


def test_needs_two_arms(tmp_path):
    a = str(tmp_path / "a.mp4")
    clip(a, "gray", None)
    with pytest.raises(SystemExit):
        ab.main(["frames", "--out", str(tmp_path / "o"), "--arm", f"x={a}"])

"""Tests run against a real copy of ComfyUI-BubbleText.

Set BUBBLETEXT_DIR to the node folder (e.g. <ComfyUI>/custom_nodes/ComfyUI-BubbleText).
Korean checks also need a font with Hangul: KOREAN_FONT, a Korean font already in
the node's fonts/ folder, or Windows' malgun.ttf.
"""

import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import bubble_doctor as bd  # noqa: E402
import patch_bubbletext as pb  # noqa: E402

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

SRC = os.environ.get("BUBBLETEXT_DIR")
pytestmark = pytest.mark.skipif(not SRC or not (Path(SRC) / "bubble_text.py").exists(),
                                reason="set BUBBLETEXT_DIR to a ComfyUI-BubbleText folder")
TEXT = "우리 여섯 명, 다 모였네."


def _korean_font() -> Path | None:
    cands = [os.environ.get("KOREAN_FONT"), r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf"]
    if SRC:
        cands += [str(p) for p in (Path(SRC) / "fonts").glob("*.[to]tf")]
    for c in cands:
        if c and Path(c).exists():
            try:
                from fontTools.ttLib import TTFont

                if 0xAC00 in TTFont(c, lazy=True, fontNumber=0).getBestCmap():
                    return Path(c)
            except Exception:
                continue
    return None


def _latin_font() -> str:
    for c in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
        if Path(c).exists():
            return c
    pytest.skip("no Latin test font")


@pytest.fixture
def node(tmp_path):
    """A private copy of the node with a Latin and (if available) a Korean font in fonts/."""
    dst = tmp_path / "ComfyUI-BubbleText"
    shutil.copytree(SRC, dst, ignore=shutil.ignore_patterns(".git", "images", "__pycache__"))
    (dst / "fonts").mkdir(exist_ok=True)
    shutil.copy(_latin_font(), dst / "fonts" / "latin.ttf")
    kf = _korean_font()
    if kf:
        shutil.copy(kf, dst / "fonts" / ("korean" + kf.suffix))
    return dst


def scene(path: Path, dark_hair=True, w=1664, h=928):
    """A white bubble with AI gibberish, and a dark 'hair' blob with a few holes."""
    img = Image.new("RGB", (w, h), (170, 190, 210))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(_latin_font(), 30)
    if dark_hair:
        d.ellipse((900, 250, 1300, 700), fill=(12, 12, 14))
        for i in range(6):
            d.text((980 + i * 45, 430), "o", font=f, fill=(90, 90, 95))
    d.ellipse((150, 80, 750, 380), fill=(252, 252, 252), outline=(0, 0, 0), width=6)
    d.text((300, 210), "HELO WROLD TXET", font=f, fill=(0, 0, 0))
    img.save(path)
    return path


# ------------------------------------------------------------------ patch


@pytest.mark.parametrize("crlf", [False, True])
def test_patch_apply_and_revert_restore_the_file(node, crlf):
    target = node / "bubble_text.py"
    if crlf:
        target.write_bytes(target.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    before = target.read_bytes()
    assert pb.main(["status", "--node-dir", str(node)]) == 0
    assert pb.main(["apply", "--node-dir", str(node)]) == 0
    after = target.read_bytes()
    assert b"dark = [] if white else" in after
    assert (b"\r\n" in after) == crlf and after.count(b"\n") == before.count(b"\n") + 1
    assert pb.main(["apply", "--node-dir", str(node)]) == 0  # idempotent
    assert pb.main(["revert", "--node-dir", str(node)]) == 0
    assert target.read_bytes() == before
    assert not (node / "bubble_text.py.orig").exists()


def test_patch_refuses_unknown_version(node):
    target = node / "bubble_text.py"
    target.write_text(target.read_text(encoding="utf-8").replace("dark_paper=True)", "dark_paper=True, x=1)"),
                      encoding="utf-8")
    before = target.read_bytes()
    assert pb.main(["apply", "--node-dir", str(node)]) == 1
    assert target.read_bytes() == before


def test_patched_node_ignores_dark_areas_when_a_white_bubble_exists(node, tmp_path):
    img = bd.read_rgb(scene(tmp_path / "s.png"))
    stock = bd.load_node(node)
    assert any(b["dark"] for b in stock.find_bubbles(img, 195)), "stock node should show the problem"
    patched_dir = tmp_path / "patched"
    shutil.copytree(node, patched_dir)
    assert pb.main(["apply", "--node-dir", str(patched_dir)]) == 0
    patched = bd.load_node(patched_dir)
    found = patched.find_bubbles(img, 195)
    assert found and not any(b["dark"] for b in found)
    # with no white bubble at all, black bubbles are still found (the documented fallback)
    dark_only = bd.read_rgb(scene(tmp_path / "d.png")).copy()
    dark_only[60:400, 130:770] = (170, 190, 210)
    assert any(b["dark"] for b in patched.find_bubbles(dark_only, 195))


# ------------------------------------------------------------------ doctor


def test_scan_flags_dark_areas_next_to_white_bubble(node, tmp_path, capsys):
    (tmp_path / "in").mkdir()
    scene(tmp_path / "in" / "a.png")
    rc = bd.main(["scan", "--node-dir", str(node), "--in", str(tmp_path / "in"), "--out", str(tmp_path / "out"),
                  "--text", TEXT])
    out = capsys.readouterr().out
    assert rc == 1
    assert "taken as black bubbles next to a white bubble" in out
    assert "split across 2 bubbles" in out
    assert (tmp_path / "out" / "a__scan.png").exists()


def test_render_fixed_writes_only_into_the_white_bubble(node, tmp_path):
    if not _korean_font():
        pytest.skip("no Korean font available")
    (tmp_path / "in").mkdir()
    scene(tmp_path / "in" / "a.png")
    bt = bd.load_node(node)
    rgb = bd.read_rgb(tmp_path / "in" / "a.png")
    font = next(n for n in bt.available_fonts() if n.startswith("korean"))
    as_is, m1 = bd.render_one(bt, rgb, TEXT, font, 64, 0.08, 195, False, False)
    fixed, m2 = bd.render_one(bt, rgb, TEXT, font, 110, 0.12, 195, True, False)
    hair = (slice(260, 690), slice(910, 1290))
    assert m1[hair].any() and not m2[hair].any()
    assert np.array_equal(fixed[hair], rgb[hair])  # the hair is left untouched
    assert m2[100:360, 200:700].any()  # text went into the white bubble
    rc = bd.main(["render", "--node-dir", str(node), "--in", str(tmp_path / "in"), "--out", str(tmp_path / "out"),
                  "--text", TEXT, "--font", font])
    assert rc == 0 and (tmp_path / "out" / "a__compare.png").exists()


def test_fonts_reports_missing_hangul(node, capsys):
    rc = bd.main(["fonts", "--node-dir", str(node), "--text", TEXT])
    out = capsys.readouterr().out
    assert "latin.ttf" in out and "MISSING" in out
    if _korean_font():
        assert rc == 0 and "OK for the text" in out
    else:
        assert rc == 1


def test_workflow_flags_mask_preview_and_latin_font(node, tmp_path):
    wf = {
        "nodes": [
            {"id": 1, "type": "SpeechBubbleTextAuto",
             "widgets_values": [True, TEXT, "latin.ttf", True, 64, "left → right", True, "auto", 0.08, 195],
             "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10]},
                         {"name": "bubble mask", "type": "MASK", "links": [11]}]},
            {"id": 2, "type": "SaveImage"},
            {"id": 3, "type": "MaskToImage"},
        ],
        "links": [[10, 1, 0, 2, 0, "IMAGE"], [11, 1, 1, 3, 0, "MASK"]],
    }
    p = tmp_path / "wf.json"
    p.write_text(json.dumps(wf, ensure_ascii=False), encoding="utf-8")
    lines = bd.analyse_workflow(p, bd.load_node(node))
    text = "\n".join(lines)
    assert "text='우리 여섯 명, 다 모였네.'" in text
    assert "no Hangul glyphs" in text
    assert "bubble mask is shown/saved as an image" in text


def test_fix_workflow_writes_a_copy(tmp_path):
    wf = {"nodes": [{"id": 5, "type": "SpeechBubblePrompt",
                     "widgets_values": [True, TEXT, "comicbd.ttf", True, 64, "left → right", True, "auto", 0.08, 195,
                                        "natural (Anima)"]},
                    {"id": 6, "type": "KSampler", "widgets_values": [1, "fixed", 20]}],
          "links": []}
    src = tmp_path / "wf.json"
    src.write_text(json.dumps(wf, ensure_ascii=False), encoding="utf-8")
    original = src.read_bytes()
    changed = bd.fix_workflow(src, tmp_path / "wf_fixed.json", "NanumGothic-Bold.ttf", 110, 0.12, False)
    assert src.read_bytes() == original
    new = json.loads((tmp_path / "wf_fixed.json").read_text(encoding="utf-8"))
    vals = new["nodes"][0]["widgets_values"]
    assert vals[2] == "NanumGothic-Bold.ttf" and vals[3] is False and vals[4] == 110 and vals[8] == 0.12
    assert vals[1] == TEXT and vals[10] == "natural (Anima)"
    assert new["nodes"][1]["widgets_values"] == [1, "fixed", 20]
    assert len(changed) == 1 and "font 'comicbd.ttf' -> 'NanumGothic-Bold.ttf'" in changed[0]
    with pytest.raises(SystemExit):
        bd.fix_workflow(src, src, "x.ttf", None, None, None)


def test_text_file_with_bom_and_quotes(node, tmp_path, capsys):
    f = tmp_path / "text.txt"
    f.write_bytes("\ufeff그러게, \"진짜\"로.\n\n둘째 말풍선".encode("utf-8"))
    rc = bd.main(["fonts", "--node-dir", str(node), "--text-file", str(f)])
    out = capsys.readouterr().out
    assert "MISSING" in out  # latin.ttf lacks Hangul, so the text was read correctly
    assert "\ufeff" not in out

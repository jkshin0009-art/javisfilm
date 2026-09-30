import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import gatereview as gr  # noqa: E402
import qclabel  # noqa: E402


def pic(d, name, data, gate=None):
    p = d / name
    p.write_bytes(data)
    if gate is not None:
        p.with_suffix(".gate.json").write_text(json.dumps(gate), encoding="utf-8")
    return p


def lines(root):
    return [json.loads(l) for l in (root / "labels.jsonl").read_text(encoding="utf-8").splitlines()]


def test_record_keeps_copy_and_gate(tmp_path):
    d = tmp_path / "look"
    d.mkdir()
    root = tmp_path / "labels"
    p = pic(d, "p03.png", b"not really a png",
            {"verdict": "FAIL", "axes": {"legs_ok": {"pass": False}, "hands_ok": {"pass": None},
                                          "offfloor": {"pass": True}}})
    lid = qclabel.record("red", p, slug="s1", look="a", panel=3, source="panel_eye", note="다리", root=root)
    assert lid
    r = lines(root)[0]
    assert r["verdict"] == "redo" and r["panel"] == 3 and r["gate_verdict"] == "FAIL"
    assert r["gate_fails"] == ["legs_ok"] and r["gate_unmeasured"] == ["hands_ok"]
    assert (root / r["copy"]).is_file() and (root / r["gate"]).is_file()
    p.unlink()                                                  # the project discards the picture
    assert (root / r["copy"]).is_file()                         # the copy stays


def test_record_is_safe(tmp_path, monkeypatch):
    root = tmp_path / "labels"
    assert qclabel.record(True, tmp_path / "missing.png", root=root)      # recorded without a copy
    assert lines(root)[0]["verdict"] == "ok" and lines(root)[0]["copy"] is None
    monkeypatch.setenv("FJ_QC_LABELS", "off")
    assert qclabel.record("ok", tmp_path / "x.png", root=root) is None
    monkeypatch.delenv("FJ_QC_LABELS")
    blocked = tmp_path / "file"
    blocked.write_text("x")
    assert qclabel.record("ok", tmp_path / "x.png", root=blocked / "sub") is None   # cannot write: no raise


def test_labels_report(tmp_path, capsys):
    d = tmp_path / "look"
    d.mkdir()
    root = tmp_path / "labels"
    fail_legs = {"verdict": "FAIL", "axes": {"legs_ok": {"pass": False}}}
    fail_unm = {"verdict": "FAIL", "axes": {"scale_grounding_ok": {"pass": None}}}
    passed = {"verdict": "PASS", "axes": {"legs_ok": {"pass": True}}}
    a = pic(d, "a.png", b"a", fail_legs)
    qclabel.record("ok", a, source="select", root=root)
    qclabel.record("redo", a, source="panel_eye", root=root)      # same picture later sent back: counts once
    qclabel.record("redo", pic(d, "b.png", b"b", fail_legs), source="rebake", root=root)
    qclabel.record("ok", pic(d, "c.png", b"c", fail_legs), source="select", root=root)
    qclabel.record("ok", pic(d, "e.png", b"e", fail_unm), source="select", root=root)
    qclabel.record("redo", pic(d, "f.png", b"f", passed), source="fix_panel", root=root)
    qclabel.record("redo", pic(d, "g.png", b"g"), source="rebake", root=root)
    recs = gr.read_labels(root)
    assert len(recs) == 6
    assert gr.main(["labels", "--labels", str(root), "--report", str(tmp_path / "L.md")]) == 0
    text = (tmp_path / "L.md").read_text(encoding="utf-8")
    assert "pictures judged by the person: 6 (sent back 4, kept 2)" in text
    assert "| FAIL defect | 2 | 1 |" in text and "| FAIL unmeasured only | 0 | 1 |" in text
    assert "| PASS | 1 | 0 |" in text and "| no gate | 1 | 0 |" in text
    assert "the gate failed 2/3" in text and "the gate failed 2/2 (false alarms)" in text
    assert "| legs_ok | 2 | 1 | 67% | 표본 부족 |" in text
    assert "1 judged pictures have no gate verdict" in text


def test_rebake_after_fix_keeps_reason(tmp_path):
    d = tmp_path / "look"
    d.mkdir()
    root = tmp_path / "labels"
    p = pic(d, "p05.png", b"x")
    qclabel.record("redo", p, source="fix_panel", note="손가락", root=root)
    qclabel.record("redo", p, source="rebake", root=root)
    (r,) = gr.read_labels(root)
    assert r["source"] == "rebake" and r["note"] == "손가락"

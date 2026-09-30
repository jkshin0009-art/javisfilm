import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import gatereview as gr  # noqa: E402


def gate(d, name, verdict, axes, frame=None, image=True):
    p = d / f"{name}.gate.json"
    p.write_text(json.dumps({"at": "t", "axes": axes, "error": None, "verdict": verdict,
                             "frame": frame if frame is not None else f"{name}.png"}), encoding="utf-8")
    if image:
        (d / f"{name}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return p


def make_root(tmp_path):
    d = tmp_path / "gates"
    d.mkdir()
    for i in range(6):
        gate(d, f"off{i}", "FAIL", {"offfloor": {"value": 30, "limit": 10, "pass": False, "reason": "feet up"},
                                    "hands_ok": {"pass": True}, "count": True})
    for i in range(3):
        gate(d, f"legs{i}", "FAIL", {"legs_ok": {"pass": False}, "offfloor": {"pass": True}})
    for i in range(4):
        gate(d, f"unm{i}", "FAIL", {"scale_grounding_ok": {"pass": None}, "offfloor": {"pass": True},
                                    "seat_order": {"na": True}})
    for i in range(2):
        gate(d, f"ok{i}", "PASS", {"offfloor": {"pass": True}, "hands_ok": {"pass": True, "observe": True}})
    gate(d, "noimg", "FAIL", {"offfloor": {"pass": False}}, frame="missing.png", image=False)
    (d / "broken.gate.json").write_text("{", encoding="utf-8")
    return d


def test_stats_categories(tmp_path):
    cuts = gr.load(make_root(tmp_path))
    cats = [c["category"] for c in cuts]
    assert cats.count("defect") == 10 and cats.count("unmeasured_only") == 4 and cats.count("pass") == 2
    assert cats.count("unreadable") == 1
    text = gr.stats_text(cuts)
    assert "| offfloor | 9 | 7 | 0 | 0 | 0 |" in text
    assert "| scale_grounding_ok | 0 | 0 | 4 | 0 | 0 |" in text
    assert "| hands_ok | 8 | 0 | 0 | 0 | 2 |" in text
    assert "only unmeasured ones: 4" in text


def test_image_lookup(tmp_path):
    d = tmp_path / "g"
    d.mkdir()
    imgs = tmp_path / "frames" / "deep"
    imgs.mkdir(parents=True)
    (imgs / "shot7.png").write_bytes(b"x")
    g = gate(d, "a", "FAIL", {}, frame="C:/elsewhere/shot7.png", image=False)
    assert gr.find_image(g, "C:/elsewhere/shot7.png", None, {}) is None
    cuts = gr.load(d, image_root=tmp_path / "frames")
    assert cuts[0]["image"] == (imgs / "shot7.png").resolve()
    base = tmp_path
    assert gr.find_image(g, "frames/deep/shot7.png", base, {}) == (imgs / "shot7.png").resolve()


def test_sample_page_and_score(tmp_path, capsys):
    root = make_root(tmp_path)
    out = tmp_path / "work"
    assert gr.main(["sample", "--root", str(root), "--out", str(out), "--per-axis", "4",
                    "--unmeasured", "2", "--passed", "2"]) == 0
    data = json.loads((out / "rows.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    kinds = [(r["kind"], r["axis"]) for r in rows]
    assert kinds.count(("axis", "offfloor")) == 4 and kinds.count(("axis", "legs_ok")) == 3
    assert kinds.count(("unmeasured", "")) == 2 and kinds.count(("pass", "")) == 2
    assert len({r["gate"] for r in rows}) == len(rows)
    page = (out / "gate_review.html").read_text(encoding="utf-8")
    assert page.count('class="card"') == len(rows) and "gate_votes.csv" in page
    votes = tmp_path / "gate_votes.csv"
    lines = ["id,answer"]
    for r in rows:
        if r["axis"] == "offfloor":
            lines.append(f"{r['id']},{'defect' if r['id'] == rows[0]['id'] else 'clean'}")
        elif r["axis"] == "legs_ok":
            lines.append(f"{r['id']},defect")
        elif r["kind"] == "unmeasured":
            lines.append(f"{r['id']},clean")
        else:
            lines.append(f"{r['id']},")
    votes.write_text("\ufeff" + "\n".join(lines), encoding="utf-8")
    assert gr.main(["score", "--out", str(out), "--csv", str(votes)]) == 0
    text = (out / "GATE_SCORE.md").read_text(encoding="utf-8")
    assert "| offfloor | 4 | 1 | 3 | 0 | 25%" in text and "표본 부족" in text
    assert "| legs_ok | 3 | 3 | 0 | 0 | 100%" in text
    assert "clean share: 100%" in text
    assert "feet up" not in text                         # the report carries no gate reasons


def test_referee_marks_without_a_person(tmp_path, monkeypatch, capsys):
    import boardcheck as bc
    root = make_root(tmp_path)
    d = root
    for i in range(3):
        gate(d, f"cos{i}", "FAIL", {"costume_lock": {"pass": False}})
    out = tmp_path / "work"
    assert gr.main(["sample", "--root", str(root), "--out", str(out), "--per-axis", "6",
                    "--unmeasured", "2", "--passed", "2"]) == 0
    seen = []

    class FakeBackend:
        def __init__(self, url, timeout=120.0):
            self.url = url

        def ok(self, images, state, questions):
            seen.append((len(images), sorted(questions)))
            return {k: {"offfloor": 0.9, "legs_ok": 0.1}.get(k, 0.05) if len(questions) == 1 else 0.05
                    for k in questions}

    monkeypatch.setattr(bc, "LogprobBackend", FakeBackend)
    monkeypatch.setattr(bc, "prepared", lambda src, cache, side: src)
    assert gr.main(["referee", "--out", str(out)]) == 0
    rows = {r["id"]: r for r in json.loads((out / "rows.json").read_text(encoding="utf-8"))["rows"]}
    import csv as _csv
    with open(out / "auto_votes.csv", encoding="utf-8-sig") as f:
        votes = {r["id"]: r for r in _csv.DictReader(f)}
    for rid, r in rows.items():
        want = {"offfloor": "defect", "legs_ok": "clean", "costume_lock": "unsure"}.get(r["axis"], "clean")
        assert votes[rid]["answer"] == want, (r, votes[rid])
    assert all(n == 1 for n, _ in seen) and sorted(gr.GENERIC) in [q for _, q in seen]
    text = (out / "GATE_SCORE_AUTO.md").read_text(encoding="utf-8")
    assert "machine referee" in text and "| offfloor | 6 | 6 | 0 | 0 | 100%" in text
    assert "| legs_ok | 3 | 0 | 3 | 0 | 0%" in text and "| costume_lock | 3 | 0 | 0 | 3 |" in text
    assert "referee time" in text


def test_calibrate_on_known_bad(tmp_path, monkeypatch):
    import boardcheck as bc
    imgs = tmp_path / "bad"
    imgs.mkdir()
    for n in ("h1", "h2", "l1", "x1"):
        (imgs / f"{n}.png").write_bytes(b"x")
    lst = tmp_path / "known_bad.csv"
    lst.write_text("image,kinds\n"
                   f"{imgs / 'h1.png'},hands_ok\n{imgs / 'h2.png'},hands_ok\n"
                   f"{imgs / 'l1.png'},hands_ok legs_ok\n{imgs / 'x1.png'},\n{imgs / 'gone.png'},legs_ok\n",
                   encoding="utf-8")
    asked = []

    class FakeBackend:
        def __init__(self, url, timeout=120.0):
            pass

        def ok(self, images, state, questions):
            asked.append(sorted(questions))
            name = os.path.basename(str(images[0]))
            return {k: {"h1.png": 0.95, "h2.png": 0.1}.get(name, 0.5) for k in questions}

    monkeypatch.setattr(bc, "LogprobBackend", FakeBackend)
    monkeypatch.setattr(bc, "prepared", lambda src, cache, side: src)
    out = tmp_path / "work"
    assert gr.main(["calibrate", "--list", str(lst), "--out", str(out)]) == 0
    text = (out / "REFEREE_CHECK.md").read_text(encoding="utf-8")
    assert "listed: 5   image found: 4" in text
    assert "| hands_ok | 2 | 1 | 0 | 1 |" in text and "| hands_ok legs_ok | 1 | 0 | 1 | 0 |" in text
    assert "| any | 1 | 0 | 1 | 0 |" in text and "caught 1/4 (25%)" in text and "misses most" in text
    assert sorted(gr.GENERIC) in asked and ["hands_ok", "legs_ok"] in asked

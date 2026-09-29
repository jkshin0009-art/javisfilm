import os
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import face_check as fc  # noqa: E402

cv2 = pytest.importorskip("cv2")


# ------------------------------------------------------------------ unit tests (no model)


def unit(v):
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v)


def member(mid, vec):
    return fc.CastMember(mid, mid, [unit(vec)], ["x"])


def face(vec, h=100):
    return fc.Face(np.array([0, 0, h, h], dtype=float), 0.9, unit(vec))


MEMBERS = [member("A", [1, 0, 0, 0]), member("B", [0, 1, 0, 0]), member("C", [0, 0, 1, 0])]


def test_assign_is_one_to_one():
    # two faces both closest to A: only one may be A, the other must not be forced onto B/C
    out = fc.assign([face([1, 0.1, 0, 0]), face([1, 0.05, 0, 0.3])], MEMBERS, 0.35)
    names = [w for _, w, _, _ in out]
    assert names.count("A") == 1 and None in names


def test_match_clip_uses_token_boundaries():
    ids = ["C1", "C10", "X3a", "X3"]
    assert fc.match_clip("S01_C10_take2", ids) == "C10"
    assert fc.match_clip("S01-C1-final", ids) == "C1"
    assert fc.match_clip("EXP_X3a", ids) == "X3a"
    assert fc.match_clip("render_final", ids) is None


def _shot(expected):
    return fc.ShotResult("c", "f", 1, 0, 1, "medium", expected)


def test_judge_pass_check_redo():
    r = _shot(["A", "B"])
    r.frames = r.frames_with_faces = 10
    r.hits = {"A": [0.7] * 10, "B": [0.6] * 9}
    fc.judge(r, 0.35)
    assert r.verdict == "PASS"

    r = _shot(["A", "B"])
    r.frames = r.frames_with_faces = 10
    r.hits = {"A": [0.7] * 10, "B": [0.5] * 5}
    fc.judge(r, 0.35)
    assert r.verdict == "CHECK"

    r = _shot(["A", "B"])
    r.frames = r.frames_with_faces = 10
    r.hits = {"A": [0.7] * 10}
    r.best = {"B": [0.2] * 10}
    r.unexpected = {"C": 8}
    fc.judge(r, 0.35)
    assert r.verdict == "REDO"
    assert any("B found in 0%" in x for x in r.reasons) and any("C appears" in x for x in r.reasons)


def test_lookalike_only_above_threshold():
    assert fc.lookalike(np.array([0.1, 0.8, 0.2]), MEMBERS, 0.35) == "B"
    assert fc.lookalike(np.array([0.1, 0.2, 0.3]), MEMBERS, 0.35) is None


def test_judge_small_faces_are_not_failures():
    r = _shot(["A", "B", "C"])
    r.frames = 10
    r.small_faces = 30
    fc.judge(r, 0.35)
    assert r.verdict == "SMALL"


def test_scene_shot_windows(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump({"clips": [{"id": "C1", "duration": 9, "shots": [
        {"framing": "wide", "cast": ["A", "B"]}, {"at": 4, "framing": "close-up", "cast": ["A"]}]}]}))
    shots = fc.load_scene_shots(p)["C1"]
    assert [(s.start, s.end, s.cast) for s in shots] == [(0.0, 4.0, ["A", "B"]), (4.0, 9.0, ["A"])]


# ------------------------------------------------------------------ integration (real model)


def _backend():
    pytest.importorskip("insightface")
    model_dir = Path(os.path.expanduser("~/.insightface/models/buffalo_l"))
    if not (model_dir / "w600k_r50.onnx").exists():
        pytest.skip("buffalo_l model not downloaded")
    return fc.InsightFaceBackend(gpu=False)


def _group_photo():
    import insightface

    p = Path(insightface.__file__).parent / "data" / "images" / "t1.jpg"
    if not p.exists():
        pytest.skip("insightface sample image t1.jpg not found")
    return cv2.imread(str(p))


def _crop(img, bbox, pad=0.6):
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    x1, y1 = max(0, int(x1 - w * pad)), max(0, int(y1 - h * pad))
    x2, y2 = min(img.shape[1], int(x2 + w * pad)), min(img.shape[0], int(y2 + h * pad))
    return img[y1:y2, x1:x2].copy()


def _write_video(path, frames, fps=24):
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in frames:
        vw.write(f)
    vw.release()
    assert path.exists() and path.stat().st_size > 0


def _closeup(crop, size=(640, 640)):
    return cv2.resize(crop, size, interpolation=cv2.INTER_CUBIC)


@pytest.fixture(scope="module")
def scenario(tmp_path_factory):
    backend = _backend()
    img = _group_photo()
    faces = sorted(backend.faces(img), key=lambda f: f.bbox[0])
    assert len(faces) == 6
    ids = list("ABCDEF")
    root = tmp_path_factory.mktemp("fc")
    (root / "refs").mkdir()
    crops = {}
    chars = []
    for cid, f in zip(ids, faces):
        crops[cid] = _crop(img, f.bbox)
        cv2.imwrite(str(root / "refs" / f"{cid}.png"), _closeup(crops[cid], (256, 256)))
        chars.append({"id": cid, "name": cid, "slot": ids.index(cid) + 1, "look": "x", "short": "x",
                      "face": f"refs/{cid}.png"})
    (root / "cast.yaml").write_text(yaml.safe_dump({"characters": chars}))

    vids = root / "videos"
    vids.mkdir()
    # T_OK: the untouched group photo, drifting slightly
    _write_video(vids / "T_OK.mp4", [np.roll(img, i, axis=1) for i in range(0, 72, 2)])
    # T_SWAP: C's face replaced by E's face -> C is missing, the fake C matches nobody
    swapped = img.copy()
    c, e = faces[2].bbox.astype(int), faces[4].bbox.astype(int)
    e_face = img[e[1]:e[3], e[0]:e[2]]
    swapped[c[1]:c[3], c[0]:c[2]] = cv2.resize(e_face, (c[2] - c[0], c[3] - c[1]))
    _write_video(vids / "T_SWAP.mp4", [swapped] * 36)
    # T_CUTS: close-up of A for 2 s, then close-up of B -> both shots pass
    _write_video(vids / "T_CUTS.mp4", [_closeup(crops["A"])] * 48 + [_closeup(crops["B"])] * 48)
    # T_WRONG: same cut but D shows up where B is expected
    _write_video(vids / "T_WRONG.mp4", [_closeup(crops["A"])] * 48 + [_closeup(crops["D"])] * 48)

    all6 = ids
    scene = {"clips": [
        {"id": "T_OK", "duration": 3, "shots": [{"framing": "wide", "cast": all6}]},
        {"id": "T_SWAP", "duration": 1.5, "shots": [{"framing": "wide", "cast": all6}]},
        {"id": "T_CUTS", "duration": 4, "shots": [{"framing": "close-up", "cast": ["A"]},
                                                 {"at": 2, "framing": "close-up", "cast": ["B"]}]},
        {"id": "T_WRONG", "duration": 4, "shots": [{"framing": "close-up", "cast": ["A"]},
                                                  {"at": 2, "framing": "close-up", "cast": ["B"]}]},
    ]}
    (root / "scene.yaml").write_text(yaml.safe_dump(scene))
    members, problems = fc.load_cast_faces(root / "cast.yaml", backend)
    assert problems == []
    shots = fc.load_scene_shots(root / "scene.yaml")
    results = fc.analyse(fc.collect_inputs(vids), members, backend, shots, fps=4, threshold=0.35,
                         min_face=40, frames_dir=root / "out" / "frames")
    report = fc.write_reports(results, members, root / "out", 0.35)
    return {(r.clip, r.shot): r for r in results}, report, root, members


def test_real_untouched_group_passes(scenario):
    res, _, _, _ = scenario
    r = res[("T_OK", 1)]
    assert r.verdict == "PASS", r.reasons
    assert all(len(r.hits.get(c, [])) == r.frames_with_faces for c in "ABCDEF")


def test_real_swapped_face_is_redo(scenario):
    res, _, _, _ = scenario
    r = res[("T_SWAP", 1)]
    assert r.verdict == "REDO", r.reasons
    assert any(x.startswith("C found in 0%") for x in r.reasons)
    assert r.duplicates.get("E") and any("looks like E" in x for x in r.reasons)


def test_real_cuts_follow_scene_file(scenario):
    res, _, _, _ = scenario
    assert res[("T_CUTS", 1)].verdict == "PASS"
    assert res[("T_CUTS", 2)].verdict == "PASS"
    wrong = res[("T_WRONG", 2)]
    assert wrong.verdict == "REDO"
    assert "D" in wrong.unexpected and not wrong.hits.get("B")


def test_real_reports_and_flagged_frames(scenario):
    _, report, root, _ = scenario
    assert "| T_SWAP | 1 |" in report and "Re-render: T_SWAP, T_WRONG" in report
    assert (root / "out" / "face_report.csv").exists()
    flagged = sorted(p.name for p in (root / "out" / "frames").glob("*.jpg"))
    assert any(n.startswith("T_SWAP_shot1") for n in flagged)
    assert any(n.startswith("T_WRONG_shot2") for n in flagged)


def test_real_cast_matrix_has_no_lookalikes(scenario):
    _, _, _, members = scenario
    pairs = fc.cast_matrix(members)
    assert len(pairs) == 15
    assert max(s for _, _, s in pairs) < fc.SIMILAR_PAIR

#!/usr/bin/env python3
"""Check that generated clips keep each character's face.

Compares every face found in the videos with the cast's reference faces
(ArcFace embeddings via InsightFace) and, when a scene file is given, checks
each shot against the characters that are supposed to be in it.

    python face_check.py cast   --cast examples/cast.yaml
    python face_check.py videos --cast examples/cast.yaml --scene examples/S01_diner.yaml --in renders/ --out out/face

`cast` prints how similar the characters' faces are to each other: pairs that
look alike are hard for H3 to keep apart and for this checker to tell apart.
`videos` writes face_report.md / face_report.csv and annotated frames of every
shot that needs a look or a re-render.

Model licence: InsightFace's buffalo_l weights are for non-commercial research
use. Check the licence before using the scores in a commercial production.
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SIMILAR_PAIR = 0.45  # reference faces this similar are easy to confuse
CUT_GUARD_S = 0.25  # frames this close to a cut are skipped


# --------------------------------------------------------------------------- backend


@dataclass
class Face:
    bbox: np.ndarray  # x1, y1, x2, y2
    score: float
    emb: np.ndarray  # L2-normalised

    @property
    def height(self) -> float:
        return float(self.bbox[3] - self.bbox[1])


class InsightFaceBackend:
    def __init__(self, gpu: bool = False, det_size: int = 640):
        from insightface.app import FaceAnalysis  # imported here so tests can run without it

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if gpu else ["CPUExecutionProvider"]
        self.app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"], providers=providers)
        self.app.prepare(ctx_id=0 if gpu else -1, det_size=(det_size, det_size))

    def faces(self, img: np.ndarray) -> list[Face]:
        out = []
        for f in self.app.get(img):
            emb = getattr(f, "normed_embedding", None)
            if emb is None:
                continue
            out.append(Face(np.asarray(f.bbox, dtype=float), float(f.det_score), np.asarray(emb, dtype=np.float32)))
        return out


# --------------------------------------------------------------------------- cast


@dataclass
class CastMember:
    id: str
    name: str
    embs: list[np.ndarray] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def read_image(path: Path) -> np.ndarray | None:
    import cv2

    data = np.fromfile(str(path), dtype=np.uint8)  # works with non-ASCII Windows paths
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def load_cast_faces(cast_path: Path, backend, use_sheet: bool = True, min_score: float = 0.5) -> tuple[list[CastMember], list[str]]:
    import yaml

    data = yaml.safe_load(cast_path.read_text(encoding="utf-8")) or {}
    base = cast_path.parent
    members, problems = [], []
    for c in data.get("characters") or []:
        m = CastMember(id=str(c["id"]), name=str(c.get("name") or c["id"]))
        files = [c.get("face")] + list(c.get("face_refs") or [])
        if use_sheet:
            files.append(c.get("sheet"))
        for f in [x for x in files if x]:
            p = base / f
            if not p.exists():
                problems.append(f"{m.id}: file not found: {f}")
                continue
            img = read_image(p)
            if img is None:
                problems.append(f"{m.id}: cannot read image: {f}")
                continue
            found = [x for x in backend.faces(img) if x.score >= min_score]
            if not found:
                problems.append(f"{m.id}: no face found in {f}")
                continue
            # A face close-up has one face; a character sheet repeats the same
            # person, so every detected face in it is a valid view.
            for x in found:
                m.embs.append(x.emb)
                m.sources.append(f)
        if not m.embs:
            problems.append(f"{m.id}: no usable reference face; this character cannot be checked")
        members.append(m)
    return members, problems


def similarity(face_emb: np.ndarray, member: CastMember) -> float:
    if not member.embs:
        return -1.0
    return float(max(float(np.dot(face_emb, e)) for e in member.embs))


def cast_matrix(members: list[CastMember]) -> list[tuple[str, str, float]]:
    pairs = []
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            if a.embs and b.embs:
                s = max(float(np.dot(x, y)) for x in a.embs for y in b.embs)
                pairs.append((a.id, b.id, s))
    return pairs


# --------------------------------------------------------------------------- scene


@dataclass
class ShotSpec:
    clip: str
    index: int
    start: float
    end: float
    framing: str
    cast: list[str]


def load_scene_shots(scene_path: Path) -> dict[str, list[ShotSpec]]:
    import yaml

    data = yaml.safe_load(scene_path.read_text(encoding="utf-8")) or {}
    out: dict[str, list[ShotSpec]] = {}
    for c in data.get("clips") or []:
        shots = c.get("shots") or []
        specs = []
        for i, s in enumerate(shots):
            start = float(s.get("at", 0) or 0)
            end = float(shots[i + 1].get("at")) if i + 1 < len(shots) else float(c["duration"])
            cast = [str(x) for x in (s.get("cast") or [])]
            specs.append(ShotSpec(str(c["id"]), i + 1, start, end, str(s.get("framing", "")), cast))
        out[str(c["id"])] = specs
    return out


def match_clip(name: str, clip_ids: list[str]) -> str | None:
    """Longest clip id that appears in the file name as its own token."""
    best = None
    for cid in clip_ids:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(cid)}(?![A-Za-z0-9])", name, re.I):
            if best is None or len(cid) > len(best):
                best = cid
    return best


# --------------------------------------------------------------------------- frames


def iter_frames(path: Path, fps: float, folder_fps: float = 24.0):
    """Yield (time_s, frame) sampled at about `fps` from a video or an image folder."""
    import cv2

    if path.is_dir():
        files = sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXT)
        step = max(1, round(folder_fps / fps))
        for i, f in enumerate(files):
            if i % step == 0:
                img = read_image(f)
                if img is not None:
                    yield i / folder_fps, img
        return
    cap = cv2.VideoCapture(str(path))
    tmp = None
    if not cap.isOpened() and not str(path).isascii():
        # OpenCV on Windows cannot open non-ASCII paths (e.g. Korean folder names)
        import shutil
        import tempfile

        tmp = Path(tempfile.mkdtemp()) / ("clip" + path.suffix)
        shutil.copyfile(path, tmp)
        cap = cv2.VideoCapture(str(tmp))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video {path}")
    vfps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    step = max(1, round(vfps / fps))
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            yield i / vfps, frame
        i += 1
    cap.release()
    if tmp is not None:
        tmp.unlink(missing_ok=True)


def assign(faces: list[Face], members: list[CastMember], threshold: float):
    """One face per character: returns [(face, member_id or None, best_sim, sims)]."""
    if not faces:
        return []
    sims = np.array([[similarity(f.emb, m) for m in members] for f in faces], dtype=float)
    chosen: dict[int, int] = {}
    try:
        from scipy.optimize import linear_sum_assignment

        rows, cols = linear_sum_assignment(-sims)
        chosen = {int(r): int(c) for r, c in zip(rows, cols)}
    except ImportError:  # greedy fallback
        used = set()
        for r, c in sorted(((r, c) for r in range(len(faces)) for c in range(len(members))),
                           key=lambda rc: -sims[rc[0], rc[1]]):
            if r not in chosen and c not in used:
                chosen[r] = c
                used.add(c)
    out = []
    for r, f in enumerate(faces):
        c = chosen.get(r)
        best = float(sims[r].max()) if sims.shape[1] else -1.0
        if c is not None and sims[r, c] >= threshold:
            out.append((f, members[c].id, float(sims[r, c]), sims[r]))
        else:
            out.append((f, None, best, sims[r]))
    return out


def lookalike(sims: np.ndarray, members: list[CastMember], threshold: float) -> str | None:
    """For a face that matched nobody: the character it resembles, if any."""
    if not len(sims):
        return None
    j = int(np.argmax(sims))
    return members[j].id if sims[j] >= threshold else None


# --------------------------------------------------------------------------- analysis


@dataclass
class ShotResult:
    clip: str
    file: str
    shot: int
    start: float
    end: float
    framing: str
    expected: list[str]
    frames: int = 0
    frames_with_faces: int = 0
    small_faces: int = 0
    unknown_faces: int = 0
    duplicates: dict[str, int] = field(default_factory=dict)  # second face that looks like X
    hits: dict[str, list[float]] = field(default_factory=dict)  # member -> sims of matched faces
    best: dict[str, list[float]] = field(default_factory=dict)  # member -> best sim per frame, matched or not
    unexpected: dict[str, int] = field(default_factory=dict)
    worst: list[tuple[float, float, str]] = field(default_factory=list)  # (score, time, why)
    verdict: str = ""
    reasons: list[str] = field(default_factory=list)


def analyse(files: list[Path], members: list[CastMember], backend, shots_by_clip: dict[str, list[ShotSpec]],
            fps: float, threshold: float, min_face: int, frames_dir: Path | None, max_frames_per_shot: int = 3):
    import cv2

    ids = [m.id for m in members]
    results: list[ShotResult] = []
    for path in files:
        clip = match_clip(path.stem, list(shots_by_clip)) if shots_by_clip else None
        specs = shots_by_clip.get(clip) if clip else None
        if not specs:
            specs = [ShotSpec(path.stem, 1, 0.0, 1e9, "", [])]
        shot_res = [ShotResult(clip or path.stem, path.name, s.index, s.start, s.end, s.framing, s.cast) for s in specs]
        keep: dict[int, list[tuple[float, float, np.ndarray, list]]] = {i: [] for i in range(len(specs))}
        for t, frame in iter_frames(path, fps):
            k = next((i for i, s in enumerate(specs) if s.start <= t < s.end), None)
            if k is None:
                continue
            s = specs[k]
            just_after_cut = s.index > 1 and t - s.start < CUT_GUARD_S
            just_before_cut = k + 1 < len(specs) and s.end - t < CUT_GUARD_S
            if just_after_cut or just_before_cut:
                continue
            r = shot_res[k]
            r.frames += 1
            faces = [f for f in backend.faces(frame) if f.score >= 0.5]
            big = [f for f in faces if f.height >= min_face]
            r.small_faces += len(faces) - len(big)
            if not big:
                continue
            r.frames_with_faces += 1
            assigned = assign(big, members, threshold)
            frame_best = {m: -1.0 for m in ids}
            for f, who, sim, sims in assigned:
                for j, m in enumerate(ids):
                    frame_best[m] = max(frame_best[m], float(sims[j]))
                if who is None:
                    twin = lookalike(sims, members, threshold)
                    if twin:
                        r.duplicates[twin] = r.duplicates.get(twin, 0) + 1
                    else:
                        r.unknown_faces += 1
                elif who in s.cast or not s.cast:
                    r.hits.setdefault(who, []).append(sim)
                else:
                    r.unexpected[who] = r.unexpected.get(who, 0) + 1
            for m in ids:
                r.best.setdefault(m, []).append(frame_best[m])
            # frame badness: expected people missing or strangers present
            missing = [c for c in s.cast if not any(w == c for _, w, _, _ in assigned)]
            bad = len(missing) + sum(1 for _, w, _, _ in assigned if w is None or (s.cast and w not in s.cast))
            if bad and frames_dir is not None:
                keep[k].append((bad, t, frame, assigned))
        for k, r in enumerate(shot_res):
            judge(r, threshold)
            if frames_dir is not None and r.verdict in ("REDO", "CHECK") and keep[k]:
                frames_dir.mkdir(parents=True, exist_ok=True)
                for bad, t, frame, assigned in sorted(keep[k], key=lambda x: -x[0])[:max_frames_per_shot]:
                    img = frame.copy()
                    for f, who, sim, sims_row in assigned:
                        x1, y1, x2, y2 = [int(v) for v in f.bbox]
                        ok = who is not None and (not r.expected or who in r.expected)
                        color = (60, 200, 60) if ok else (40, 40, 230)
                        twin = None if who else lookalike(sims_row, members, threshold)
                        tag = who or (f"2nd {twin}" if twin else "?")
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(img, f"{tag} {sim:.2f}", (x1, max(12, y1 - 5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
                    name = f"{r.clip}_shot{r.shot}_{t:06.2f}s.jpg"
                    cv2.imencode(".jpg", img)[1].tofile(str(frames_dir / name))
            results.append(r)
    return results


def judge(r: ShotResult, threshold: float) -> None:
    """PASS / CHECK / REDO / SMALL / NOFACE for one shot."""
    if r.frames_with_faces == 0:
        if r.small_faces:
            r.verdict = "SMALL"
            r.reasons.append("faces too small to judge; check costume and position by eye")
        else:
            r.verdict = "NOFACE" if r.expected else "PASS"
            if r.expected:
                r.reasons.append("no face detected")
        return
    n = r.frames_with_faces
    redo, check = False, False
    for c in r.expected:
        hits = r.hits.get(c, [])
        ratio = len(hits) / n
        med = statistics.median(hits) if hits else None
        if ratio < 0.3:
            redo = True
            best = statistics.median(r.best.get(c, [-1.0]))
            r.reasons.append(f"{c} found in {ratio:.0%} of frames (best match median {best:.2f})")
        elif ratio < 0.6 or (med is not None and med < threshold + 0.1):
            check = True
            r.reasons.append(f"{c} found in {ratio:.0%} of frames, median similarity {med:.2f}")
    for c, k in r.unexpected.items():
        if k / n >= 0.3:
            redo = True
            r.reasons.append(f"{c} appears in {k / n:.0%} of frames but is not in this shot")
        else:
            check = True
            r.reasons.append(f"{c} appears in {k} frame(s) but is not in this shot")
    for c, k in r.duplicates.items():
        if k / n >= 0.3:
            redo = True
            r.reasons.append(f"a second face looks like {c} in {k / n:.0%} of frames: identity duplicated onto another person")
        else:
            check = True
            r.reasons.append(f"a second face looks like {c} in {k} frame(s)")
    if r.expected and r.unknown_faces / n >= 0.5:
        check = True
        r.reasons.append(f"faces matching nobody in {r.unknown_faces} frame(s): possible identity drift or an extra person")
    r.verdict = "REDO" if redo else ("CHECK" if check else "PASS")


# --------------------------------------------------------------------------- reports

ORDER = {"REDO": 0, "NOFACE": 1, "CHECK": 2, "SMALL": 3, "PASS": 4}


def write_reports(results: list[ShotResult], members: list[CastMember], out: Path, threshold: float) -> str:
    out.mkdir(parents=True, exist_ok=True)
    ids = [m.id for m in members]
    with (out / "face_report.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clip", "file", "shot", "start", "end", "framing", "expected", "verdict", "frames",
                    "frames_with_faces", "small_faces", "unknown_faces", "duplicates"]
                   + [f"{m}_hit_ratio" for m in ids] + [f"{m}_median_sim" for m in ids] + ["reasons"])
        for r in results:
            n = max(1, r.frames_with_faces)
            w.writerow([r.clip, r.file, r.shot, r.start, r.end if r.end < 1e8 else "", r.framing, " ".join(r.expected),
                        r.verdict, r.frames, r.frames_with_faces, r.small_faces, r.unknown_faces,
                        " ".join(f"{k}:{v}" for k, v in sorted(r.duplicates.items()))]
                       + [f"{len(r.hits.get(m, [])) / n:.2f}" for m in ids]
                       + [f"{statistics.median(r.hits[m]):.3f}" if r.hits.get(m) else "" for m in ids]
                       + ["; ".join(r.reasons)])
    lines = ["# Face consistency report", "",
             f"threshold {threshold:.2f} (cosine similarity, InsightFace buffalo_l)", "",
             "| clip | shot | framing | expected | verdict | faces found (median similarity) | reasons |",
             "|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: (x.clip, x.shot)):
        n = max(1, r.frames_with_faces)
        found = ", ".join(f"{m} {len(v) / n:.0%} ({statistics.median(v):.2f})" for m, v in sorted(r.hits.items()))
        lines.append(f"| {r.clip} | {r.shot} | {r.framing} | {' '.join(r.expected) or '-'} | **{r.verdict}** | "
                     f"{found or '-'} | {'; '.join(r.reasons) or '-'} |")
    counts = {v: sum(1 for r in results if r.verdict == v) for v in ORDER}
    lines += ["", "Totals: " + ", ".join(f"{k} {v}" for k, v in counts.items() if v)]
    redo = sorted({r.clip for r in results if r.verdict in ("REDO", "NOFACE")})
    if redo:
        lines += ["", "Re-render: " + ", ".join(redo)]
    text = "\n".join(lines) + "\n"
    (out / "face_report.md").write_text(text, encoding="utf-8")
    return text


# --------------------------------------------------------------------------- CLI


def collect_inputs(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    items = sorted(p for p in root.iterdir() if p.suffix.lower() in VIDEO_EXT)
    # sub-folders full of frames count as one clip each
    items += sorted(p for p in root.iterdir() if p.is_dir() and any(q.suffix.lower() in IMAGE_EXT for q in p.iterdir()))
    return items


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("cast", "videos"))
    ap.add_argument("--cast", required=True)
    ap.add_argument("--scene", help="scene YAML: per-shot expected characters (files are matched by clip id in the name)")
    ap.add_argument("--in", dest="inp", help="video file, or folder of videos / frame folders")
    ap.add_argument("--out", default="out/face")
    ap.add_argument("--fps", type=float, default=2.0, help="frames per second to sample (default 2)")
    ap.add_argument("--threshold", type=float, default=0.35, help="minimum cosine similarity for a match (default 0.35)")
    ap.add_argument("--min-face", type=int, default=40, help="faces shorter than this many pixels are not judged (default 40)")
    ap.add_argument("--no-sheet", action="store_true", help="use only face images, not character sheets, as references")
    ap.add_argument("--gpu", action="store_true", help="run InsightFace on CUDA (needs onnxruntime-gpu)")
    args = ap.parse_args(argv)

    backend = InsightFaceBackend(gpu=args.gpu)
    members, problems = load_cast_faces(Path(args.cast), backend, use_sheet=not args.no_sheet)
    for p in problems:
        print(f"warning: {p}")
    print("reference faces: " + ", ".join(f"{m.id}={len(m.embs)}" for m in members))

    if args.command == "cast":
        pairs = sorted(cast_matrix(members), key=lambda x: -x[2])
        print("\nmost similar pairs (higher = easier to confuse):")
        for a, b, s in pairs:
            flag = "  <-- look alike: change hair/costume or face" if s >= SIMILAR_PAIR else ""
            print(f"  {a}-{b}: {s:.2f}{flag}")
        return 0

    if not args.inp:
        ap.error("videos needs --in")
    shots = load_scene_shots(Path(args.scene)) if args.scene else {}
    files = collect_inputs(Path(args.inp))
    if not files:
        print(f"no videos or frame folders in {args.inp}")
        return 1
    out = Path(args.out)
    results = analyse(files, members, backend, shots, args.fps, args.threshold, args.min_face, out / "frames")
    print(write_reports(results, members, out, args.threshold))
    print(f"wrote {out / 'face_report.md'}, {out / 'face_report.csv'} and flagged frames in {out / 'frames'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

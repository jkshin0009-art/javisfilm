"""qclabel: keep the person's own verdicts on cuts as an answer key, with no extra work.

The project calls record() where the person already judges a cut: marks a panel red
or ok, re-bakes chosen panels, fixes a panel's prompt, picks a look for the animatic.
Each call keeps a small copy of the picture and of its gate.json (if any) next to one
JSON line, so the answer key survives cleanups and any checker can be scored against
it later (gatereview.py labels).

Call it BEFORE the picture is discarded or overwritten. It never raises and never
blocks for long; FJ_QC_LABELS=off turns it off, FJ_QC_LABELS_DIR moves it. By default
it writes to data/qc_labels under the project root (the folder above the one this
file sits in, e.g. film_assistant/ for film_assistant/core/qclabel.py), whatever the
working folder is. Self-contained: copy this file into the project as it is.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

DEFAULT_DIR = "data/qc_labels"
MAX_SIDE = 1024
_lock = threading.Lock()

REDO = ("redo", "red", "bad", "reject", "no")
OK = ("ok", "good", "accept", "yes", "green")


def enabled() -> bool:
    return os.environ.get("FJ_QC_LABELS", "on").strip().lower() not in ("off", "0", "false", "no")


def root_dir(root=None) -> Path:
    if root or os.environ.get("FJ_QC_LABELS_DIR"):
        return Path(root or os.environ["FJ_QC_LABELS_DIR"])
    project = Path(__file__).resolve().parent.parent
    return project / DEFAULT_DIR if (project / "data").is_dir() else Path(DEFAULT_DIR)


def _verdict(v) -> str:
    if v is True:
        return "ok"
    if v is False:
        return "redo"
    s = str(v).strip().lower()
    return "redo" if s in REDO else ("ok" if s in OK else s)


def _axis_status(entry) -> str:
    if isinstance(entry, bool):
        return "pass" if entry else "fail"
    if not isinstance(entry, dict):
        return "unmeasured"
    if entry.get("na"):
        return "na"
    p = entry.get("pass")
    return "pass" if p is True else ("fail" if p is False else "unmeasured")


def _gate_summary(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8-sig"))
    axes = d.get("axes") if isinstance(d.get("axes"), dict) else {}
    st = {k: _axis_status(v) for k, v in axes.items()}
    return {"gate_verdict": str(d.get("verdict") or "").upper() or None,
            "gate_fails": sorted(k for k, s in st.items() if s == "fail"),
            "gate_unmeasured": sorted(k for k, s in st.items() if s == "unmeasured")}


def _copy_image(src: Path, stem: Path) -> str:
    try:
        from PIL import Image
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((MAX_SIDE, MAX_SIDE))
            out = stem.with_suffix(".jpg")
            im.save(out, "JPEG", quality=90)
            return out.name
    except Exception:
        out = stem.with_suffix(src.suffix.lower() or ".png")
        shutil.copy2(src, out)
        return out.name


def record(verdict, image, *, slug: str = "", look: str = "", panel=None, source: str = "",
           note: str = "", root=None) -> Optional[str]:
    """verdict: "redo" / "ok" (or True = ok, False = redo). image: the picture judged.
    Returns the label id, or None when off or when anything went wrong."""
    if not enabled():
        return None
    try:
        r = root_dir(root)
        (r / "img").mkdir(parents=True, exist_ok=True)
        (r / "gate").mkdir(parents=True, exist_ok=True)
        lid = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        src = Path(image) if image else None
        rec = {"id": lid, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": _verdict(verdict),
               "source": source, "slug": slug, "look": look, "panel": panel,
               "image": str(src) if src else "", "copy": None, "sha1": None, "gate": None,
               "gate_verdict": None, "gate_fails": [], "gate_unmeasured": [], "note": note or ""}
        if src is not None and src.is_file():
            rec["sha1"] = hashlib.sha1(src.read_bytes()).hexdigest()
            rec["copy"] = "img/" + _copy_image(src, r / "img" / lid)
            g = src.with_suffix(".gate.json")
            if g.is_file():
                shutil.copy2(g, r / "gate" / f"{lid}.gate.json")
                rec["gate"] = f"gate/{lid}.gate.json"
                try:
                    rec.update(_gate_summary(g))
                except Exception:
                    pass
        with _lock, open(r / "labels.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return lid
    except Exception:
        return None

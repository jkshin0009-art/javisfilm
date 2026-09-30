"""board-check: first-pass review of generated storyboard panels.

A person should only have to look at the panels that are likely wrong. For every
panel this asks the vision model a fixed set of typed questions with the panel
image attached (Jev-style: an answer and a probability, no generated text):

  context   does the image match the panel's own description: overall, people count,
            shot size, action, place, mood (each only when the manifest has that field)
  defect    hands, face, body, text/speech bubble drawn in, duplicated person, bad crop
  identity  (optional, --cast) do the faces belong to the characters the panel names
  continuity (optional) same clothes and hair as the previous panel

and writes review.html: problem panels first, each with the checks that failed and
how sure the model is, plus buttons to mark the model right or wrong. Those marks
export as feedback.csv, and `feedback` turns them into per-check precision so the
thresholds can be tuned on the project's own panels.

Two backends:
  logprobs  any llama-server with --mmproj (chat-upgrade Decider, one question per call,
            the image prefix cached between questions)
  decision  llama-server built with the /decision endpoint (graydini/llama.cpp
            multimodal-decision): every question in one batched pass

  map       MANIFEST              draft the field mapping (board_map.json) from the manifest keys
  run       --board DIR           review every panel, write review.json + review.html
  feedback  --review DIR --csv    precision per check from the marks a person made
  one       --image FILE          check one picture against its cut before it is used
                                  (e.g. as a video's first frame): the same questions plus
                                  the aspect ratio; exit 1 when a check fails, 2 when the
                                  model could not be asked
"""
from __future__ import annotations

import argparse
import base64
import csv
import html
import io
import json
import os
import re
import sys
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "chat-upgrade"))

from chatup.decide import Decider, Question  # noqa: E402
from chatup.llm import LLMClient, LLMError  # noqa: E402

# ---------------------------------------------------------------- checks
SHOTS = ["익스트림 클로즈업", "클로즈업", "미디엄 샷", "풀 샷", "와이드 샷"]
SHOT_WORDS = [
    (0, ("extreme close", "ecu", "익스트림", "초근접", "매크로")),
    (1, ("close", "cu", "클로즈", "바스트", "bust", "근접")),
    (2, ("medium", "mid", "ms", "미디엄", "웨이스트", "허리", "니샷", "knee")),
    (3, ("full", "fs", "풀샷", "풀 샷", "전신")),
    (4, ("wide", "long", "establishing", "ws", "ls", "와이드", "롱", "원경", "설정", "부감")),
]
PEOPLE = ["0명", "1명", "2명", "3명", "4명 이상"]

LABELS = {
    "matches_spec": "콘티와 맞음", "people_count": "인물 수", "shot_size": "샷 크기", "action_ok": "행동",
    "place_ok": "장소", "mood_ok": "표정·감정", "hands_ok": "손", "face_ok": "얼굴", "body_ok": "몸·팔다리",
    "no_text": "글자·말풍선", "no_duplicates": "복제 인물", "framing_ok": "잘림", "identity": "인물 얼굴",
    "continuity": "앞 컷과 옷·머리", "aspect_ok": "화면비",
}

# (name, group, question with {field} slots, fields it needs)
OK_CHECKS = [
    ("matches_spec", "context", "이 그림이 위 콘티 설명의 장면과 맞는가? 인물, 행동, 장소, 구도 중 하나라도 크게 다르면 아니다.",
     ("any",)),
    ("action_ok", "context", "그림 속 인물이 '{action}'을(를) 하고 있는가?", ("action",)),
    ("place_ok", "context", "그림의 장소가 '{location}'(으)로 보이는가?", ("location",)),
    ("mood_ok", "context", "인물의 표정과 분위기가 '{emotion}'에 맞는가?", ("emotion",)),
    ("hands_ok", "defect", "보이는 손이 모두 자연스러운가? 손가락 수나 모양이 이상하면 아니다. 손이 안 보이면 예.", ()),
    ("face_ok", "defect", "보이는 얼굴이 모두 일그러지거나 녹아내린 곳 없이 자연스러운가? 얼굴이 안 보이면 예.", ()),
    ("body_ok", "defect", "팔다리 수, 관절, 몸의 비율이 자연스러운가? 팔다리가 더 있거나 없거나 이상하게 꺾이면 아니다.", ()),
    ("no_text", "defect", "그림 안에 글자, 워터마크, 말풍선이 전혀 없는가?", ()),
    ("no_duplicates", "defect", "같은 사람이 한 그림에 두 번 나오는 것처럼 복제된 인물이 없는가?", ()),
    ("framing_ok", "defect", "주요 인물의 머리나 얼굴이 화면 가장자리에서 어색하게 잘리지 않았는가?", ()),
]

# The first pass asks only these (plus identity/continuity when switched on); --checks full
# asks everything. Fewer questions per panel is most of the speed.
CORE = {"matches_spec", "people_count", "hands_ok", "face_ok", "no_text", "identity", "continuity"}

DEFAULT_MAP = {
    "panels": None, "id": None, "image": None, "image_pattern": "p{n:02d}.png",
    "cast": None, "speaker": None, "shot": None, "action": None, "location": None,
    "emotion": None, "lines": None, "description": None,
}
GUESS = {
    "id": ("id", "panel_id", "pid", "no", "index", "num"),
    "image": ("image", "img", "file", "path", "png", "output", "image_path"),
    "cast": ("characters", "cast", "persons", "people", "chars", "personas", "who"),
    "speaker": ("speaker", "talker", "voice"),
    "shot": ("shot", "shot_size", "framing", "camera", "angle"),
    "action": ("action", "pose", "acting", "motion", "beat"),
    "location": ("location", "place", "set", "background", "bg", "scene_location"),
    "emotion": ("emotion", "mood", "expression", "feeling"),
    "lines": ("lines", "dialogue", "line", "text", "caption"),
    "description": ("description", "desc", "prompt", "visual", "summary", "content"),
}


def shot_index(text: str) -> Optional[int]:
    t = (text or "").lower()
    for idx, words in SHOT_WORDS:
        for w in words:
            if len(w) <= 3:
                if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t):
                    return idx
            elif w in t:
                return idx
    return None


# ---------------------------------------------------------------- manifest
def _dig(obj, path: Optional[str]):
    if not path:
        return obj
    for part in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def find_panels(manifest, path: Optional[str]) -> List[Dict]:
    got = _dig(manifest, path)
    if isinstance(got, list):
        return [p for p in got if isinstance(p, dict)]
    best: List[Dict] = []

    def walk(o):
        nonlocal best
        if isinstance(o, list) and o and all(isinstance(x, dict) for x in o) and len(o) > len(best):
            best = o
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(manifest)
    return best


def guess_map(panels: List[Dict]) -> Dict:
    keys: Dict[str, int] = {}
    for p in panels:
        for k in p:
            keys[k] = keys.get(k, 0) + 1
    m = dict(DEFAULT_MAP)
    for field, cands in GUESS.items():
        for c in cands:
            hit = next((k for k in keys if k.lower() == c), None)
            if hit:
                m[field] = hit
                break
    return m


def as_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple)):
        return ", ".join(as_text(x) for x in v if as_text(x))
    if isinstance(v, dict):
        for k in ("text", "line", "name", "value"):
            if k in v:
                return as_text(v[k])
        return ", ".join(f"{k}: {as_text(x)}" for k, x in v.items() if as_text(x))
    return str(v)


def as_names(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[,/·&]| and ", v) if s.strip()]
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            out += as_names(x.get("name") or x.get("id")) if isinstance(x, dict) else as_names(x)
        return out
    return [str(v)]


def panel_spec(panel: Dict, m: Dict) -> Dict[str, str]:
    spec = {}
    for field in ("speaker", "shot", "action", "location", "emotion", "lines", "description"):
        if m.get(field):
            t = as_text(panel.get(m[field]))
            if t:
                spec[field] = t[:400]
    cast = as_names(panel.get(m["cast"])) if m.get("cast") else []
    if cast:
        spec["cast"] = ", ".join(cast)
    return spec


def spec_text(spec: Dict[str, str]) -> str:
    names = [("shot", "샷"), ("cast", "등장인물"), ("speaker", "말하는 사람"), ("action", "행동"),
             ("location", "장소"), ("emotion", "감정"), ("lines", "대사"), ("description", "설명")]
    lines = [f"{label}: {spec[k]}" for k, label in names if spec.get(k)]
    return "\n".join(lines) if lines else "(콘티 설명 없음)"


def panel_image(board: Path, panel: Dict, m: Dict, n: int) -> Optional[Path]:
    if m.get("image"):
        v = panel.get(m["image"])
        if isinstance(v, str) and v:
            for p in (Path(v), board / v, board / Path(v).name):
                if p.is_file():
                    return p
    if m.get("image_pattern"):
        p = board / m["image_pattern"].format(n=n, id=panel.get(m.get("id") or "", n))
        if p.is_file():
            return p
    return None


# ---------------------------------------------------------------- images
def prepared(src: Path, cache: Path, max_side: int) -> Path:
    """A JPEG no larger than max_side, cached; the original if Pillow is missing."""
    try:
        from PIL import Image
    except ImportError:
        return src
    cache.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{src.parent.name}_{src.stem}_{int(src.stat().st_mtime)}_{max_side}.jpg")
    out = cache / key
    if not out.exists():
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((max_side, max_side))
            im.save(out, "JPEG", quality=90)
    return out


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ---------------------------------------------------------------- backends
class LogprobBackend:
    """One Jev-style question per call through the chat endpoint; images first, so the
    image and the panel description are a prefix the server can reuse between questions."""

    name = "logprobs"

    def __init__(self, url: str, rotations="adaptive", timeout: float = 120.0) -> None:
        self.decider = Decider(LLMClient(url, timeout=timeout), rotations=rotations)

    def ok(self, images: Sequence[Path], state: str, questions: Dict[str, str]) -> Dict[str, float]:
        out = {}
        for name, text in questions.items():
            d = self.decider.decide(state, Question.noul(text, name=f"bc_{name}"), images=[str(p) for p in images])
            out[name] = d.yes if d.confidence is not None else float("nan")
        return out

    def choice(self, images: Sequence[Path], state: str, name: str, text: str, options: List[str]) -> Dict[str, float]:
        d = self.decider.decide(state, Question.choice(text, options, name=f"bc_{name}"), images=[str(p) for p in images])
        return dict(d.distribution) if d.confidence is not None else {}


class DecisionBackend:
    """POST /decision (graydini/llama.cpp multimodal-decision): all questions about one
    image set in one batched pass. Booleans come back with the probability of the chosen
    value; enums with the chosen value and its probability only."""

    name = "decision"

    def __init__(self, url: str, timeout: float = 120.0) -> None:
        base = url.rstrip("/")
        self.url = (base[:-3] if base.endswith("/v1") else base) + "/decision"
        self.timeout = timeout
        self.pending: Dict[str, Dict] = {}

    def _post(self, body: Dict) -> Dict:
        req = urllib.request.Request(self.url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise LLMError(f"HTTP {e.code} from {self.url}: {e.read().decode('utf-8', 'replace')[:300]}") from None
        except (urllib.error.URLError, OSError) as e:
            raise LLMError(f"cannot reach {self.url}: {e}") from None

    def ask_all(self, images: Sequence[Path], state: str, oks: Dict[str, str],
                choices: Dict[str, Tuple[str, List[str]]]) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        props = {n: {"type": "boolean", "description": q} for n, q in oks.items()}
        for n, (q, opts) in choices.items():
            props[n] = {"type": "enum", "choices": opts, "description": q}
        body = {"instructions": "Answer each question about the attached storyboard panel image. "
                                "The panel description comes first.",
                "schema": {"properties": props}, "contexts": [state],
                "images": [[b64(p) for p in images]]}
        res = self._post(body)
        fields = ((res.get("results") or [{}])[0]).get("fields") or {}
        ok_out, ch_out = {}, {}
        for n in oks:
            f = fields.get(n) or {}
            p = float(f.get("probability", float("nan")))
            ok_out[n] = p if f.get("value") is True else (1.0 - p if f.get("value") is False else float("nan"))
        for n, (_, opts) in choices.items():
            f = fields.get(n) or {}
            if f.get("value") in opts:
                p = float(f.get("probability", 0.0))
                rest = (1.0 - p) / max(1, len(opts) - 1)
                ch_out[n] = {o: (p if o == f["value"] else rest) for o in opts}
        return ok_out, ch_out

    def ok(self, images, state, questions):
        return self.ask_all(images, state, questions, {})[0]


# ---------------------------------------------------------------- identity
def identity_verdict(assigned, expected: Sequence[str], min_face: float = 40.0) -> Tuple[float, str]:
    """assigned: face_check.assign() output with member ids; expected: cast ids named by the
    panel. Returns (probability the faces are right, reason)."""
    faces = [a for a in assigned if a[0].height >= min_face]
    if not faces or not expected:
        return 1.0, ""
    got = {a[1] for a in faces if a[1]}
    extra = sorted(got - set(expected))
    if extra:
        return 0.1, "not in this panel: " + ", ".join(extra)
    if not got & set(expected):
        return 0.3, "no face matches the panel's characters"
    return 1.0, ""


class Identity:
    def __init__(self, cast_path: Path, threshold: float, gpu: bool) -> None:
        sys.path.insert(0, str(HERE.parent / "h3-multicast"))
        import face_check as fc
        self.fc = fc
        self.backend = fc.InsightFaceBackend(gpu=gpu)
        self.members, self.problems = fc.load_cast_faces(cast_path, self.backend)
        self.threshold = threshold
        self.lock = threading.Lock()          # one face model, shared by the panel workers
        self.by_name = {}
        for m in self.members:
            self.by_name[m.name] = m.id
            self.by_name[m.id] = m.id

    def check(self, image: Path, cast_names: Sequence[str]) -> Tuple[float, str]:
        img = self.fc.read_image(image)
        if img is None:
            return 1.0, ""
        expected = [self.by_name[n] for n in cast_names if n in self.by_name]
        with self.lock:
            faces = self.backend.faces(img)
        return identity_verdict(self.fc.assign(faces, self.members, self.threshold), expected)


# ---------------------------------------------------------------- run
def status_of(p_bad: float, th_bad: float, th_check: float) -> str:
    if p_bad != p_bad:      # nan: no reading
        return "check"
    return "bad" if p_bad >= th_bad else ("check" if p_bad >= th_check else "ok")


RANK = {"bad": 0, "check": 1, "ok": 2}


def review_panel(backend, img: Path, spec: Dict[str, str], prev: Optional[Tuple[Path, Dict]] = None,
                 identity: Optional[Identity] = None, continuity: bool = False,
                 only: Optional[set] = None) -> Dict[str, Dict]:
    state = "콘티 설명:\n" + spec_text(spec)
    use = (lambda name: True) if only is None else (lambda name: name in only)
    oks = {}
    for name, group, q, needs in OK_CHECKS:
        if not use(name):
            continue
        if needs == ("any",):
            if not spec:
                continue
        elif any(not spec.get(f) for f in needs):
            continue
        oks[name] = q.format(**{k: v[:120] for k, v in spec.items()})
    choices: Dict[str, Tuple[str, List[str]]] = {}
    exp_shot = shot_index(spec.get("shot", ""))
    if exp_shot is not None and use("shot_size"):
        choices["shot_size"] = ("이 그림의 샷 크기는?", SHOTS)
    n_cast = len(as_names(spec.get("cast"))) if spec.get("cast") else None
    if n_cast and use("people_count"):
        choices["people_count"] = ("그림에 얼굴이나 몸이 보이는 사람은 몇 명인가?", PEOPLE)

    if isinstance(backend, DecisionBackend):
        p_ok, dists = backend.ask_all([img], state, oks, choices)
    else:
        p_ok = backend.ok([img], state, oks)
        dists = {n: backend.choice([img], state, n, q, opts) for n, (q, opts) in choices.items()}

    checks: Dict[str, Dict] = {}
    for name, p in p_ok.items():
        group = next(g for n, g, _, _ in OK_CHECKS if n == name)
        checks[name] = {"group": group, "p_bad": round(1.0 - p, 4) if p == p else float("nan")}
    if "shot_size" in dists and dists["shot_size"]:
        d = dists["shot_size"]
        near = sum(d.get(SHOTS[i], 0.0) for i in range(len(SHOTS)) if abs(i - exp_shot) <= 1)
        seen = max(d, key=d.get)
        checks["shot_size"] = {"group": "context", "p_bad": round(1.0 - near, 4),
                               "note": f"expected {SHOTS[exp_shot]}, looks {seen}"}
    if "people_count" in dists and dists["people_count"]:
        d = dists["people_count"]
        want = PEOPLE[min(n_cast, 4)]
        seen = max(d, key=d.get)
        checks["people_count"] = {"group": "context", "p_bad": round(1.0 - d.get(want, 0.0), 4),
                                  "note": f"expected {want}, looks {seen}"}
    if identity is not None and spec.get("cast") and use("identity"):
        p, why = identity.check(img, as_names(spec["cast"]))
        checks["identity"] = {"group": "identity", "p_bad": round(1.0 - p, 4), "note": why}
    if continuity and prev is not None and use("continuity"):
        prev_img, prev_spec = prev
        shared = set(as_names(spec.get("cast"))) & set(as_names(prev_spec.get("cast")))
        if shared or not (spec.get("cast") or prev_spec.get("cast")):
            q = "두 그림에 함께 나오는 같은 인물의 옷차림과 머리 모양이 같은가? 같은 인물이 없으면 예."
            p = backend.ok([prev_img, img], "첫 그림은 앞 컷, 두 번째 그림은 이번 컷이다.", {"continuity": q})["continuity"]
            checks["continuity"] = {"group": "continuity", "p_bad": round(1.0 - p, 4) if p == p else float("nan")}
    return checks


def aspect_check(img: Path, want: str) -> Dict:
    """want like "16:9". Measured on the file itself, so a picture squeezed into the
    wrong frame fails no matter what any report says."""
    from PIL import Image
    with Image.open(img) as im:
        w, h = im.size
    a, b = (float(x) for x in want.split(":"))
    off = abs((w / h) / (a / b) - 1.0)
    return {"group": "context", "p_bad": 1.0 if off > 0.03 else 0.0, "note": f"expected {want}, got {w}x{h}"}


def cmd_one(a) -> int:
    img = Path(a.image)
    if not img.is_file():
        print(f"no such image: {img}")
        return 2
    spec = {k: v for k, v in (("shot", a.shot), ("cast", a.cast), ("action", a.action),
                              ("location", a.location), ("emotion", a.emotion),
                              ("description", a.description)) if v}
    checks: Dict[str, Dict] = {}
    if a.aspect:
        checks["aspect_ok"] = aspect_check(img, a.aspect)
    backend = DecisionBackend(a.url, a.timeout) if a.backend == "decision" else \
        LogprobBackend(a.url, "adaptive", a.timeout)
    err = ""
    try:
        small = prepared(img, HERE / "work" / "one_cache", a.max_side)
        checks.update(review_panel(backend, small, spec))
    except LLMError as e:
        err = str(e)
    worst = max((c["p_bad"] for c in checks.values() if c["p_bad"] == c["p_bad"]), default=float("nan"))
    st = status_of(worst, a.bad, a.check)
    for k, c in sorted(checks.items(), key=lambda kv: -(kv[1]["p_bad"] if kv[1]["p_bad"] == kv[1]["p_bad"] else 1)):
        p = c["p_bad"]
        mark = status_of(p, a.bad, a.check)
        print(f"{mark:5s} {LABELS.get(k, k)} ({k}) {'?' if p != p else f'{p:.0%}'}  {c.get('note', '')}".rstrip())
    if err:
        print(f"ERROR {err}")
    print(f"RESULT {st}" + ("  (the model was not asked)" if err else ""))
    if a.out:
        Path(a.out).write_text(json.dumps({"image": str(img.resolve()), "spec": spec, "checks": checks,
                                           "status": st, "error": err}, ensure_ascii=False, indent=1),
                               encoding="utf-8")
    return 2 if err else (1 if st == "bad" else 0)


def cmd_map(a) -> int:
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8-sig"))
    panels = find_panels(manifest, a.panels)
    if not panels:
        print("no panel list found")
        return 1
    keys: Dict[str, str] = {}
    for p in panels:
        for k, v in p.items():
            keys.setdefault(k, type(v).__name__)
    print(f"{len(panels)} panels; keys (type only, no values):")
    for k, t in keys.items():
        print(f"  {k}: {t}")
    m = guess_map(panels)
    m["panels"] = a.panels
    out = Path(a.out) if a.out else Path(a.manifest).with_name("board_map.json")
    out.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"draft mapping: {out}\n" + json.dumps(m, ensure_ascii=False, indent=1))
    return 0


def load_map(board: Path, manifest, path: Optional[str]) -> Dict:
    m = dict(DEFAULT_MAP)
    src = Path(path) if path else board / "board_map.json"
    if src.is_file():
        m.update(json.loads(src.read_text(encoding="utf-8-sig")))
    else:
        m.update({k: v for k, v in guess_map(find_panels(manifest, None)).items() if v})
    return m


def cmd_run(a) -> int:
    board = Path(a.board)
    manifest = json.loads((board / a.manifest).read_text(encoding="utf-8-sig"))
    m = load_map(board, manifest, a.map)
    panels = find_panels(manifest, m.get("panels"))
    out = Path(a.out) if a.out else HERE / "work" / board.name
    out.mkdir(parents=True, exist_ok=True)
    rpath = out / "review.json"
    review = json.loads(rpath.read_text(encoding="utf-8")) if rpath.exists() and not a.force else {}
    review.setdefault("board", str(board.resolve()))
    review.setdefault("panels", {})
    backend = DecisionBackend(a.url, a.timeout) if a.backend == "decision" else \
        LogprobBackend(a.url, "adaptive" if a.careful else 1, a.timeout)
    only = None if a.checks == "full" else CORE
    identity = Identity(Path(a.cast), a.face_threshold, a.gpu) if a.cast else None
    if identity is not None:
        for pr in identity.problems:
            print("CAST " + pr)
    want = {s.strip() for s in a.ids.split(",") if s.strip()} if a.ids else None
    t_all = time.perf_counter()
    jobs = []
    prev = None
    for n, panel in enumerate(panels, start=1):
        pid = str(panel.get(m["id"]) if m.get("id") and panel.get(m["id"]) is not None else f"p{n:02d}")
        img = panel_image(board, panel, m, n)
        spec = panel_spec(panel, m)
        if img is None:
            review["panels"][pid] = {"n": n, "image": None, "status": "check", "checks": {},
                                     "error": "image not found"}
            prev = None
            continue
        small = prepared(img, out / "cache", a.max_side)
        skip = (want and pid not in want) or (a.limit and len(jobs) >= a.limit) or \
            (pid in review["panels"] and not a.force and not review["panels"][pid].get("error"))
        if not skip:
            jobs.append((pid, n, img, small, spec, prev))
        prev = (small, spec)

    lock = threading.Lock()

    def work(job) -> None:
        pid, n, img, small, spec, prev_panel = job
        t0 = time.perf_counter()
        try:
            checks = review_panel(backend, small, spec, prev_panel, identity, a.continuity, only)
            err = ""
        except LLMError as e:
            checks, err = {}, str(e)
        worst = max((c["p_bad"] for c in checks.values() if c["p_bad"] == c["p_bad"]), default=float("nan"))
        st = "check" if err else status_of(worst, a.bad, a.check)
        rec = {"n": n, "image": str(img.resolve()), "spec": spec, "checks": checks, "status": st,
               "worst": worst if worst == worst else None, "ms": round((time.perf_counter() - t0) * 1000),
               "error": err}
        flagged = [f"{LABELS.get(k, k)} {c['p_bad']:.0%}" for k, c in checks.items()
                   if c["p_bad"] == c["p_bad"] and c["p_bad"] >= a.check]
        with lock:
            review["panels"][pid] = rec
            print(f"{pid:>6} {st:5s} {(time.perf_counter() - t0):5.1f}s  {'; '.join(flagged) or err}", flush=True)
            rpath.write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")

    # Panels are independent, so several go to the server at once; each panel's own
    # questions stay in order in one worker, which keeps its image in one slot's cache.
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        list(ex.map(work, jobs))
    done = len(jobs)
    review.update({"backend": backend.name, "thresholds": {"bad": a.bad, "check": a.check},
                   "updated": time.strftime("%Y-%m-%d %H:%M:%S")})
    rpath.write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    write_html(out, review)
    counts = {s: sum(1 for p in review["panels"].values() if p["status"] == s) for s in ("bad", "check", "ok")}
    secs = time.perf_counter() - t_all
    print(f"RESULT panels {len(review['panels'])}: bad {counts['bad']}, check {counts['check']}, ok {counts['ok']}"
          f"  ({done} reviewed in {secs:.0f} s, {secs / max(1, done):.1f} s each)")
    print(f"Open {out / 'review.html'}")
    (out / "summary.md").write_text(summary_md(review, secs, done), encoding="utf-8")
    return 0


def summary_md(review: Dict, secs: float, done: int) -> str:
    """Counts only: no descriptions, dialogue or names, so it can be shared."""
    ps = list(review["panels"].values())
    lines = ["# board-check summary", "", f"- backend: {review.get('backend')}  thresholds: {review.get('thresholds')}",
             f"- panels: {len(ps)}  reviewed this run: {done}  time: {secs:.0f} s ({secs / max(1, done):.1f} s per panel)",
             "- status: " + ", ".join(f"{s} {sum(1 for p in ps if p['status'] == s)}" for s in ("bad", "check", "ok")),
             "", "| check | panels asked | flagged bad | flagged check | median p_bad |", "|---|---|---|---|---|"]
    th = review.get("thresholds") or {"bad": 0.7, "check": 0.4}
    names = []
    for p in ps:
        for k in p.get("checks", {}):
            if k not in names:
                names.append(k)
    for k in names:
        vals = sorted(p["checks"][k]["p_bad"] for p in ps if k in p.get("checks", {})
                      and p["checks"][k]["p_bad"] == p["checks"][k]["p_bad"])
        if not vals:
            continue
        bad = sum(1 for v in vals if v >= th["bad"])
        chk = sum(1 for v in vals if th["check"] <= v < th["bad"])
        lines.append(f"| {LABELS.get(k, k)} ({k}) | {len(vals)} | {bad} | {chk} | {vals[len(vals) // 2]:.2f} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- html
def write_html(out: Path, review: Dict) -> None:
    th = review.get("thresholds") or {"bad": 0.7, "check": 0.4}
    items = sorted(review["panels"].items(), key=lambda kv: (RANK.get(kv[1]["status"], 1),
                                                             -(kv[1].get("worst") or 0), kv[1]["n"]))
    cards = []
    for pid, p in items:
        chips = []
        for k, c in sorted(p.get("checks", {}).items(), key=lambda kv: -(kv[1]["p_bad"] if kv[1]["p_bad"] == kv[1]["p_bad"] else 1)):
            v = c["p_bad"]
            if v != v:
                cls, txt = "check", "?"
            elif v >= th["bad"]:
                cls, txt = "bad", f"{v:.0%}"
            elif v >= th["check"]:
                cls, txt = "check", f"{v:.0%}"
            else:
                continue
            note = f" – {html.escape(c['note'])}" if c.get("note") else ""
            chips.append(f'<button class="chip {cls}" data-check="{k}" title="누르면 오판으로 표시">'
                         f'{html.escape(LABELS.get(k, k))} {txt}{note}</button>')
        spec = "<br>".join(html.escape(l) for l in spec_text(p.get("spec") or {}).split("\n"))
        img = Path(p["image"]).as_uri() if p.get("image") else ""
        err = f'<div class="err">{html.escape(p["error"])}</div>' if p.get("error") else ""
        cards.append(
            f'<div class="card {p["status"]}" data-id="{html.escape(pid)}" data-status="{p["status"]}">'
            f'<a href="{img}" target="_blank"><img loading="lazy" src="{img}"></a>'
            f'<div class="body"><div class="head"><b>{html.escape(pid)}</b> <span class="st">{p["status"]}</span>'
            f'<span class="verdict"><button data-v="ok">통과 (1)</button><button data-v="redo">다시 (2)</button></span></div>'
            f'<div class="chips">{"".join(chips) or "<i>문제 없음</i>"}</div>{err}<div class="spec">{spec}</div></div></div>')
    counts = {s: sum(1 for _, p in items if p["status"] == s) for s in ("bad", "check", "ok")}
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>콘티 검수</title><style>
:root{{--bg:#fafafa;--fg:#222;--card:#fff;--line:#ddd;--bad:#c62828;--check:#b26a00;--ok:#2e7d32;--sel:#1565c0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--bad:#ef5350;--check:#ffb74d;--ok:#81c784;--sel:#64b5f6}}}}
body{{margin:0;padding:12px 16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}}
.bar{{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:2}}
.bar button{{margin-right:6px}} .card{{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);
border-left:6px solid var(--line);border-radius:6px;margin:10px 0;padding:10px}}
.card.bad{{border-left-color:var(--bad)}} .card.check{{border-left-color:var(--check)}} .card.ok{{border-left-color:var(--ok)}}
.card.sel{{outline:2px solid var(--sel)}} .card img{{width:320px;max-width:40vw;border-radius:4px}}
.body{{flex:1;min-width:0}} .chips{{margin:6px 0}} .chip{{border:1px solid;border-radius:12px;padding:2px 8px;margin:2px;
background:transparent;color:inherit;cursor:pointer}} .chip.bad{{border-color:var(--bad);color:var(--bad)}}
.chip.check{{border-color:var(--check);color:var(--check)}} .chip.disputed{{text-decoration:line-through;opacity:.5}}
.spec{{font-size:12px;opacity:.8}} .verdict{{float:right}} .verdict button.on[data-v=ok]{{background:var(--ok);color:#fff}}
.verdict button.on[data-v=redo]{{background:var(--bad);color:#fff}} .err{{color:var(--bad)}}
@media (max-width:640px){{.card{{flex-direction:column}} .card img{{width:100%;max-width:100%}}}}
</style>
<div class="bar"><b>콘티 검수</b> 문제 {counts['bad']} · 확인 {counts['check']} · 통과 {counts['ok']}
 &nbsp; <button data-f="all">전체</button><button data-f="bad">문제</button><button data-f="check">확인</button><button data-f="ok">통과</button>
 <button id="csv">판정 CSV 내보내기</button> <small>j/k 이동 · 1 통과 · 2 다시 · 칩 클릭 = 오판 표시</small></div>
<div id="list">{''.join(cards)}</div>
<script>
const KEY='boardcheck:'+{json.dumps(review.get('board', ''))};
let marks={{}};try{{marks=JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch(e){{}}
const save=()=>{{try{{localStorage.setItem(KEY,JSON.stringify(marks))}}catch(e){{}}}};
const cards=[...document.querySelectorAll('.card')];let cur=0;
function paint(c){{const m=marks[c.dataset.id]||{{}};c.querySelectorAll('.verdict button').forEach(b=>b.classList.toggle('on',m.v===b.dataset.v));
 c.querySelectorAll('.chip').forEach(b=>b.classList.toggle('disputed',(m.d||[]).includes(b.dataset.check)));}}
function sel(i){{if(!cards.length)return;cards[cur].classList.remove('sel');cur=Math.max(0,Math.min(cards.length-1,i));
 cards[cur].classList.add('sel');cards[cur].scrollIntoView({{block:'center'}});}}
cards.forEach((c,i)=>{{paint(c);c.addEventListener('click',()=>{{cards[cur].classList.remove('sel');cur=i;c.classList.add('sel')}});
 c.querySelectorAll('.verdict button').forEach(b=>b.onclick=()=>{{const m=marks[c.dataset.id]||(marks[c.dataset.id]={{}});
  m.v=m.v===b.dataset.v?undefined:b.dataset.v;save();paint(c)}});
 c.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{{const m=marks[c.dataset.id]||(marks[c.dataset.id]={{}});m.d=m.d||[];
  const k=b.dataset.check;m.d=m.d.includes(k)?m.d.filter(x=>x!==k):m.d.concat([k]);save();paint(c)}});}});
document.addEventListener('keydown',e=>{{if(e.target.tagName==='INPUT')return;const c=cards[cur];
 if(e.key==='j')sel(cur+1);else if(e.key==='k')sel(cur-1);
 else if((e.key==='1'||e.key==='2')&&c){{const m=marks[c.dataset.id]||(marks[c.dataset.id]={{}});m.v=e.key==='1'?'ok':'redo';save();paint(c);sel(cur+1)}}}});
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>cards.forEach(c=>c.style.display=
 (b.dataset.f==='all'||c.dataset.status===b.dataset.f)?'':'none'));
document.getElementById('csv').onclick=()=>{{const rows=[['panel','status','human','disputed']];
 cards.forEach(c=>{{const m=marks[c.dataset.id]||{{}};rows.push([c.dataset.id,c.dataset.status,m.v||'',(m.d||[]).join(' ')])}});
 const blob=new Blob(['\\ufeff'+rows.map(r=>r.map(x=>'"'+String(x).replace(/"/g,'""')+'"').join(',')).join('\\n')],{{type:'text/csv'}});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='feedback.csv';a.click();}};
sel(0);
</script></html>"""
    (out / "review.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------- feedback
def cmd_feedback(a) -> int:
    out = Path(a.review)
    review = json.loads((out / "review.json").read_text(encoding="utf-8"))
    th = review.get("thresholds") or {"bad": 0.7, "check": 0.4}
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8-sig", newline="")))
    marked = {r["panel"]: r for r in rows if r.get("human")}
    stats: Dict[str, Dict[str, int]] = {}
    missed = 0
    agree_panel = 0
    for pid, r in marked.items():
        p = review["panels"].get(pid)
        if not p:
            continue
        disputed = set((r.get("disputed") or "").split())
        flagged = [k for k, c in p.get("checks", {}).items() if c["p_bad"] == c["p_bad"] and c["p_bad"] >= th["check"]]
        if r["human"] == "redo" and not flagged:
            missed += 1
        if (r["human"] == "redo") == (p["status"] != "ok"):
            agree_panel += 1
        for k in flagged:
            s = stats.setdefault(k, {"flagged": 0, "confirmed": 0, "disputed": 0})
            s["flagged"] += 1
            if k in disputed or r["human"] == "ok":
                s["disputed"] += 1
            else:
                s["confirmed"] += 1
    lines = ["# board-check feedback", "", f"- panels marked by a person: {len(marked)}",
             f"- model and person agree on redo/ok: {agree_panel}/{len(marked)}",
             f"- panels the person sent back that the model passed: {missed}", "",
             "| check | flagged | person agreed | false alarm | precision |", "|---|---|---|---|---|"]
    for k, s in sorted(stats.items(), key=lambda kv: -kv[1]["flagged"]):
        prec = s["confirmed"] / s["flagged"] if s["flagged"] else 0.0
        lines.append(f"| {LABELS.get(k, k)} ({k}) | {s['flagged']} | {s['confirmed']} | {s['disputed']} | {prec:.0%} |")
    lines += ["", "A check with low precision is flagging too much: raise its threshold or drop it. "
                  "Panels sent back but passed are misses: look at what they have in common."]
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


# ---------------------------------------------------------------- cli
def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="boardcheck")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("map")
    p.add_argument("manifest")
    p.add_argument("--panels", default=None, help="dotted path to the panel list, if not found automatically")
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_map)

    p = sub.add_parser("run")
    p.add_argument("--board", required=True, help="folder with the manifest and panel images")
    p.add_argument("--manifest", default="manifest.json")
    p.add_argument("--map", default=None, help="board_map.json (default: next to the manifest, else guessed)")
    p.add_argument("--out", default=None)
    p.add_argument("--url", default="http://127.0.0.1:5678")
    p.add_argument("--backend", choices=("logprobs", "decision"), default="logprobs")
    p.add_argument("--checks", choices=("core", "full"), default="core",
                   help="core: overall match, people count, hands, face, text/bubble (fast); full: all checks")
    p.add_argument("--careful", action="store_true", help="logprobs: read each question in both answer orders")
    p.add_argument("--workers", type=int, default=3, help="panels in flight at once (server slots)")
    p.add_argument("--max-side", type=int, default=1024)
    p.add_argument("--cast", default=None, help="h3-multicast cast.yaml for the face identity check")
    p.add_argument("--face-threshold", type=float, default=0.35)
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--continuity", action="store_true")
    p.add_argument("--bad", type=float, default=0.7)
    p.add_argument("--check", type=float, default=0.4)
    p.add_argument("--ids", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--force", action="store_true")
    p.add_argument("--timeout", type=float, default=120.0)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("one", help="check one picture against its cut, before it becomes a first frame")
    p.add_argument("--image", required=True)
    p.add_argument("--action", default="", help="what the person does, e.g. 'sits at the controls'")
    p.add_argument("--location", default="")
    p.add_argument("--shot", default="")
    p.add_argument("--cast", default="", help="names, comma separated (people count)")
    p.add_argument("--emotion", default="")
    p.add_argument("--description", default="")
    p.add_argument("--aspect", default="", help="expected ratio, e.g. 16:9")
    p.add_argument("--url", default="http://127.0.0.1:5678")
    p.add_argument("--backend", choices=("logprobs", "decision"), default="logprobs")
    p.add_argument("--max-side", type=int, default=1024)
    p.add_argument("--bad", type=float, default=0.7)
    p.add_argument("--check", type=float, default=0.4)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_one)

    p = sub.add_parser("feedback")
    p.add_argument("--review", required=True, help="the run's output folder")
    p.add_argument("--csv", required=True)
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_feedback)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

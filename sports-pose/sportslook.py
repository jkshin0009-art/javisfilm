"""sportslook: find the sports pose asset for a storyboard panel and hand it to a prompt agent.

Standard library only, one file, so a project can copy it (film_assistant/core/sportslook.py).
It reads the built library (library/index.json, library/<sport>/<CODE>/agent.json,
library/sequences.json); it never runs the pose engine.

  match(text)            which assets a panel text asks for (Korean or English), best first
  pack(text, ...)        everything a prompt agent needs for the best asset: guide text for the
                         LLM, the prompt with {SUBJECT} {PARTNER_B} {SETTING} filled, the negative,
                         the OpenPose control image of the camera the text asks for, scene rules
  Hook(root)             the same behind a switch file (off / observe / act) with a log that holds
                         asset codes and times only, never panel text

CLI:
  python sportslook.py match "태권도 선수가 돌려차기를 찬다"
  python sportslook.py pack "배구 스파이크 측면" --subject "a tall woman in a red jersey" --setting "indoor arena"
  python sportslook.py scan manifest.json          which panels of a storyboard would use an asset
  python sportslook.py report hooks.jsonl          counts from a Hook log

The library is found at $SPORTS_POSE_LIBRARY, else next to this file (sports-pose/library).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# words that name the sport (or a role only that sport has); a panel that names one of these
# only matches assets of that sport
SPORT_WORDS = {
    "volleyball": ["배구", "volleyball"],
    "soccer": ["축구", "soccer", "football", "골키퍼", "goalkeeper"],
    "baseball": ["야구", "baseball", "투수", "타자", "pitcher", "batter"],
    "basketball": ["농구", "basketball"],
    "tennis": ["테니스", "tennis"],
    "badminton": ["배드민턴", "badminton", "셔틀콕", "shuttlecock"],
    "fishing": ["낚시", "낚싯대", "fishing", "angler", "fishing rod"],
    "boxing": ["권투", "복싱", "복서", "boxing", "boxer"],
    "taekwondo": ["태권도", "taekwondo"],
    "swimming": ["수영", "swimming", "swimmer"],
    "judo": ["유도", "judo", "judoka"],
    "wrestling": ["레슬링", "wrestling", "wrestler", "그레코로만", "greco-roman"],
}
# words in asset names that say nothing about the movement
STOP = {"자세", "순간", "준비", "기본", "동작", "장면", "선수", "경기", "the", "a", "an", "of", "to", "at", "on",
        "in", "with", "and", "for", "position", "pose", "moment", "player", "athlete"}
# everyday (or film-set) words: they count toward a match only when the panel also names the sport
COMMON = {
    # Korean
    "공", "놓는", "뒤로", "젖히기", "젖힘", "다리", "들기", "팔", "손", "발", "몸", "몸통", "잡기", "방향", "10시", "1시",
    "위", "앞", "옆", "뒤", "점프", "착지", "걸린", "고기", "리드", "무릎", "굽힘", "후", "직전", "마지막", "스텝", "당기기",
    "공중", "뻗기", "들어가기", "누운", "옆으로", "쏘는", "맞는", "날리기", "수비", "공격", "셋", "포인트", "로우", "숏",
    "정점", "가속", "최대", "도약", "킥", "펀치", "패스", "토스", "로드", "대인", "낮은", "복식", "디펜스", "라이트",
    # English
    "shot", "set", "start", "ready", "point", "balance", "release", "lift", "knee", "front", "high", "guard", "hand",
    "hands", "arm", "arms", "body", "lock", "grip", "standard", "landing", "throw", "bow", "arrow", "fish", "load",
    "contact", "impact", "step", "stride", "foot", "plant", "follow-through", "pass", "hit", "drive", "save", "dive",
    "diving", "full", "stretch", "power", "wind-up", "windup", "peak", "right", "left", "lead", "rear", "straight",
    "open", "low", "short", "back", "stop", "forward", "over", "water", "jump", "jumping", "kick", "kicking", "track",
    "block", "blocking", "final", "approach", "reach", "air", "cast", "casting", "pocket", "duel", "attack", "defense",
    "defensive", "slide", "net", "rim", "one-hand", "double", "two-handed", "double-handed", "underhand", "overhead",
    "side", "side-on", "first-time", "recovery", "breath", "breathing", "stroke", "marks", "take", "your", "toss",
    "serve", "cross", "hook", "jab", "dig", "platform", "bump", "hitter", "pitch", "pitching", "bat", "batting", "swing",
    "header", "headed", "goal", "smash", "bent", "pumping", "loaded", "rotation", "max", "external", "foot-down",
    "plant", "takeoff", "backswing", "cocking", "cock", "lay", "trophy", "loading", "net shot", "wind", "down", "leg",
    "legs", "step", "fighting", "reeling", "punch", "stance", "shoulder", "sleeve", "lapel", "moment", "save",
}
# words with another everyday or film meaning (블로킹 = actor blocking, 파이팅 = a cheer, 캐스팅 = casting):
# they never trigger a match without the sport's name
AMBIGUOUS = {"다이빙", "스탠스", "스트레이트", "크로스", "파이팅", "블로킹", "블로커", "스트로크", "버터플라이", "캐스팅",
             "태클", "가드", "세트", "서브", "스윙", "슈팅", "타격", "원투", "헤딩", "훅", "잽", "슛", "스매시", "스매싱",
             "런지", "클린치", "양다리", "스트라이드"}
# words that name one sport's movement so clearly that the sport's name may be left out
SPORT_IMPLIED = {"자유형": "swimming", "평영": "swimming", "접영": "swimming", "배영": "swimming", "스타트대": "swimming",
                 "덩크": "basketball", "레이업": "basketball", "점프슛": "basketball", "투구": "baseball",
                 "강속구": "baseball", "업어치기": "judo", "낙법": "judo", "메치기": "judo", "돌려차기": "taekwondo",
                 "뒤차기": "taekwondo", "리시브": "volleyball"}
# verbs in a panel -> the movement words assets use (count only once the sport is known)
ALIASES = {"던지": ["투구", "pitch", "캐스팅", "cast"], "던진": ["투구", "pitch", "캐스팅", "cast"],
           "숨": ["호흡", "breath", "breathing"], "차는": ["킥", "kick"], "찬다": ["킥", "kick"], "걷어차": ["킥", "kick"],
           "친다": ["타격", "hit", "swing"], "치는": ["타격", "hit", "swing"], "때리": ["hit", "impact", "타점"],
           "주먹": ["펀치", "punch"], "메치": ["메치기", "throw"], "잡고": ["잡기", "grip"], "잡는": ["잡기", "grip"]}
# the moment a single-frame asset usually shows, preferred when a panel does not name the phase
KEY_PHASES = ("contact", "impact", "release", "extension", "landing", "kake", "grip", "guard", "breath")
# camera words in a panel -> words in the asset's camera names
CAMERA_WORDS = [
    (("측면", "옆모습", "옆에서", "프로필", "side view", "profile"), ("side",)),
    (("정면", "앞에서", "front view", "facing camera"), ("front",)),
    (("와이드", "전경", "풀샷", "원경", "wide shot", "establishing"), ("wide", "cinema")),
    (("로우앵글", "로우 앵글", "낮은 앵글", "아래에서 올려", "low angle"), ("low",)),
    (("부감", "위에서 내려", "하이앵글", "하이 앵글", "overhead", "high angle", "bird"), ("overhead", "high")),
    (("뒤에서", "등 뒤", "어깨 너머", "over the shoulder", "from behind"), ("shoulder", "behind", "rear")),
    (("수중", "물속", "underwater"), ("underwater",)),
]
_KO = re.compile(r"[가-힣]")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _has(text: str, word: str) -> bool:
    """Korean words match inside longer words (particles attach: 돌려차기를); English words match whole."""
    if _KO.search(word):
        return word in text
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text) is not None


def default_root() -> Path:
    env = os.environ.get("SPORTS_POSE_LIBRARY")
    return Path(env) if env else Path(__file__).resolve().parent / "library"


class Library:
    def __init__(self, root: Optional[os.PathLike] = None):
        self.root = Path(root) if root else default_root()
        rows = json.loads((self.root / "index.json").read_text(encoding="utf-8"))["assets"]
        self.rows = {r["code"]: r for r in rows}
        p = self.root / "sequences.json"
        self.sequences = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
        self._agents: Dict[str, Dict] = {}
        self._index()

    def _index(self) -> None:
        """Movement words of every asset, weighted 1 / number of sports that use the word, and the
        asset names (minus the sport word) that are specific enough to trigger a match on their own."""
        sport_words = {w for ws in SPORT_WORDS.values() for w in ws}
        self.words: Dict[str, List[str]] = {}
        names_left: Dict[str, List[List[str]]] = {}
        where: Dict[str, set] = {}
        for code, r in self.rows.items():
            ws, lefts = set(), []
            for n in (_norm(n) for n in r["names"].get("ko", []) + r["names"].get("en", [])):
                for w in sorted(sport_words, key=len, reverse=True):
                    n = n.replace(w, " ")
                toks = [t for t in re.split(r"[\s,()/]+", n) if t and t not in STOP]
                ws.update(t for t in toks if _KO.search(t) or len(t) >= 3)
                if toks:
                    lefts.append(toks)
            for k in r.get("keywords", []):
                k = _norm(k)
                if k not in sport_words and k not in STOP and len(k) >= 3:
                    ws.add(k)
            self.words[code], names_left[code] = sorted(ws), lefts
            for t in ws:
                where.setdefault(t, set()).add(r["sport"])
        self.weight = {t: 1.0 / len(s) for t, s in where.items()}

        def specific(tok: str) -> bool:
            return (tok not in COMMON and tok not in AMBIGUOUS and self.weight.get(tok, 0) >= 0.5
                    and (len(tok) >= 2 if _KO.search(tok) else len(tok) >= 4))
        self.phrases = {code: sorted({" ".join(toks) for toks in lefts if any(specific(t) for t in toks)
                                      and (len(toks) >= 2 or _KO.search(toks[0]))})
                        for code, lefts in names_left.items()}

    def agent(self, code: str) -> Dict:
        if code not in self._agents:
            r = self.rows[code]
            base = self.root / r["sport"] / code
            a = json.loads((base / "agent.json").read_text(encoding="utf-8"))
            a["_dir"] = str(base)
            self._agents[code] = a
        return self._agents[code]

    # ------------------------------------------------------------ matching
    def match(self, text: str, k: int = 3) -> List[Tuple[float, str]]:
        """Assets the text asks for, best first. Empty when the text names no movement we have:
        the caller then writes the prompt as before (never force the nearest asset)."""
        t = _norm(text)
        sports = {s for s, ws in SPORT_WORDS.items() if any(_has(t, w) for w in ws)}
        if not sports:                             # 자유형, 덩크, 업어치기 ... name the sport by themselves
            sports = {s for w, s in SPORT_IMPLIED.items() if _has(t, w)}
        extra = " ".join(x for v, xs in ALIASES.items() if v in t for x in xs)
        tt = t + " " + extra if extra else t     # verbs count as movement words, never as the sport
        out = []
        for code, r in self.rows.items():
            if sports and r["sport"] not in sports:
                continue
            tech = sum(self.weight[w] for w in self.words[code] if _has(tt, w))
            phrase = any(_has(t, p) for p in self.phrases[code])
            if not ((r["sport"] in sports and tech >= 0.3) or phrase):
                continue
            s = 1.5 * (r["sport"] in sports) + tech + 2.0 * phrase + 0.1 * (r.get("phase") in KEY_PHASES)
            out.append((round(s, 2), code))
        out.sort(key=lambda x: (-x[0], x[1]))
        return out[:k]

    def camera(self, agent: Dict, text: str) -> Dict:
        """The asset camera the panel text asks for (side, front, wide, low, high, behind); else the first."""
        t = _norm(text)
        cams = agent["cameras"]
        best, best_s = cams[0], 0
        for cam in cams:
            label = (cam["name"] + " " + cam.get("words", "")).lower()
            s = sum(1 for said, want in CAMERA_WORDS if any(_has(t, w) for w in said) and any(x in label for x in want))
            if s > best_s:
                best, best_s = cam, s
        return best

    # ------------------------------------------------------------ what the prompt agent gets
    def guide(self, agent: Dict, cam: Dict, full: bool = False) -> str:
        """Instructions plus the asset text, to put in the prompt agent's request (English: the image
        prompt is English)."""
        others = "".join(f", {{PARTNER_{p['id']}}} (the {p['role']})" for p in agent.get("partners", []))
        lines = [f"SPORTS POSE ASSET #{agent['code']} (a checked skeleton; follow it exactly)",
                 f"This panel shows: {agent['summary']}",
                 "When you write the image prompt for this panel:",
                 "- Copy the body sentences of the template below word for word. Keep the angles, left and right, "
                 "which hand or foot, the hand shapes, the foot contact and where the hands touch the other athlete.",
                 f"- Fill only {{SUBJECT}} (the character's look from the cast){others} and {{SETTING}} "
                 "(place, light, time of day).",
                 "- Add no pose words of your own (such as 'dynamic pose' or 'arms raised').",
                 f"- Camera: {cam['words']} {cam.get('text', '')} The pose control image matches this camera.",
                 "", "Template:", agent["prompt"]]
        if agent.get("scene_rules"):
            lines += ["", "If the panel shows the whole match, keep to these rules:"]
            lines += [f"- {x}" for x in agent["scene_rules"]]
        if full:
            lines += ["", "Full asset (copy any line you need word for word):", agent["block"]]
        return "\n".join(lines)

    def pack(self, text: str, subject: Optional[str] = None, setting: Optional[str] = None,
             partners: Optional[Dict[str, str]] = None, full: bool = False) -> Optional[Dict]:
        hits = self.match(text, k=3)
        if not hits:
            return None
        score, code = hits[0]
        a = self.agent(code)
        cam = self.camera(a, text)
        prompt = fill(a["prompt"], subject, setting, partners)
        seq = (a.get("sequence") or {}).get("id")
        return {"code": code, "score": score, "others": [c for _, c in hits[1:]], "sport": a["sport"],
                "summary": a["summary"], "camera": cam["name"], "size": cam["size"],
                "openpose_png": str(Path(a["_dir"]) / cam["openpose_png"]),
                "openpose_json": str(Path(a["_dir"]) / cam["openpose_json"]),
                "prompt": prompt, "unfilled": re.findall(r"\{[A-Z_]+\}", prompt),
                "negative": a["negative"], "guide": self.guide(a, cam, full), "scene_rules": a.get("scene_rules", []),
                "sequence": seq, "motion": (self.sequences.get(seq) or {}).get("motion") if seq else None,
                "checks_passed": a.get("checks_passed", True)}


def fill(template: str, subject: Optional[str] = None, setting: Optional[str] = None,
         partners: Optional[Dict[str, str]] = None) -> str:
    out = template
    if subject:
        out = out.replace("{SUBJECT}", subject.strip())
    if setting:
        out = out.replace("{SETTING}", setting.strip().rstrip("."))
    for pid, look in (partners or {}).items():
        out = out.replace(f"{{PARTNER_{pid}}}", look.strip())
    return out


# ---------------------------------------------------------------- behind a switch, for a project
class Hook:
    """For a project: modes file {"default": "off"} (re-read on every call), places such as
    "prompt", "pose", "video". off: nothing. observe: log what would be used, return None.
    act: log and return the pack. Any error returns None, so the caller keeps its own prompt."""

    def __init__(self, root: os.PathLike, library: Optional[os.PathLike] = None,
                 modes_file: str = "sports_modes.json", log_dir: str = "data/sports_logs"):
        self.root = Path(root)
        self.modes_path = self.root / modes_file
        self.log_path = self.root / log_dir / "hooks.jsonl"
        self.library_path = library or os.environ.get("SPORTS_POSE_LIBRARY") or self.root / "javisfilm" / "sports-pose" / "library"
        self._lib: Optional[Library] = None

    def mode(self, place: str) -> str:
        try:
            m = json.loads(self.modes_path.read_text(encoding="utf-8-sig"))
            v = str(m.get(place, m.get("default", "off"))).lower()
            return v if v in ("off", "observe", "act") else "off"
        except Exception:
            return "off"

    def library(self) -> Library:
        if self._lib is None:
            self._lib = Library(self.library_path)
        return self._lib

    def lookup(self, place: str, text: str, panel: Optional[str] = None, **fill_args) -> Optional[Dict]:
        m = self.mode(place)
        if m == "off" or not text:
            return None
        t0 = time.time()
        pack, err = None, ""
        try:
            pack = self.library().pack(text, **fill_args)
        except Exception as e:                     # never break the caller
            err = type(e).__name__
        self._log({"t": round(time.time(), 1), "place": place, "mode": m, "panel": panel,
                   "code": pack["code"] if pack else None, "score": pack["score"] if pack else None,
                   "camera": pack["camera"] if pack else None, "ms": round(1000 * (time.time() - t0), 1),
                   "error": err})
        return pack if m == "act" else None

    def _log(self, row: Dict) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ---------------------------------------------------------------- storyboard scan and log report
TEXT_KEYS = ("description", "desc", "visual", "action", "summary", "content", "prompt", "scene", "shot")


def panels_in(manifest, keys=TEXT_KEYS) -> List[Dict]:
    """Every dict in a storyboard manifest that carries panel text under one of `keys`."""
    found: List[Dict] = []

    def walk(x):
        if isinstance(x, dict):
            if any(isinstance(x.get(k), str) and x.get(k) for k in keys):
                found.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(manifest)
    return found


def panel_text(p: Dict, keys=TEXT_KEYS) -> str:
    return " ".join(str(p[k]) for k in keys if isinstance(p.get(k), str))


def scan(manifest_path: os.PathLike, lib: Library, keys=TEXT_KEYS) -> List[Dict]:
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    rows = []
    for i, p in enumerate(panels_in(m, keys), 1):
        hits = lib.match(panel_text(p, keys))
        rows.append({"panel": i, "code": hits[0][1] if hits else None, "score": hits[0][0] if hits else None,
                     "others": [c for _, c in hits[1:]]})
    return rows


def report(log_path: os.PathLike) -> str:
    rows = [json.loads(x) for x in Path(log_path).read_text(encoding="utf-8").splitlines() if x.strip()]
    by_place: Dict[str, List[Dict]] = {}
    for r in rows:
        by_place.setdefault(r["place"], []).append(r)
    out = ["# sportslook hook log", "", f"{len(rows)} lookups", "",
           "| place | lookups | matched | errors | median ms |", "|---|---|---|---|---|"]
    for place, rs in sorted(by_place.items()):
        ms = sorted(r["ms"] for r in rs)
        out.append(f"| {place} | {len(rs)} | {sum(1 for r in rs if r['code'])} | {sum(1 for r in rs if r.get('error'))} | "
                   f"{ms[len(ms) // 2] if ms else 0} |")
    counts: Dict[str, int] = {}
    for r in rows:
        if r["code"]:
            counts[r["code"]] = counts.get(r["code"], 0) + 1
    out += ["", "| asset | times |", "|---|---|"] + [f"| {c} | {n} |" for c, n in sorted(counts.items(), key=lambda x: -x[1])]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="sportslook")
    ap.add_argument("--library", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("match")
    p.add_argument("text")
    p = sub.add_parser("pack")
    p.add_argument("text")
    p.add_argument("--subject")
    p.add_argument("--setting")
    p.add_argument("--partner", action="append", default=[], help="B=a tall man in a blue judogi")
    p.add_argument("--full", action="store_true")
    p = sub.add_parser("scan")
    p.add_argument("manifest", nargs="+")
    p.add_argument("--keys", default=",".join(TEXT_KEYS), help="panel text keys, comma separated")
    p = sub.add_parser("report")
    p.add_argument("log")
    a = ap.parse_args(argv)
    if a.cmd == "report":
        print(report(a.log), end="")
        return 0
    lib = Library(a.library)
    if a.cmd == "match":
        print(json.dumps([{"score": s, "code": c} for s, c in lib.match(a.text)], ensure_ascii=False))
    elif a.cmd == "pack":
        partners = dict(x.split("=", 1) for x in a.partner)
        print(json.dumps(lib.pack(a.text, a.subject, a.setting, partners, a.full), ensure_ascii=False, indent=1))
    elif a.cmd == "scan":
        total = hit = 0
        keys = tuple(k.strip() for k in a.keys.split(",") if k.strip())
        for mf in a.manifest:
            rows = scan(mf, lib, keys)
            total += len(rows)
            hit += sum(1 for r in rows if r["code"])
            for r in rows:
                if r["code"]:
                    print(f"{Path(mf).parent.name}\tpanel {r['panel']}\t{r['code']}\t{r['score']}")
        print(f"panels {total}, with a sports asset {hit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

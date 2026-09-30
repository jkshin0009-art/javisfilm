"""gatereview: how often is the project's frame_gate right?

The gate fails 312 of 339 cuts, and no human label is linked to its verdicts, so
nobody can say how much of that is real. This tool asks a person, one cut at a
time, and turns the answers into a per-axis hit rate.

  stats   --root DIR             count the *.gate.json verdicts: PASS, FAIL with a defect found,
                                 FAIL only because an axis could not be measured, errors; and per
                                 axis pass / fail / unmeasured / na
  sample  --root DIR --out DIR   pick cuts to look at: for each of the most-failed axes, cuts it
                                 failed; cuts failed only for want of a measurement; cuts that
                                 passed. Writes gate_review.html (keys 1 / 2 / 3) and rows.json
  score   --out DIR --csv FILE   per axis, how often the gate was right, and what to do about it
  referee --out DIR              no person needed: a second look by the vision model (the 5678
                                 server, Jev-style probability reading, both answer orders) marks
                                 every sampled cut, then scores the gate against those marks

Reads the gate files and images only. The page and rows.json hold image paths and
the gate's reasons and stay in work/; the score report holds axis names and counts.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

SUFFIX = ".gate.json"
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
STATUSES = ("pass", "fail", "unmeasured", "na")


# ---------------------------------------------------------------- reading
def axis_status(entry) -> str:
    if isinstance(entry, bool):
        return "pass" if entry else "fail"
    if not isinstance(entry, dict):
        return "unmeasured"
    if entry.get("na"):
        return "na"
    p = entry.get("pass")
    if p is True:
        return "pass"
    if p is False:
        return "fail"
    return "unmeasured"


def find_image(gate: Path, frame, base: Optional[Path], index: Dict[str, Path]) -> Optional[Path]:
    cands: List[Path] = []
    if isinstance(frame, str) and frame.strip():
        f = Path(frame.strip())
        if f.is_absolute():
            cands.append(f)
        else:
            cands += [gate.parent / f] + ([base / f] if base else [])
        cands.append(gate.parent / f.name)
    stem = gate.name[: -len(SUFFIX)]
    cands += [gate.parent / (stem + ext) for ext in IMAGE_EXT] + [gate.parent / stem]
    for c in cands:
        if c.suffix.lower() in IMAGE_EXT and c.is_file():
            return c.resolve()
    if isinstance(frame, str) and frame.strip():
        hit = index.get(Path(frame.strip()).name.lower())
        if hit:
            return hit
    return None


def load(root: Path, base: Optional[Path] = None, image_root: Optional[Path] = None) -> List[Dict]:
    index: Dict[str, Path] = {}
    if image_root:
        for p in image_root.rglob("*"):
            if p.suffix.lower() in IMAGE_EXT:
                index.setdefault(p.name.lower(), p.resolve())
    cuts = []
    for g in sorted(root.rglob("*" + SUFFIX)):
        try:
            d = json.loads(g.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            cuts.append({"gate": g, "category": "unreadable", "error": str(e)[:120], "axes": {}, "image": None})
            continue
        axes = d.get("axes") if isinstance(d.get("axes"), dict) else {}
        status = {k: axis_status(v) for k, v in axes.items()}
        observe = {k for k, v in axes.items() if isinstance(v, dict) and v.get("observe")}
        verdict = str(d.get("verdict") or "").upper() or None
        fails = [k for k, s in status.items() if s == "fail"]
        unmeasured = [k for k, s in status.items() if s == "unmeasured"]
        if verdict == "PASS":
            cat = "pass"
        elif verdict == "FAIL":
            cat = "defect" if fails else ("unmeasured_only" if unmeasured else "fail_other")
        else:
            cat = "no_verdict"
        cuts.append({"gate": g, "verdict": verdict, "category": cat, "axes": axes, "status": status,
                     "observe": observe, "fails": fails, "unmeasured": unmeasured,
                     "error": bool(d.get("error")),
                     "image": find_image(g, d.get("frame"), base, index)})
    return cuts


def stats_text(cuts: List[Dict]) -> str:
    cats: Dict[str, int] = {}
    for c in cuts:
        cats[c["category"]] = cats.get(c["category"], 0) + 1
    per: Dict[str, Dict[str, int]] = {}
    observe: Dict[str, int] = {}
    for c in cuts:
        for k, s in c.get("status", {}).items():
            per.setdefault(k, {x: 0 for x in STATUSES})[s] += 1
        for k in c.get("observe", ()):
            observe[k] = observe.get(k, 0) + 1
    single = sum(1 for c in cuts if c["category"] == "defect" and len(c["fails"]) == 1)
    lines = ["# frame_gate verdicts", "",
             f"- gate files: {len(cuts)}   with image found: {sum(1 for c in cuts if c.get('image'))}",
             f"- PASS: {cats.get('pass', 0)}",
             f"- FAIL with a failed axis (defect found): {cats.get('defect', 0)}   of which one axis only: {single}",
             f"- FAIL with no failed axis, only unmeasured ones: {cats.get('unmeasured_only', 0)}",
             f"- FAIL with neither: {cats.get('fail_other', 0)}   no verdict: {cats.get('no_verdict', 0)}   "
             f"unreadable: {cats.get('unreadable', 0)}   with error key: {sum(1 for c in cuts if c.get('error'))}",
             "", "| axis | pass | fail | unmeasured | na | observe-flagged |", "|---|---|---|---|---|---|"]
    for k, s in sorted(per.items(), key=lambda kv: -kv[1]["fail"]):
        lines.append(f"| {k} | {s['pass']} | {s['fail']} | {s['unmeasured']} | {s['na']} | {observe.get(k, 0)} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- sample
def _short(v, n=160) -> str:
    if v is None:
        return ""
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[: n - 1] + "…"


def pick_rows(cuts: List[Dict], axes: List[str], per_axis: int, n_unmeasured: int, n_pass: int,
              seed: int) -> List[Dict]:
    rng = random.Random(seed)
    usable = [c for c in cuts if c.get("image")]
    used = set()
    rows: List[Dict] = []

    def take(pool, n):
        pool = [c for c in pool if str(c["gate"]) not in used]
        rng.shuffle(pool)                                      # plain random: keeps the hit rate unbiased
        for c in pool[:n]:
            used.add(str(c["gate"]))
            yield c

    for ax in axes:
        for c in take([c for c in usable if ax in c["fails"]], per_axis):
            e = c["axes"].get(ax) if isinstance(c["axes"].get(ax), dict) else {}
            rows.append({"kind": "axis", "axis": ax, "gate": str(c["gate"]), "image": str(c["image"]),
                         "value": _short(e.get("value"), 60), "limit": _short(e.get("limit"), 60),
                         "reason": _short(e.get("reason")), "also": [f for f in c["fails"] if f != ax]})
    for c in take([c for c in usable if c["category"] == "unmeasured_only"], n_unmeasured):
        rows.append({"kind": "unmeasured", "axis": "", "gate": str(c["gate"]), "image": str(c["image"]),
                     "unmeasured": c["unmeasured"]})
    for c in take([c for c in usable if c["category"] == "pass"], n_pass):
        rows.append({"kind": "pass", "axis": "", "gate": str(c["gate"]), "image": str(c["image"])})
    for i, r in enumerate(rows, 1):
        r["id"] = f"r{i:03d}"
    return rows


def write_page(out: Path, rows: List[Dict]) -> None:
    cards = []
    last = None
    for r in rows:
        group = r["axis"] if r["kind"] == "axis" else r["kind"]
        if group != last:
            title = {"unmeasured": "측정을 못 해서 실패 처리된 컷", "pass": "검수기가 통과시킨 컷"}.get(
                group, f"검수기가 '{group}' 축에서 실패시킨 컷")
            cards.append(f"<h2>{html.escape(title)}</h2>")
            last = group
        if r["kind"] == "axis":
            q = (f"검수기: <b>{html.escape(r['axis'])}</b> 실패"
                 + (f" (값 {html.escape(r['value'])}, 기준 {html.escape(r['limit'])})" if r["value"] or r["limit"] else "")
                 + (f"<br><small>이유: {html.escape(r['reason'])}</small>" if r["reason"] else "")
                 + (f"<br><small>이 컷이 함께 실패한 축: {html.escape(', '.join(r['also']))}</small>" if r["also"] else "")
                 + "<br>그림을 보면 <b>이 결함</b>이 정말 있나요?")
        elif r["kind"] == "unmeasured":
            q = (f"검수기: 측정 못 함({html.escape(', '.join(r['unmeasured']))})이라 실패 처리"
                 "<br>그림을 보면 결함이 있나요?")
        else:
            q = "검수기: 통과<br>그림을 보면 결함이 있나요?"
        img = Path(r["image"]).as_uri()
        cards.append(
            f'<div class="card" data-id="{r["id"]}"><a href="{img}" target="_blank"><img loading="lazy" src="{img}"></a>'
            f'<div class="body"><div class="q"><b>{r["id"]}</b> {q}</div><div class="v">'
            f'<button data-v="defect">1 결함 있음</button><button data-v="clean">2 멀쩡함</button>'
            f'<button data-v="unsure">3 모르겠음</button></div></div></div>')
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>검수기 채점</title><style>
:root{{--bg:#fafafa;--fg:#222;--card:#fff;--line:#ddd;--bad:#c62828;--ok:#2e7d32;--mid:#757575;--sel:#1565c0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--bad:#ef5350;--ok:#81c784;--mid:#9e9e9e;--sel:#64b5f6}}}}
body{{margin:0;padding:12px 16px;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
.bar{{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:2}}
h2{{font-size:16px;margin:22px 0 4px}}
.card{{display:flex;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:6px;margin:10px 0;padding:10px}}
.card.sel{{outline:2px solid var(--sel)}} .card img{{width:560px;max-width:55vw;border-radius:4px}}
.body{{flex:1;min-width:0}} .v{{margin-top:10px}} .v button{{font-size:15px;margin:0 6px 6px 0;padding:6px 12px}}
.v button.on[data-v=defect]{{background:var(--bad);color:#fff}} .v button.on[data-v=clean]{{background:var(--ok);color:#fff}}
.v button.on[data-v=unsure]{{background:var(--mid);color:#fff}}
@media (max-width:700px){{.card{{flex-direction:column}} .card img{{width:100%;max-width:100%}}}}
</style>
<div class="bar"><b>검수기 채점</b> <span id="n"></span> &nbsp; <button id="csv">gate_votes.csv 내보내기</button>
 <small>그림만 보고 고르세요 · 1 결함 있음 · 2 멀쩡함 · 3 모르겠음 · j/k 이동 · 그림 클릭 = 원본</small></div>
{''.join(cards)}
<script>
const KEY='gatereview:'+{json.dumps(str(out.resolve()))};
let marks={{}};try{{marks=JSON.parse(localStorage.getItem(KEY)||'{{}}')}}catch(e){{}}
const save=()=>{{try{{localStorage.setItem(KEY,JSON.stringify(marks))}}catch(e){{}}}};
const cards=[...document.querySelectorAll('.card')];let cur=0;
function paint(c){{c.querySelectorAll('.v button').forEach(b=>b.classList.toggle('on',marks[c.dataset.id]===b.dataset.v));
 document.getElementById('n').textContent=Object.keys(marks).length+' / '+cards.length+' 표시함';}}
function sel(i){{if(!cards.length)return;cards[cur].classList.remove('sel');cur=Math.max(0,Math.min(cards.length-1,i));
 cards[cur].classList.add('sel');cards[cur].scrollIntoView({{block:'center'}});}}
function mark(c,v){{if(marks[c.dataset.id]===v)delete marks[c.dataset.id];else marks[c.dataset.id]=v;save();paint(c);}}
cards.forEach((c,i)=>{{paint(c);c.addEventListener('click',()=>{{cards[cur].classList.remove('sel');cur=i;c.classList.add('sel')}});
 c.querySelectorAll('.v button').forEach(b=>b.onclick=()=>mark(c,b.dataset.v));}});
document.addEventListener('keydown',e=>{{const c=cards[cur];if(e.key==='j')sel(cur+1);else if(e.key==='k')sel(cur-1);
 else if(c&&'123'.includes(e.key)&&e.key.length===1){{marks[c.dataset.id]=['defect','clean','unsure']['123'.indexOf(e.key)];save();paint(c);sel(cur+1)}}}});
document.getElementById('csv').onclick=()=>{{const rows=[['id','answer']];cards.forEach(c=>rows.push([c.dataset.id,marks[c.dataset.id]||'']));
 const blob=new Blob(['\\ufeff'+rows.map(r=>r.join(',')).join('\\n')],{{type:'text/csv'}});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='gate_votes.csv';a.click();}};
sel(0);
</script></html>"""
    (out / "gate_review.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------- referee
# Yes = the defect is there. Axes that need a reference the picture does not carry
# (costume sheet, seat plan, expected head count, prop layout) are not refereed.
REFEREE_STATE = "영화 콘티용으로 생성한 그림 한 장이다. 그림만 보고 답한다."
REFEREE_Q = {
    "offfloor": "서 있거나 걷는 인물의 발이 바닥이나 땅에 닿지 않고 공중에 떠 있는가? "
                "앉거나 누운 인물, 발이 화면 밖인 인물은 해당하지 않는다.",
    "legs_ok": "다리가 더 있거나 없거나, 무릎이 불가능한 방향으로 꺾이거나, 다리 모양이 망가진 인물이 있는가?",
    "hands_ok": "손가락 수가 이상하거나, 손 모양이 뭉개지거나 녹아내린 손이 있는가? 손이 안 보이면 아니다.",
    "limbs_ok": "팔이나 다리가 더 있거나 없는 인물이 있는가?",
    "faces_ok": "일그러지거나 녹아내리거나 뭉개진 얼굴이 있는가? 얼굴이 안 보이면 아니다.",
    "scale_grounding_ok": "인물의 크기가 주변의 문, 가구, 다른 사람에 비해 어색하게 크거나 작은가?",
    "joints": "관절이 불가능한 방향으로 꺾인 인물이 있는가?",
    "identity_unique": "같은 사람이 한 그림에 두 번 나오는 것처럼 복제된 인물이 있는가?",
    "intruding": "화면에 있어서는 안 될 물체나 다른 사람의 몸 일부가 어색하게 끼어들어 있는가?",
}
GENERIC = ("hands_ok", "legs_ok", "faces_ok", "offfloor")     # asked of cuts with no failed axis


def referee_vote(p: float, hi: float, lo: float) -> str:
    if p != p:
        return "unsure"
    return "defect" if p >= hi else ("clean" if p <= lo else "unsure")


def cmd_referee(a) -> int:
    import time
    import boardcheck as bc
    out = Path(a.out)
    data = json.loads((out / "rows.json").read_text(encoding="utf-8"))
    rows = data["rows"]
    backend = bc.LogprobBackend(a.url, timeout=a.timeout)
    cache = out / "cache"
    votes: Dict[str, str] = {}
    table = []
    t0 = time.perf_counter()
    for i, r in enumerate(rows, 1):
        t1 = time.perf_counter()
        if r["kind"] == "axis":
            qs = {r["axis"]: REFEREE_Q[r["axis"]]} if r["axis"] in REFEREE_Q else {}
        else:
            qs = {k: REFEREE_Q[k] for k in GENERIC}
        if not qs:
            vote, p, note = "unsure", float("nan"), "needs a reference the picture does not carry"
        else:
            img = bc.prepared(Path(r["image"]), cache, a.max_side)
            ps = backend.ok([img], REFEREE_STATE, qs)
            vals = [v for v in ps.values() if v == v]
            if r["kind"] == "axis":
                p = vals[0] if vals else float("nan")
                vote = referee_vote(p, a.hi, a.lo)
            else:                                       # any clear defect -> defect; all clearly absent -> clean
                p = max(vals) if vals else float("nan")
                vote = ("defect" if vals and p >= a.hi else
                        "clean" if vals and len(vals) == len(qs) and p <= a.lo else "unsure")
            note = ""
        votes[r["id"]] = vote
        table.append({"id": r["id"], "answer": vote, "p": "" if p != p else round(p, 4), "note": note,
                      "s": round(time.perf_counter() - t1, 2)})
        print(f"{r['id']} {r['kind']:10s} {r['axis'] or '-':20s} -> {vote:7s} "
              f"p={'-' if p != p else f'{p:.2f}'} {table[-1]['s']:.1f}s", flush=True)
    secs = time.perf_counter() - t0
    with open(out / "auto_votes.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "answer", "p", "note", "s"])
        w.writeheader()
        w.writerows(table)
    asked = [t["s"] for t in table if t["note"] == ""]
    text = score_text(rows, votes, data.get("fail_count"), source=(
        f"machine referee: {a.url}, probability reading in both answer orders, "
        f"defect at p>={a.hi}, clean at p<={a.lo}. Same model family as the gate, "
        f"so this shows which gate verdicts hold up under a second look, not ground truth"))
    text += (f"\n- referee time: {secs:.0f} s for {len(rows)} cuts; per asked cut median "
             f"{sorted(asked)[len(asked) // 2] if asked else 0:.1f} s\n")
    print(text)
    target = Path(a.report) if a.report else out / "GATE_SCORE_AUTO.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Saved: {target}")
    return 0


# ---------------------------------------------------------------- score
def advice(right: int, wrong: int) -> str:
    n = right + wrong
    if n < 5:
        return "표본 부족"
    r = right / n
    if r >= 0.8:
        return "믿을 만함: 지금처럼 막기"
    if r >= 0.5:
        return "반반: 막지 말고 사람 확인 목록으로"
    return "대부분 오판: 막기에서 빼고 질문·기준을 고칠 것"


def score_text(rows: List[Dict], votes: Dict[str, str], stats: Optional[Dict[str, int]] = None,
               source: str = "a person's eye") -> str:
    def tally(rs):
        t = {"defect": 0, "clean": 0, "unsure": 0, "blank": 0}
        for r in rs:
            t[votes.get(r["id"]) or "blank"] = t.get(votes.get(r["id"]) or "blank", 0) + 1
        return t

    marked = sum(1 for r in rows if votes.get(r["id"]))
    lines = ["# frame_gate: how often it is right", "", f"- answer key: {source}",
             f"- rows: {len(rows)}   marked: {marked}", "",
             "## axes that failed a cut", "",
             "| axis | looked at | defect really there (gate right) | clean (gate wrong) | unsure | gate right | advice |",
             "|---|---|---|---|---|---|---|"]
    axes = list(dict.fromkeys(r["axis"] for r in rows if r["kind"] == "axis"))
    for ax in axes:
        t = tally([r for r in rows if r["kind"] == "axis" and r["axis"] == ax])
        n = t["defect"] + t["clean"]
        rate = f"{t['defect'] / n:.0%}" if n else "-"
        extra = ""
        if stats and ax in stats and n:
            extra = f" (≈{round(stats[ax] * t['defect'] / n)} of its {stats[ax]} fails are real)"
        lines.append(f"| {ax} | {n + t['unsure']} | {t['defect']} | {t['clean']} | {t['unsure']} | {rate}{extra} | "
                     f"{advice(t['defect'], t['clean'])} |")
    for kind, title, good in (("unmeasured", "cuts failed only because an axis was not measured", "clean"),
                              ("pass", "cuts the gate passed", "clean")):
        rs = [r for r in rows if r["kind"] == kind]
        if not rs:
            continue
        t = tally(rs)
        n = t["defect"] + t["clean"]
        lines += ["", f"## {title}", "", f"- looked at {n + t['unsure']}: clean {t['clean']}, defect {t['defect']}, "
                                         f"unsure {t['unsure']}"]
        if kind == "unmeasured" and n:
            lines.append(f"- clean share: {t['clean'] / n:.0%}. A high share means the rule \"unmeasured cannot pass\" "
                         "is throwing away good cuts: mark them 're-measure / person check' instead of FAIL.")
        if kind == "pass" and n:
            lines.append(f"- missed defects: {t['defect']}/{n}.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- cli
def cmd_stats(a) -> int:
    cuts = load(Path(a.root), Path(a.base) if a.base else None, Path(a.image_root) if a.image_root else None)
    text = stats_text(cuts)
    print(text)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
    return 0


def cmd_sample(a) -> int:
    cuts = load(Path(a.root), Path(a.base) if a.base else None, Path(a.image_root) if a.image_root else None)
    print(stats_text(cuts))
    fail_count: Dict[str, int] = {}
    for c in cuts:
        for k in c.get("fails", ()):
            fail_count[k] = fail_count.get(k, 0) + 1
    axes = [x.strip() for x in a.axes.split(",") if x.strip()] if a.axes else \
        [k for k, _ in sorted(fail_count.items(), key=lambda kv: -kv[1])][: a.top_axes]
    rows = pick_rows(cuts, axes, a.per_axis, a.unmeasured, a.passed, a.seed)
    if not rows:
        print("no cut with a findable image; pass --base (project folder) or --image-root")
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "rows.json").write_text(json.dumps({"root": str(Path(a.root).resolve()), "fail_count": fail_count,
                                               "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    write_page(out, rows)
    no_img = sum(1 for c in cuts if not c.get("image"))
    kinds = {k: sum(1 for r in rows if r["kind"] == k) for k in ("axis", "unmeasured", "pass")}
    print(f"RESULT {len(rows)} cuts to look at: {kinds['axis']} failed on {', '.join(axes)}, "
          f"{kinds['unmeasured']} failed only unmeasured, {kinds['pass']} passed. "
          f"Gate files without a findable image: {no_img}")
    print(f"Open {out / 'gate_review.html'}")
    return 0


def cmd_score(a) -> int:
    out = Path(a.out)
    data = json.loads((out / "rows.json").read_text(encoding="utf-8"))
    votes: Dict[str, str] = {}
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("answer") or "").strip() in ("defect", "clean", "unsure"):
                votes[r["id"].strip()] = r["answer"].strip()
    text = score_text(data["rows"], votes, data.get("fail_count"))
    print(text)
    target = Path(a.report) if a.report else out / "GATE_SCORE.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Saved: {target}")
    return 0


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="gatereview")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def where(p):
        p.add_argument("--root", required=True, help="folder searched for *.gate.json (recursively)")
        p.add_argument("--base", default=None, help="folder that relative 'frame' paths start from (project root)")
        p.add_argument("--image-root", default=None, help="also look up images by file name under this folder")

    p = sub.add_parser("stats")
    where(p)
    p.add_argument("--report", default=None)
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("sample")
    where(p)
    p.add_argument("--out", required=True)
    p.add_argument("--axes", default="", help="comma list; default: the most-failed axes")
    p.add_argument("--top-axes", type=int, default=5)
    p.add_argument("--per-axis", type=int, default=10)
    p.add_argument("--unmeasured", type=int, default=10)
    p.add_argument("--passed", type=int, default=10)
    p.add_argument("--seed", type=int, default=7)
    p.set_defaults(fn=cmd_sample)
    p = sub.add_parser("referee")
    p.add_argument("--out", required=True, help="the folder sample wrote")
    p.add_argument("--url", default="http://127.0.0.1:5678", help="llama-server with --mmproj")
    p.add_argument("--hi", type=float, default=0.8, help="defect at or above this probability")
    p.add_argument("--lo", type=float, default=0.2, help="clean at or below this probability")
    p.add_argument("--max-side", type=int, default=1024)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--report", default=None)
    p.set_defaults(fn=cmd_referee)
    p = sub.add_parser("score")
    p.add_argument("--out", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--report", default=None)
    p.set_defaults(fn=cmd_score)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

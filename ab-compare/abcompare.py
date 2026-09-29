"""ab-compare: compare renders of the same clip made with one setting changed.

For single-variable A/B tests (a LoRA off, a different step LoRA, a realism LoRA,
a prompt line removed): every arm is the same clip, seed and prompt except for the
one thing under test. This tool

  frames   pulls frames at the same moments from every arm, measures highlights
           (blown-out and glowing pixels, the numbers behind "light leaks"), can
           ask the vision model a yes/no light-leak question per frame, and writes
           a blind page: arms under shuffled letters, one row per moment, pick the best
  reveal   maps the letters back to arms and tallies the votes next to the numbers

Needs ffmpeg and Pillow. The vision check uses chat-upgrade/chatup (llama-server + mmproj).
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "chat-upgrade"))
sys.path.insert(0, str(HERE.parent / "reverse-check"))

LEAK_Q = ("이 장면에 광원 주변으로 빛이 번지거나 새어 나와 화면 일부가 뿌옇게 번지는 현상"
          "(블룸, 광선 번짐, 빛 샘)이 눈에 띄게 있는가?")


def ffmpeg_bin(explicit=None) -> str:
    from revcheck import find_ffmpeg
    return find_ffmpeg(explicit)


def duration(ff: str, path: str) -> float:
    from revcheck import duration as d
    return d(ff, path)


def grab(ff: str, video: str, t: float, out: Path, width: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([ff, "-hide_banner", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                        "-vf", f"scale={width}:-2", str(out)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0 or not out.exists():
        raise RuntimeError(f"ffmpeg could not read {video} at {t:.2f}s: {p.stderr[-300:]}")


def light_metrics(path: Path) -> Dict[str, float]:
    """Share of pixels that are blown out (luma > 240) and glowing (200-240), and mean luma.
    A light leak or bloom shows up as a jump in both, spread over a large area."""
    from PIL import Image
    with Image.open(path) as im:
        hist = im.convert("L").histogram()
    n = float(sum(hist)) or 1.0
    return {"blown": round(sum(hist[241:]) / n, 5), "glow": round(sum(hist[200:241]) / n, 5),
            "luma": round(sum(i * c for i, c in enumerate(hist)) / n / 255.0, 4)}


def cmd_frames(a) -> int:
    arms = []
    for spec in a.arm:
        if "=" not in spec:
            raise SystemExit(f"--arm needs NAME=PATH, got {spec!r}")
        name, path = spec.split("=", 1)
        if not os.path.isfile(path):
            raise SystemExit(f"{name}: file not found: {path}")
        arms.append((name.strip(), path))
    if len(arms) < 2:
        raise SystemExit("give at least two --arm")
    ff = ffmpeg_bin(a.ffmpeg)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lengths = {name: duration(ff, p) for name, p in arms}
    shortest = min(lengths.values())
    if a.times:
        times = [float(t) for t in a.times.split(",")]
    else:
        times = [round(shortest * (i + 0.5) / a.count, 3) for i in range(a.count)]
    times = [t for t in times if t < shortest]
    decider = None
    if a.vlm:
        from chatup.decide import Decider, Question
        from chatup.llm import LLMClient
        decider = Decider(LLMClient(a.vlm, timeout=180))
        q = Question.noul(LEAK_Q, name="light_leak")
    metrics: Dict[str, Dict] = {}
    for name, path in arms:
        rows = []
        for i, t in enumerate(times):
            fp = out / "frames" / name / f"t{i:02d}.png"
            grab(ff, path, t, fp, a.width)
            m = light_metrics(fp)
            m["t"] = t
            if decider is not None:
                d = decider.decide("영상 한 장면의 프레임이다.", q, images=[str(fp)])
                m["leak_p"] = round(d.yes, 4) if d.confidence is not None else None
            rows.append(m)
        def mean(k):
            vals = [r[k] for r in rows if r.get(k) is not None]
            return round(sum(vals) / len(vals), 5) if vals else None
        metrics[name] = {"file": os.path.abspath(path), "length": round(lengths[name], 3), "frames": rows,
                         "blown": mean("blown"), "glow": mean("glow"), "luma": mean("luma"),
                         "leak_p": mean("leak_p")}
        extra = f" leak_p {metrics[name]['leak_p']:.2f}" if metrics[name]["leak_p"] is not None else ""
        print(f"{name:16s} blown {metrics[name]['blown']:.4f}  glow {metrics[name]['glow']:.4f}  "
              f"luma {metrics[name]['luma']:.3f}{extra}")
    letters = [chr(ord("A") + i) for i in range(len(arms))]
    order = [n for n, _ in arms]
    random.Random(a.seed).shuffle(order)
    key = dict(zip(letters, order))
    (out / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps({"times": times, "arms": metrics, "note": a.note},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    write_blind(out, times, key, a.note)
    lens = {round(v, 1) for v in lengths.values()}
    if len(lens) > 1:
        print(f"note: arms differ in length {sorted(lens)}; frames are taken at the same seconds")
    print(f"RESULT {len(arms)} arms x {len(times)} frames. Blind page: {out / 'blind.html'} "
          f"(letters are in key.json; do not open it before voting)")
    return 0


def write_blind(out: Path, times: List[float], key: Dict[str, str], note: str) -> None:
    letters = list(key)
    head = "".join(f"<th>{l}</th>" for l in letters)
    rows = []
    for i, t in enumerate(times):
        cells = []
        for l in letters:
            src = f"frames/{key[l]}/t{i:02d}.png"
            cells.append(f'<td><label><img src="{html.escape(src)}"><br>'
                         f'<input type="radio" name="r{i}" value="{l}"> {l}</label></td>')
        rows.append(f"<tr><th>{t:.1f}s</th>{''.join(cells)}</tr>")
    opts = "".join(f"<option>{l}</option>" for l in letters)
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A/B 비교</title><style>
:root{{--bg:#fafafa;--fg:#222;--line:#ccc}}@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--line:#444}}}}
body{{margin:0;padding:12px 16px;background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif}}
table{{border-collapse:collapse}} td,th{{border:1px solid var(--line);padding:4px;vertical-align:top;text-align:center}}
img{{width:360px;max-width:28vw}} .wrap{{overflow-x:auto}}
</style>
<h3>같은 컷, 설정 하나만 다른 버전들 (이름은 가림)</h3><p>{html.escape(note)}</p>
<p>줄마다 가장 좋은 것 하나를 고르세요. 빛 번짐, 뭉개짐, 얼굴이 기준입니다. 마지막에 전체 1등과 꼴찌를 고르고 CSV를 내보냅니다.</p>
<div class="wrap"><table><tr><th>시각</th>{head}</tr>{''.join(rows)}</table></div>
<p>전체 1등 <select id="best"><option></option>{opts}</select> 꼴찌 <select id="worst"><option></option>{opts}</select>
 <button id="csv">votes.csv 내보내기</button></p>
<script>
document.getElementById('csv').onclick=()=>{{const rows=[['row','choice']];
 document.querySelectorAll('input[type=radio]:checked').forEach(r=>rows.push([r.name,r.value]));
 rows.push(['best',document.getElementById('best').value]);rows.push(['worst',document.getElementById('worst').value]);
 const blob=new Blob([rows.map(r=>r.join(',')).join('\\n')],{{type:'text/csv'}});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='votes.csv';a.click();}};
</script></html>"""
    (out / "blind.html").write_text(page, encoding="utf-8")


def cmd_reveal(a) -> int:
    out = Path(a.out)
    key = json.loads((out / "key.json").read_text(encoding="utf-8"))
    data = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    rows_won: Dict[str, int] = {v: 0 for v in key.values()}
    best = worst = ""
    with open(a.votes, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            arm = key.get((row.get("choice") or "").strip())
            if row["row"] == "best":
                best = arm or ""
            elif row["row"] == "worst":
                worst = arm or ""
            elif arm:
                rows_won[arm] += 1
    n_rows = len(data["times"])
    lines = ["# A/B result", "", f"- note: {data.get('note') or '-'}", f"- frames per arm: {n_rows}",
             f"- overall best: {best or '-'}   worst: {worst or '-'}", "",
             "| arm | rows won | blown (>240) | glow (200-240) | mean luma | light-leak p (vision) |",
             "|---|---|---|---|---|---|"]
    for arm, m in sorted(data["arms"].items(), key=lambda kv: -rows_won.get(kv[0], 0)):
        lp = f"{m['leak_p']:.2f}" if m.get("leak_p") is not None else "-"
        lines.append(f"| {arm} | {rows_won.get(arm, 0)}/{n_rows} | {m['blown']:.4f} | {m['glow']:.4f} | "
                     f"{m['luma']:.3f} | {lp} |")
    lines += ["", "blown and glow are shares of the frame; lower usually means fewer leaks, but a darker "
                  "grade also lowers them, so read them with mean luma and the votes."]
    text = "\n".join(lines) + "\n"
    print(text)
    target = Path(a.report) if a.report else out / "RESULT.md"
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
    ap = argparse.ArgumentParser(prog="abcompare")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("frames")
    p.add_argument("--out", required=True)
    p.add_argument("--arm", action="append", default=[], help="NAME=PATH, one per arm (two or more)")
    p.add_argument("--count", type=int, default=6, help="frames per arm, spread over the clip")
    p.add_argument("--times", default="", help="explicit seconds, e.g. 0.5,1.8,3.2")
    p.add_argument("--width", type=int, default=768)
    p.add_argument("--vlm", default="", help="llama-server with --mmproj, e.g. http://127.0.0.1:5678")
    p.add_argument("--note", default="", help="what differs between the arms, shown on the page")
    p.add_argument("--seed", type=int, default=None, help="letter shuffle seed (default random)")
    p.add_argument("--ffmpeg", default=None)
    p.set_defaults(fn=cmd_frames)
    p = sub.add_parser("reveal")
    p.add_argument("--out", required=True)
    p.add_argument("--votes", required=True)
    p.add_argument("--report", default=None)
    p.set_defaults(fn=cmd_reveal)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

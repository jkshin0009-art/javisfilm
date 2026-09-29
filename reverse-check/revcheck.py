"""reverse-check: verify reverse prompting on real example videos.

Cut a stretch of a video (e.g. the example clips in the middle of a tutorial)
into shots, run the project's own reverse-prompt logic on every shot, and check
each prompt against the frames it came from, and against the real prompt when
it is known.

  shots     VIDEO -> WORK/shots.json, frames/, clips/, index.html (thumbnails to look at)
  classify  label shots: example clip / UI recording / presenter / title card / other
  prompt    run a reverse-prompt command per shot (--cmd, the project's logic)
            or the built-in vision-model baseline (--vlm)
  score     per shot and prompt source: does the prompt get subject, action, camera,
            place, light and style right, does it invent things, and (with truth.csv)
            does it say what the real prompt said
  report    markdown summary

Judgments are Jev-style typed questions (chat-upgrade/chatup) asked to the vision
model behind llama-server (--mmproj), with the frames attached.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "chat-upgrade"))

from chatup.decide import Decider, Question  # noqa: E402
from chatup.llm import LLMClient, LLMError, with_images  # noqa: E402

KINDS = {
    "showcase": "AI로 만든 영상 예시가 화면 대부분을 채우고 재생되는 장면",
    "ui": "프로그램이나 웹 화면을 녹화한 장면 (메뉴, 버튼, 노드, 입력칸이 보임)",
    "presenter": "사람이 카메라 앞에서 설명하는 장면",
    "title": "글자나 제목만 있는 화면",
    "other": "그 밖의 장면",
}

ASPECTS = [
    ("subject", "인물이나 주요 대상(누구·무엇인지, 몇 명인지, 생김새와 옷)"),
    ("action", "움직임과 행동(무엇을 하는지, 어떻게 변하는지)"),
    ("camera", "카메라 구도와 움직임(샷 크기, 앵글, 고정·이동)"),
    ("place", "장소와 배경"),
    ("light", "조명과 색감"),
    ("style", "화풍과 질감(실사, 애니메이션, 3D, 필름 느낌 등)"),
]

VLM_INSTRUCTION = (
    "These images are frames from one shot of a video, in time order (start, middle, end). "
    "Write the text-to-video prompt that would recreate this shot. One paragraph in English, "
    "about 80-140 words, covering: the subjects and their appearance, the action and how it "
    "changes over the shot, camera framing and movement, the setting, lighting and color, and "
    "the visual style. Describe only what is visible. No preamble, no lists."
)


# ---------------------------------------------------------------- helpers
def parse_time(t) -> float:
    """"8:51", "1:02:03.5", "531" or a number -> seconds."""
    if isinstance(t, (int, float)):
        return float(t)
    parts = str(t).strip().split(":")
    sec = 0.0
    for p in parts:
        sec = sec * 60 + float(p)
    return sec


def fmt_time(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m}:{s:04.1f}"


def find_ffmpeg(explicit: Optional[str] = None) -> str:
    for cand in (explicit, os.environ.get("FFMPEG")):
        if cand:
            return cand
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("ffmpeg not found: install it, put it on PATH, or pass --ffmpeg / set FFMPEG")


def run_ff(ffmpeg: str, args: Sequence[str], check: bool = True) -> str:
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({p.returncode}): {p.stderr[-800:]}")
    return p.stderr


def duration(ffmpeg: str, video: str) -> float:
    err = run_ff(ffmpeg, ["-i", video], check=False)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
    if not m:
        raise RuntimeError(f"cannot read duration of {video}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def vf_chain(crop: Optional[str], max_side: Optional[int]) -> List[str]:
    chain = []
    if crop:
        chain.append(f"crop={crop}")
    if max_side:
        chain.append(f"scale='if(gte(iw,ih),min(iw,{max_side}),-2)':'if(gte(iw,ih),-2,min(ih,{max_side}))'")
    return chain


def load(work: str) -> Dict:
    with open(os.path.join(work, "shots.json"), encoding="utf-8") as f:
        return json.load(f)


def save(work: str, data: Dict) -> None:
    tmp = os.path.join(work, "shots.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(work, "shots.json"))


def pick(data: Dict, only: str = "", ids: str = "") -> List[Dict]:
    shots = data["shots"]
    if ids:
        want = {i.strip() for i in ids.split(",") if i.strip()}
        shots = [s for s in shots if s["id"] in want]
    if only:
        kinds = {k.strip() for k in only.split(",")}
        shots = [s for s in shots if s.get("kind") in kinds]
    return shots


def vision_client(a) -> LLMClient:
    return LLMClient(a.url, model=a.model, timeout=a.timeout)


# ---------------------------------------------------------------- shots
def cmd_shots(a) -> int:
    ff = find_ffmpeg(a.ffmpeg)
    total = duration(ff, a.video)
    start = parse_time(a.start) if a.start else 0.0
    end = min(parse_time(a.end), total) if a.end else total
    if end <= start:
        raise SystemExit(f"empty range: {start} - {end} (video is {total:.1f}s)")
    os.makedirs(os.path.join(a.work, "frames"), exist_ok=True)
    chain = vf_chain(a.crop, None)
    detect = ",".join(chain + [f"select='gt(scene,{a.threshold})'", "showinfo"])
    err = run_ff(ff, ["-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", a.video, "-an", "-vf", detect,
                      "-f", "null", "-"])
    cuts = sorted(start + float(t) for t in re.findall(r"pts_time:([0-9.]+)", err))
    bounds = [start] + [c for c in cuts if start < c < end] + [end]
    shots = []
    for s0, s1 in zip(bounds, bounds[1:]):
        if s1 - s0 < a.min_len:
            continue
        shots.append({"id": f"s{len(shots) + 1:03d}", "start": round(s0, 3), "end": round(s1, 3)})
        if len(shots) >= a.max_shots:
            break
    frame_chain = vf_chain(a.crop, a.max_side)
    for sh in shots:
        span = sh["end"] - sh["start"]
        frames = []
        for tag, frac in (("a", 0.2), ("b", 0.5), ("c", 0.8)):
            rel = os.path.join("frames", f"{sh['id']}_{tag}.jpg")
            args = ["-y", "-ss", f"{sh['start'] + span * frac:.3f}", "-i", a.video, "-frames:v", "1", "-q:v", "3"]
            if frame_chain:
                args += ["-vf", ",".join(frame_chain)]
            run_ff(ff, args + [os.path.join(a.work, rel)])
            frames.append(rel)
        sh["frames"] = frames
        if a.clips:
            os.makedirs(os.path.join(a.work, "clips"), exist_ok=True)
            rel = os.path.join("clips", f"{sh['id']}.mp4")
            clip_end = min(sh["end"], sh["start"] + a.clip_max)
            args = ["-y", "-ss", f"{sh['start']:.3f}", "-to", f"{clip_end:.3f}", "-i", a.video, "-an"]
            if a.crop:
                args += ["-vf", f"crop={a.crop}"]
            try:
                run_ff(ff, args + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                                   os.path.join(a.work, rel)])
            except RuntimeError:
                run_ff(ff, args + ["-c:v", "mpeg4", "-q:v", "3", os.path.join(a.work, rel)])
            sh["clip"] = rel
    data = {"video": os.path.abspath(a.video), "start": start, "end": end, "crop": a.crop,
            "threshold": a.threshold, "created": time.strftime("%Y-%m-%d %H:%M:%S"), "shots": shots}
    save(a.work, data)
    write_index(a.work, data)
    print(f"{len(shots)} shots between {fmt_time(start)} and {fmt_time(end)} "
          f"({len(cuts)} cuts at threshold {a.threshold})")
    print(f"Open {os.path.join(a.work, 'index.html')} to look at them.")
    return 0


def write_index(work: str, data: Dict) -> None:
    rows = []
    for sh in data["shots"]:
        imgs = "".join(f'<img src="{html.escape(f.replace(os.sep, "/"))}">' for f in sh.get("frames", []))
        kind = sh.get("kind") or ""
        p = f' ({sh["kind_p"]:.2f})' if sh.get("kind_p") is not None else ""
        rows.append(f"<tr><td>{sh['id']}</td><td>{fmt_time(sh['start'])} - {fmt_time(sh['end'])}</td>"
                    f"<td>{html.escape(kind)}{p}</td><td>{imgs}</td></tr>")
    page = ("<!doctype html><meta charset='utf-8'><title>shots</title><style>"
            "body{font:14px sans-serif;margin:16px}img{height:110px;margin-right:4px}"
            "td{padding:4px 8px;border-bottom:1px solid #ccc;vertical-align:top}</style>"
            f"<p>{html.escape(data['video'])} {fmt_time(data['start'])} - {fmt_time(data['end'])}</p>"
            "<table><tr><th>shot</th><th>time</th><th>kind</th><th>frames (start, middle, end)</th></tr>"
            + "".join(rows) + "</table>")
    with open(os.path.join(work, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


# ---------------------------------------------------------------- classify
def cmd_classify(a) -> int:
    data = load(a.work)
    dec = Decider(vision_client(a), rotations=a.rotations)
    keys = list(KINDS)
    q = Question.choice("이 화면은 영상 강좌의 어떤 장면인가?", [KINDS[k] for k in keys], name="shot_kind")
    for sh in pick(data, ids=a.ids):
        frame = os.path.join(a.work, sh["frames"][1])
        d = dec.decide("영상 강좌의 한 장면이다. 이미지는 그 장면의 가운데 프레임이다.", q, images=[frame])
        sh["kind"] = keys[[KINDS[k] for k in keys].index(d.answer)] if d.answer else None
        sh["kind_p"] = round(d.confidence, 3) if d.confidence is not None else None
        print(f"{sh['id']} {fmt_time(sh['start'])}  {sh['kind']}  p={sh['kind_p']}  {d.ms:.0f} ms")
        save(a.work, data)
    write_index(a.work, data)
    counts: Dict[str, int] = {}
    for sh in data["shots"]:
        counts[str(sh.get("kind"))] = counts.get(str(sh.get("kind")), 0) + 1
    print("RESULT kinds: " + ", ".join(f"{k} {n}" for k, n in sorted(counts.items())))
    return 0


# ---------------------------------------------------------------- prompt
def fill(template: str, work: str, sh: Dict, out: str) -> str:
    q = (lambda p: subprocess.list2cmdline([p])) if os.name == "nt" else shlex.quote
    frames = [os.path.abspath(os.path.join(work, f)) for f in sh["frames"]]
    clip = os.path.abspath(os.path.join(work, sh["clip"])) if sh.get("clip") else ""
    return (template.replace("{frames}", " ".join(q(f) for f in frames))
            .replace("{frame}", q(frames[1])).replace("{clip}", q(clip) if clip else "")
            .replace("{shot}", sh["id"]).replace("{out}", q(out)))


def cmd_prompt(a) -> int:
    data = load(a.work)
    name = a.name or ("vlm" if a.vlm else "project")
    outdir = os.path.join(a.work, "prompts", name)
    os.makedirs(outdir, exist_ok=True)
    client = vision_client(a) if a.vlm else None
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    done = 0
    for sh in pick(data, a.only, a.ids):
        path = os.path.join(outdir, sh["id"] + ".txt")
        if os.path.exists(path) and not a.force:
            continue
        t0 = time.perf_counter()
        if client is not None:
            frames = [os.path.join(a.work, f) for f in sh["frames"]]
            text = client.chat([{"role": "user", "content": with_images(VLM_INSTRUCTION, frames)}],
                               max_tokens=400, temperature=0.2)
        else:
            if not a.cmd:
                raise SystemExit("give --cmd (the project's reverse-prompt command) or --vlm")
            tmp_out = path + ".out"
            cmd = fill(a.cmd, a.work, sh, tmp_out)
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=a.cmd_timeout, env=env)
            if p.returncode != 0:
                print(f"{sh['id']} FAILED ({p.returncode}): {p.stderr.strip()[-300:]}")
                continue
            if "{out}" in a.cmd and os.path.exists(tmp_out):
                with open(tmp_out, encoding="utf-8-sig") as f:
                    text = f.read()
                os.remove(tmp_out)
            else:
                text = p.stdout
        text = text.strip()
        if not text:
            print(f"{sh['id']} EMPTY")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        done += 1
        print(f"{sh['id']} {fmt_time(sh['start'])}  {len(text)} chars  {(time.perf_counter() - t0):.1f} s")
    print(f"RESULT prompts[{name}]: {done} written in {outdir}")
    return 0


# ---------------------------------------------------------------- score
def read_truth(work: str) -> Dict[str, str]:
    path = os.path.join(work, "truth.csv")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid, text = (row.get("shot") or "").strip(), (row.get("prompt") or "").strip()
            if sid and text:
                out[sid] = text
    return out


def sources(work: str) -> List[str]:
    root = os.path.join(work, "prompts")
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))) if os.path.isdir(root) else []


def cmd_score(a) -> int:
    data = load(a.work)
    dec = Decider(vision_client(a), rotations=a.rotations)
    truth = read_truth(a.work)
    names = [n.strip() for n in a.names.split(",")] if a.names else sources(a.work)
    path = os.path.join(a.work, "scores.json")
    scores = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            scores = json.load(f)
    for sh in pick(data, a.only, a.ids):
        frames = [os.path.join(a.work, f) for f in sh["frames"]]
        for name in names:
            ppath = os.path.join(a.work, "prompts", name, sh["id"] + ".txt")
            if not os.path.exists(ppath):
                continue
            if sh["id"] in scores.get(name, {}) and not a.force:
                continue
            with open(ppath, encoding="utf-8") as f:
                prompt = f.read().strip()
            t0 = time.perf_counter()
            state = ("이미지 3장은 한 장면의 앞, 가운데, 뒤 프레임이다(시간 순서).\n"
                     "아래는 이 장면을 다시 만들기 위해 쓴 장면 설명(프롬프트)이다.\n\n" + prompt[:2500])
            aspects = {}
            for key, desc in ASPECTS:
                q = Question.noul(f"이 장면 설명이 장면의 {desc}을(를) 맞게 설명하는가? "
                                  "설명에 그 내용이 빠져 있거나 틀리면 아니다.", name=f"rc_{key}")
                aspects[key] = round(dec.decide(state, q, images=frames).yes, 4)
            qi = Question.noul("장면 설명에 이 장면에는 없는 중요한 대상, 행동, 장소가 들어 있는가?", name="rc_invented")
            invented = round(dec.decide(state, qi, images=frames).yes, 4)
            rec = {"aspects": aspects, "mean": round(sum(aspects.values()) / len(aspects), 4),
                   "invented": invented, "chars": len(prompt)}
            if sh["id"] in truth:
                tstate = f"A (실제로 쓴 프롬프트):\n{truth[sh['id']][:2000]}\n\nB (영상에서 거꾸로 만든 프롬프트):\n{prompt[:2000]}"
                tas = {}
                for key, desc in ASPECTS:
                    q = Question.noul(f"A와 B가 {desc}에 대해 같은 내용을 말하는가? 한쪽에만 있으면 아니다.",
                                      name=f"rt_{key}")
                    tas[key] = round(dec.decide(tstate, q).yes, 4)
                rec["truth"] = tas
                rec["truth_mean"] = round(sum(tas.values()) / len(tas), 4)
            rec["ms"] = round((time.perf_counter() - t0) * 1000)
            scores.setdefault(name, {})[sh["id"]] = rec
            with open(path, "w", encoding="utf-8") as f:
                json.dump(scores, f, ensure_ascii=False, indent=1)
            extra = f" truth={rec['truth_mean']:.2f}" if "truth_mean" in rec else ""
            print(f"{sh['id']} [{name}] fit={rec['mean']:.2f} invented={invented:.2f}{extra}  {rec['ms'] / 1000:.1f} s")
    print(f"RESULT scores saved: {path}")
    return 0


# ---------------------------------------------------------------- report
def cmd_report(a) -> int:
    data = load(a.work)
    spath = os.path.join(a.work, "scores.json")
    scores = {}
    if os.path.exists(spath):
        with open(spath, encoding="utf-8") as f:
            scores = json.load(f)
    meta = {}
    mpath = os.path.join(a.work, "meta.json")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as f:
            meta = json.load(f)
    names = sorted(scores)
    lines = ["# reverse-check report", ""]
    if meta:
        lines.append(f"- video: {meta.get('title', '')} ({meta.get('channel') or meta.get('uploader', '')})")
        if meta.get("webpage_url"):
            lines.append(f"- url: {meta['webpage_url']}")
    offset = parse_time(a.offset) if a.offset else 0.0
    lines += [f"- range: {fmt_time(data['start'] + offset)} - {fmt_time(data['end'] + offset)} of the source",
              f"- shots: {len(data['shots'])}  (kinds: " + ", ".join(
                  f"{k} {sum(1 for s in data['shots'] if s.get('kind') == k)}" for k in KINDS
                  if any(s.get('kind') == k for s in data['shots'])) + ")",
              f"- prompt sources: {', '.join(names) or '(none scored)'}", ""]
    lines.append("fit = share of the six aspects the vision model says the prompt gets right "
                 "(mean probability); invented = probability the prompt adds something not on screen; "
                 "truth = agreement with the real prompt, per aspect, when truth.csv has it.")
    lines.append("")
    head = "| shot | time | kind |" + "".join(f" {n} fit | {n} invented | {n} truth |" for n in names)
    lines += [head, "|" + "---|" * (3 + 3 * len(names))]
    for sh in data["shots"]:
        if a.only and sh.get("kind") not in a.only.split(","):
            continue
        cells = [sh["id"], fmt_time(sh["start"] + offset), str(sh.get("kind") or "-")]
        for n in names:
            r = scores.get(n, {}).get(sh["id"])
            cells += ([f"{r['mean']:.2f}", f"{r['invented']:.2f}", f"{r['truth_mean']:.2f}" if "truth_mean" in r else "-"]
                      if r else ["-", "-", "-"])
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## averages", "", "| source | shots | fit | invented | truth | " +
              " | ".join(k for k, _ in ASPECTS) + " |", "|" + "---|" * (5 + len(ASPECTS))]
    for n in names:
        rs = list(scores[n].values())
        if not rs:
            continue
        tr = [r["truth_mean"] for r in rs if "truth_mean" in r]
        asp = [f"{sum(r['aspects'][k] for r in rs) / len(rs):.2f}" for k, _ in ASPECTS]
        lines.append(f"| {n} | {len(rs)} | {sum(r['mean'] for r in rs) / len(rs):.2f} | "
                     f"{sum(r['invented'] for r in rs) / len(rs):.2f} | "
                     f"{(f'{sum(tr) / len(tr):.2f} ({len(tr)})' if tr else '-')} | " + " | ".join(asp) + " |")
    if a.with_prompts:
        lines += ["", "## prompts", ""]
        for sh in data["shots"]:
            for n in names:
                ppath = os.path.join(a.work, "prompts", n, sh["id"] + ".txt")
                if sh["id"] in scores.get(n, {}) and os.path.exists(ppath):
                    with open(ppath, encoding="utf-8") as f:
                        text = f.read().strip()
                    lines.append(f"- **{sh['id']} [{n}]** {text[:700]}{'…' if len(text) > 700 else ''}")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {a.out}")
    return 0


# ---------------------------------------------------------------- cli
def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="revcheck")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def vision(p):
        p.add_argument("--url", default="http://127.0.0.1:5678", help="llama-server with --mmproj")
        p.add_argument("--model", default=None)
        p.add_argument("--timeout", type=float, default=180.0)

    p = sub.add_parser("shots")
    p.add_argument("video")
    p.add_argument("--work", required=True)
    p.add_argument("--start", default="")
    p.add_argument("--end", default="")
    p.add_argument("--threshold", type=float, default=0.3, help="ffmpeg scene score for a cut (0-1)")
    p.add_argument("--min-len", type=float, default=1.0, help="drop shots shorter than this (s)")
    p.add_argument("--max-shots", type=int, default=80)
    p.add_argument("--crop", default=None, help="w:h:x:y, when the example plays inside a window")
    p.add_argument("--max-side", type=int, default=768, help="longest side of saved frames")
    p.add_argument("--no-clips", dest="clips", action="store_false")
    p.add_argument("--clip-max", type=float, default=10.0)
    p.add_argument("--ffmpeg", default=None)
    p.set_defaults(fn=cmd_shots)

    p = sub.add_parser("classify")
    p.add_argument("--work", required=True)
    p.add_argument("--ids", default="")
    p.add_argument("--rotations", default="adaptive")
    vision(p)
    p.set_defaults(fn=cmd_classify)

    p = sub.add_parser("prompt")
    p.add_argument("--work", required=True)
    p.add_argument("--cmd", default="", help='command per shot; placeholders {frame} {frames} {clip} {shot} {out}')
    p.add_argument("--vlm", action="store_true", help="built-in baseline: the vision model writes the prompt")
    p.add_argument("--name", default="", help="prompt source name (default project, or vlm)")
    p.add_argument("--only", default="", help="kinds to run, e.g. showcase")
    p.add_argument("--ids", default="")
    p.add_argument("--force", action="store_true")
    p.add_argument("--cmd-timeout", type=float, default=600.0)
    vision(p)
    p.set_defaults(fn=cmd_prompt)

    p = sub.add_parser("score")
    p.add_argument("--work", required=True)
    p.add_argument("--names", default="", help="prompt sources to score (default all)")
    p.add_argument("--only", default="")
    p.add_argument("--ids", default="")
    p.add_argument("--force", action="store_true")
    p.add_argument("--rotations", default="adaptive")
    vision(p)
    p.set_defaults(fn=cmd_score)

    p = sub.add_parser("report")
    p.add_argument("--work", required=True)
    p.add_argument("--only", default="")
    p.add_argument("--offset", default="", help="add to times, when the video was cut from a longer one")
    p.add_argument("--with-prompts", action="store_true")
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args(argv)
    if getattr(a, "rotations", None) not in (None, "adaptive", "full"):
        a.rotations = int(a.rotations)
    try:
        return a.fn(a)
    except LLMError as e:
        print(f"[ERROR] vision model: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

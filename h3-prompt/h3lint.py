"""h3lint: does a MiniMax H3 prompt follow the grammar H3 is prompted with?

The rules come from reading IAMCCS-nodes (GPL-3.0, github.com/IAMCCS/IAMCCS-nodes,
iamccs_prompter.py and iamccs_minimax_h3_shotboard_core.py), which composes H3
prompts in what it calls MiniMax's official grammar. No code is copied; this file
only checks a finished prompt string against those rules:

  reference mode   six headings in this order: subject_definitions, summary,
                   retention_analysis, detailed_description, overall_soundscape,
                   non_diegetic_music (an empty one is written N/A); summary starts
                   "[reference generation"; every <Subject N> is defined; lip sync to
                   <Audio 1> says fully_copy in retention_analysis
  base mode        integrated_multimodal_description (starts "[Shot 1]"),
                   overall_soundscape, non_diegetic_music
  everywhere       positive observable language (no "no / do not / never / without /
                   avoid" sentences; "No score" in the music section is fine);
                   dialogue as <Subject N> (SN): <d>[Language] words</d>; one
                   motivated camera move rather than a list; later cuts only as
                   "[Shot N] At MM:SS.mmm"; timeline seconds rising and inside the
                   clip; at most 7000 characters; for a clip made of several chunks,
                   no line of dialogue in the last second of a chunk that is not the last;
                   references written as <Picture N>; one subject is not both she and he;
                   no heading label or repeated sentence pasted inside a section

  shape  PATH... [--n 3]   the skeleton of a prompt: headings, [Shot N], tags, times and
         (Nw) for each run of other words, so its structure can be shared without its text
  check  PATH... [--duration S | --frames N] [--chunk-ends 5.0,10.0] [--pictures N]
         [--report FILE] [--details FILE]
         PATH: .txt (one prompt), .json (a string, a list of strings, or objects with a
         "prompt" key), .jsonl (one object per line), or a folder of those.
         The report holds rule names and counts only; --details holds, per prompt,
         the rules it broke (still no prompt text).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

H3_FPS = 24
H3_MAX_CHARS = 7000
H3_MAX_TRAINED_FRAMES = 362
REF_HEADINGS = ("subject_definitions", "summary", "retention_analysis", "detailed_description",
                "overall_soundscape", "non_diegetic_music")
BASE_HEADINGS = ("integrated_multimodal_description", "overall_soundscape", "non_diegetic_music")
CAMERA_MOVES = {
    "push-in": r"push[\s-]?in|push(?:es|ing)? (?:in|forward)|dolly[\s-]?in",
    "pull-out": r"pull[\s-]?(?:out|back)|dolly[\s-]?(?:out|back)",
    "dolly/track": r"\bdolly\b|track(?:ing)?\s+(?:shot|move|left|right|alongside|with)|lateral tracking",
    "pan": r"\bpans?\b|\bpanning\b|whip[\s-]?pan",
    "tilt": r"\btilts?\b|\btilting\b",
    "orbit": r"\borbit(?:s|ing)?\b|\barc(?:s|ing)? around\b",
    "crane": r"\bcrane\b|\bjib\b|\bboom (?:up|down)\b",
    "zoom": r"\bzoom(?:s|ing)?\b|\bcrash zoom\b",
    "handheld": r"\bhandheld\b|\bhand-held\b",
    "rack focus": r"\brack[\s-]?focus\b|\bfocus pull\b",
}
NEGATIVE_START = re.compile(r"^(?:no|not|do\s+not|don't|never|without|avoid)\b", re.I)
DIALOGUE_OK = re.compile(r"<Subject\s+\d+>\s*\(S\d+\):\s*<d>\[[^\]]+\]\s*[^<]+?</d>")
TIME = r"(\d+(?:\.\d+)?)"
RANGE_RE = re.compile(rf"(?:Timeline\s+)?{TIME}\s*s?(?:econds?)?\s*(?:-|–|—|to)\s*({TIME[1:-1]}|end)\s*s?(?:econds?)?\s*:", re.I)
AT_RE = re.compile(rf"\bAt\s+(?:(\d+):)?{TIME}\s*(?:s\b|sec|seconds?\b)?", re.I)
SHOT_RE = re.compile(r"\[Shot\s+(\d+)\]", re.I)


# ---------------------------------------------------------------- parsing
def sections_of(prompt: str) -> List[Tuple[str, str]]:
    """[(heading, body)] for lines of the form 'heading:' at the start of a line."""
    names = "|".join(REF_HEADINGS + BASE_HEADINGS)
    parts = re.split(rf"(?im)^\s*({names})\s*:[ \t]*", prompt)
    out = []
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i].lower(), parts[i + 1].strip()))
    return out


def sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip()]


def timeline(text: str) -> List[Tuple[float, Optional[float], str]]:
    """(start, end or None for 'end'/open, the words that belong to that time) for each
    timed segment. A line may hold several ranges; each owns the text up to the next."""
    out = []
    for line in text.splitlines():
        marks = []
        for m in RANGE_RE.finditer(line):
            b = None if m.group(2).lower() == "end" else float(m.group(2))
            marks.append((m.start(), m.end(), float(m.group(1)), b))
        if not marks:
            for m in AT_RE.finditer(line):
                mins = float(m.group(1)) if m.group(1) else 0.0
                marks.append((m.start(), m.end(), mins * 60 + float(m.group(2)), None))
        for i, (_, stop, a, b) in enumerate(marks):
            nxt = marks[i + 1][0] if i + 1 < len(marks) else len(line)
            out.append((a, b, line[stop:nxt]))
    return out


# ---------------------------------------------------------------- rules
def check(prompt: str, duration: Optional[float] = None, chunk_ends: Sequence[float] = (),
          pictures: Optional[int] = None) -> Dict[str, str]:
    """{rule: short reason} for every rule the prompt breaks. Empty = clean."""
    bad: Dict[str, str] = {}
    text = prompt.strip()
    if not text:
        return {"empty": "no prompt text"}
    if len(text) > H3_MAX_CHARS:
        bad["too_long"] = f"{len(text)} chars > {H3_MAX_CHARS}"
    secs = sections_of(text)
    heads = [h for h, _ in secs]
    body = dict(secs)
    if "subject_definitions" in heads or "retention_analysis" in heads:
        mode = "reference"
        if tuple(heads) != REF_HEADINGS:
            bad["ref_headings"] = f"got {heads}"
        if body.get("summary") and body["summary"] != "N/A" and not body["summary"].lower().startswith("[reference generation"):
            bad["ref_summary_tag"] = "summary does not start with [reference generation"
        defined = set(re.findall(r"<(Subject|Picture|Audio|Video)\s+(\d+)>", body.get("subject_definitions", "")))
        used = set(re.findall(r"<(Subject|Picture|Audio|Video)\s+(\d+)>", text))
        missing = sorted(f"<{k} {n}>" for k, n in used - defined if k == "Subject")
        if missing:
            bad["undefined_subject"] = ", ".join(missing)
        lipsync = re.search(r"lip[\s-]?sync|synchroni[sz]", text, re.I)
        if "<Audio 1>" in text and lipsync and "fully_copy" not in body.get("retention_analysis", ""):
            bad["audio_retention"] = "lip sync to <Audio 1> but retention_analysis does not say fully_copy"
    elif "integrated_multimodal_description" in heads:
        mode = "base"
        if tuple(heads) != BASE_HEADINGS:
            bad["base_headings"] = f"got {heads}"
        detail = body.get("integrated_multimodal_description", "")
        if detail and not detail.lstrip().lower().startswith("[shot 1]"):
            bad["shot1_marker"] = "integrated_multimodal_description does not start with [Shot 1]"
    else:
        mode = "free"
        bad["no_h3_grammar"] = "neither the reference nor the base heading set"

    # positive language
    negs = []
    scan = secs if secs else [("", text)]
    for head, part in scan:
        for s in sentences(part):
            s2 = re.sub(r"^\[Shot\s+\d+\]\s*", "", s, flags=re.I)
            s2 = re.sub(r"^(?:Timeline\s+)?[\d.]+\s*s?\s*(?:-|to)\s*(?:[\d.]+|end)\s*s?\s*:\s*", "", s2, flags=re.I)
            if NEGATIVE_START.match(s2) and not (head == "non_diegetic_music" and re.match(r"^no (?:score|music)\b", s2, re.I)):
                negs.append(s2[:20])
            elif re.search(r",\s*(?:no|without)\s+\w+", s2, re.I) and head != "non_diegetic_music":
                negs.append(s2[:20])
    if negs:
        bad["negative_language"] = f"{len(negs)} negative phrase(s)"

    # dialogue
    d_open, d_close = text.count("<d>"), text.count("</d>")
    if d_open != d_close:
        bad["dialogue_tags"] = f"<d> {d_open} vs </d> {d_close}"
    elif d_open:
        no_speaker = no_lang = 0
        for m in re.finditer(r"<d>(.*?)</d>", text, re.S):
            if not re.search(r"<Subject\s+\d+>\s*\(S\d+\):\s*$", text[max(0, m.start() - 40):m.start()]):
                no_speaker += 1
            if not re.match(r"\s*\[[^\]]+\]", m.group(1)):
                no_lang += 1
        if no_speaker or no_lang:
            bad["dialogue_format"] = (f"{d_open} <d> block(s): {no_speaker} without '<Subject N> (SN):' right before, "
                                      f"{no_lang} without [Language]")
    outside = re.sub(r"<d>.*?</d>", "", text, flags=re.S)
    if re.search(r"(?:says?|said|shouts?|whispers?|asks?|replies|answers)\s*[,:]?\s*[\"“'][^\"”']{2,}[\"”']", outside, re.I):
        bad["dialogue_untagged"] = "quoted speech outside <d>...</d>"

    # who is who
    subjects = set(re.findall(r"<Subject\s+(\d+)>", text))
    fem = len(re.findall(r"\b(?:she|her|hers|herself)\b", text, re.I))
    male = len(re.findall(r"\b(?:he|him|his|himself)\b", text, re.I))
    if len(subjects) <= 1 and fem and male:
        bad["pronoun_mix"] = f"one subject, but {fem} she/her and {male} he/his"
    bare = re.findall(r"(?<![<\w])(Picture|Audio|Video)\s+\d+(?!\s*>)", text)
    if bare:
        bad["bare_reference"] = f"{len(bare)} reference(s) written without <...>, e.g. {bare[0]} N"

    # camera
    moves = [name for name, pat in CAMERA_MOVES.items() if re.search(pat, text, re.I)]
    if len(moves) > 2:
        bad["camera_moves"] = f"{len(moves)} kinds: {', '.join(moves)}"

    # a heading or a block pasted into another section
    heading_names = "|".join(REF_HEADINGS + BASE_HEADINGS)
    nested = [h for h, part in secs if re.search(rf"(?i)\b(?:{heading_names})\s*:", part)]
    if nested:
        bad["nested_heading"] = f"a heading label inside {', '.join(sorted(set(nested)))}"
    seen: Dict[str, int] = {}
    for sent in sentences(text):
        key = re.sub(rf"(?i)^(?:(?:{heading_names})\s*:\s*)?(?:\[Shot\s+\d+\]\s*)?", "", sent.strip())
        key = re.sub(r"\s+", " ", key).strip().lower()
        if len(key.split()) >= 8:
            seen[key] = seen.get(key, 0) + 1
    repeats = sum(1 for n in seen.values() if n > 1)
    if repeats:
        bad["repeated_text"] = f"{repeats} sentence(s) of 8+ words appear more than once"

    # cuts: count markers only where the shots are described, not where retention points at them
    described = "\n".join(part for h, part in secs if h in ("detailed_description", "integrated_multimodal_description")) \
        if secs else text
    described = re.sub(rf"(?is)\b(?:{heading_names})\s*:.*", "", described)     # ignore a pasted copy
    shots = [int(n) for n in SHOT_RE.findall(re.sub(r"\(from \[Shot\s+\d+\]\)", "", described, flags=re.I))]
    if shots and (shots[0] != 1 or shots != sorted(shots) or len(set(shots)) != len(shots)):
        bad["shot_numbers"] = f"[Shot] markers {shots}"
    for m in re.finditer(r"\[Shot\s+(\d+)\]", described, re.I):
        if int(m.group(1)) > 1 and not re.match(r"\s*At\s+\d{1,2}:\d{2}(?:\.\d+)?", described[m.end():], re.I):
            bad["cut_format"] = "a later [Shot N] is not followed by 'At MM:SS.mmm'"
            break

    # timeline
    times = timeline(described)                  # a pasted copy restarts the clock; read only the real text
    starts = [a for a, _, _ in times]
    if starts != sorted(starts):
        bad["timeline_order"] = "timed lines do not rise"
    for a, b, _ in times:
        if b is not None and b <= a:
            bad["timeline_range"] = f"{a}-{b}"
        if duration is not None and (a >= duration or (b is not None and b > duration + 0.05)):
            bad["timeline_outside"] = f"{a}-{b if b is not None else 'end'} outside {duration:.2f}s"
    if duration is not None:
        frames = round(duration * H3_FPS)
        if frames % 17 != 5:
            bad["frames_grid"] = f"{frames} frames is not 17k+5"
        if frames > H3_MAX_TRAINED_FRAMES:
            bad["frames_long"] = f"{frames} > {H3_MAX_TRAINED_FRAMES} trained frames"
    ends = sorted(float(x) for x in chunk_ends)
    for ce in ends[:-1] if len(ends) > 1 else []:
        for i, (a, b, words) in enumerate(times):
            nxt = times[i + 1][0] if i + 1 < len(times) and times[i + 1][0] > a else None
            stop = b if b is not None else (nxt if nxt is not None else (duration or 1e9))
            if "<d>" in words and a < ce and stop > ce - 1.0:
                bad["dialogue_at_chunk_end"] = f"dialogue runs into the last second before {ce:g}s"
    if pictures is not None:
        used_pics = {int(n) for n in re.findall(r"<Picture\s+(\d+)>", text)}
        if used_pics and max(used_pics) > pictures:
            bad["picture_missing"] = f"<Picture {max(used_pics)}> but {pictures} picture(s)"
    bad.setdefault("_mode", mode)
    return bad


# ---------------------------------------------------------------- input
def prompts_from(path: Path) -> Iterable[Tuple[str, str]]:
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.suffix.lower() in (".txt", ".json", ".jsonl") and p.is_file():
                yield from prompts_from(p)
        return
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8-sig")
    if suffix == ".txt":
        yield str(path), raw
        return
    if suffix == ".jsonl":
        for i, line in enumerate(raw.splitlines()):
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                p = obj.get("prompt") if isinstance(obj, dict) else obj
                if isinstance(p, str):
                    yield f"{path}#{i + 1}", p
        return
    try:
        obj = json.loads(raw)
    except ValueError:
        return
    items = obj if isinstance(obj, list) else [obj]
    for i, it in enumerate(items):
        p = it.get("prompt") if isinstance(it, dict) else it
        if isinstance(p, str):
            yield f"{path}#{i + 1}", p


KEEP_TOKEN = re.compile(
    r"^(?:\w+:|\[Shot\s+\d+\]|\[[A-Za-z][\w +-]*\]|<\/?\w+(?:\s+\d+)?>|\(S\d+\):?|At|Timeline|N/A|"
    r"\d+(?:[.:]\d+)*s?|\d+(?:\.\d+)?s?-(?:\d+(?:\.\d+)?|end)s?:?|to|-)$", re.I)


def shape(prompt: str) -> str:
    """The prompt's skeleton: headings, markers, tags and times kept, every run of other
    words replaced by (Nw). Shows the structure without the text."""
    out = []
    for line in prompt.splitlines():
        toks = re.findall(r"<\/?\w+(?:\s+\d+)?>|\[[^\]]*\]|\(S\d+\):?|[^\s<\[(]+|[<\[(]", line)
        parts, run = [], 0
        for t in toks:
            if KEEP_TOKEN.match(t) and not (t.endswith(":") and t[:-1].lower() not in REF_HEADINGS + BASE_HEADINGS
                                            and not re.match(r"^[\d.]+s?-", t) and t.lower() != "(s1):"
                                            and not re.match(r"^\(S\d+\):$", t)):
                if run:
                    parts.append(f"({run}w)")
                    run = 0
                parts.append(t)
            else:
                run += 1
        if run:
            parts.append(f"({run}w)")
        out.append(" ".join(parts))
    return "\n".join(out)


def report(results: List[Tuple[str, Dict[str, str]]]) -> str:
    n = len(results)
    modes: Dict[str, int] = {}
    rules: Dict[str, int] = {}
    for _, bad in results:
        modes[bad.get("_mode", "?")] = modes.get(bad.get("_mode", "?"), 0) + 1
        for k in bad:
            if not k.startswith("_"):
                rules[k] = rules.get(k, 0) + 1
    clean = sum(1 for _, bad in results if not [k for k in bad if not k.startswith("_")])
    lines = ["# H3 prompt grammar check", "", f"- prompts: {n}   clean: {clean}",
             "- grammar: " + ", ".join(f"{k} {v}" for k, v in sorted(modes.items())), "",
             "| rule | prompts breaking it |", "|---|---|"]
    for k, v in sorted(rules.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="h3lint")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("paths", nargs="+")
    p.add_argument("--duration", type=float, default=None, help="clip seconds")
    p.add_argument("--frames", type=int, default=None, help="clip frames (24 fps)")
    p.add_argument("--chunk-ends", default="", help="seconds where Extender chunks end, e.g. 5.0,10.0,15.0")
    p.add_argument("--pictures", type=int, default=None, help="reference pictures connected")
    p.add_argument("--report", default=None)
    p.add_argument("--details", default=None)
    p.add_argument("--ignore", default="", help="rules to leave out, e.g. dialogue_format,negative_language")
    p = sub.add_parser("shape", help="print the skeleton of the first N prompts (no words)")
    p.add_argument("paths", nargs="+")
    p.add_argument("--n", type=int, default=3)
    a = ap.parse_args(argv)
    if a.cmd == "shape":
        shown = 0
        for path in a.paths:
            for name, prompt in prompts_from(Path(path)):
                if shown >= a.n:
                    return 0
                print(f"===== {Path(name).name} ({len(prompt)} chars)")
                print(shape(prompt))
                shown += 1
        return 0 if shown else 1
    duration = a.duration if a.duration is not None else (a.frames / H3_FPS if a.frames else None)
    ends = [float(x) for x in a.chunk_ends.split(",") if x.strip()]
    results = []
    for path in a.paths:
        for name, prompt in prompts_from(Path(path)):
            ignore = {x.strip() for x in a.ignore.split(",") if x.strip()}
            results.append((name, {k: v for k, v in check(prompt, duration, ends, a.pictures).items()
                                   if k not in ignore}))
    if not results:
        print("no prompts found")
        return 1
    text = report(results)
    print(text)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
    if a.details:
        Path(a.details).parent.mkdir(parents=True, exist_ok=True)
        with open(a.details, "w", encoding="utf-8") as f:
            for name, bad in results:
                f.write(json.dumps({"prompt": name, "broken": bad}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

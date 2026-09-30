"""h3compose: one place that turns a cut into a MiniMax H3 prompt.

The LLM only fills content fields (scene, timed beats, acting, camera, light, sound,
music) as JSON. Code assembles them into H3's grammar (the same grammar h3lint.py
checks), inserts subjects as <Subject N> and dialogue verbatim as
<Subject N> (SN): <d>[Language] ...</d>, and checks the result: h3lint's format rules,
the clip rules below, and optionally Jev-style meaning questions to the LLM
(two compositions in one clip? a camera move that does not fit?). A broken result is
sent back to the writer with the reasons, at most `tries` times.

Clip rules (from IAMCCS-nodes' H3 contract and what broke in our own prompts):
  - one clip = one composition. When the facts hold two (a face close-up that becomes
    a giant wide reveal), the writer answers {"split": [...]} and the caller makes two clips
  - people are named only as <Subject N>, never he/she, so one person cannot become two;
    a subject that is not a person (a robot, a vehicle) carries "kind" instead of "gender"
  - frames on the 17k+5 grid, at most 362; beats rise, start at 0 and end at the clip end
  - an Extender chunk followed by another has no new line in its last 1.0 s; a chunk that
    continues a previous one has no new line in its first 1.0 s

Components (the project's rule: modules, inheritance, components):

  Clip            the grammar of one clip; subclasses change only what differs
    FirstFrameClip  (i2v)   + the alignment line for <Picture 1>
    ReferenceClip   (ref)   six headings, subject_definitions and retention_analysis
      LipsyncClip           + <Audio 1> reused 1:1 and the mouth-sync sentence
  Checker         clip rules + h3lint + optional Jev meaning questions; a lane that
                  keeps a rule on purpose subclasses it and lists the rule in `ignore`
  Writer          asks the LLM for the content fields, composes, checks, retries; a lane
                  (runner, animatic, chat director, MV) subclasses it and overrides facts()

The module functions compose(), check(), write() are thin wrappers over these.
Self-contained (standard library + h3lint.py next to it). The LLM client needs
chat(messages, max_tokens=..., temperature=...) -> str, like chatup.llm.LLMClient.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Sequence, Tuple

try:                                    # copied into a package (e.g. film_assistant/core/h3/)
    from . import h3lint
except ImportError:                     # run from this folder
    import h3lint

FPS = h3lint.H3_FPS
MAX_FRAMES = h3lint.H3_MAX_TRAINED_FRAMES
EDGE = 1.0                      # seconds kept free of new lines at a chunk boundary
GENDER_WORD = {"male": "man", "m": "man", "man": "man", "female": "woman", "f": "woman", "woman": "woman"}
SEMANTIC_QUESTIONS = {
    "two_compositions": ("아래 영상 설명은 끊김 없는 한 클립이다. 이 한 클립 안에서 장소가 바뀌거나, 인물 가까이 보던 화면이 "
                         "거대한 원경으로 바뀌는 것처럼 서로 다른 두 장면(구도)을 이어 붙이라고 요구하는가?"),
    "camera_mismatch": ("아래 영상 설명에서 카메라 움직임이 설명된 구도와 맞지 않는가? 예: 넓은 원경을 보여 주면서 "
                        "인물 얼굴로 다가간다고 쓰는 것처럼."),
}
LINT_IGNORE = {"_mode"}

WRITER_SYSTEM = """You write the content fields of one MiniMax H3 video clip. Code assembles your fields into the H3 prompt grammar, so write only content.
Return ONE JSON object and nothing else, with these keys:
  "scene": where we are and what is visible at 0.00s (one or two sentences)
  "beats": [{"start": seconds, "end": seconds, "action": one visible action}] covering 0 to the clip length, in order
  "acting": performance details (breath, gaze, micro-expression, body weight)
  "camera": exactly one motivated camera move that fits the framing, or a locked-off frame
  "light": light direction, colour and texture that stay constant
  "sound": diegetic sound in chronological order
  "music": non-diegetic score, or "" for none
  "summary": one sentence on what the whole clip is about, worded differently from "scene"
If the facts describe two different compositions for one continuous clip (a different place, or a close view that becomes a giant wide reveal), do not merge them: return {"split": ["first composition", "second composition"]} instead.
Rules:
1. Name people only as their tag, e.g. <Subject 1>. Never use he, she, his, her, him, they or them for a person.
2. Write positive, observable language: describe the visible state you want. Do not write sentences that start with no, not, never, without, avoid or do not.
3. Keep every given fact (wardrobe, place, time of day, props) exactly. Do not invent people, props, captions, logos or cuts.
4. One camera move only, and it must fit the framing: a wide reveal is not a push toward a face.
5. Do not write dialogue words; the given lines are inserted verbatim. Make the acting match when each line is spoken.
6. If "continues_previous" is true, the first 1.0 s continues the previous motion with ambience only. If "final_chunk" is false, the last 1.0 s holds the motion with ambience only.
7. Be concise: the whole clip in under 350 words."""


# ---------------------------------------------------------------- helpers
def seconds(frames: int) -> float:
    return frames / float(FPS)


def _subject_tag(n: int) -> str:
    return f"<Subject {n}>"


def _dialogue_line(line: Dict) -> str:
    n = int(line.get("subject", 1))
    lang = str(line.get("lang") or "Korean").strip()
    text = str(line.get("text", "")).strip()
    return f"{_subject_tag(n)} (S{n}): <d>[{lang}] {text}</d>"


def _json_object(text: str) -> Optional[Dict]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    start = text.find("{")
    while start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        return obj if isinstance(obj, dict) else None
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    return None


# ---------------------------------------------------------------- Clip: the grammar
class Clip:
    """One H3 clip in the base (text-to-video) grammar. shot = {mode, frames, subjects:[{look,
    gender | kind, picture}], lipsync_audio, final_chunk, continues_previous, sections:{scene,
    beats, acting, dialogue, light, camera, sound, music, summary}}."""

    mode = "base"

    def __init__(self, shot: Dict) -> None:
        self.shot = shot
        self.sec = shot.get("sections") or {}
        self.subjects = shot.get("subjects") or []
        self.frames = int(shot.get("frames") or 0)

    @property
    def duration(self) -> float:
        return seconds(self.frames)

    # -- facts the clip must satisfy before any text exists
    def validate(self) -> Dict[str, str]:
        bad: Dict[str, str] = {}
        if self.frames % 17 != 5 or self.frames < 5:
            lower = max(5, self.frames - ((self.frames - 5) % 17))
            bad["frames_grid"] = f"{self.frames} frames is not 17k+5 (nearest {lower} or {lower + 17})"
        if self.frames > MAX_FRAMES:
            bad["frames_long"] = f"{self.frames} > {MAX_FRAMES}"
        ids = set(range(1, len(self.subjects) + 1))
        for line in self.sec.get("dialogue") or []:
            if int(line.get("subject", 0)) not in ids:
                bad["dialogue_subject"] = f"line for <Subject {line.get('subject')}> that is not defined"
            if line.get("start") is None:
                continue
            start = float(line["start"])
            end = float(line.get("end", start + max(1.0, 0.33 * len(str(line.get("text", "")).split()))))
            if not self.shot.get("final_chunk", True) and end > self.duration - EDGE:
                bad["dialogue_at_chunk_end"] = f"a line runs past {self.duration - EDGE:.2f}s in a chunk that is not the last"
            if self.shot.get("continues_previous") and start < EDGE:
                bad["dialogue_at_chunk_start"] = f"a line starts before {EDGE:.1f}s in a continuing chunk"
        return bad

    def beats_problems(self) -> Dict[str, str]:
        return beats_problems(self.sec.get("beats") or [], self.duration)

    # -- text pieces; subclasses override only what differs
    def timeline(self) -> Tuple[str, List[str]]:
        beats, dialogue = self.sec.get("beats") or [], list(self.sec.get("dialogue") or [])
        lines, placed = [], set()
        for i, b in enumerate(beats):
            a, e = float(b["start"]), float(b["end"])
            last = i == len(beats) - 1 and e >= self.duration - 0.05
            text = str(b.get("action", "")).strip().rstrip(".")
            spoken = [j for j, d in enumerate(dialogue) if d.get("start") is not None and a <= float(d["start"]) < e]
            placed.update(spoken)
            extra = "".join(" " + _dialogue_line(dialogue[j]) for j in spoken)
            lines.append(f"{a:.2f}s-end: {text}.{extra}" if last else f"{a:.2f}-{e:.2f}s: {text}.{extra}")
        return " ".join(lines), [_dialogue_line(d) for j, d in enumerate(dialogue) if j not in placed]

    def body_parts(self) -> List[str]:
        timeline, loose = self.timeline()
        return [self.sec.get("scene", ""), timeline, self.sec.get("acting", ""), " ".join(loose),
                self.sec.get("light", ""), self.sec.get("camera", "")]

    def body(self) -> str:
        return "\n".join(p.strip() for p in self.body_parts() if p and p.strip())

    def sound(self) -> str:
        return (self.sec.get("sound") or "").strip() or "N/A"

    def music(self) -> str:
        return (self.sec.get("music") or "").strip() or "N/A"

    def prefix(self) -> str:
        return ""

    def blocks(self) -> List[Tuple[str, str]]:
        return [("integrated_multimodal_description", f"[Shot 1] {self.body()}"),
                ("overall_soundscape", self.sound()), ("non_diegetic_music", self.music())]

    def render(self) -> str:
        text = "\n\n".join(f"{h}:\n{b}" for h, b in self.blocks())
        pre = self.prefix()
        return f"{pre}\n\n{text}" if pre else text

    def picture_count(self) -> Optional[int]:
        return max([int(s.get("picture") or 0) for s in self.subjects] + [0]) or None


class FirstFrameClip(Clip):
    """i2v: <Picture 1> is the first frame."""

    mode = "i2v"

    def prefix(self) -> str:
        return "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."


class ReferenceClip(Clip):
    """ref: subjects come from reference pictures; six headings in a fixed order."""

    mode = "ref"
    summary_tag = "[reference generation]"

    def validate(self) -> Dict[str, str]:
        bad = super().validate()
        if not any(s.get("picture") for s in self.subjects):
            bad["no_reference"] = "reference mode without a subject picture"
        return bad

    def who(self, s: Dict) -> str:
        return GENDER_WORD.get(str(s.get("gender") or "").lower()) or str(s.get("kind") or "person")

    def definitions(self) -> List[str]:
        out = []
        for n, s in enumerate(self.subjects, 1):
            look = str(s.get("look", "")).strip().rstrip(".")
            src = f" shown in <Picture {s['picture']}>" if s.get("picture") else ""
            out.append(f"{_subject_tag(n)}: {look + ', ' if look else ''}the {self.who(s)}{src}; "
                       "preserve face, body proportions, wardrobe and hairstyle.")
        return out

    def retention(self) -> List[str]:
        return [f"{_subject_tag(n)}: fully_preserved - keep identity, face and wardrobe from <Picture {s['picture']}>."
                for n, s in enumerate(self.subjects, 1) if s.get("picture")]

    def summary(self) -> str:
        text = (self.sec.get("summary") or "").strip()
        if not text:                                   # never repeat the scene sentence here
            tags = ", ".join(_subject_tag(n) for n in range(1, len(self.subjects) + 1)) or "the subject"
            text = f"One continuous shot of {tags} in a single composition."
        return f"{self.summary_tag} {text}"

    def blocks(self) -> List[Tuple[str, str]]:
        return [("subject_definitions", "\n".join(self.definitions()) or "N/A"),
                ("summary", self.summary()),
                ("retention_analysis", "\n".join(self.retention()) or "N/A"),
                ("detailed_description", f"[Shot 1] {self.body()}"),
                ("overall_soundscape", self.sound()), ("non_diegetic_music", self.music())]


class LipsyncClip(ReferenceClip):
    """ref + <Audio 1>: the given performance is reused 1:1 and the mouth follows it."""

    summary_tag = "[reference generation + audio reuse]"

    def definitions(self) -> List[str]:
        return super().definitions() + ["<Audio 1>: the complete spoken or sung performance of <Subject 1> (S1)."]

    def retention(self) -> List[str]:
        return super().retention() + ["<Audio 1>: fully_copy - reuse <Audio 1> 1:1 as the timing of the performance."]

    def body_parts(self) -> List[str]:
        return super().body_parts() + ["Synchronize <Subject 1> (S1)'s mouth shapes, breaths and facial acting to <Audio 1>."]


CLIPS = {"base": Clip, "i2v": FirstFrameClip, "ref": ReferenceClip}


def clip_for(shot: Dict) -> Clip:
    mode = shot.get("mode", "base")
    if mode == "ref" and shot.get("lipsync_audio"):
        return LipsyncClip(shot)
    return CLIPS.get(mode, Clip)(shot)


def beats_problems(beats: Sequence[Dict], dur: float) -> Dict[str, str]:
    bad: Dict[str, str] = {}
    if not beats:
        return {"no_beats": "the writer returned no timed beats"}
    prev = -1.0
    for b in beats:
        a, e = float(b.get("start", -1)), float(b.get("end", -1))
        if a < prev or e <= a:
            bad["beats_order"] = "beats do not rise"
        if e > dur + 0.05:
            bad["beats_outside"] = f"a beat ends at {e:.2f}s after the clip end {dur:.2f}s"
        prev = a
    if float(beats[0].get("start", 1)) > 0.05:
        bad["beats_start"] = "the first beat does not start at 0"
    return bad


# ---------------------------------------------------------------- Checker
class Checker:
    """Clip rules + beats + h3lint + optional meaning questions. A lane that keeps a rule
    on purpose subclasses this and lists the rule in `ignore`."""

    ignore: frozenset = frozenset()
    questions: Dict[str, str] = SEMANTIC_QUESTIONS

    def __init__(self, decider=None, threshold: float = 0.8) -> None:
        self.decider = decider
        self.threshold = threshold

    def check(self, clip: Clip, prompt: str) -> Dict[str, str]:
        bad = dict(clip.validate())
        bad.update(clip.beats_problems())
        lint = h3lint.check(prompt, duration=clip.duration, pictures=clip.picture_count())
        bad.update({k: v for k, v in lint.items() if k not in LINT_IGNORE})
        if self.decider is not None:
            bad.update(self.semantic(prompt))
        return {k: v for k, v in bad.items() if k not in self.ignore}

    def semantic(self, prompt: str) -> Dict[str, str]:
        from importlib import import_module
        Question = import_module("chatup.decide").Question
        out = {}
        for name, q in self.questions.items():
            try:
                d = self.decider.decide(prompt, Question.noul(q, name=f"h3_{name}"))
            except Exception as e:                        # a judge problem never blocks writing
                out[f"{name}_unchecked"] = str(e)[:80]
                continue
            if d.confidence is not None and d.yes >= self.threshold:
                out[name] = f"p={d.yes:.2f}"
        return out


class MVChecker(Checker):
    """The MV lane keeps its dialogue form (v11 passed with it) and its incident clauses."""

    ignore = frozenset({"dialogue_format", "negative_language"})


# ---------------------------------------------------------------- Writer
class Writer:
    """Asks the LLM for the content fields, composes with the Clip for the shot's mode,
    checks with the Checker, and retries with the reasons. A lane subclasses it and
    overrides facts() to hand over what that lane knows about a cut."""

    system = WRITER_SYSTEM
    fields = ("scene", "beats", "acting", "camera", "light", "sound", "music", "summary")

    def __init__(self, llm, checker: Optional[Checker] = None, *, tries: int = 3, max_tokens: int = 900,
                 temperature: float = 0.4) -> None:
        self.llm = llm
        self.checker = checker or Checker()
        self.tries = tries
        self.max_tokens = max_tokens
        self.temperature = temperature

    def facts(self, shot: Dict, facts: Dict) -> Dict:
        subjects = [{"tag": _subject_tag(n), "gender": s.get("gender", ""), "kind": s.get("kind", "person"),
                     "look": s.get("look", "")} for n, s in enumerate(shot.get("subjects") or [], 1)]
        lines = [{"tag": _subject_tag(int(d.get("subject", 1))), "start": d.get("start"), "text": d.get("text", "")}
                 for d in (shot.get("sections") or {}).get("dialogue") or []]
        return {"clip_seconds": round(seconds(int(shot.get("frames") or 0)), 2), "mode": shot.get("mode", "base"),
                "subjects": subjects, "spoken_lines": lines,
                "continues_previous": bool(shot.get("continues_previous")),
                "final_chunk": bool(shot.get("final_chunk", True)), "facts": facts}

    def write(self, shot: Dict, facts: Dict) -> Dict:
        """{"prompt", "problems", "tries", "split", "sections"}; prompt is None on a split,
        on bad clip facts, or when no try gave usable JSON."""
        pre = clip_for(shot).validate()
        if pre:
            return {"prompt": None, "problems": pre, "tries": 0, "split": None, "sections": None}
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": json.dumps(self.facts(shot, facts), ensure_ascii=False)}]
        last: Dict = {"prompt": None, "problems": {"no_answer": "the writer returned nothing usable"},
                      "tries": 0, "split": None, "sections": None}
        for attempt in range(1, self.tries + 1):
            reply = self.llm.chat(messages, max_tokens=self.max_tokens, temperature=self.temperature)
            obj = _json_object(reply)
            if obj is None:
                last.update(tries=attempt, problems={"not_json": "the writer did not return a JSON object"})
                messages += [{"role": "assistant", "content": reply[:2000]},
                             {"role": "user", "content": "Return only one JSON object with the listed keys."}]
                continue
            if obj.get("split"):
                return {"prompt": None, "problems": {}, "tries": attempt, "split": obj["split"], "sections": None}
            sections = dict(shot.get("sections") or {})
            sections.update({k: obj[k] for k in self.fields if k in obj})
            clip = clip_for(dict(shot, sections=sections))
            prompt = clip.render()
            problems = self.checker.check(clip, prompt)
            hard = {k: v for k, v in problems.items() if not k.endswith("_unchecked")}
            last = {"prompt": prompt, "problems": problems, "tries": attempt, "split": None, "sections": sections}
            if not hard:
                return last
            messages += [{"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)[:3000]},
                         {"role": "user", "content": "The assembled clip broke these rules: "
                          + "; ".join(f"{k} ({v})" for k, v in hard.items())
                          + ". Rewrite the JSON so none of them happens. If it cannot be one composition, return split."}]
        return last


# ---------------------------------------------------------------- module functions (thin wrappers)
def validate(shot: Dict) -> Dict[str, str]:
    return clip_for(shot).validate()


def compose(shot: Dict) -> str:
    return clip_for(shot).render()


def check(shot: Dict, prompt: str, decider=None, threshold: float = 0.8) -> Dict[str, str]:
    return Checker(decider, threshold).check(clip_for(shot), prompt)


def semantic_check(prompt: str, decider, threshold: float = 0.8) -> Dict[str, str]:
    return Checker(decider, threshold).semantic(prompt)


def facts_for_writer(shot: Dict, facts: Dict) -> Dict:
    return Writer(None).facts(shot, facts)


def write(shot: Dict, facts: Dict, llm, *, tries: int = 3, decider=None, max_tokens: int = 900,
          temperature: float = 0.4, checker: Optional[Checker] = None) -> Dict:
    return Writer(llm, checker or Checker(decider), tries=tries, max_tokens=max_tokens,
                  temperature=temperature).write(shot, facts)


# ---------------------------------------------------------------- clip rules
def seconds(frames: int) -> float:
    return frames / float(FPS)


def validate(shot: Dict) -> Dict[str, str]:
    """Problems in the clip facts themselves, before any text is written."""
    bad: Dict[str, str] = {}
    frames = int(shot.get("frames") or 0)
    if frames % 17 != 5 or frames < 5:
        lower = max(5, frames - ((frames - 5) % 17))
        bad["frames_grid"] = f"{frames} frames is not 17k+5 (nearest {lower} or {lower + 17})"
    if frames > MAX_FRAMES:
        bad["frames_long"] = f"{frames} > {MAX_FRAMES}"
    dur = seconds(frames)
    subjects = shot.get("subjects") or []
    mode = shot.get("mode", "base")
    if mode == "ref" and not any(s.get("picture") for s in subjects):
        bad["no_reference"] = "reference mode without a subject picture"
    ids = set(range(1, len(subjects) + 1))
    for line in (shot.get("sections") or {}).get("dialogue") or []:
        if int(line.get("subject", 0)) not in ids:
            bad["dialogue_subject"] = f"line for <Subject {line.get('subject')}> that is not defined"
        start = line.get("start")
        if start is None:
            continue
        start = float(start)
        end = float(line.get("end", start + max(1.0, 0.33 * len(str(line.get("text", "")).split()))))
        if not shot.get("final_chunk", True) and end > dur - EDGE:
            bad["dialogue_at_chunk_end"] = f"a line runs past {dur - EDGE:.2f}s in a chunk that is not the last"
        if shot.get("continues_previous") and start < EDGE:
            bad["dialogue_at_chunk_start"] = f"a line starts before {EDGE:.1f}s in a continuing chunk"
    return bad


def beats_problems(beats: Sequence[Dict], dur: float) -> Dict[str, str]:
    bad: Dict[str, str] = {}
    if not beats:
        return {"no_beats": "the writer returned no timed beats"}
    prev = -1.0
    for b in beats:
        a, e = float(b.get("start", -1)), float(b.get("end", -1))
        if a < prev or e <= a:
            bad["beats_order"] = "beats do not rise"
        if e > dur + 0.05:
            bad["beats_outside"] = f"a beat ends at {e:.2f}s after the clip end {dur:.2f}s"
        prev = a
    if float(beats[0].get("start", 1)) > 0.05:
        bad["beats_start"] = "the first beat does not start at 0"
    return bad


# ---------------------------------------------------------------- compose
def _subject_tag(n: int) -> str:
    return f"<Subject {n}>"


def _dialogue_line(line: Dict) -> str:
    n = int(line.get("subject", 1))
    lang = str(line.get("lang") or "Korean").strip()
    text = str(line.get("text", "")).strip()
    return f"{_subject_tag(n)} (S{n}): <d>[{lang}] {text}</d>"


def _timeline(beats: Sequence[Dict], dialogue: Sequence[Dict], dur: float) -> Tuple[str, List[str]]:
    lines, placed = [], set()
    for i, b in enumerate(beats):
        a, e = float(b["start"]), float(b["end"])
        tail = "end" if (i == len(beats) - 1 and e >= dur - 0.05) else f"{e:.2f}s"
        text = str(b.get("action", "")).strip().rstrip(".")
        spoken = [j for j, d in enumerate(dialogue) if d.get("start") is not None and a <= float(d["start"]) < e]
        placed.update(spoken)
        extra = "".join(" " + _dialogue_line(dialogue[j]) for j in spoken)
        lines.append(f"{a:.2f}-{tail}: {text}.{extra}" if tail != "end" else f"{a:.2f}s-end: {text}.{extra}")
    rest = [_dialogue_line(d) for j, d in enumerate(dialogue) if j not in placed]
    return " ".join(lines), rest


def compose(shot: Dict) -> str:
    """The H3 prompt for one clip. shot = {mode: base|i2v|ref, frames, subjects:[{look, gender,
    picture}], lipsync_audio, sections:{scene, beats, acting, dialogue, light, camera, sound, music,
    summary}}."""
    mode = shot.get("mode", "base")
    sec = shot.get("sections") or {}
    subjects = shot.get("subjects") or []
    dur = seconds(int(shot.get("frames") or 0))
    dialogue = list(sec.get("dialogue") or [])
    timeline, loose_lines = _timeline(sec.get("beats") or [], dialogue, dur)
    body_parts = [sec.get("scene", ""), timeline, sec.get("acting", ""), " ".join(loose_lines),
                  sec.get("light", ""), sec.get("camera", "")]
    lipsync = bool(shot.get("lipsync_audio")) and mode == "ref"
    if lipsync:
        body_parts.append("Synchronize <Subject 1> (S1)'s mouth shapes, breaths and facial acting to <Audio 1>.")
    body = "\n".join(p.strip() for p in body_parts if p and p.strip())
    sound = (sec.get("sound") or "").strip() or "N/A"
    music = (sec.get("music") or "").strip() or "N/A"
    if mode == "ref":
        defs, keep = [], []
        for n, s in enumerate(subjects, 1):
            who = GENDER_WORD.get(str(s.get("gender") or "").lower()) or str(s.get("kind") or "person")
            look = str(s.get("look", "")).strip().rstrip(".")
            pic = s.get("picture")
            src = f" shown in <Picture {pic}>" if pic else ""
            defs.append(f"{_subject_tag(n)}: {look + ', ' if look else ''}the {who}{src}; "
                        "preserve face, body proportions, wardrobe and hairstyle.")
            if pic:
                keep.append(f"{_subject_tag(n)}: fully_preserved - keep identity, face and wardrobe from <Picture {pic}>.")
        if lipsync:
            defs.append("<Audio 1>: the complete spoken or sung performance of <Subject 1> (S1).")
            keep.append("<Audio 1>: fully_copy - reuse <Audio 1> 1:1 as the timing of the performance.")
        tag = "[reference generation + audio reuse]" if lipsync else "[reference generation]"
        summary = (sec.get("summary") or "").strip()
        if not summary:                                  # never repeat the scene sentence here
            tags = ", ".join(_subject_tag(n) for n in range(1, len(subjects) + 1)) or "the subject"
            summary = f"One continuous shot of {tags} in a single composition."
        blocks = [("subject_definitions", "\n".join(defs) or "N/A"),
                  ("summary", f"{tag} {summary}".strip()),
                  ("retention_analysis", "\n".join(keep) or "N/A"),
                  ("detailed_description", f"[Shot 1] {body}".strip()),
                  ("overall_soundscape", sound), ("non_diegetic_music", music)]
        return "\n\n".join(f"{h}:\n{b}" for h, b in blocks)
    text = (f"integrated_multimodal_description:\n[Shot 1] {body}\n\n"
            f"overall_soundscape:\n{sound}\n\nnon_diegetic_music:\n{music}")
    if mode == "i2v":
        text = ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) "
                "is fully referenced.\n\n" + text)
    return text


def check(shot: Dict, prompt: str, decider=None, threshold: float = 0.8) -> Dict[str, str]:
    """Everything wrong with a composed clip: clip rules, beats, h3lint, and (with a decider,
    e.g. chatup.decide.Decider on the 5678 server) the meaning questions."""
    dur = seconds(int(shot.get("frames") or 0))
    bad = dict(validate(shot))
    bad.update(beats_problems((shot.get("sections") or {}).get("beats") or [], dur))
    pics = max([int(s.get("picture") or 0) for s in shot.get("subjects") or []] + [0]) or None
    bad.update({k: v for k, v in h3lint.check(prompt, duration=dur, pictures=pics).items() if k not in LINT_IGNORE})
    if decider is not None:
        bad.update(semantic_check(prompt, decider, threshold))
    return bad


def semantic_check(prompt: str, decider, threshold: float = 0.8) -> Dict[str, str]:
    """Jev-style yes/no questions about meaning; flags only confident yeses."""
    from importlib import import_module
    Question = import_module("chatup.decide").Question
    out = {}
    for name, q in SEMANTIC_QUESTIONS.items():
        try:
            d = decider.decide(prompt, Question.noul(q, name=f"h3_{name}"))
        except Exception as e:                            # a judge problem never blocks writing
            out[f"{name}_unchecked"] = str(e)[:80]
            continue
        if d.confidence is not None and d.yes >= threshold:
            out[name] = f"p={d.yes:.2f}"
    return out


# ---------------------------------------------------------------- writer
def _json_object(text: str) -> Optional[Dict]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    start = text.find("{")
    while start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        return obj if isinstance(obj, dict) else None
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    return None


def facts_for_writer(shot: Dict, facts: Dict) -> Dict:
    subjects = [{"tag": _subject_tag(n), "gender": s.get("gender", ""), "kind": s.get("kind", "person"),
                 "look": s.get("look", "")}
                for n, s in enumerate(shot.get("subjects") or [], 1)]
    lines = [{"tag": _subject_tag(int(d.get("subject", 1))), "start": d.get("start"), "text": d.get("text", "")}
             for d in (shot.get("sections") or {}).get("dialogue") or []]
    return {"clip_seconds": round(seconds(int(shot.get("frames") or 0)), 2), "mode": shot.get("mode", "base"),
            "subjects": subjects, "spoken_lines": lines,
            "continues_previous": bool(shot.get("continues_previous")),
            "final_chunk": bool(shot.get("final_chunk", True)), "facts": facts}


def write(shot: Dict, facts: Dict, llm, *, tries: int = 3, decider=None, max_tokens: int = 900,
          temperature: float = 0.4) -> Dict:
    """Ask the LLM for the content fields, compose, check, and retry with the reasons.
    Returns {"prompt", "problems", "tries", "split", "sections"}; prompt is None on a split
    or when every try failed to parse."""
    pre = validate(shot)
    if pre:
        return {"prompt": None, "problems": pre, "tries": 0, "split": None, "sections": None}
    messages = [{"role": "system", "content": WRITER_SYSTEM},
                {"role": "user", "content": json.dumps(facts_for_writer(shot, facts), ensure_ascii=False)}]
    last: Dict = {"prompt": None, "problems": {"no_answer": "the writer returned nothing usable"},
                  "tries": 0, "split": None, "sections": None}
    for attempt in range(1, tries + 1):
        reply = llm.chat(messages, max_tokens=max_tokens, temperature=temperature)
        obj = _json_object(reply)
        if obj is None:
            last.update(tries=attempt, problems={"not_json": "the writer did not return a JSON object"})
            messages += [{"role": "assistant", "content": reply[:2000]},
                         {"role": "user", "content": "Return only one JSON object with the listed keys."}]
            continue
        if obj.get("split"):
            return {"prompt": None, "problems": {}, "tries": attempt, "split": obj["split"], "sections": None}
        sections = dict(shot.get("sections") or {})
        for key in ("scene", "beats", "acting", "camera", "light", "sound", "music", "summary"):
            if key in obj:
                sections[key] = obj[key]
        trial = dict(shot, sections=sections)
        prompt = compose(trial)
        problems = check(trial, prompt, decider)
        hard = {k: v for k, v in problems.items() if not k.endswith("_unchecked")}
        last = {"prompt": prompt, "problems": problems, "tries": attempt, "split": None, "sections": sections}
        if not hard:
            return last
        messages += [{"role": "assistant", "content": json.dumps(obj, ensure_ascii=False)[:3000]},
                     {"role": "user", "content": "The assembled clip broke these rules: "
                      + "; ".join(f"{k} ({v})" for k, v in hard.items())
                      + ". Rewrite the JSON so none of them happens. If it cannot be one composition, return split."}]
    return last


# ---------------------------------------------------------------- cli
def main(argv=None) -> int:
    import argparse
    import sys
    from pathlib import Path
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="h3compose")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("try", help="write one clip from a JSON file {shot:{...}, facts:{...}}")
    p.add_argument("clip")
    p.add_argument("--url", default="http://127.0.0.1:5678")
    p.add_argument("--judge", action="store_true", help="also ask the meaning questions (Jev)")
    p.add_argument("--tries", type=int, default=3)
    p.add_argument("--out", required=True, help="where to write the prompt and the problems (a work folder)")
    a = ap.parse_args(argv)
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parent / "chat-upgrade"))
    from chatup.llm import LLMClient
    data = json.loads(Path(a.clip).read_text(encoding="utf-8-sig"))
    llm = LLMClient(a.url, timeout=300)
    decider = None
    if a.judge:
        from chatup.decide import Decider
        decider = Decider(llm)
    res = write(data["shot"], data.get("facts") or {}, llm, tries=a.tries, decider=decider)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.clip).stem
    if res["prompt"]:
        (out / f"{stem}.h3.txt").write_text(res["prompt"], encoding="utf-8")
    (out / f"{stem}.h3.json").write_text(json.dumps({k: res[k] for k in ("problems", "tries", "split")},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    state = "split" if res["split"] else ("clean" if res["prompt"] and not res["problems"] else "problems")
    print(f"RESULT {stem}: {state} after {res['tries']} tries; rules: {sorted(res['problems']) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build MiniMax H3 Ref2VA prompts for scenes with many characters.

A cast file fixes each character's reference slot for the whole film, and a
scene file lists clips and shots. For every clip this writes the six-section
full-reference prompt (subject_definitions, summary, retention_analysis,
detailed_description, overall_soundscape, non_diegetic_music) plus a manifest
that says which image or audio file goes into which Extender slot.

    python h3_scene.py build examples/S01_diner.yaml --cast examples/cast.yaml --out out
    python h3_scene.py check examples/S01_diner.yaml --cast examples/cast.yaml
    python h3_scene.py build ... --llm http://127.0.0.1:5678   # expand the description with a local LLM
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# MiniMax H3 README, H3-Base-Ref2VA row: <= 9 images, <= 3 videos, <= 3 audio, <= 12 files.
MAX_PICTURES = 9
MAX_VIDEOS = 3
MAX_AUDIO = 3
MAX_MIXED = 12
MIN_DURATION, MAX_DURATION = 4.0, 15.0
# h3-studio validates against a 7,000-character prompt cap.
PROMPT_CHAR_CAP = 7000
# ref-en.txt: "For generation tasks, detailed_description is normally 350-500 English words."
DESC_WORDS = (350, 500)
SECTIONS = (
    "subject_definitions",
    "summary",
    "retention_analysis",
    "detailed_description",
    "overall_soundscape",
    "non_diegetic_music",
)
GUIDE_URL = (
    "https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/"
    "skills/h3-prompt-writing/references/ref-en.txt"
)

# name -> (English phrase, max identity-critical faces, rough face height as a
# fraction of the frame). The fraction feeds a heuristic: H3 reasons on a 32x
# grid (16x VAE + 2x2 patches), so face_px / 32 is about how many tokens tall a
# face is. Below ~3 tokens the face cannot carry identity; costume and hair do.
FRAMINGS = {
    "extreme-wide": ("extreme wide shot", 6, 0.03),
    "wide": ("wide shot", 6, 0.06),
    "full": ("full shot", 4, 0.10),
    "medium": ("medium shot", 3, 0.20),
    "over-the-shoulder": ("over-the-shoulder shot", 2, 0.25),
    "medium-close": ("medium close-up", 2, 0.30),
    "close-up": ("close-up", 1, 0.50),
    "extreme-close-up": ("extreme close-up", 1, 0.80),
}
FACE_TOKENS_MIN = 3.0
MAX_SPEAKERS_PER_CLIP = 2  # MiniMax-H3 issue #17: voices bleed between subjects.
# Rough speaking rates used to warn when a line cannot fit its shot.
SPEECH_RATE = {"korean": 7.0, "japanese": 8.0, "chinese": 5.0}  # characters per second
ENGLISH_WPS = 2.7


class SceneError(Exception):
    pass


@dataclass
class Character:
    id: str
    name: str
    slot: int
    look: str
    short: str
    sheet: str | None = None
    face: str | None = None
    voice: str | None = None
    voice_desc: str | None = None
    ref: str = "auto"  # auto | sheet | face

    def ref_image(self) -> str | None:
        if self.ref == "face":
            return self.face or self.sheet
        if self.ref == "sheet":
            return self.sheet or self.face
        return self.sheet or self.face


@dataclass
class Location:
    id: str
    look: str
    short: str
    image: str | None = None
    slot: int = 7


@dataclass
class Line:
    who: str
    text: str
    lang: str = "Korean"
    delivery: str = ""
    to: str | None = None
    offscreen: bool = False


@dataclass
class Shot:
    index: int
    at: float
    framing: str
    cast: list[str]
    action: str = ""
    camera: str = ""
    order: list[str] | None = None
    plate: bool = False
    lines: list[Line] = field(default_factory=list)
    end: float = 0.0


@dataclass
class Policy:
    slots: str = "fixed"  # fixed: Picture N = cast slot | compact: 1..k per load set
    load: str = "scene"  # scene: all scene refs are global refs | clip: only refs the clip uses
    unused: str = "omit"  # omit | define_absent (only when load=scene)

    def validate(self, where: str) -> None:
        if self.slots not in ("fixed", "compact"):
            raise SceneError(f"{where}: policy.slots must be fixed or compact, got {self.slots!r}")
        if self.load not in ("scene", "clip"):
            raise SceneError(f"{where}: policy.load must be scene or clip, got {self.load!r}")
        if self.unused not in ("omit", "define_absent"):
            raise SceneError(f"{where}: policy.unused must be omit or define_absent, got {self.unused!r}")


@dataclass
class Clip:
    id: str
    duration: float
    shots: list[Shot]
    summary: str = ""
    motion_context: bool = False
    policy: Policy = field(default_factory=Policy)
    seed: int | None = None


@dataclass
class Scene:
    id: str
    title: str
    location: Location
    style: str
    width: int
    height: int
    blocking: list[str]
    soundscape: str
    music: str
    clips: list[Clip]
    plate_image: str | None = None
    plate_slot: int = 8
    plate_role: str = "anchor"  # anchor | first_frame
    plate_desc: str = ""


@dataclass
class Ref:
    """One reference asset loaded for a clip."""

    kind: str  # character | location | plate | voice
    key: str  # character id, location id, "plate", or character id for voices
    file: str | None
    logical_slot: int  # stable slot in the cast/scene
    label_no: int = 0  # number used in the prompt (<Picture n> / <Audio n>)
    subject_no: int = 0  # <Subject n>, 0 for plate and voices
    used: bool = True  # False when loaded (scene-global) but not on screen in this clip


@dataclass
class Result:
    clip: Clip
    prompt: str
    manifest: dict
    errors: list[str]
    warnings: list[str]
    notes: list[str]


# --------------------------------------------------------------------------- loading


def _req(d: dict, key: str, where: str):
    if key not in d or d[key] in (None, ""):
        raise SceneError(f"{where}: missing '{key}'")
    return d[key]


def load_cast(path: Path) -> tuple[dict[str, Character], dict[str, Location]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    chars: dict[str, Character] = {}
    for i, c in enumerate(data.get("characters") or []):
        where = f"{path.name}: characters[{i}]"
        ch = Character(
            id=str(_req(c, "id", where)),
            name=str(c.get("name") or c["id"]),
            slot=int(_req(c, "slot", where)),
            look=str(_req(c, "look", where)).strip().rstrip("."),
            short=str(c.get("short") or c.get("name") or c["id"]).strip(),
            sheet=c.get("sheet"),
            face=c.get("face"),
            voice=c.get("voice"),
            voice_desc=c.get("voice_desc"),
            ref=str(c.get("ref") or "auto"),
        )
        if ch.id in chars:
            raise SceneError(f"{where}: duplicate character id {ch.id!r}")
        if not 1 <= ch.slot <= MAX_PICTURES:
            raise SceneError(f"{where}: slot must be 1..{MAX_PICTURES}, got {ch.slot}")
        if ch.ref not in ("auto", "sheet", "face"):
            raise SceneError(f"{where}: ref must be auto, sheet or face")
        clash = [o.id for o in chars.values() if o.slot == ch.slot]
        if clash:
            raise SceneError(f"{where}: slot {ch.slot} already used by character {clash[0]!r}")
        chars[ch.id] = ch
    locs: dict[str, Location] = {}
    for i, l in enumerate(data.get("locations") or []):
        where = f"{path.name}: locations[{i}]"
        loc = Location(
            id=str(_req(l, "id", where)),
            look=str(_req(l, "look", where)).strip().rstrip("."),
            short=str(l.get("short") or l["id"]).strip(),
            image=l.get("image"),
            slot=int(l.get("slot") or 7),
        )
        locs[loc.id] = loc
    if not chars:
        raise SceneError(f"{path.name}: no characters")
    return chars, locs


def _policy(d: dict | None, base: Policy, where: str) -> Policy:
    d = d or {}
    p = Policy(
        slots=str(d.get("slots", base.slots)),
        load=str(d.get("load", base.load)),
        unused=str(d.get("unused", base.unused)),
    )
    p.validate(where)
    return p


def load_scene(path: Path, chars: dict[str, Character], locs: dict[str, Location],
               override: Policy | None = None) -> Scene:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    where = path.name
    loc_id = str(_req(data, "location", where))
    if loc_id not in locs:
        raise SceneError(f"{where}: unknown location {loc_id!r}")
    res = data.get("resolution") or [1344, 768]
    blocking = [str(x) for x in (data.get("blocking") or [])]
    for cid in blocking:
        if cid not in chars:
            raise SceneError(f"{where}: blocking lists unknown character {cid!r}")
    plate = data.get("group_plate") or {}
    base_policy = _policy(data.get("policy"), Policy(), f"{where}: policy")
    scene = Scene(
        id=str(_req(data, "scene", where)),
        title=str(data.get("title") or ""),
        location=locs[loc_id],
        style=str(data.get("style") or "").strip(),
        width=int(res[0]),
        height=int(res[1]),
        blocking=blocking,
        soundscape=str(data.get("soundscape") or "Quiet room tone continues throughout the video.").strip(),
        music=str(data.get("music") or "N/A").strip(),
        clips=[],
        plate_image=plate.get("image"),
        plate_slot=int(plate.get("slot") or 8),
        plate_role=str(plate.get("role") or "anchor"),
        plate_desc=str(plate.get("desc") or "").strip(),
    )
    if scene.plate_role not in ("anchor", "first_frame"):
        raise SceneError(f"{where}: group_plate.role must be anchor or first_frame")
    if not 1 <= scene.plate_slot <= MAX_PICTURES:
        raise SceneError(f"{where}: group_plate.slot must be 1..{MAX_PICTURES}")
    if not 1 <= scene.location.slot <= MAX_PICTURES:
        raise SceneError(f"{where}: location slot must be 1..{MAX_PICTURES}")
    for ci, c in enumerate(data.get("clips") or []):
        cw = f"{where}: clips[{ci}]"
        shots = []
        for si, s in enumerate(_req(c, "shots", cw)):
            sw = f"{cw}.shots[{si}]"
            framing = str(_req(s, "framing", sw))
            if framing not in FRAMINGS:
                raise SceneError(f"{sw}: framing must be one of {', '.join(FRAMINGS)}")
            cast = [str(x) for x in (s.get("cast") or [])]
            for cid in cast:
                if cid not in chars:
                    raise SceneError(f"{sw}: unknown character {cid!r}")
            lines = []
            for li, ln in enumerate(s.get("lines") or []):
                lw = f"{sw}.lines[{li}]"
                who = str(_req(ln, "who", lw))
                if who not in chars:
                    raise SceneError(f"{lw}: unknown speaker {who!r}")
                lines.append(Line(
                    who=who,
                    text=str(_req(ln, "text", lw)).strip(),
                    lang=str(ln.get("lang") or "Korean"),
                    delivery=str(ln.get("delivery") or "").strip(),
                    to=str(ln["to"]) if ln.get("to") else None,
                    offscreen=bool(ln.get("offscreen", False)),
                ))
            order = [str(x) for x in s["order"]] if s.get("order") else None
            shots.append(Shot(
                index=si + 1,
                at=float(s.get("at", 0.0) or 0.0),
                framing=framing,
                cast=cast,
                action=str(s.get("action") or "").strip(),
                camera=str(s.get("camera") or "").strip(),
                order=order,
                plate=bool(s.get("group_plate", False)),
                lines=lines,
            ))
        clip_policy = _policy(c.get("policy"), base_policy, f"{cw}: policy")
        if override:
            clip_policy = override
        scene.clips.append(Clip(
            id=str(_req(c, "id", cw)),
            duration=float(_req(c, "duration", cw)),
            shots=shots,
            summary=str(c.get("summary") or "").strip(),
            motion_context=bool(c.get("motion_context", False)),
            policy=clip_policy,
            seed=int(c["seed"]) if c.get("seed") is not None else None,
        ))
    if not scene.clips:
        raise SceneError(f"{where}: no clips")
    return scene


# --------------------------------------------------------------------------- helpers


def ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    return f"{ms // 60000:02d}:{(ms // 1000) % 60:02d}.{ms % 1000:03d}"


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text[-1] not in ".!?":
        text += "."
    return text[0].upper() + text[1:]


def _join_names(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _a(phrase: str) -> str:
    return ("an " if phrase[:1].lower() in "aeiou" else "a ") + phrase


def speech_seconds(line: Line) -> float:
    lang = line.lang.lower()
    if lang in SPEECH_RATE:
        return len(re.sub(r"\s", "", line.text)) / SPEECH_RATE[lang]
    return max(1, len(line.text.split())) / ENGLISH_WPS


def _hangul_outside_dialogue(text: str) -> bool:
    stripped = re.sub(r"<d>.*?</d>", "", text, flags=re.S)
    return bool(re.search(r"[\uac00-\ud7a3]", stripped))


# --------------------------------------------------------------------------- building


def _clip_refs(scene: Scene, clip: Clip, chars: dict[str, Character]) -> tuple[list[Ref], list[str]]:
    """Decide which assets are loaded for this clip and number them."""
    errors: list[str] = []
    on_screen: list[str] = []
    for shot in clip.shots:
        for cid in shot.cast:
            if cid not in on_screen:
                on_screen.append(cid)
        for ln in shot.lines:
            if ln.who not in on_screen:
                on_screen.append(ln.who)
    uses_plate = any(s.plate for s in clip.shots)

    if clip.policy.load == "scene":
        scene_cast: list[str] = []
        for c in scene.clips:
            for s in c.shots:
                for cid in s.cast + [ln.who for ln in s.lines]:
                    if cid not in scene_cast:
                        scene_cast.append(cid)
        loaded_chars = scene_cast
        load_plate = bool(scene.plate_image) and any(s.plate for c in scene.clips for s in c.shots)
    else:
        loaded_chars = on_screen
        load_plate = uses_plate

    refs: list[Ref] = []
    for cid in sorted(loaded_chars, key=lambda x: chars[x].slot):
        ch = chars[cid]
        refs.append(Ref("character", cid, ch.ref_image(), ch.slot, used=cid in on_screen))
    loc = scene.location
    if loc.image:  # without an image the location is described in plain text only
        refs.append(Ref("location", loc.id, loc.image, loc.slot))
    if load_plate:
        refs.append(Ref("plate", "plate", scene.plate_image, scene.plate_slot, used=uses_plate))
    if uses_plate and not scene.plate_image:
        errors.append(f"{clip.id}: a shot sets group_plate but the scene has no group_plate.image")

    by_slot: dict[int, Ref] = {}
    for r in refs:
        if r.logical_slot in by_slot:
            other = by_slot[r.logical_slot]
            errors.append(f"{clip.id}: slot {r.logical_slot} is used by both {other.key!r} and {r.key!r}")
        by_slot[r.logical_slot] = r
    refs.sort(key=lambda r: r.logical_slot)
    for i, r in enumerate(refs, start=1):
        r.label_no = r.logical_slot if clip.policy.slots == "fixed" else i

    # Voices: one <Audio n> per speaker that has a voice file, in speaker order.
    speakers: list[str] = []
    for shot in clip.shots:
        for ln in shot.lines:
            if ln.who not in speakers:
                speakers.append(ln.who)
    audio_no = 0
    for cid in speakers:
        if chars[cid].voice:
            audio_no += 1
            refs.append(Ref("voice", cid, chars[cid].voice, audio_no, label_no=audio_no))
    return refs, errors


def _label_maps(refs: list[Ref], clip: Clip) -> tuple[dict[str, int], int | None, int | None]:
    """Assign <Subject n>: characters and location, contiguous in slot order."""
    subj: dict[str, int] = {}
    n = 0
    loc_subject = None
    for r in refs:
        if r.kind == "character" and (r.used or clip.policy.unused == "define_absent"):
            n += 1
            r.subject_no = n
            subj[r.key] = n
        elif r.kind == "location":
            n += 1
            r.subject_no = n
            loc_subject = n
    plate_pic = next((r.label_no for r in refs if r.kind == "plate" and r.used), None)
    return subj, loc_subject, plate_pic


def build_clip(scene: Scene, clip: Clip, chars: dict[str, Character]) -> Result:
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    # ---- timing
    if not MIN_DURATION <= clip.duration <= MAX_DURATION:
        errors.append(f"{clip.id}: duration {clip.duration}s is outside {MIN_DURATION:g}-{MAX_DURATION:g}s")
    prev = -1.0
    for i, shot in enumerate(clip.shots):
        if i == 0 and shot.at not in (0, 0.0):
            errors.append(f"{clip.id}: shot 1 must start at 0 (it has no timestamp in H3 format)")
        if shot.at <= prev:
            errors.append(f"{clip.id}: shot {shot.index} starts at {shot.at}s, not after shot {shot.index - 1}")
        if shot.at >= clip.duration:
            errors.append(f"{clip.id}: shot {shot.index} starts at {shot.at}s, past the clip end {clip.duration}s")
        prev = shot.at
    for i, shot in enumerate(clip.shots):
        shot.end = clip.shots[i + 1].at if i + 1 < len(clip.shots) else clip.duration

    refs, ref_errors = _clip_refs(scene, clip, chars)
    errors += ref_errors
    subj, loc_subject, plate_pic = _label_maps(refs, clip)
    pictures = [r for r in refs if r.kind != "voice"]
    voices = [r for r in refs if r.kind == "voice"]

    # ---- reference limits
    if len(pictures) > MAX_PICTURES:
        errors.append(f"{clip.id}: {len(pictures)} reference images, H3 Ref2VA takes at most {MAX_PICTURES}")
    if len(voices) > MAX_AUDIO:
        errors.append(f"{clip.id}: {len(voices)} voice references, H3 Ref2VA takes at most {MAX_AUDIO}")
    if len(pictures) + len(voices) > MAX_MIXED:
        errors.append(f"{clip.id}: {len(pictures) + len(voices)} reference files, H3 Ref2VA takes at most {MAX_MIXED}")
    for r in pictures:
        if not r.file:
            errors.append(f"{clip.id}: no image file for {r.kind} {r.key!r} (Picture slot {r.logical_slot})")
    unused = [r.key for r in pictures if not r.used]
    if unused:
        notes.append(f"{clip.id}: loaded but not on screen: {', '.join(unused)} (policy load=scene, unused={clip.policy.unused})")

    # ---- speakers
    speaker_ids: dict[str, int] = {}
    for shot in clip.shots:
        for ln in shot.lines:
            if ln.who not in speaker_ids:
                speaker_ids[ln.who] = len(speaker_ids) + 1
            if ln.who not in shot.cast and not ln.offscreen:
                errors.append(f"{clip.id}: shot {shot.index}: speaker {ln.who!r} is not in the shot cast (set offscreen: true if intended)")
            if ln.to and ln.to not in subj:
                errors.append(f"{clip.id}: shot {shot.index}: line addressed to {ln.to!r}, who is not defined in this clip")
    if len(speaker_ids) > MAX_SPEAKERS_PER_CLIP:
        warnings.append(
            f"{clip.id}: {len(speaker_ids)} speakers in one clip; voices can bleed between subjects "
            f"(MiniMax-H3 issue #17). Keep to {MAX_SPEAKERS_PER_CLIP} per clip and split the rest"
        )

    # ---- shot composition heuristics
    for shot in clip.shots:
        phrase, max_faces, frac = FRAMINGS[shot.framing]
        face_tokens = scene.height * frac / 32.0
        if len(shot.cast) > max_faces:
            warnings.append(
                f"{clip.id}: shot {shot.index} is {_a(phrase)} with {len(shot.cast)} people; "
                f"keep at most {max_faces} identity-critical faces, cover the rest with closer shots"
            )
        if shot.cast and face_tokens < FACE_TOKENS_MIN:
            notes.append(
                f"{clip.id}: shot {shot.index} ({shot.framing}) faces are about {face_tokens:.1f} tokens tall at "
                f"{scene.width}x{scene.height}; identity will come from costume, hair and position"
            )
        for ln in shot.lines:
            need = speech_seconds(ln)
            have = shot.end - shot.at
            if need > have * 0.9:
                warnings.append(
                    f"{clip.id}: shot {shot.index}: line by {ln.who} needs about {need:.1f}s but the shot is {have:.1f}s"
                )

    def S(cid: str) -> str:
        return f"<Subject {subj[cid]}>"

    locS = f"<Subject {loc_subject}>" if loc_subject else scene.location.short

    def fill(text: str) -> str:
        def rep(m):
            key = m.group(1)
            if key in subj:
                return S(key)
            if key in ("LOC", scene.location.id):
                return locS
            errors.append(f"{clip.id}: placeholder {{{key}}} does not match a character in this clip")
            return m.group(0)
        return re.sub(r"\{([A-Za-z0-9_]+)\}", rep, text)

    # ---- subject_definitions
    sd: list[str] = []
    for r in pictures:
        if r.kind == "character" and r.subject_no:
            ch = chars[r.key]
            line = (f"<Subject {r.subject_no}> is {ch.name}, {ch.look}. <Picture {r.label_no}> defines "
                    f"{ch.name}'s exact face, hairstyle, body proportions, clothing and accessories.")
            if not r.used:
                line += f" <Subject {r.subject_no}> does not appear in this clip."
            sd.append(line)
        elif r.kind == "location":
            sd.append(f"<Subject {r.subject_no}> is {scene.location.look}, from <Picture {r.label_no}>, "
                      f"used as the environment of every shot.")
    if plate_pic:
        plate_shots = [s for s in clip.shots if s.plate]
        shot_list = _join_names([f"[Shot {s.index}]" for s in plate_shots])
        order = _plate_order(scene, plate_shots[0])
        who = _join_names([S(c) for c in order if c in subj])
        role = "the first frame of" if scene.plate_role == "first_frame" else "the composition anchor for"
        desc = f" {scene.plate_desc.rstrip('.')}." if scene.plate_desc else ""
        sd.append(f"<Picture {plate_pic}> is {role} {shot_list}, placing {who} from left to right.{desc}")
    for r in voices:
        ch = chars[r.key]
        vd = f", {ch.voice_desc}" if ch.voice_desc else ""
        sd.append(f"<Audio {r.label_no}> is the voice-timbre reference for {S(r.key)} (S{speaker_ids[r.key]}){vd}.")

    # ---- detailed_description
    seen: set[str] = set()
    desc_lines: list[str] = []
    if scene.style:
        desc_lines.append(_sentence(scene.style))
    for shot in clip.shots:
        phrase = FRAMINGS[shot.framing][0]
        order = _plate_order(scene, shot)
        # First appearance in the clip gets the full look, later ones the short tag.
        people = []
        for cid in order:
            ch = chars[cid]
            people.append((S(cid), ch.short if cid in seen else f"{ch.name}, {ch.look}"))
            seen.add(cid)
        if shot.index == 1:
            where_txt = f"{locS}, {scene.location.look}" if loc_subject else scene.location.look
            head = f"[Shot 1] {_a(phrase).capitalize()} shows {where_txt}."
        elif len(people) == 1:
            head = f"[Shot {shot.index}] At {ts(shot.at)}, the shot cuts to {_a(phrase)} of {people[0][0]} in {locS}."
        else:
            head = f"[Shot {shot.index}] At {ts(shot.at)}, the shot cuts to {_a(phrase)} in {locS}."
        parts = [head]
        if shot.plate and plate_pic:
            parts.append(f"The staging follows <Picture {plate_pic}>, which fixes where each person is placed.")
        if len(people) > 1:
            parts.append("From left to right: " + "; ".join(f"{lab}, {desc}" for lab, desc in people) + ".")
        elif people:
            where = ", at the center of the frame" if shot.index == 1 else ""
            parts.append(f"{people[0][0]} is {people[0][1]}{where}.")
        if shot.camera:
            parts.append(_sentence(fill(shot.camera)))
        if shot.action:
            parts.append(_sentence(fill(shot.action)))
        for ln in shot.lines:
            sx = speaker_ids[ln.who]
            who = f"{S(ln.who)} (S{sx})" + (" off-screen" if ln.offscreen else "")
            verb = f"turns to {S(ln.to)} and says" if ln.to else "says"
            voice = next((r for r in voices if r.key == ln.who), None)
            how = []
            if ln.delivery:
                how.append(ln.delivery.rstrip("."))
            if voice:
                how.append(f"using the voice timbre referenced from <Audio {voice.label_no}>")
            how_txt = (", " + ", ".join(how) + ",") if how else ""
            parts.append(f"{who}{how_txt} {verb}, <d>[{ln.lang}] {ln.text}</d>")
        desc_lines.append(" ".join(p for p in parts if p))

    # ---- summary
    types = ["reference generation"]
    if plate_pic and scene.plate_role == "first_frame":
        types.insert(0, "keyframe completion")
    if voices:
        types.append("audio reference")
    on_screen_labels = [S(c) for c in subj if any(c in s.cast for s in clip.shots)]
    flow = []
    for shot in clip.shots:
        phrase = FRAMINGS[shot.framing][0]
        members = [S(c) for c in (shot.order or shot.cast)]
        flow.append(f"{_a(phrase)} of {_join_names(members)}" if members else _a(phrase) + f" of {locS}")
    auto = "It opens on " + flow[0]
    if len(flow) > 1:
        auto += ", then cuts to " + _join_names(flow[1:])
    auto += "."
    summary = f"[{' + '.join(types)}] The target video shows {_join_names(on_screen_labels) or locS} in {locS}. "
    summary += (fill(clip.summary) + " " if clip.summary else "") + auto
    if voices:
        summary += " " + " ".join(
            f"<Audio {r.label_no}> guides the voice of {S(r.key)}." for r in voices)

    # ---- retention_analysis
    ra: list[str] = []
    for r in pictures:
        if r.kind == "character" and r.used:
            shots_in = [s for s in clip.shots if r.key in s.cast]
            where = ", ".join(f"[Shot {s.index}]" for s in shots_in)
            ch = chars[r.key]
            only_small = shots_in and all(scene.height * FRAMINGS[s.framing][2] / 32.0 < FACE_TOKENS_MIN for s in shots_in)
            if not shots_in:  # speaks off-screen only
                continue
            if only_small:
                ra.append(f"{S(r.key)} (appears in {where}): partially_preserved - {ch.name}'s hair, costume and "
                          f"silhouette are retained; the face is too small in frame to carry full facial detail.")
            else:
                ra.append(f"{S(r.key)} (appears in {where}): fully_preserved - {ch.name}'s face, hairstyle, "
                          f"clothing and accessories are retained.")
        elif r.kind == "location":
            ra.append(f"{locS} (appears in " + ", ".join(f"[Shot {s.index}]" for s in clip.shots)
                      + f"): fully_preserved - the look of {scene.location.short} is retained.")
    if plate_pic:
        first = next(s for s in clip.shots if s.plate)
        if scene.plate_role == "first_frame":
            ra.append(f"<Picture {plate_pic}> ([Shot {first.index}] first frame): fully_preserved - the opening "
                      f"frame, placement and costumes match the plate.")
        else:
            ra.append(f"<Picture {plate_pic}> ([Shot {first.index}] composition anchor): partially_preserved - "
                      f"the left-to-right placement is retained while the people move.")
    for r in voices:
        ra.append(f"<Audio {r.label_no}>: reference - the voice of {S(r.key)} follows <Audio {r.label_no}>'s "
                  f"timbre without copying the original signal.")

    detailed = "\n".join(desc_lines)
    prompt = assemble({
        "subject_definitions": "\n".join(sd),
        "summary": summary.strip(),
        "retention_analysis": "\n".join(ra),
        "detailed_description": detailed,
        "overall_soundscape": _sentence(scene.soundscape),
        "non_diegetic_music": scene.music if scene.music.upper() == "N/A" else _sentence(scene.music),
    })

    # ---- final checks on the text
    errors += check_prompt(prompt, pictures, voices, clip.id)
    words = len(re.sub(r"<d>.*?</d>", "", detailed, flags=re.S).split())
    if words < DESC_WORDS[0]:
        notes.append(f"{clip.id}: detailed_description is {words} words; the official guide suggests "
                     f"{DESC_WORDS[0]}-{DESC_WORDS[1]} (add detail to action/camera, or use --llm)")
    if len(prompt) > PROMPT_CHAR_CAP:
        warnings.append(f"{clip.id}: prompt is {len(prompt)} characters, over the {PROMPT_CHAR_CAP} cap h3-studio enforces")

    manifest = make_manifest(scene, clip, refs, subj, speaker_ids, chars)
    return Result(clip, prompt, manifest, errors, warnings, notes)


def _plate_order(scene: Scene, shot: Shot) -> list[str]:
    return shot.order or [c for c in scene.blocking if c in shot.cast] + [c for c in shot.cast if c not in scene.blocking]


def assemble(sections: dict[str, str]) -> str:
    return "\n\n".join(f"{name}:\n{sections[name].strip()}" for name in SECTIONS) + "\n"


def split_sections(prompt: str) -> dict[str, str]:
    pattern = re.compile(r"^(" + "|".join(SECTIONS) + r"):[ \t]*\n?", re.M)
    found = list(pattern.finditer(prompt))
    out: dict[str, str] = {}
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(prompt)
        out[m.group(1)] = prompt[m.end():end].strip()
    return out


def check_prompt(prompt: str, pictures: list[Ref], voices: list[Ref], clip_id: str) -> list[str]:
    """Structural checks that apply to both template and LLM output."""
    errors = []
    names = [m.group(1) for m in re.finditer(r"^(" + "|".join(SECTIONS) + r"):", prompt, re.M)]
    if names != list(SECTIONS):
        errors.append(f"{clip_id}: sections are {names}, expected {list(SECTIONS)}")
    pic_nos = {r.label_no for r in pictures}
    for m in re.finditer(r"<Picture (\d+)>", prompt):
        if int(m.group(1)) not in pic_nos:
            errors.append(f"{clip_id}: <Picture {m.group(1)}> has no loaded image; the Extender leaves it "
                          f"unmapped and the reference silently does not bind")
    aud_nos = {r.label_no for r in voices}
    for m in re.finditer(r"<Audio (\d+)>", prompt):
        if int(m.group(1)) not in aud_nos:
            errors.append(f"{clip_id}: <Audio {m.group(1)}> has no loaded audio file")
    sections = split_sections(prompt)
    defined = set(re.findall(r"<Subject (\d+)>", sections.get("subject_definitions", "")))
    used = set(re.findall(r"<Subject (\d+)>", prompt))
    for n in sorted(used - defined, key=int):
        errors.append(f"{clip_id}: <Subject {n}> is used but not defined in subject_definitions")
    if _hangul_outside_dialogue(prompt):
        errors.append(f"{clip_id}: Korean text outside <d>...</d>; the six sections must be English")
    return errors


def make_manifest(scene: Scene, clip: Clip, refs: list[Ref], subj: dict[str, int],
                  speaker_ids: dict[str, int], chars: dict[str, Character]) -> dict:
    scope = "global (scene project)" if clip.policy.load == "scene" else "local (this clip)"
    pics = []
    for r in refs:
        if r.kind == "voice":
            continue
        who = chars[r.key].name if r.kind == "character" else (scene.location.id if r.kind == "location" else "group plate")
        pics.append({
            "extender_slot": r.logical_slot if clip.policy.slots == "fixed" else r.label_no,
            "prompt_label": f"<Picture {r.label_no}>",
            "what": f"{r.kind}: {who}",
            "file": r.file,
            "load_as": scope,
            "on_screen": r.used,
        })
    audio = [{
        "extender_slot": r.label_no,
        "prompt_label": f"<Audio {r.label_no}>",
        "what": f"voice of {chars[r.key].name} (S{speaker_ids[r.key]})",
        "file": r.file,
        "load_as": "local (this clip)",
    } for r in refs if r.kind == "voice"]
    return {
        "scene": scene.id,
        "clip": clip.id,
        "duration_s": clip.duration,
        "resolution": [scene.width, scene.height],
        "motion_context": "ON" if clip.motion_context else "OFF",
        "seed": clip.seed,
        "policy": {"slots": clip.policy.slots, "load": clip.policy.load, "unused": clip.policy.unused},
        "pictures": pics,
        "audio": audio,
        "speakers": {f"S{n}": chars[c].name for c, n in speaker_ids.items()},
    }


def manifest_text(m: dict) -> str:
    out = [f"{m['scene']} {m['clip']}  {m['duration_s']:g}s  {m['resolution'][0]}x{m['resolution'][1]}  "
           f"Motion Context {m['motion_context']}  seed {m['seed'] if m['seed'] is not None else 'any'}  policy {m['policy']}"]
    for p in m["pictures"]:
        flag = "" if p["on_screen"] else "   (loaded, not on screen)"
        out.append(f"  Picture slot {p['extender_slot']}: {p['file']}  <- {p['what']}  [{p['load_as']}]{flag}")
    for a in m["audio"]:
        out.append(f"  Audio slot {a['extender_slot']}: {a['file']}  <- {a['what']}  [{a['load_as']}]")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- local LLM


def load_guide(src: str | None, cache_dir: Path) -> str:
    if src and not src.startswith("http"):
        return Path(src).read_text(encoding="utf-8")
    cache = cache_dir / "ref-en.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    with urllib.request.urlopen(src or GUIDE_URL, timeout=60) as r:
        text = r.read().decode("utf-8")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


LLM_SYSTEM = """You expand the detailed_description section of a MiniMax H3 full-reference (Ref2VA) prompt.
Follow the official guide below. Output ONLY the new detailed_description text: no section name, no other sections, no commentary.
Hard rules:
- Keep the first style sentence, then every [Shot N] marker in the same order, with the same "At MM:SS.mmm" timestamps.
- Keep every <Subject N>, <Picture N> and <Audio N> label exactly as written, attached to the same person or asset. Do not add labels that are not in the draft.
- Keep every <d>[Language] ...</d> dialogue span and its (Sx) speaker ID exactly, character for character.
- Keep the left-to-right placement of people.
- Write in English. Only text inside <d>...</d> may be in another language.
- Add concrete visual detail per shot: composition, positions, lighting, gestures, expressions, camera movement and speed, and sound. Aim for 350-500 English words in total.

OFFICIAL GUIDE:
"""


def _llm_call(url: str, messages: list[dict], timeout: int) -> str:
    body = json.dumps({
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 1800,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["choices"][0]["message"].get("content") or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^detailed_description:\s*", "", text)
    return text.strip()


def compare_description(draft: str, new: str) -> list[str]:
    """Why an LLM rewrite of detailed_description is not acceptable (empty = OK)."""
    problems = []
    lab = re.compile(r"<(?:Subject|Picture|Audio) \d+>")
    if set(lab.findall(new)) != set(lab.findall(draft)):
        problems.append(f"labels changed: draft {sorted(set(lab.findall(draft)))} vs new {sorted(set(lab.findall(new)))}")
    d_old = re.findall(r"<d>.*?</d>", draft, flags=re.S)
    d_new = re.findall(r"<d>.*?</d>", new, flags=re.S)
    if d_old != d_new:
        problems.append("dialogue <d>...</d> spans were changed, dropped or reordered")
    sp = re.compile(r"<Subject \d+> \(S\d+\)")
    if sorted(set(sp.findall(draft))) != sorted(set(sp.findall(new))):
        problems.append("speaker IDs (Sx) were changed")
    shots = re.compile(r"\[Shot (\d+)\](?: At (\d\d:\d\d\.\d{3}))?")
    if shots.findall(draft) != shots.findall(new):
        problems.append("[Shot N] markers or timestamps changed")
    if _hangul_outside_dialogue(new):
        problems.append("Korean text outside <d>...</d>")
    words = len(re.sub(r"<d>.*?</d>", "", new, flags=re.S).split())
    if words < 200 or words > 800:
        problems.append(f"length {words} words is outside 200-800")
    return problems


def llm_expand(result: Result, url: str, guide: str, timeout: int = 600) -> None:
    sections = split_sections(result.prompt)
    draft = sections["detailed_description"]
    context = "\n\n".join(f"{k}:\n{sections[k]}" for k in ("subject_definitions", "summary"))
    messages = [
        {"role": "system", "content": LLM_SYSTEM + guide},
        {"role": "user", "content": f"{context}\n\nDRAFT detailed_description:\n{draft}"},
    ]
    for attempt in (1, 2):
        try:
            new = _llm_call(url, messages, timeout)
        except Exception as exc:  # network, HTTP, bad JSON
            result.warnings.append(f"{result.clip.id}: LLM call failed ({exc}); kept the template text")
            return
        problems = compare_description(draft, new)
        if not problems:
            sections["detailed_description"] = new
            candidate = assemble(sections)
            if len(candidate) > PROMPT_CHAR_CAP:
                result.warnings.append(f"{result.clip.id}: LLM text makes the prompt {len(candidate)} characters; kept the template text")
                return
            result.prompt = candidate
            result.notes = [n for n in result.notes if "detailed_description is" not in n]
            result.notes.append(f"{result.clip.id}: detailed_description expanded by the local LLM (attempt {attempt})")
            return
        messages += [
            {"role": "assistant", "content": new},
            {"role": "user", "content": "Rejected: " + "; ".join(problems) + ". Rewrite it and follow every hard rule."},
        ]
    result.warnings.append(f"{result.clip.id}: LLM output broke the rules twice ({'; '.join(problems)}); kept the template text")


# --------------------------------------------------------------------------- CLI


def run(args: argparse.Namespace) -> int:
    cast_path = Path(args.cast)
    chars, locs = load_cast(cast_path)
    override = None
    if args.slots or args.load or args.unused:
        override = Policy(slots=args.slots or "fixed", load=args.load or "scene", unused=args.unused or "omit")
        override.validate("command line")
    scene = load_scene(Path(args.scene), chars, locs, override)
    results = [build_clip(scene, clip, chars) for clip in scene.clips]

    if args.check_files:
        base = cast_path.parent
        for res in results:
            for item in res.manifest["pictures"] + res.manifest["audio"]:
                f = item["file"]
                if f and not (base / f).exists() and not Path(f).exists():
                    res.errors.append(f"{res.clip.id}: file not found: {f}")

    if args.command == "build" and args.llm:
        guide = load_guide(args.guide, Path(args.out) / ".cache")
        for res in results:
            if not res.errors:
                llm_expand(res, args.llm, guide)

    total_err = sum(len(r.errors) for r in results)
    report = [f"# {scene.id} {scene.title}".rstrip(), ""]
    for res in results:
        status = "ERROR" if res.errors else ("WARN" if res.warnings else "OK")
        report.append(f"## {res.clip.id}: {status}")
        report.append("```")
        report.append(manifest_text(res.manifest).rstrip())
        report.append("```")
        for kind, items in (("error", res.errors), ("warning", res.warnings), ("note", res.notes)):
            for it in items:
                report.append(f"- {kind}: {it}")
        report.append("")
    report_text = "\n".join(report)
    print(report_text)

    if args.command == "build":
        out = Path(args.out) / scene.id
        out.mkdir(parents=True, exist_ok=True)
        for res in results:
            (out / f"{res.clip.id}.prompt.txt").write_text(res.prompt, encoding="utf-8")
            (out / f"{res.clip.id}.refs.txt").write_text(manifest_text(res.manifest), encoding="utf-8")
            (out / f"{res.clip.id}.refs.json").write_text(json.dumps(res.manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "report.md").write_text(report_text, encoding="utf-8")
        print(f"wrote {len(results)} clip prompts to {out}")
    return 1 if total_err else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "check"))
    ap.add_argument("scene", help="scene YAML")
    ap.add_argument("--cast", required=True, help="cast YAML (characters and locations)")
    ap.add_argument("--out", default="out", help="output folder for build (default: out)")
    ap.add_argument("--slots", choices=("fixed", "compact"), help="override policy.slots for every clip")
    ap.add_argument("--load", choices=("scene", "clip"), help="override policy.load for every clip")
    ap.add_argument("--unused", choices=("omit", "define_absent"), help="override policy.unused for every clip")
    ap.add_argument("--check-files", action="store_true", help="fail when a reference file is missing")
    ap.add_argument("--llm", help="OpenAI-compatible server to expand detailed_description, e.g. http://127.0.0.1:5678")
    ap.add_argument("--guide", help=f"path or URL of the official ref-en.txt guide (default: {GUIDE_URL})")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except SceneError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""sportspose: sports technique poses as assets a prompt agent can follow.

A pose asset (assets/<sport>/<CODE>.json) gives joint angles taken from biomechanics
papers and technique manuals. From it this tool builds one 3D skeleton, checks it
(joint range of motion, the sport's own angle rules with their sources, feet on the
floor, hands on the ball), and writes, all from that same skeleton:

  library/<sport>/<CODE>/prompt.md          the 5-section asset text (angles, objects, camera,
                                            motion) plus a ready prompt and negative prompt
  library/<sport>/<CODE>/openpose_<cam>.png ControlNet OpenPose image (body + hands), per camera
  library/<sport>/<CODE>/openpose_<cam>.json the same keypoints, OpenPose JSON (ComfyUI / editor)
  library/<sport>/<CODE>/preview.png        front / side / top wireframe with ball, net, floor
  library/<sport>/<CODE>/skeleton3d.json    3D joint positions in metres
  library/index.json                        what a prompt agent searches (Korean / English names)

Because the numbers in the text are measured on the same skeleton that is drawn, the
prompt and the pose image cannot disagree.

  build [CODE ...]      validate and write the library (all assets by default)
  check [CODE ...]      validate only
  find QUERY            best matching assets for a prompt agent (Korean or English)
  show CODE             print the prompt block of one asset
  sequence ID           the phases of one movement in order (for a video prompt), e.g. BASEBALL_PITCH

Frames. World: x = direction of play (toward the net / goal / plate / basket), y = left of
that, z = up, metres, floor at z = 0. Angles in degrees.
  pelvis  yaw (+ = turned left), tilt (+ = leaning forward), side (+ = leaning to the right)
  trunk   thorax on pelvis: flex (+ forward, - arched back), side (+ bend right), rot (+ turn left)
  head    on thorax: flex (+ chin down, - looking up), side (+ tilt right), rot (+ turn left),
          or look_at: a point or object name
  arm     elev 0 = hanging, 90 = horizontal, 180 = overhead, in the vertical plane `plane`
          (0 = straight out to the side, 90 = straight forward, -40 = behind the shoulder line,
          130 = across the chest); rot = humeral rotation (+ external); elbow flexion (0 = straight);
          pron = forearm pronation (0 = thumb up with the elbow bent, 90 = palm down);
          wrist = flexion toward the palm (- = extension); hand = finger shape;
          reach = {"to": object, "w": weight}: solve the arm so the palm lies on it
  leg     flex = hip flexion (- = extension), abd = abduction, rot = hip rotation (+ external),
          knee flexion, ankle = plantarflexion (+ toes down, - = dorsiflexion)
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
LIBRARY = HERE / "library"

Vec = Tuple[float, float, float]
Mat = Tuple[Vec, Vec, Vec]          # rows


# ---------------------------------------------------------------- vector math
def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a: Vec) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec) -> Vec:
    n = length(a)
    return (0.0, 0.0, 0.0) if n < 1e-12 else mul(a, 1.0 / n)


def comb(*terms) -> Vec:
    """comb((k1, v1), (k2, v2), ...) = k1*v1 + k2*v2 + ..."""
    x = y = z = 0.0
    for k, v in terms:
        x += k * v[0]
        y += k * v[1]
        z += k * v[2]
    return (x, y, z)


def mv(m: Mat, v: Vec) -> Vec:
    return (dot(m[0], v), dot(m[1], v), dot(m[2], v))


def mm(a: Mat, b: Mat) -> Mat:
    cols = list(zip(*b))
    return tuple(tuple(dot(r, c) for c in cols) for r in a)  # type: ignore[return-value]


def rot(axis: Vec, deg: float) -> Mat:
    """Rotation by deg about axis, right-hand rule (Rodrigues)."""
    x, y, z = unit(axis)
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    k = 1 - c
    return ((c + x * x * k, x * y * k - z * s, x * z * k + y * s),
            (y * x * k + z * s, c + y * y * k, y * z * k - x * s),
            (z * x * k - y * s, z * y * k + x * s, c + z * z * k))


def angle_between(a: Vec, b: Vec) -> float:
    c = dot(unit(a), unit(b))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


X: Vec = (1.0, 0.0, 0.0)
Y: Vec = (0.0, 1.0, 0.0)
Z: Vec = (0.0, 0.0, 1.0)
DOWN: Vec = (0.0, 0.0, -1.0)


class Frame:
    """Orthonormal frame: columns are the local x (forward), y (left), z (up) axes in world."""

    def __init__(self, m: Mat):
        self.m = m

    @staticmethod
    def identity() -> "Frame":
        return Frame(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))

    def then(self, local: Mat) -> "Frame":          # rotate about this frame's own axes
        return Frame(mm(self.m, local))

    def to_world(self, v: Vec) -> Vec:
        return mv(self.m, v)

    def to_local(self, v: Vec) -> Vec:
        t = tuple(zip(*self.m))
        return mv(t, v)  # type: ignore[arg-type]

    @property
    def x(self) -> Vec:
        return (self.m[0][0], self.m[1][0], self.m[2][0])

    @property
    def y(self) -> Vec:
        return (self.m[0][1], self.m[1][1], self.m[2][1])

    @property
    def z(self) -> Vec:
        return (self.m[0][2], self.m[1][2], self.m[2][2])


def euler_fsr(flex: float, side: float, rot_: float) -> Mat:
    """flexion (+ forward) about y, then side bend (+ right) about x, then axial rotation (+ left) about z."""
    return mm(mm(rot(Y, flex), rot(X, side)), rot(Z, rot_))


# ---------------------------------------------------------------- body model
# Segment lengths as a fraction of standing height H (Drillis & Contini 1966, in Winter,
# Biomechanics and Motor Control of Human Movement, fig. 4.1): hip joint 0.530H, shoulder
# 0.818H, upper arm 0.186H, forearm 0.146H, hand 0.108H, thigh 0.245H, shank 0.246H,
# ankle height 0.039H, foot 0.152H. Joint-centre widths are narrower than the body widths
# of that figure (biacromial 0.259H, hips 0.191H): the hip joint centres are about 0.098H apart
# (Bell/Harrington, 0.72 x ASIS width); 0.12H sits between that and where OpenPose-trained
# detectors put the hip keypoints.
SEG = {
    "trunk": 0.288, "neck": 0.112, "shoulder_w": 0.225, "hip_w": 0.12,
    "upper_arm": 0.186, "forearm": 0.146, "hand": 0.108,
    "thigh": 0.245, "shank": 0.246, "ankle_h": 0.039, "foot": 0.152,
}
# Face points in the head frame (fraction of H) from the head centre.
FACE = {
    "nose": (0.058, 0.0, -0.016), "eye": (0.047, 0.018, 0.006), "ear": (0.0, 0.045, 0.0),
    "forehead": (0.05, 0.0, 0.032), "crown": (0.0, 0.0, 0.068), "chin": (0.042, 0.0, -0.058),
}
SIDES = {"r": -1.0, "l": 1.0}          # sign of the body's y axis for that side

POSE_DEFAULTS = {
    "pelvis": {"yaw": 0.0, "tilt": 0.0, "side": 0.0},
    "trunk": {"flex": 0.0, "side": 0.0, "rot": 0.0},
    "head": {"flex": 0.0, "side": 0.0, "rot": 0.0},
    "arm": {"elev": 10.0, "plane": 20.0, "rot": 0.0, "elbow": 10.0, "pron": 30.0, "wrist": 0.0,
            "hand": "relaxed"},
    "leg": {"flex": 0.0, "abd": 5.0, "rot": 5.0, "knee": 3.0, "ankle": 0.0},
}

# Finger shapes: per finger (thumb, index, middle, ring, little) flexion at the three joints,
# plus spread between fingers (deg) and thumb opposition 0..1.
HAND_SHAPES = {
    "flat":     {"curl": [(5, 5, 0)] + [(0, 5, 0)] * 4, "spread": 3, "oppose": 0.0},
    "relaxed":  {"curl": [(10, 10, 10), (20, 25, 10), (25, 30, 15), (28, 32, 15), (30, 35, 15)],
                 "spread": 4, "oppose": 0.3},
    "spread":   {"curl": [(0, 5, 0)] + [(5, 8, 3)] * 4, "spread": 14, "oppose": 0.0},
    "cupped":   {"curl": [(15, 15, 10), (25, 25, 15), (28, 28, 15), (30, 30, 15), (32, 32, 15)],
                 "spread": 10, "oppose": 0.4},
    "ball_hold": {"curl": [(10, 10, 5), (18, 20, 10), (20, 22, 10), (22, 22, 10), (24, 24, 10)],
                  "spread": 16, "oppose": 0.1},
    "grip":     {"curl": [(30, 35, 30), (75, 80, 45), (80, 85, 45), (85, 85, 45), (88, 85, 45)],
                 "spread": 2, "oppose": 0.8},
    "fist":     {"curl": [(35, 45, 40), (90, 100, 60), (90, 100, 60), (90, 100, 60), (90, 100, 60)],
                 "spread": 0, "oppose": 0.9},
    "platform": {"curl": [(0, 0, 0), (5, 10, 5), (8, 12, 5), (10, 12, 5), (12, 14, 5)],
                 "spread": 0, "oppose": 0.0},
}
# hand geometry (fraction of hand length): knuckle position along the hand, across the palm
# (+ toward the thumb), and segment lengths
FINGERS = [  # name, base_along, base_across, (proximal, middle, distal)
    ("thumb", 0.12, 0.30, (0.25, 0.20, 0.16)),
    ("index", 0.47, 0.20, (0.24, 0.14, 0.10)),
    ("middle", 0.48, 0.05, (0.26, 0.16, 0.11)),
    ("ring", 0.46, -0.10, (0.24, 0.15, 0.11)),
    ("little", 0.42, -0.24, (0.19, 0.11, 0.09)),
]


class Body:
    """3D skeleton from a pose spec. points: name -> (x, y, z) in metres."""

    def __init__(self, pose: Dict, height: float = 1.8):
        self.h = height
        self.pose = self._fill(pose)
        self.points: Dict[str, Vec] = {}
        self.vecs: Dict[str, Vec] = {}
        self.frames: Dict[str, Frame] = {}
        self.hands: Dict[str, List[Vec]] = {}
        self.build()

    @staticmethod
    def _fill(pose: Dict) -> Dict:
        out = {}
        for part in ("pelvis", "trunk", "head"):
            out[part] = {**POSE_DEFAULTS[part], **(pose.get(part) or {})}
        for side in "rl":
            out[side + "_arm"] = {**POSE_DEFAULTS["arm"], **(pose.get(side + "_arm") or {})}
            out[side + "_leg"] = {**POSE_DEFAULTS["leg"], **(pose.get(side + "_leg") or {})}
        return out

    def L(self, key: str) -> float:
        return SEG[key] * self.h

    def build(self, origin: Vec = (0.0, 0.0, 0.0)) -> None:
        p = self.pose
        pts, vecs = self.points, self.vecs
        pts.clear()
        vecs.clear()
        pel = Frame.identity().then(rot(Z, p["pelvis"]["yaw"])).then(rot(Y, p["pelvis"]["tilt"])).then(
            rot(X, p["pelvis"]["side"]))
        tr = p["trunk"]
        thx = pel.then(euler_fsr(tr["flex"], tr["side"], tr["rot"]))
        self.frames.update(pelvis=pel, thorax=thx)
        pts["pelvis"] = origin
        pts["neck"] = add(origin, mul(thx.z, self.L("trunk")))
        for s, sg in SIDES.items():
            pts[s + "_hip"] = add(origin, mul(pel.y, sg * self.L("hip_w") / 2))
            pts[s + "_shoulder"] = add(pts["neck"], mul(thx.y, sg * self.L("shoulder_w") / 2))
        self._head()
        for s in "rl":
            self._arm(s)
            self._leg(s)

    def _head(self, look: Optional[Vec] = None) -> None:
        p = self.pose["head"]
        thx = self.frames["thorax"]
        flex, rot_ = p["flex"], p["rot"]
        if look is not None:                       # aim the face at a point
            hc = add(self.points["neck"], mul(thx.z, self.L("neck")))
            d = thx.to_local(unit(sub(look, hc)))
            # the eyes turn up to about 25 deg in the head, so the head turns only for the rest
            ang = angle_between(X, d)
            if ang > 25:
                k = (ang - 25) / ang
                d = unit(comb((1 - k, X), (k, d)))
            else:
                d = X
            rot_ = math.degrees(math.atan2(d[1], d[0]))
            flex = -math.degrees(math.asin(max(-1.0, min(1.0, d[2]))))
            if abs(rot_) > 90:                     # target over the crown or behind: tip the head back instead
                rot_ = math.copysign(180 - abs(rot_), rot_) * 0.5
                flex = -75.0 if d[2] > 0 else 60.0
            rot_ = max(-80.0, min(80.0, rot_))
            flex = max(-75.0, min(60.0, flex))
            p["rot"], p["flex"] = round(rot_, 1), round(flex, 1)
        hd = thx.then(euler_fsr(flex, p["side"], rot_))
        self.frames["head"] = hd
        # the neck takes about half of the bend; the rest is at the skull base, so the head
        # centre moves only half as far as the face turns
        half = thx.then(euler_fsr(flex / 2, p["side"] / 2, 0.0))
        c = add(self.points["neck"], mul(half.z, self.L("neck")))
        self.points["head"] = c
        H = self.h

        def at(off: Vec) -> Vec:
            return add(c, hd.to_world(mul(off, H)))
        self.points["nose"] = at(FACE["nose"])
        self.points["forehead"] = at(FACE["forehead"])
        self.points["crown"] = at(FACE["crown"])
        self.points["chin"] = at(FACE["chin"])
        for s, sg in SIDES.items():
            e, r = FACE["eye"], FACE["ear"]
            self.points[s + "_eye"] = at((e[0], sg * e[1], e[2]))
            self.points[s + "_ear"] = at((r[0], sg * r[1], r[2]))
        self.vecs["head_fwd"] = hd.x
        self.vecs["head_up"] = hd.z

    def _arm(self, s: str) -> None:
        a = self.pose[s + "_arm"]
        sg = SIDES[s]
        thx = self.frames["thorax"]
        pl, el = a["plane"], a["elev"]
        h = comb((math.cos(math.radians(pl)), (0.0, sg, 0.0)), (math.sin(math.radians(pl)), X))
        axis = cross(DOWN, h)
        R_e = rot(axis, el) if length(axis) > 1e-9 else rot(X, 0)
        theta = -sg * a["rot"]                              # + = external rotation
        R_r = rot(DOWN, theta)
        u = mv(R_e, DOWN)                                   # humerus, thorax-local
        f_ref = mv(R_e, mv(R_r, X))                         # where the forearm goes when the elbow bends
        med = mv(R_e, mv(R_r, (0.0, -sg, 0.0)))             # medial: palm normal at pron 0
        phi = math.radians(a["elbow"])
        w = comb((math.cos(phi), u), (math.sin(phi), f_ref))   # forearm
        # the elbow flexion axis is perpendicular to u and f_ref, so `med` is unchanged by it
        pn = mv(rot(w, sg * a["pron"]), med)                # palm normal (out of the palm)
        wf = math.radians(a["wrist"])
        hand_dir = comb((math.cos(wf), w), (math.sin(wf), pn))
        pn2 = comb((math.cos(wf), pn), (-math.sin(wf), w))
        u, w, hand_dir, pn2 = (thx.to_world(v) for v in (u, w, hand_dir, pn2))
        sh = self.points[s + "_shoulder"]
        el_pt = add(sh, mul(u, self.L("upper_arm")))
        wr = add(el_pt, mul(w, self.L("forearm")))
        self.points[s + "_elbow"] = el_pt
        self.points[s + "_wrist"] = wr
        hl = self.L("hand")
        self.points[s + "_palm"] = add(add(wr, mul(hand_dir, 0.36 * hl)), mul(pn2, 0.012 * self.h))
        self.points[s + "_fingertip"] = add(wr, mul(hand_dir, hl))
        self.vecs[s + "_upper_arm"] = u
        self.vecs[s + "_forearm"] = w
        self.vecs[s + "_hand"] = hand_dir
        self.vecs[s + "_palm_normal"] = pn2
        thumb = mul(unit(cross(hand_dir, pn2)), -sg)      # toward the thumb side
        self.vecs[s + "_thumb_side"] = thumb
        self.hands[s] = self._hand_points(wr, hand_dir, pn2, thumb, a.get("hand") or "relaxed")

    def _hand_points(self, wr: Vec, L_: Vec, N: Vec, T: Vec, shape: str) -> List[Vec]:
        """21 OpenPose hand keypoints: wrist, then thumb, index, middle, ring, little (4 each)."""
        spec = HAND_SHAPES.get(shape, HAND_SHAPES["relaxed"])
        hl = self.L("hand")
        breadth = 0.47 * hl
        out = [wr]
        for i, (name, along, across, segs) in enumerate(FINGERS):
            base = add(add(wr, mul(L_, along * hl)), mul(T, across * breadth))
            if name == "thumb":
                opp = spec["oppose"]
                # thumb leaves the palm toward the thumb side and forward; opposition turns it toward the palm
                d = unit(comb((0.75, L_), (0.55 - 0.35 * opp, T), (0.15 + 0.55 * opp, N)))
                side_ax = unit(cross(d, N)) if length(cross(d, N)) > 1e-6 else T
                bend_to = N
            else:
                spread = math.radians(spec["spread"] * (1.5 - i))          # index spreads toward the thumb
                d = unit(comb((math.cos(spread), L_), (math.sin(spread), T)))
                side_ax = T
                bend_to = N
            pts = [base]
            cur = d
            total = 0.0
            for k, seg in enumerate(segs):
                total += math.radians(spec["curl"][i][k])
                perp = unit(sub(bend_to, mul(d, dot(bend_to, d))))
                cur = comb((math.cos(total), d), (math.sin(total), perp))
                pts.append(add(pts[-1], mul(cur, seg * hl)))
            del side_ax
            out += pts
        return out

    def _leg(self, s: str) -> None:
        g = self.pose[s + "_leg"]
        sg = SIDES[s]
        pel = self.frames["pelvis"]
        R = mm(mm(rot(Y, -g["flex"]), rot(X, sg * g["abd"])), rot(DOWN, -sg * g["rot"]))
        t = mv(R, DOWN)
        a_t = mv(R, X)
        k = math.radians(g["knee"])
        shank = comb((math.cos(k), t), (-math.sin(k), a_t))
        a_s = comb((math.cos(k), a_t), (math.sin(k), t))
        ank = g.get("ankle_mode") or (g["ankle"] if isinstance(g["ankle"], str) else None)
        if ank:                                    # "flat": sole parallel to the floor; "toes:30": heel up 30 deg
            g["ankle_mode"] = ank
            want = 0.0 if ank == "flat" else float(ank.split(":")[1])
            sw, aw = pel.to_world(shank), pel.to_world(a_s)
            # foot = cos(p) a_s + sin(p) shank; its downward pitch must be `want`:
            # R cos(p - phi) = -sin(want)
            R = math.hypot(aw[2], sw[2])
            phi = math.atan2(sw[2], aw[2])
            c_ = max(-1.0, min(1.0, -math.sin(math.radians(want)) / R)) if R > 1e-9 else 0.0
            cands = [math.degrees(phi + sg_ * math.acos(c_)) for sg_ in (1, -1)]
            cands = [((x + 180) % 360) - 180 for x in cands]
            best = min(cands, key=lambda x: (abs(x) > 90, abs(x)))
            g["ankle"] = round(best, 1)
        pf = math.radians(g["ankle"])
        foot = comb((math.cos(pf), a_s), (math.sin(pf), shank))
        foot_up = comb((-math.cos(pf), shank), (math.sin(pf), a_s))
        t, shank, foot, foot_up = (pel.to_world(v) for v in (t, shank, foot, foot_up))
        hip = self.points[s + "_hip"]
        knee = add(hip, mul(t, self.L("thigh")))
        ankle = add(knee, mul(shank, self.L("shank")))
        ah, fl = self.L("ankle_h"), self.L("foot")
        self.points[s + "_knee"] = knee
        self.points[s + "_ankle"] = ankle
        self.points[s + "_heel"] = comb((1, ankle), (-0.22 * fl, foot), (-ah, foot_up))
        self.points[s + "_ball"] = comb((1, ankle), (0.55 * fl, foot), (-ah, foot_up))
        self.points[s + "_toe"] = comb((1, ankle), (0.78 * fl, foot), (-0.75 * ah, foot_up))
        self.points[s + "_instep"] = comb((1, ankle), (0.32 * fl, foot), (-0.1 * ah, foot_up))
        self.vecs[s + "_thigh"] = t
        self.vecs[s + "_shank"] = shank
        self.vecs[s + "_foot"] = foot
        self.vecs[s + "_foot_up"] = foot_up

    # -- whole-body helpers
    def shift(self, d: Vec) -> None:
        for k in self.points:
            self.points[k] = add(self.points[k], d)
        for s in self.hands:
            self.hands[s] = [add(p, d) for p in self.hands[s]]

    def all_points(self) -> List[Vec]:
        return list(self.points.values()) + [p for h in self.hands.values() for p in h]

    def foot_points(self, s: str) -> List[Vec]:
        return [self.points[s + k] for k in ("_heel", "_ball", "_toe")]


# ---------------------------------------------------------------- scene: support, objects
BALLS = {"volleyball": 0.21, "soccer": 0.22, "basketball": 0.24, "baseball": 0.074, "handball": 0.19,
         "tennis": 0.067}


class Scene:
    """Body + support (floor contact or flight) + objects + environment, solved together."""

    def __init__(self, asset: Dict):
        self.asset = asset
        ath = asset.get("athlete") or {}
        self.height = float(ath.get("height_m", 1.8))
        self.body = Body(asset.get("pose") or {}, self.height)
        self.objects: Dict[str, Dict] = {}
        self.env_points: Dict[str, Vec] = {}
        self.env: List[Dict] = list(asset.get("environment") or [])
        for e in self.env:
            k = e.get("kind")
            if k == "net":
                self.env_points["net_top"] = (float(e.get("x_m", 1.0)), float(e.get("y_m", 0.0)),
                                              float(e.get("height_m", 2.43)))
            elif k == "rim":
                self.env_points["rim"] = (float(e.get("x_m", 1.0)), float(e.get("y_m", 0.0)),
                                          float(e.get("height_m", 3.05)))
            elif k == "point":
                self.env_points[e["name"]] = tuple(float(v) for v in e["at"])  # type: ignore[assignment]
        self._place()

    def ground(self, p: Vec) -> float:
        """Floor height under a point. Flat at 0 unless the asset gives a pitching mound:
        {"kind": "mound", "top_x_m": x where the flat top ends, "slope": 1/12, "drop_m": 0.254}."""
        g = self.asset.get("ground")
        if not g or g.get("kind") != "mound":
            return 0.0
        x0 = float(g.get("top_x_m", 0.0))
        return -min(float(g.get("drop_m", 0.254)), max(0.0, p[0] - x0) * float(g.get("slope", 1 / 12)))

    def above_ground(self, p: Vec) -> float:
        return p[2] - self.ground(p)

    # a reference is a body point, an object (or object_tip / object_sweet), an environment
    # point, a pair midpoint (hands_mid ...), or [x, y, z] in the world
    def point(self, ref) -> Vec:
        if isinstance(ref, (list, tuple)):
            return (float(ref[0]), float(ref[1]), float(ref[2]))
        b = self.body
        if ref in b.points:
            return b.points[ref]
        if ref in self.objects:
            return self.objects[ref]["center"]
        for suffix in ("_tip", "_sweet", "_knob", "_hand1", "_hand2"):
            if ref.endswith(suffix) and ref[: -len(suffix)] in self.objects:
                return self.objects[ref[: -len(suffix)]][suffix[1:]]
        if ref.startswith(("right_", "left_")) and ("r_" if ref[0] == "r" else "l_") + ref.split("_", 1)[1] in b.points:
            return b.points[("r_" if ref[0] == "r" else "l_") + ref.split("_", 1)[1]]      # right_palm = r_palm
        if ref in self.env_points:
            return self.env_points[ref]
        pairs = {"hands_mid": ("r_wrist", "l_wrist"), "palms_mid": ("r_palm", "l_palm"),
                 "feet_mid": ("r_ankle", "l_ankle"), "shoulders_mid": ("r_shoulder", "l_shoulder"),
                 "hips_mid": ("r_hip", "l_hip"), "eyes_mid": ("r_eye", "l_eye")}
        if ref in pairs:
            a, c = pairs[ref]
            return mul(add(b.points[a], b.points[c]), 0.5)
        raise KeyError(f"unknown point '{ref}'")

    def _object(self, o: Dict) -> Dict:
        b = self.body
        r = o.get("diameter_m", 0.0) / 2
        out = dict(o)
        if o.get("kind") == "bat":                 # a stick; the knob end at `at` + offset
            off = o.get("offset_m", [0, 0, 0])
            knob = add(self.point(o.get("at", "hands_mid")), (float(off[0]), float(off[1]), float(off[2])))
            if "toward" in o:
                d = unit(sub(self.point(o["toward"]), knob))
            else:
                yw, pt = math.radians(o.get("yaw", 0)), math.radians(o.get("pitch", 0))
                d = (math.cos(pt) * math.cos(yw), math.cos(pt) * math.sin(yw), math.sin(pt))
            L_ = float(o.get("length_m", 0.84))
            hand1 = add(knob, mul(d, 0.05))        # bottom hand just above the knob
            out.update(center=hand1, knob=knob, hand1=hand1, hand2=add(hand1, mul(d, 0.09)),
                       tip=add(knob, mul(d, L_)), sweet=add(knob, mul(d, L_ - float(o.get("sweet_from_tip_m", 0.16)))),
                       dir=d)
            return out
        if "touch" in o:                           # a ball resting on a body surface
            t = o["touch"]
            if t.endswith("_palm"):
                c = add(b.points[t], mul(b.vecs[t[:-5] + "_palm_normal"], r + 0.005))
            elif t == "palms":
                mid = mul(add(b.points["r_palm"], b.points["l_palm"]), 0.5)
                n = unit(add(b.vecs["r_palm_normal"], b.vecs["l_palm_normal"]))
                gap = length(sub(b.points["r_palm"], b.points["l_palm"])) / 2
                c = add(mid, mul(n, math.sqrt(max(0.0, r * r - gap * gap)) + 0.005))
            elif t.endswith("_instep"):
                c = add(b.points[t], mul(b.vecs[t[:2] + "foot_up"], r + 0.01))
            elif t == "forehead":
                c = add(b.points["forehead"], mul(b.vecs["head_fwd"], r + 0.01))
            elif t == "forearms":                  # volleyball platform, just above the wrists
                w = mul(add(b.points["r_wrist"], b.points["l_wrist"]), 0.5)
                e = mul(add(b.points["r_elbow"], b.points["l_elbow"]), 0.5)
                mid = add(w, mul(sub(e, w), 0.25))
                n = unit(cross(sub(b.points["l_elbow"], b.points["r_elbow"]), sub(e, w)))
                if n[2] < 0:
                    n = mul(n, -1)
                c = add(mid, mul(n, r + 0.035))
            else:
                raise KeyError(f"unknown touch surface '{t}'")
        else:
            off = o.get("offset_m", [0, 0, 0])
            c = add(self.point(o.get("at", [0, 0, 0])), (float(off[0]), float(off[1]), float(off[2])))
        if o.get("on_floor"):
            c = (c[0], c[1], self.ground(c) + r)
        out["center"] = c
        return out

    def _objects(self) -> None:
        self.objects = {}
        for o in self.asset.get("objects") or []:
            self.objects[o["name"]] = self._object(o)

    def _support(self) -> None:
        """Shift the skeleton onto the floor (listed contacts touch z = 0) or into the air."""
        b = self.body
        sup = self.asset.get("support") or {"contacts": ["r_foot", "l_foot"]}
        if "airborne_m" in sup:
            dz = float(sup["airborne_m"]) - min(p[2] for p in b.all_points())
        elif "pelvis_z_m" in sup:                  # pelvis height given; the feet are placed by reach targets
            z = self._pel_z if sup["pelvis_z_m"] == "auto" else float(sup["pelvis_z_m"])
            dz = z - b.points["pelvis"][2]
        else:
            cs: List[Vec] = []
            for c in sup.get("contacts", []):
                cs += b.foot_points(c[0]) if c.endswith("_foot") else [b.points[c]]
            dz = -min(self.above_ground(p) for p in (cs or b.all_points()))
        xy = sup.get("root_xy", [0.0, 0.0])
        pel = b.points["pelvis"]
        b.shift((float(xy[0]) - pel[0], float(xy[1]) - pel[1], dz))

    def _auto_pelvis(self, reach: Dict) -> None:
        """Pelvis height at which both feet reach their targets with the knees closest to the given angles."""
        import copy
        saved = copy.deepcopy(self.body.pose)
        best = (1e9, 0.9)
        for i in range(40):
            self._pel_z = 0.45 + 0.02 * i
            self.body.pose = copy.deepcopy(saved)
            self.body.build()
            self._support()
            self._objects()
            err = 0.0
            for limb in ("r_leg", "l_leg"):
                spec = reach.get(limb)
                if spec:
                    self._reach(limb, {**spec, "starts": 1})
                    err += (100 * self.reach_gap(limb, spec)) ** 2
                    err += ((self.body.pose[limb]["knee"] - saved[limb]["knee"]) / 10) ** 2
            best = min(best, (err, self._pel_z))
        self.body.pose = saved
        self._pel_z = best[1]

    def _place(self) -> None:
        pose = self.asset.get("pose") or {}
        look = (pose.get("head") or {}).get("look_at")
        reach = {limb: (pose.get(limb) or {}).get("reach") for limb in ("r_leg", "l_leg", "r_arm", "l_arm")}
        self._pel_z = 0.9
        if (self.asset.get("support") or {}).get("pelvis_z_m") == "auto":
            self._auto_pelvis(reach)
        for _ in range(4):                         # support, objects, reach and gaze depend on each other
            self.body.build()
            self._support()
            self._objects()
            for limb, spec in reach.items():
                if spec:
                    self._reach(limb, spec)
                    self._objects()
            if look:
                self.body._head(self.point(look))
                self._objects()
        self.body.build()
        self._support()
        self._objects()

    def _reach(self, limb: str, spec: Dict) -> None:
        """Adjust a limb's angles so its end (palm, or instep / sole / heel / toe for a leg) lands
        on an object's surface, or on a point (pattern search, regularised toward the given angles)."""
        b = self.body
        s, kind = limb[0], limb[2:]
        ref = spec["to"]
        floor = ref == "floor"                     # put the lowest point of this foot on the floor
        o = self.objects.get(ref)
        if floor:
            c, r = (0.0, 0.0, 0.0), 0.0
        elif o is not None and o.get("kind") != "point":
            c, r = o["center"], o.get("diameter_m", 0.0) / 2
        else:
            c, r = self.point(ref), 0.0
        if kind == "arm":
            eff, nrm, keys0, rng = s + "_palm", s + "_palm_normal", ("elev", "plane", "rot", "elbow", "pron", "wrist"), \
                ARM_SOLVE_RANGE
            rebuild = b._arm
        else:
            eff = s + "_" + spec.get("point", "instep")
            nrm = s + ("_foot_up" if spec.get("point", "instep") == "instep" else "_sole")
            keys0, rng, rebuild = ("flex", "abd", "rot", "knee", "ankle"), LEG_SOLVE_RANGE, b._leg
        part = b.pose[limb]
        rng = {**rng, **{k: tuple(v) for k, v in (spec.get("range") or {}).items()}}
        start = {k: min(max(float(part[k]), rng[k][0]), rng[k][1]) for k in keys0}
        keys = [k for k in keys0 if k not in spec.get("fix", [])
                and not (k == "ankle" and part.get("ankle_mode"))]
        face_w = spec.get("face_w", 30.0 if (r > 0 or spec.get("face")) else 0.0)
        side = spec.get("side")                    # where on the ball the end goes (from its centre)
        side = unit(tuple(float(v) for v in side)) if side else None  # type: ignore[arg-type]
        want = unit(tuple(float(v) for v in spec["face"])) if spec.get("face") else None  # type: ignore[arg-type]

        def normal() -> Vec:
            if nrm.endswith("_sole"):
                return mul(b.vecs[s + "_foot_up"], -1)
            return b.vecs[nrm]

        def cost(vals: Dict[str, float]) -> float:
            part.update(vals)
            rebuild(s)
            e = b.points[eff]
            face = 1.0
            if floor:
                d = min(self.above_ground(q) for q in b.foot_points(s))
            elif side:
                d = length(sub(e, add(c, mul(side, r))))
                face = dot(normal(), mul(side, -1))
            else:
                d = length(sub(e, c)) - r
                face = dot(normal(), unit(sub(c, e))) if r > 0 else 1.0
            if want:
                face = dot(normal(), want)
            reg = sum(((vals[k] - start[k]) / 60.0) ** 2 for k in vals)
            lim = sum(max(0.0, lo - vals[k], vals[k] - hi) ** 2 / 25.0
                      for k, (lo, hi) in rng.items() if k in vals)
            return (d * 100) ** 2 + face_w * (1 - face) + spec.get("w", 0.3) * reg + lim

        def search(cur: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
            best = cost(cur)
            step = 16.0
            while step > 0.2:
                improved = False
                for k in keys:
                    for sgn in (1, -1):
                        trial = dict(cur)
                        trial[k] = cur[k] + sgn * step
                        if not rng[k][0] <= trial[k] <= rng[k][1]:     # never leave the joint's range
                            continue
                        v = cost(trial)
                        if v < best - 1e-9:
                            cur, best, improved = trial, v, True
                if not improved:
                    step /= 2
            return best, cur

        # several deterministic starts: the given angles, then spread-out variations of them
        rnd = __import__("random").Random(7)
        starts = [dict(start)]
        for _ in range(int(spec.get("starts", 8))):
            starts.append({k: (min(max(v + rnd.uniform(-45, 45), rng[k][0]), rng[k][1]) if k in keys else v)
                           for k, v in start.items()})
        best, cur = min((search(s0) for s0 in starts), key=lambda t: t[0])
        part.update({k: round(v, 1) for k, v in cur.items()})
        rebuild(s)

    def reach_gap(self, limb: str, spec: Dict) -> float:
        """Distance (m) from the limb end to where the reach wanted it."""
        b = self.body
        s, kind = limb[0], limb[2:]
        if spec["to"] == "floor":
            return min(self.above_ground(q) for q in b.foot_points(s))
        o = self.objects.get(spec["to"])
        if o is not None and o.get("kind") != "point":
            c, r = o["center"], o.get("diameter_m", 0.0) / 2
        else:
            c, r = self.point(spec["to"]), 0.0
        e = b.points[s + "_palm"] if kind == "arm" else b.points[s + "_" + spec.get("point", "instep")]
        if spec.get("side"):
            return length(sub(e, add(c, mul(unit(tuple(spec["side"])), r))))  # type: ignore[arg-type]
        return length(sub(e, c)) - r


ARM_SOLVE_RANGE = {"elev": (0, 180), "plane": (-60, 135), "rot": (-80, 175), "elbow": (0, 150),
                   "pron": (-80, 90), "wrist": (-70, 70)}
LEG_SOLVE_RANGE = {"flex": (-30, 130), "abd": (-25, 70), "rot": (-40, 50), "knee": (0, 145), "ankle": (-30, 75)}


# ---------------------------------------------------------------- limits and checks
# (min, max) hard: anatomically impossible outside; soft: unusual, worth a second look.
# Soft limits follow normal adult active ROM (AAOS: shoulder flexion/abduction 180, extension 60,
# ER 90 / IR 70; elbow 150; wrist 80/70; hip flexion 120, extension 20-30, abduction 40-45;
# knee 135-150; ankle 20 dorsi / 50 plantar; neck 45-60 flex / 45-75 ext, rotation 60-80;
# trunk flexion 80, extension 25-40, rotation 45, side bend 35), widened for trained athletes.
# Hard limits add what athletes reach in these movements: throwers' arm external rotation at
# MER 160-185 (includes scapula and spine; Fleisig/Dillman JOSPT 1993), kickers' plantarflexion
# with the midfoot, split-level hip ranges. Numbers from search extracts: see SOURCES.md.
ROM = {
    "pelvis.tilt": ((-60, 95), (-40, 80)),
    "trunk.flex": ((-45, 95), (-35, 75)), "trunk.side": ((-45, 45), (-35, 35)),
    "trunk.rot": ((-65, 65), (-50, 50)),
    "head.flex": ((-80, 65), (-65, 56)), "head.side": ((-45, 45), (-35, 35)),
    "head.rot": ((-85, 85), (-75, 75)),
    "arm.elev": ((0, 185), (0, 180)), "arm.plane": ((-100, 145), (-95, 135)),
    "arm.rot": ((-90, 185), (-70, 120)), "arm.elbow": ((-10, 150), (-5, 145)),
    "arm.pron": ((-90, 95), (-85, 90)), "arm.wrist": ((-80, 85), (-70, 80)),
    "leg.flex": ((-35, 145), (-30, 125)), "leg.abd": ((-35, 85), (-25, 50)),
    "leg.rot": ((-50, 65), (-40, 50)), "leg.knee": ((-8, 155), (-3, 145)),
    "leg.ankle": ((-42, 80), (-35, 60)),
}


def check_rom(pose: Dict) -> List[Tuple[str, str]]:
    out = []
    for key, ((hlo, hhi), (slo, shi)) in ROM.items():
        part, j = key.split(".")
        names = [part] if part in ("pelvis", "trunk", "head") else [s + "_" + part for s in "rl"]
        for n in names:
            v = pose[n].get(j)
            if not isinstance(v, (int, float)):
                continue
            if v < hlo or v > hhi:
                out.append(("error", f"{n}.{j} = {v:.0f} is outside the anatomical range {hlo}..{hhi}"))
            elif v < slo or v > shi:
                out.append(("warn", f"{n}.{j} = {v:.0f} is beyond the usual range {slo}..{shi}"))
    for s in "rl":
        a = pose[s + "_arm"]
        if a["elev"] > 60 and a["plane"] < -55:
            out.append(("error", f"{s}_arm: raised {a['elev']:.0f} deg behind the shoulder line "
                                 f"(plane {a['plane']:.0f}); the shoulder cannot do that"))
        g = pose[s + "_leg"]
        if g["knee"] < 20 and g["flex"] > 115:
            out.append(("warn", f"{s}_leg: straight-knee hip flexion {g['flex']:.0f} needs split-level "
                                "hamstring flexibility"))
    return out


class Metrics:
    """Measured on the placed skeleton; names usable in an asset's rules."""

    def __init__(self, sc: Scene):
        self.sc = sc
        b = sc.body
        P = b.points
        m: Dict[str, float] = {}
        for s in "rl":
            m[s + "_elbow_flex"] = 180 - angle_between(sub(P[s + "_shoulder"], P[s + "_elbow"]),
                                                       sub(P[s + "_wrist"], P[s + "_elbow"]))
            m[s + "_knee_flex"] = 180 - angle_between(sub(P[s + "_hip"], P[s + "_knee"]),
                                                      sub(P[s + "_ankle"], P[s + "_knee"]))
            m[s + "_shoulder_elev"] = angle_between(b.vecs[s + "_upper_arm"], mul(b.frames["thorax"].z, -1))
            m[s + "_hip_flex"] = sc.body.pose[s + "_leg"]["flex"]
            m[s + "_foot_pitch"] = math.degrees(math.asin(max(-1, min(1, -b.vecs[s + "_foot"][2]))))
            m[s + "_wrist_z"] = P[s + "_wrist"][2]
            m[s + "_forearm_tilt"] = angle_between(b.vecs[s + "_forearm"], Z)     # 0 = forearm pointing straight up
            m[s + "_hand_z"] = P[s + "_fingertip"][2]
            m[s + "_foot_z"] = min(sc.above_ground(p) for p in b.foot_points(s))
            fwd0 = self.facing()
            for seg in ("thigh", "shank"):             # segment angle from vertical, + = distal end forward
                v = b.vecs[s + "_" + seg]
                m[f"{s}_{seg}_fwd"] = math.degrees(math.atan2(dot(v, fwd0), -v[2]))
            for k in ("elev", "plane", "rot", "elbow", "pron", "wrist"):
                m[f"{s}_arm.{k}"] = sc.body.pose[s + "_arm"][k]
            for k in ("flex", "abd", "rot", "knee", "ankle"):
                m[f"{s}_leg.{k}"] = sc.body.pose[s + "_leg"][k]
        for part in ("pelvis", "trunk", "head"):
            for k, v in sc.body.pose[part].items():
                if isinstance(v, (int, float)):
                    m[f"{part}.{k}"] = v
        trunk = sub(P["neck"], P["pelvis"])
        fwd = self.facing()
        left = cross(Z, fwd)
        m["trunk_lean_fwd"] = math.degrees(math.atan2(dot(trunk, fwd), trunk[2]))
        m["trunk_lean_right"] = math.degrees(math.atan2(-dot(trunk, left), trunk[2]))
        m["trunk_from_vertical"] = angle_between(trunk, Z)
        hips = sub(P["l_hip"], P["r_hip"])
        shs = sub(P["l_shoulder"], P["r_shoulder"])
        m["hip_shoulder_sep"] = self._yaw(shs) - self._yaw(hips)
        m["pelvis_yaw_world"] = self._yaw(hips) - 90
        m["shoulder_yaw_world"] = self._yaw(shs) - 90
        ra, la = P["r_ankle"], P["l_ankle"]
        m["ankle_gap_m"] = math.hypot(ra[0] - la[0], ra[1] - la[1])
        m["stride_pct_height"] = 100 * m["ankle_gap_m"] / sc.height
        m["stance_over_shoulders"] = m["ankle_gap_m"] / length(shs)
        m["lowest_z"] = min(sc.above_ground(p) for p in b.all_points())
        m["pelvis_z"] = P["pelvis"][2]
        m["head_z"] = P["crown"][2]
        self.m = m

    @staticmethod
    def _yaw(v: Vec) -> float:
        a = math.degrees(math.atan2(v[1], v[0]))
        return a

    def facing(self) -> Vec:
        """Horizontal direction the pelvis faces."""
        yaw = math.radians(self.sc.body.pose["pelvis"]["yaw"])
        return (math.cos(yaw), math.sin(yaw), 0.0)

    def chest_facing(self) -> Vec:
        """Horizontal direction the chest faces (for arms and head)."""
        t = self.sc.body.frames["thorax"]
        v = (t.x[0], t.x[1], 0.0)
        if length(v) < 0.3:                        # chest facing the floor or the sky: use the head-to-hips line
            v = (-t.z[0], -t.z[1], 0.0) if t.x[2] < 0 else (t.z[0], t.z[1], 0.0)
        return unit(v) if length(v) > 1e-6 else self.facing()

    def get(self, name: str) -> float:
        if name in self.m:
            return self.m[name]
        parts = name.split(":")
        if len(parts) == 3 and parts[0] in ("dist", "gap", "fwd", "left", "up"):
            a, b = self.sc.point(parts[1]), self.sc.point(parts[2])
            d = sub(a, b)
            if parts[0] == "dist":
                return 100 * length(d)
            if parts[0] == "gap":                  # surface gap: minus the object radii
                ra = self.sc.objects.get(parts[1], {}).get("diameter_m", 0) / 2
                rb = self.sc.objects.get(parts[2], {}).get("diameter_m", 0) / 2
                return 100 * (length(d) - ra - rb)
            axis = {"fwd": X, "left": Y, "up": Z}[parts[0]]
            return 100 * dot(d, axis)
        if len(parts) == 2 and parts[0] == "z":
            return self.sc.point(parts[1])[2]
        raise KeyError(f"unknown metric '{name}'")


def fill(text: str, met: "Metrics") -> str:
    """Replace {metric} in authored text with its value measured on the skeleton."""
    def rep(mo):
        name = mo.group(1)
        try:
            v = met.get(name)
        except KeyError:
            return mo.group(0)
        return f"{v:.2f}" if name.startswith("z:") or name.endswith("_m") or name.endswith("_z") else f"{v:.0f}"
    return re.sub(r"\{([a-z][a-z0-9_.]*(?::[a-z0-9_]+)*)\}", rep, text)


def validate(sc: Scene) -> List[Tuple[str, str]]:
    issues = check_rom(sc.body.pose)
    b = sc.body
    met = Metrics(sc)
    sup = sc.asset.get("support") or {"contacts": ["r_foot", "l_foot"]}
    tol = 0.03
    for k, p in b.points.items():
        if sc.above_ground(p) < -tol:
            issues.append(("error", f"{k} is {-sc.above_ground(p) * 100:.0f} cm below the floor"))
    for s, hand in b.hands.items():
        if min(sc.above_ground(p) for p in hand) < -tol:
            issues.append(("error", f"{s} hand goes below the floor"))
    if "airborne_m" not in sup:
        for c in sup.get("contacts", []):
            z = (min(sc.above_ground(p) for p in b.foot_points(c[0])) if c.endswith("_foot")
                 else sc.above_ground(b.points[c]))
            if z > tol:
                issues.append(("error", f"{c} should touch the floor but floats {z * 100:.0f} cm above it"))
        # a foot not listed as a contact but touching the floor is fine; a listed foot must touch.
    for o in sc.objects.values():
        if o.get("kind") in ("ball",) and sc.above_ground(o["center"]) - o.get("diameter_m", 0) / 2 < -tol:
            issues.append(("error", f"{o['name']} is under the floor"))
    for limb in ("r_arm", "l_arm", "r_leg", "l_leg"):
        spec = (sc.asset.get("pose") or {}).get(limb, {}).get("reach")
        if spec:
            gap = sc.reach_gap(limb, spec)
            if abs(gap) > spec.get("tol_m", 0.03):
                issues.append(("error", f"{limb} ends {gap * 100:.0f} cm from {spec['to']} "
                                        "(cannot reach it: move the object or change the start angles)"))
    for r in sc.asset.get("rules") or []:
        try:
            v = met.get(r["m"])
        except KeyError as e:
            issues.append(("error", f"rule {r['m']}: {e}"))
            continue
        lo, hi = r.get("min", -1e9), r.get("max", 1e9)
        if not lo <= v <= hi:
            issues.append(("error", f"rule {r['m']} = {v:.1f} not in {lo}..{hi} ({r.get('why', '')})"))
    return issues


# ---------------------------------------------------------------- cameras and OpenPose
BODY18 = ["nose", "neck", "r_shoulder", "r_elbow", "r_wrist", "l_shoulder", "l_elbow", "l_wrist",
          "r_hip", "r_knee", "r_ankle", "l_hip", "l_knee", "l_ankle", "r_eye", "l_eye", "r_ear", "l_ear"]
# ControlNet 1.1 annotator (controlnet_aux util.draw_bodypose), 1-based pairs
LIMBS = [(2, 3), (2, 6), (3, 4), (4, 5), (6, 7), (7, 8), (2, 9), (9, 10), (10, 11), (2, 12), (12, 13),
         (13, 14), (2, 1), (1, 15), (15, 17), (1, 16), (16, 18)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0),
          (0, 255, 0), (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
          (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]
HAND_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (0, 9), (9, 10), (10, 11),
              (11, 12), (0, 13), (13, 14), (14, 15), (15, 16), (0, 17), (17, 18), (18, 19), (19, 20)]


class Camera:
    """Pinhole camera placed around the athlete. azimuth: 0 = on the target side looking back
    at the athlete (the view from the net / goal / catcher), 90 = athlete's left (+y), 180 = behind.
    elevation: + above looking down, - below looking up. lens_mm: 35 mm-equivalent focal length."""

    def __init__(self, spec: Dict, sc: Scene):
        self.spec = spec
        self.name = spec.get("name", "cam")
        self.W, self.H = spec.get("size", [1024, 1024])
        self.lens = float(spec.get("lens_mm", 50))
        self.fpx = self.lens / 36.0 * max(self.W, self.H)
        pts = self._frame_points(sc)
        tgt = spec.get("target")
        self.target = sc.point(tgt) if tgt else mul(add(
            (min(p[0] for p in pts), min(p[1] for p in pts), min(p[2] for p in pts)),
            (max(p[0] for p in pts), max(p[1] for p in pts), max(p[2] for p in pts))), 0.5)
        az, el = math.radians(spec.get("azimuth", 0)), math.radians(spec.get("elevation", 0))
        self.dir = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
        fill = float(spec.get("fill", 0.8))
        lo, hi = 0.3, 400.0
        for _ in range(60):                        # distance at which the figure fills `fill` of the frame
            mid = (lo + hi) / 2
            self._place(mid, spec)
            xs, ys = zip(*[self.project(p)[:2] for p in pts])
            big = max((max(ys) - min(ys)) / self.H, (max(xs) - min(xs)) / self.W)
            if big > fill:
                lo = mid
            else:
                hi = mid
        self._place(hi, spec)
        xs, ys = zip(*[self.project(p)[:2] for p in pts])
        cx, cy = spec.get("center", [0.5, 0.5])
        self.shift = (cx * self.W - (max(xs) + min(xs)) / 2, cy * self.H - (max(ys) + min(ys)) / 2)
        self.distance = hi

    def _frame_points(self, sc: Scene) -> List[Vec]:
        pts = list(sc.body.all_points())
        for o in sc.objects.values():
            if not o.get("in_frame", True):
                continue
            if o.get("kind") == "bat":
                pts += [o["knob"], o["tip"]]
            elif o.get("kind") == "ball":
                r = o.get("diameter_m", 0) / 2
                c = o["center"]
                pts += [add(c, mul(a, k * r)) for a in (X, Y, Z) for k in (1, -1)]
        return pts

    def _place(self, dist: float, spec: Dict) -> None:
        self.shift = (0.0, 0.0)
        if "height_m" in spec:                     # camera at a fixed height, aimed at the target
            horiz = unit((self.dir[0], self.dir[1], 0.0))
            pos = add(self.target, mul(horiz, dist))
            pos = (pos[0], pos[1], float(spec["height_m"]))
        else:
            pos = add(self.target, mul(self.dir, dist))
        self.pos = pos
        f = unit(sub(self.target, pos))
        r = unit(cross(f, Z)) if length(cross(f, Z)) > 1e-6 else Y
        u = cross(r, f)
        roll = math.radians(spec.get("roll", 0))
        self.f, self.r, self.u = f, comb((math.cos(roll), r), (math.sin(roll), u)), \
            comb((math.cos(roll), u), (-math.sin(roll), r))

    def project(self, p: Vec) -> Tuple[float, float, float]:
        d = sub(p, self.pos)
        z = dot(d, self.f)
        if z < 1e-3:
            return (float("nan"), float("nan"), z)
        return (self.W / 2 + self.fpx * dot(d, self.r) / z + self.shift[0],
                self.H / 2 - self.fpx * dot(d, self.u) / z + self.shift[1], z)

    def facing(self, p: Vec, normal: Vec) -> float:
        """cosine between a surface normal and the direction to the camera"""
        return dot(unit(normal), unit(sub(self.pos, p)))


def keypoints(sc: Scene, cam: Camera) -> Dict:
    b = sc.body
    P = b.points
    kp = []
    head_c = P["head"]
    vis_face = cam.facing(head_c, b.vecs["head_fwd"])
    for name in BODY18:
        x, y, _ = cam.project(P[name])
        c = 1.0
        if name == "nose" and vis_face < -0.25:
            c = 0.0
        elif name.endswith("_eye") and vis_face < -0.05:
            c = 0.0
        elif name.endswith("_ear"):
            out = sub(P[name], head_c)
            if cam.facing(P[name], out) < -0.35:
                c = 0.0
        if not (0 <= x < cam.W and 0 <= y < cam.H) or x != x:
            c = 0.0
        kp.append((x, y, c))
    hands = {}
    for s, pts in b.hands.items():
        hands[s] = [(*cam.project(p)[:2], 1.0) for p in pts]
    return {"body": kp, "hands": hands}


def openpose_json(kp: Dict, cam: Camera) -> Dict:
    def flat(ps):
        return [round(v, 2) if c else 0 for x, y, c in ps for v in (x, y, c)]
    return {"canvas_width": cam.W, "canvas_height": cam.H,
            "people": [{"pose_keypoints_2d": flat(kp["body"]),
                        "hand_left_keypoints_2d": flat(kp["hands"]["l"]),
                        "hand_right_keypoints_2d": flat(kp["hands"]["r"]),
                        "face_keypoints_2d": []}]}


def _ellipse_poly(p, q, half_w: float, n: int = 36) -> List[Tuple[float, float]]:
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    a = math.hypot(q[0] - p[0], q[1] - p[1]) / 2
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    ca, sa = math.cos(ang), math.sin(ang)
    return [(mx + a * math.cos(t) * ca - half_w * math.sin(t) * sa,
             my + a * math.cos(t) * sa + half_w * math.sin(t) * ca)
            for t in (2 * math.pi * i / n for i in range(n))]


def draw_openpose(kp: Dict, W: int, H: int, hands: bool = True):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    scale = max(1.0, min(W, H) / 512)
    stick = 4 * scale
    body = kp["body"]
    for i, (a, b_) in enumerate(LIMBS):
        p, q = body[a - 1], body[b_ - 1]
        if p[2] and q[2]:
            d.polygon(_ellipse_poly(p, q, stick), fill=tuple(int(c * 0.6) for c in COLORS[i]))
    rad = 4 * scale
    for i, (x, y, c) in enumerate(body):
        if c:
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=COLORS[i])
    if hands:
        hw = max(2, int(round(2 * scale)))
        hr = max(2.0, 2 * scale)
        for pts in kp["hands"].values():
            for ie, (a, b_) in enumerate(HAND_EDGES):
                r, g, bl = colorsys.hsv_to_rgb(ie / len(HAND_EDGES), 1.0, 1.0)
                p, q = pts[a], pts[b_]
                if p[0] == p[0] and q[0] == q[0]:
                    d.line([p[:2], q[:2]], fill=(int(r * 255), int(g * 255), int(bl * 255)), width=hw)
            for x, y, c in pts:
                if x == x:
                    d.ellipse([x - hr, y - hr, x + hr, y + hr], fill=(0, 0, 255))
    return img


# ---------------------------------------------------------------- preview sheet
def draw_preview(sc: Scene, title: str, issues: List[Tuple[str, str]], cam_imgs: Sequence = ()):
    from PIL import Image, ImageDraw
    panel = 360
    views = [("seen from the target side", lambda p: (p[1], p[2])),
             ("seen from the right, target ->", lambda p: (p[0], p[2])),
             ("seen from above, target ^", lambda p: (-p[1], p[0]))]
    extra = len(cam_imgs)
    W = panel * (3 + extra)
    img = Image.new("RGB", (W, panel + 60), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.text((8, 6), title, fill=(20, 20, 20))
    bad = [m for lv, m in issues if lv == "error"]
    d.text((8, 22), ("ERRORS: " + "; ".join(bad))[:220] if bad else "checks: OK   (red = right side, blue = left side)",
           fill=(200, 0, 0) if bad else (0, 120, 0))
    b = sc.body
    P = b.points
    allp = b.all_points() + [o["center"] for o in sc.objects.values()]
    for i, (name, f) in enumerate(views):
        ox, oy = i * panel, 50
        xy = [f(p) for p in allp]
        cx = (max(x for x, _ in xy) + min(x for x, _ in xy)) / 2
        cy = (max(y for _, y in xy) + min(y for _, y in xy)) / 2
        span = max(max(x for x, _ in xy) - min(x for x, _ in xy), max(y for _, y in xy) - min(y for _, y in xy), 1.0)
        k = (panel - 40) / span

        def T(p):
            x, y = f(p)
            return (ox + panel / 2 + (x - cx) * k, oy + (panel - 10) / 2 - (y - cy) * k)
        d.rectangle([ox + 2, oy, ox + panel - 2, oy + panel - 4], outline=(200, 200, 200))
        d.text((ox + 6, oy + 4), name, fill=(90, 90, 90))
        if i == 0:
            g0 = T((0, 0, sc.ground(P["pelvis"])))
            d.line([(ox + 2, g0[1]), (ox + panel - 2, g0[1])], fill=(150, 110, 60), width=2)
        elif i == 1:
            xs = [P["pelvis"][0] + (j - 50) * 0.1 for j in range(101)]
            pts = [T((x, 0, sc.ground((x, 0, 0)))) for x in xs]
            pts = [(min(max(x, ox + 2), ox + panel - 2), y) for x, y in pts]
            d.line(pts, fill=(150, 110, 60), width=2)
        for e in sc.env:
            if e.get("kind") == "net" and i == 1:
                x0 = e.get("x_m", 1.0)
                top = T((x0, 0, e.get("height_m", 2.43)))
                bot = T((x0, 0, e.get("height_m", 2.43) - 1.0))
                d.line([bot, top], fill=(60, 60, 60), width=3)
            if e.get("kind") == "rim" and i == 1:
                c = T((e.get("x_m", 1.0), 0, e.get("height_m", 3.05)))
                d.line([(c[0] - 0.23 * k, c[1]), (c[0] + 0.23 * k, c[1])], fill=(230, 90, 0), width=3)
        segs = [("neck", "pelvis", (60, 60, 60)), ("neck", "head", (60, 60, 60)), ("r_hip", "l_hip", (60, 60, 60)),
                ("r_shoulder", "l_shoulder", (60, 60, 60))]
        for s, col in (("r", (220, 40, 40)), ("l", (40, 80, 220))):
            segs += [(s + "_shoulder", s + "_elbow", col), (s + "_elbow", s + "_wrist", col),
                     (s + "_wrist", s + "_fingertip", col), (s + "_hip", s + "_knee", col),
                     (s + "_knee", s + "_ankle", col), (s + "_heel", s + "_toe", col), (s + "_ankle", s + "_heel", col)]
        for a_, b_, col in segs:
            d.line([T(P[a_]), T(P[b_])], fill=col, width=3)
        hc = T(P["head"])
        hr = 0.07 * sc.height * k
        d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], outline=(60, 60, 60), width=2)
        d.line([T(P["head"]), T(P["nose"])], fill=(0, 150, 0), width=2)
        for o in sc.objects.values():
            c = T(o["center"])
            if o.get("kind") == "ball":
                r = o.get("diameter_m", 0.2) / 2 * k
                d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(230, 140, 0), width=3)
            elif o.get("kind") == "bat":
                d.line([T(o["center"]), T(o["tip"])], fill=(140, 90, 30), width=5)
    for j, im in enumerate(cam_imgs):
        t = im.copy()
        t.thumbnail((panel - 8, panel - 8))
        img.paste(t, (panel * (3 + j) + 4, 52))
    return img


# ---------------------------------------------------------------- text
def nice(ref: str) -> str:
    return re.sub(r"^r_", "right ", re.sub(r"^l_", "left ", ref)).replace("_", " ")


def flex_word(v: float, straight: str = "straight") -> str:
    if v < 8:
        return straight
    if v < 30:
        return "slightly bent"
    if v < 65:
        return "bent"
    if v < 110:
        return "bent to about a right angle" if 75 <= v <= 105 else "deeply bent"
    return "fully folded"


def dir_words(v: Vec, fwd: Vec, subject: str = "") -> str:
    """Direction of v in the athlete's facing frame, e.g. 'up and slightly forward'."""
    left = cross(Z, fwd)
    comps = [(dot(v, fwd), "forward", "backward"), (dot(v, left), "to the athlete's left", "to the athlete's right"),
             (v[2], "up", "down")]
    parts = []
    for c, pos, neg in sorted(comps, key=lambda t: -abs(t[0])):
        a = abs(c)
        if a < 0.25:
            continue
        w = pos if c > 0 else neg
        parts.append(w if a > 0.55 or not parts else "slightly " + w)
    return " and ".join(parts) if parts else "level"


def cm(v: float) -> str:
    return f"{abs(v) * 100:.0f} cm"


def prompt_text(sc: Scene, issues) -> Dict[str, str]:
    a = sc.asset
    b = sc.body
    P = b.points
    met = Metrics(sc)
    m = met.m
    legs_fwd = met.facing()
    chest = met.chest_facing()
    t = a.get("text") or {}
    roles = (a.get("athlete") or {}).get("roles") or {}
    F = lambda x: fill(x, met)  # noqa: E731
    lines: List[str] = [f"1. SYSTEM_INDEX_CODE: #{a['code']}", "", "2. ANATOMICAL_BONES:"]
    hp = b.pose["head"]
    head = (f"- Gaze & head: head {'tilted back' if hp['flex'] < -5 else 'tilted down' if hp['flex'] > 5 else 'level'}"
            + (f" {abs(hp['flex']):.0f} deg" if abs(hp['flex']) > 5 else "")
            + (f", turned {abs(hp['rot']):.0f} deg to the athlete's {'left' if hp['rot'] > 0 else 'right'} of the chest line"
               if abs(hp['rot']) > 5 else "")
            + f"; face pointing {dir_words(b.vecs['head_fwd'], chest)}.")
    if t.get("gaze"):
        head += " " + F(t["gaze"])
    lines.append(head)
    tr = b.pose["trunk"]
    torso = (f"- Torso: trunk line (hips to shoulders) {abs(m['trunk_lean_fwd']):.0f} deg "
             f"{'forward' if m['trunk_lean_fwd'] >= 0 else 'backward'} of vertical"
             + (f", leaning {abs(m['trunk_lean_right']):.0f} deg to the athlete's "
                f"{'right' if m['trunk_lean_right'] > 0 else 'left'}" if abs(m['trunk_lean_right']) >= 5 else "")
             + (f"; spine {'flexed' if tr['flex'] > 0 else 'arched back (extended)'} {abs(tr['flex']):.0f} deg over the pelvis"
                if abs(tr['flex']) >= 5 else "")
             + (f"; shoulder line rotated {abs(m['hip_shoulder_sep']):.0f} deg to the "
                f"{'left' if m['hip_shoulder_sep'] > 0 else 'right'} of the hip line (hip-shoulder separation)"
                if abs(m['hip_shoulder_sep']) >= 8 else "; shoulders square with the hips")
             + ".")
    if t.get("torso"):
        torso += " " + F(t["torso"])
    lines.append(torso)
    for s, nm in (("r", "Right"), ("l", "Left")):
        ar = b.pose[s + "_arm"]
        role = f" ({roles[s + '_arm']})" if roles.get(s + "_arm") else ""
        wrist = ("flexed" if ar["wrist"] > 5 else "extended (cocked back)" if ar["wrist"] < -5 else "neutral")
        txt = (f"- {nm} arm{role}: upper arm raised {m[s + '_shoulder_elev']:.0f} deg from the side of the trunk, "
               f"pointing {dir_words(b.vecs[s + '_upper_arm'], chest)}; elbow {flex_word(m[s + '_elbow_flex'])} "
               f"({m[s + '_elbow_flex']:.0f} deg flexion); forearm pointing {dir_words(b.vecs[s + '_forearm'], chest)}; "
               f"palm facing {dir_words(b.vecs[s + '_palm_normal'], chest)}; wrist {wrist}"
               + (f" {abs(ar['wrist']):.0f} deg" if abs(ar["wrist"]) > 5 else "")
               + f"; hand: {HAND_WORDS.get(ar.get('hand', 'relaxed'), ar.get('hand', 'relaxed'))}"
               + (f"; upper arm externally rotated {ar['rot']:.0f} deg (forearm laid back)"
                  if ar["rot"] >= 60 and m[s + "_elbow_flex"] >= 40 else "")
               + f"; fingertips {P[s + '_fingertip'][2]:.2f} m above the floor.")
        if t.get(s + "_arm"):
            txt += " " + F(t[s + "_arm"])
        lines.append(txt)
    sup = a.get("support") or {}
    for s, nm in (("r", "Right"), ("l", "Left")):
        g = b.pose[s + "_leg"]
        role = f" ({roles[s + '_leg']})" if roles.get(s + "_leg") else ""
        fz = m[s + "_foot_z"]
        pitch = m[s + "_foot_pitch"]
        state = ("foot flat on the floor" if fz < 0.03 and abs(pitch) < 12 else
                 "on the ball of the foot, heel raised" if fz < 0.03 and pitch > 0 else
                 "heel down, toes raised" if fz < 0.03 else
                 f"foot {fz * 100:.0f} cm above the floor")
        txt = (f"- {nm} leg{role}: hip {'flexed' if g['flex'] >= 0 else 'extended'} {abs(g['flex']):.0f} deg"
               + (f", abducted {g['abd']:.0f} deg" if g["abd"] >= 12 else "")
               + f"; knee {flex_word(m[s + '_knee_flex'])} ({m[s + '_knee_flex']:.0f} deg flexion); "
               f"thigh pointing {dir_words(b.vecs[s + '_thigh'], legs_fwd)}, shin pointing "
               f"{dir_words(b.vecs[s + '_shank'], legs_fwd)}; ankle "
               + ("plantar-flexed (toes pointed)" if g["ankle"] > 8 else "dorsiflexed" if g["ankle"] < -8 else "neutral")
               + (f" {abs(g['ankle']):.0f} deg" if abs(g["ankle"]) > 8 else "") + f"; {state}.")
        if t.get(s + "_leg"):
            txt += " " + F(t[s + "_leg"])
        lines.append(txt)
    if "airborne_m" in sup:
        lines.append(f"- Airborne: lowest point of the body {sup['airborne_m'] * 100:.0f} cm above the floor; "
                     "neither foot touches the ground.")
    else:
        lines.append(f"- Base: ankles {m['ankle_gap_m'] * 100:.0f} cm apart ({m['stride_pct_height']:.0f}% of body height, "
                     f"{m['stance_over_shoulders']:.1f}x shoulder width); every support foot touches the floor, none floats.")
    for c in t.get("cues") or []:
        lines.append(f"- Technique cue: {F(c)}")
    lines += ["", "3. OBJECT_INTERACTION:"]
    for o in sc.objects.values():
        if o.get("kind") == "point":               # invisible marks used to place hands and feet
            continue
        if o.get("kind") == "bat":
            d = o["dir"]
            lines.append(f"- {o['name']} ({o.get('length_m', 0.84) * 100:.0f} cm): gripped at the handle, barrel pointing "
                         f"{dir_words(d, chest)}; sweet spot {o['sweet'][2]:.2f} m above the floor.")
            continue
        c = o["center"]
        txt = f"- {o['name']} ({o.get('diameter_m', 0) * 100:.0f} cm diameter): center {c[2]:.2f} m above the floor"
        for ref in o.get("relate", []):
            d = sub(c, sc.point(ref))
            gap = length(d) * 100 - o.get("diameter_m", 0) * 50
            txt += (f"; touching the {nice(ref)}" if gap < 3 else
                    f"; surface {gap:.0f} cm from the {nice(ref)} ({dir_words(unit(d), chest)} of it)")
        lines.append(txt + ".")
    for e in sc.env:
        if e.get("text"):
            lines.append(f"- {F(e['text'])}")
    for x in t.get("objects") or []:
        lines.append(f"- {F(x)}")
    lines += ["", "4. CINEMATIC_CAMERA:"]
    for c in a.get("cameras") or []:
        lines.append(f"- {c.get('name')}: {camera_words(c)}" + (f" {c['text']}" if c.get("text") else ""))
    lines += ["", "5. KINETIC_ENERGY:"]
    for x in t.get("kinetic") or []:
        lines.append(f"- {F(x)}")
    block = "\n".join(lines)

    # one-paragraph generation prompt: {SUBJECT} and {SETTING} are filled by the prompt agent
    cam0 = (a.get("cameras") or [{}])[0]
    def sentence(x: str) -> str:
        x = x.strip()
        return x if not x or x[-1] in ".!?" else x + "."
    gen = " ".join(["{SUBJECT},", sentence(F(t.get("action", a.get("summary", "")))), sentence(F(t.get("core", ""))),
                    " ".join(sentence(F(c)[:1].upper() + F(c)[1:]) for c in t.get("cues") or []),
                    sentence(camera_words(cam0)[:1].upper() + camera_words(cam0)[1:]), sentence(cam0.get("text") or ""),
                    sentence("; ".join(F(k) for k in (t.get("kinetic") or [])[:2])[:1].upper()
                             + "; ".join(F(k) for k in (t.get("kinetic") or [])[:2])[1:]), "{SETTING}."])
    gen = re.sub(r"\s+", " ", gen).strip()
    avoid = list(DEFAULT_AVOID) + list(t.get("avoid") or [])
    return {"block": block, "prompt": gen, "negative": ", ".join(dict.fromkeys(avoid))}


HAND_WORDS = {
    "flat": "open, fingers together and straight", "relaxed": "relaxed, fingers softly curled",
    "spread": "open with fingers spread", "cupped": "cupped, fingers slightly curled and spread",
    "ball_hold": "fingers spread around the ball, palm not touching it fully",
    "grip": "fingers wrapped firmly around what it holds", "fist": "closed fist",
    "platform": "clasped with the other hand, thumbs parallel",
}
DEFAULT_AVOID = ["extra fingers", "missing fingers", "fused fingers", "extra limbs", "missing limbs",
                 "extra arms", "extra legs", "backward-bending elbow", "backward-bending knee", "twisted torso",
                 "floating feet", "feet sinking into the floor", "distorted hands", "deformed anatomy",
                 "duplicated athlete"]


def camera_words(c: Dict) -> str:
    el = c.get("elevation", 0)
    if "height_m" in c:
        ang = f"camera {c['height_m']:.1f} m above the floor"
        ang += ", ground-level low angle looking up" if c["height_m"] < 0.6 else ""
    elif el <= -25:
        ang = "extreme low-angle shot looking up"
    elif el <= -8:
        ang = "low-angle shot looking up"
    elif el < 8:
        ang = "eye-level shot"
    elif el < 25:
        ang = "high-angle shot looking down"
    else:
        ang = "overhead high-angle shot"
    az = ((c.get("azimuth", 0) + 180) % 360) - 180
    side = ("from the front (target side)" if abs(az) <= 20 else
            "three-quarter front view" if abs(az) < 70 else
            "side profile view" if abs(az) <= 110 else
            "three-quarter rear view" if abs(az) < 160 else "from behind")
    lens = c.get("lens_mm", 50)
    lw = "wide-angle" if lens < 30 else "standard" if lens < 60 else "short telephoto" if lens < 110 else "telephoto"
    fill = c.get("fill", 0.8)
    frame = "full-body shot" if fill <= 0.92 else "tight full-body shot"
    roll = f", dutch angle {abs(c['roll']):.0f} deg" if abs(c.get("roll", 0)) >= 3 else ""
    return f"{ang}, {side}, {lens:.0f}mm {lw} lens, {frame}{roll}."


# ---------------------------------------------------------------- assets and library
def asset_files() -> List[Path]:
    return sorted(ASSETS.rglob("*.json"))


def load_asset(code_or_path: str) -> Dict:
    p = Path(code_or_path)
    if not p.is_file():
        hits = [f for f in asset_files() if f.stem.upper() == code_or_path.upper().lstrip("#")]
        if not hits:
            raise SystemExit(f"no asset {code_or_path}")
        p = hits[0]
    a = json.loads(p.read_text(encoding="utf-8"))
    a.setdefault("code", p.stem)
    a["_path"] = str(p)
    return a


def build_one(a: Dict, out_root: Path = LIBRARY, write: bool = True) -> Tuple[List, Optional[Path]]:
    sc = Scene(a)
    issues = validate(sc)
    if not write:
        return issues, None
    out = out_root / a.get("sport", "misc") / a["code"]
    out.mkdir(parents=True, exist_ok=True)
    txt = prompt_text(sc, issues)
    cams = []
    for spec in a.get("cameras") or [{"name": "front", "azimuth": 0}]:
        cam = Camera(spec, sc)
        kp = keypoints(sc, cam)
        img = draw_openpose(kp, cam.W, cam.H)
        img.save(out / f"openpose_{cam.name}.png", optimize=True)
        (out / f"openpose_{cam.name}.json").write_text(json.dumps(openpose_json(kp, cam)), encoding="utf-8")
        cams.append((cam, img))
    draw_preview(sc, f"#{a['code']}  {a.get('summary', '')}", issues, [im for _, im in cams]).save(
        out / "preview.png", optimize=True)
    skel = {"code": a["code"], "height_m": sc.height, "units": "m", "frame": "x toward target, y left, z up",
            "joints": {k: [round(c, 4) for c in v] for k, v in sc.body.points.items()},
            "hands": {s: [[round(c, 4) for c in p] for p in pts] for s, pts in sc.body.hands.items()},
            "objects": {k: {"center": [round(c, 4) for c in o["center"]], "diameter_m": o.get("diameter_m")}
                        for k, o in sc.objects.items()},
            "solved_pose": sc.body.pose,
            "metrics": {k: round(v, 2) for k, v in Metrics(sc).m.items()}}
    (out / "skeleton3d.json").write_text(json.dumps(skel, indent=1), encoding="utf-8")
    md = [f"# {a['code']}", "", a.get("summary", ""), ""]
    names = a.get("names") or {}
    if names:
        md += [f"- 이름(ko): {', '.join(names.get('ko', []))}", f"- names (en): {', '.join(names.get('en', []))}", ""]
    md += ["## Asset (5 sections)", "", "```", txt["block"], "```", "",
           "## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)", "", "```", txt["prompt"],
           "```", "", "## Negative prompt", "", "```", txt["negative"], "```", "",
           "## Control images", ""]
    for cam, _ in cams:
        md.append(f"- `openpose_{cam.name}.png` / `.json`: {cam.W}x{cam.H}, {camera_words(cam.spec)}")
    md += ["", "## Checks", ""]
    md += [f"- {lv}: {msg}" for lv, msg in issues] or ["- all checks passed (range of motion, floor contact, "
                                                        "hand-ball contact, sport rules)"]
    md += ["", "## Sport rules (measured on this skeleton)", "", "| metric | value | allowed | why | source |",
           "|---|---|---|---|---|"]
    met = Metrics(sc)
    for r in a.get("rules") or []:
        try:
            v = f"{met.get(r['m']):.1f}"
        except KeyError:
            v = "?"
        md.append(f"| {r['m']} | {v} | {r.get('min', '')}..{r.get('max', '')} | {r.get('why', '')} | {r.get('src', '')} |")
    srcs = a.get("sources") or []
    if srcs:
        md += ["", "## Sources", ""] + [f"- [{s['id']}] {s['cite']} {s.get('url', '')}" for s in srcs]
    refs = a.get("references") or []
    if refs:
        md += ["", "## Reference photos (not stored here; `fetch_refs.py` downloads them with their licence)", ""]
        md += [f"- {r['url']} ({r.get('license', '?')}, {r.get('author', '?')})" for r in refs]
    (out / "prompt.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return issues, out


def write_index(assets: List[Dict], out_root: Path = LIBRARY) -> Path:
    rows = []
    for a in assets:
        base = f"{a.get('sport', 'misc')}/{a['code']}"
        rows.append({"code": a["code"], "sport": a.get("sport"), "technique": a.get("technique"),
                     "phase": a.get("phase"), "summary": a.get("summary", ""),
                     "names": a.get("names", {}), "keywords": a.get("keywords", []),
                     "sequence": a.get("sequence"),
                     "prompt_md": f"{base}/prompt.md",
                     "openpose": [f"{base}/openpose_{c.get('name', 'cam')}.png" for c in a.get("cameras") or []],
                     "cameras": [c.get("name") for c in a.get("cameras") or []]})
    p = out_root / "index.json"
    p.write_text(json.dumps({"assets": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def write_catalog(assets: List[Dict], out_root: Path = LIBRARY) -> Path:
    lines = ["# Sports pose asset catalog", "",
             "Generated by `python sportspose.py build`. Each row links the asset text a prompt agent follows and "
             "the preview; OpenPose control images sit in the same folder.", "",
             "| code | sport | 이름 | summary | files |", "|---|---|---|---|---|"]
    for a in sorted(assets, key=lambda x: (x.get("sport", ""), (x.get("sequence") or {}).get("id", x["code"]),
                                           (x.get("sequence") or {}).get("order", 0))):
        base = f"{a.get('sport', 'misc')}/{a['code']}"
        ko = ", ".join((a.get("names") or {}).get("ko", [])[:2])
        lines.append(f"| `{a['code']}` | {a.get('sport')} | {ko} | {a.get('summary', '')} | "
                     f"[prompt]({base}/prompt.md) · [preview]({base}/preview.png) |")
    seqs: Dict[str, List[Dict]] = {}
    for a in assets:
        if a.get("sequence"):
            seqs.setdefault(a["sequence"]["id"], []).append(a)
    if seqs:
        lines += ["", "## Sequences (for video: phases in order)", ""]
        for sid, xs in sorted(seqs.items()):
            xs.sort(key=lambda x: x["sequence"].get("order", 0))
            lines.append(f"- `{sid}`: " + " -> ".join(f"`{x['code']}`" for x in xs))
    srcs: Dict[str, Tuple[Dict, List[str]]] = {}
    for a in assets:
        for s_ in a.get("sources") or []:
            key = s_.get("url") or s_.get("cite")
            srcs.setdefault(key, (s_, []))[1].append(a["code"])
    lines += ["", "## Sources", "",
              "Numbers were taken from search-engine extracts of the papers and manuals (full texts were not "
              "reachable from the build machine), except the baseball means, computed from the Driveline "
              "OpenBiomechanics data (CC BY-NC-SA 4.0: only summary numbers are used). Check a number against "
              "its source before treating it as exact.", ""]
    for key, (s_, codes) in sorted(srcs.items(), key=lambda kv: kv[1][0].get("cite", "")):
        lines.append(f"- {s_.get('cite', '')} {s_.get('url', '')} (used by {len(codes)}: {', '.join(sorted(codes))})")
    p = out_root / "CATALOG.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def sequence_text(seq_id: str, assets: List[Dict]) -> str:
    """The phases of one movement in order, as one motion description for a video prompt."""
    xs = sorted([a for a in assets if (a.get("sequence") or {}).get("id") == seq_id],
                key=lambda a: a["sequence"].get("order", 0))
    if not xs:
        raise SystemExit(f"no sequence {seq_id}")
    out = [f"# {seq_id}: {len(xs)} phases", ""]
    beats = []
    for i, a in enumerate(xs, 1):
        sc = Scene(a)
        met = Metrics(sc)
        t = a.get("text") or {}
        core = fill(t.get("core", ""), met)
        out += [f"## {i}. #{a['code']}", "", fill(t.get("action", a.get("summary", "")), met) + ".", "", core, "",
                f"control: {a.get('sport')}/{a['code']}/openpose_{(a.get('cameras') or [{}])[0].get('name', 'cam')}.png", ""]
        beats.append(core.rstrip("."))
    out += ["## One-paragraph motion (keep the order)", "",
            "{SUBJECT}, in one continuous movement. First: " + ". Then: ".join(beats) + ". {SETTING}."]
    return "\n".join(out) + "\n"


def search(query: str, rows: List[Dict], k: int = 5) -> List[Tuple[float, Dict]]:
    q = query.lower()
    toks = [x for x in re.split(r"[\s,/_#]+", q) if x]
    scored = []
    for r in rows:
        hay = " ".join([r["code"].lower().replace("_", " "), str(r.get("sport")), str(r.get("technique")),
                        str(r.get("phase")), r.get("summary", "").lower(),
                        " ".join(r.get("names", {}).get("ko", [])), " ".join(r.get("names", {}).get("en", [])).lower(),
                        " ".join(r.get("keywords", [])).lower()])
        s = sum(2.0 if re.search(r"\b" + re.escape(t) + r"\b", hay) else 1.0 if t in hay else 0.0 for t in toks)
        if r["code"].lower() == q.replace(" ", "_").lstrip("#"):
            s += 10
        names = [n.lower() for n in r.get("names", {}).get("ko", []) + r.get("names", {}).get("en", [])]
        if s and any(q.strip() in n for n in names):             # the whole query is one of its names
            s += 3
        if s:
            scored.append((s, r))
    scored.sort(key=lambda x: (-x[0], (x[1].get("sequence") or {}).get("id", x[1]["code"]),
                               (x[1].get("sequence") or {}).get("order", 0)))
    return scored[:k]


# ---------------------------------------------------------------- cli
def _selected(codes: Sequence[str]) -> List[Dict]:
    return [load_asset(c) for c in codes] if codes else [load_asset(str(p)) for p in asset_files()]


def cmd_build(a) -> int:
    assets = _selected(a.codes)
    bad = 0
    for x in assets:
        issues, out = build_one(x, Path(a.out))
        errs = [m for lv, m in issues if lv == "error"]
        warns = [m for lv, m in issues if lv == "warn"]
        bad += bool(errs)
        print(f"{'FAIL' if errs else 'ok  '} {x['code']:34s} errors {len(errs)} warnings {len(warns)}")
        for m in errs + warns:
            print("      " + m)
    if not a.codes:
        write_index(assets, Path(a.out))
        write_catalog(assets, Path(a.out))
    print(f"{len(assets)} assets, {bad} with errors -> {a.out}")
    return 1 if bad else 0


def cmd_check(a) -> int:
    bad = 0
    for x in _selected(a.codes):
        issues, _ = build_one(x, write=False)
        errs = [m for lv, m in issues if lv == "error"]
        bad += bool(errs)
        print(f"{'FAIL' if errs else 'ok  '} {x['code']}")
        for lv, m in issues:
            print(f"      {lv}: {m}")
    return 1 if bad else 0


def cmd_find(a) -> int:
    idx = Path(a.out) / "index.json"
    rows = json.loads(idx.read_text(encoding="utf-8"))["assets"] if idx.is_file() else [
        {**x, "prompt_md": ""} for x in _selected([])]
    hits = search(a.query, rows, a.k)
    if not hits:
        print("no match")
        return 1
    for s, r in hits:
        print(f"{s:4.1f}  #{r['code']:32s} {r.get('summary', '')}")
        if a.full:
            print("      " + str(Path(a.out) / r["prompt_md"]))
            for p in r.get("openpose", []):
                print("      " + str(Path(a.out) / p))
    return 0


def cmd_sequence(a) -> int:
    print(sequence_text(a.id, _selected([])))
    return 0


def cmd_show(a) -> int:
    x = load_asset(a.code)
    sc = Scene(x)
    t = prompt_text(sc, validate(sc))
    print(t["block"])
    print("\nPROMPT:\n" + t["prompt"])
    print("\nNEGATIVE:\n" + t["negative"])
    return 0


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="sportspose")
    ap.add_argument("--out", default=str(LIBRARY))
    sub_ = ap.add_subparsers(dest="cmd", required=True)
    p = sub_.add_parser("build")
    p.add_argument("codes", nargs="*")
    p.set_defaults(fn=cmd_build)
    p = sub_.add_parser("check")
    p.add_argument("codes", nargs="*")
    p.set_defaults(fn=cmd_check)
    p = sub_.add_parser("find")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_find)
    p = sub_.add_parser("show")
    p.add_argument("code")
    p.set_defaults(fn=cmd_show)
    p = sub_.add_parser("sequence")
    p.add_argument("id", help="e.g. VOLLEYBALL_SPIKE, BASEBALL_PITCH")
    p.set_defaults(fn=cmd_sequence)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

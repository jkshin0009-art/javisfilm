"""gamerules: official game rules for the pose assets.

rules/<sport>.json holds, from the sport's rulebook (FIVB, IFAB, MLB, FIBA, ITF, BWF, IGFA, World Boxing,
WT, World Aquatics, IJF, UWW):

  dimensions   field and equipment sizes, with the rule number
  equipment    checks that the asset's net, rim, ball, bat, mound match those sizes
  scene        what a multi-player scene must show (players, uniforms, officials)
  fouls        things a single picture can show; each has a rule number, the wording, words to
               keep out of the image, and, when the skeleton can measure it, a check

A foul applies to an asset when its `techniques` (and `phases`, if given) match the asset.
Check kinds (all measured on the placed skeleton):

  clear_of_net     no body part within margin_m of the net band (net top down to net_band_m)
  not_beyond       each group of points keeps at least one point on the near side of a line
                   (x of an environment point); objects count with their near edge
  not_touching     an object does not touch the listed limb segments
  in_area          each group of points keeps at least one point inside an area on the floor
  facing           the chest faces a point within max_deg
  on_floor         the listed feet touch the floor
  higher_than      at least one of the points is above a reference point
  all_above        every listed point is above a reference point (e.g. a punch above the belt)
  near             a point lies within max_m of a target point (a kick landing on the trunk protector);
                   point and target may be lists, and the closest pair counts
  apart            the reverse of near: every listed point stays at least min_m from the targets
                   (no fist on the opponent's head in taekwondo)
  max_height       a point (plus its half size extent_m) stays below max_m above the floor
  hand_shape       a hand has one of the allowed finger shapes (a punch lands with a closed fist)
  both_touch       every listed body point lies on the object's surface (within tol_m) at once
  paired           each left/right pair of points is level along the given axes (arms or legs
                   moving together, not alternating)
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
RULES = HERE / "rules"

# body volume: capsule radius per segment as a fraction of height
RADIUS = {"trunk": 0.07, "head": 0.06, "upper_arm": 0.025, "forearm": 0.02, "hand": 0.015,
          "thigh": 0.04, "shank": 0.03, "foot": 0.02}


def load_rules(sport: str) -> Optional[Dict]:
    p = RULES / f"{sport}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def applies(foul: Dict, asset: Dict) -> bool:
    techs, phases = foul.get("techniques"), foul.get("phases")
    if techs and asset.get("technique") not in techs and "all" not in techs:
        return False
    if phases and asset.get("phase") not in phases:
        return False
    return asset["code"] not in foul.get("except", [])


def segments(sc) -> List[Tuple[str, Tuple, Tuple, float]]:
    """(name, a, b, radius) capsules for the whole body."""
    P = sc.body.points
    H = sc.height
    out = [("trunk", P["pelvis"], P["neck"], RADIUS["trunk"] * H), ("head", P["head"], P["head"], RADIUS["head"] * H)]
    for s in "rl":
        out += [(f"{s}_upper_arm", P[s + "_shoulder"], P[s + "_elbow"], RADIUS["upper_arm"] * H),
                (f"{s}_forearm", P[s + "_elbow"], P[s + "_wrist"], RADIUS["forearm"] * H),
                (f"{s}_hand", P[s + "_wrist"], P[s + "_fingertip"], RADIUS["hand"] * H),
                (f"{s}_thigh", P[s + "_hip"], P[s + "_knee"], RADIUS["thigh"] * H),
                (f"{s}_shank", P[s + "_knee"], P[s + "_ankle"], RADIUS["shank"] * H),
                (f"{s}_foot", P[s + "_heel"], P[s + "_toe"], RADIUS["foot"] * H)]
    for s, pts in sc.body.hands.items():                   # finger bones
        for a, b in ((0, 4), (5, 8), (9, 12), (13, 16), (17, 20)):
            out.append((f"{s}_fingers", pts[a], pts[b], 0.008 * H))
    return out


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def seg_point_dist(a, b, p) -> float:
    ab = tuple(y - x for x, y in zip(a, b))
    L2 = sum(v * v for v in ab)
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, sum((p[i] - a[i]) * ab[i] for i in range(3)) / L2))
    return _dist(_lerp(a, b, t), p)


def net_gap(sc, net_x: float, top: float, band: float) -> Tuple[float, str]:
    """Smallest clearance (m) between the body surface and the net band x = net_x, z in [top - band, top]."""
    best, who = 1e9, ""
    for name, a, b, r in segments(sc):
        n = 12 if a != b else 1
        prev = None
        for i in range(n + 1):
            p = _lerp(a, b, i / n) if n > 1 else a
            dz = 0.0 if top - band <= p[2] <= top else min(abs(p[2] - top), abs(p[2] - (top - band)))
            d = math.hypot(p[0] - net_x, dz) - r
            if prev is not None and (prev[0] - net_x) * (p[0] - net_x) < 0:      # this piece passes through the plane
                t = (net_x - prev[0]) / (p[0] - prev[0])
                zc = prev[2] + (p[2] - prev[2]) * t
                if top - band <= zc <= top:
                    d = -r
            if d < best:
                best, who = d, name
            prev = p
    return best, who


def _point_or_object(sc, ref: str) -> Tuple[Tuple, float]:
    if ref in sc.objects:
        o = sc.objects[ref]
        return o["center"], o.get("diameter_m", 0.0) / 2
    return sc.point(ref), 0.0


def _name(ref) -> str:
    """How a check's reference reads in a note: 'the B.belt front', or a height for [x, y, z]."""
    if isinstance(ref, (list, tuple)):
        return f"a height of {float(ref[2]):.2f} m"
    return "the " + ref.replace("_", " ")


def _area(sc, spec: Dict) -> Tuple[float, float, float, float]:
    c = sc.point(spec["around"]) if spec.get("around") else (0.0, 0.0, 0.0)
    x0, x1 = spec["x"]
    y0, y1 = spec["y"]
    return c[0] + x0, c[0] + x1, c[1] + y0, c[1] + y1


def run_check(sc, foul: Dict, rules: Dict) -> Tuple[Optional[bool], str]:
    """(passed, note). passed is None when the foul has no geometric check or lacks its reference."""
    ck = foul.get("check")
    if not ck:
        return None, "text only"
    if isinstance(ck, list):                       # several conditions: all must hold
        res = [run_check(sc, {**foul, "check": c}, rules) for c in ck]
        oks = [r[0] for r in res]
        ok = None if None in oks else all(oks)
        return ok, "; ".join(r[1] for r in res)
    kind = ck["kind"]
    try:
        if kind == "clear_of_net":
            net = next((e for e in sc.env if e.get("kind") == "net"), None)
            if not net:
                return None, "no net in this asset"
            gap, who = net_gap(sc, float(net.get("x_m", 1.0)), float(net.get("height_m", 2.43)),
                               float(ck.get("net_band_m", 1.0)))
            ok = gap >= ck.get("margin_m", 0.02)
            return ok, f"closest body part to the net: {who.replace('_', ' ')}, {gap * 100:.0f} cm"
        if kind == "not_beyond":
            line = sc.point(ck["line"])[0] + ck.get("tol_m", 0.0)
            bad = []
            for group in ck["groups"]:
                near, far = [], []
                for ref in group:
                    p, r = _point_or_object(sc, ref)
                    near.append(p[0] - r)
                    far.append(p[0] + r)
                if ck.get("all") and max(far) > line:          # every point must stay behind the line
                    bad.append(f"{'/'.join(group)} {100 * (max(far) - line):.0f} cm onto or past the line")
                elif min(near) > line:
                    bad.append(f"{'/'.join(group)} {100 * (min(near) - line):.0f} cm past")
            return (not bad), ("; ".join(bad) or "all on the near side")
        if kind == "not_touching":
            c, r = _point_or_object(sc, ck["object"])
            segs = [s for s in segments(sc) if any(s[0].startswith(p) for p in ck["limbs"])]
            gap = min(seg_point_dist(a, b, c) - rr - r for _, a, b, rr in segs)
            what = ck.get("label") or "/".join(ck["limbs"])
            return gap >= ck.get("margin_m", 0.01), f"{ck['object']} is {gap * 100:.0f} cm from the {what}"
        if kind == "in_area":
            x0, x1, y0, y1 = _area(sc, ck["area"])
            tol = ck.get("tol_m", 0.0)
            bad = []
            for group in ck["groups"]:
                inside = [x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol
                          for p in (sc.point(ref) for ref in group)]
                if not any(inside):
                    bad.append("/".join(group))
            return (not bad), ("outside: " + ", ".join(bad)) if bad else "inside"
        if kind == "facing":
            from sportspose import Metrics, angle_between, sub
            t = sc.point(ck["target"])
            f = Metrics(sc).chest_facing()
            d = sub(t, sc.body.points["neck"])
            ang = angle_between(f, (d[0], d[1], 0.0))
            return ang <= ck.get("max_deg", 45), f"chest turned {ang:.0f} deg from the {ck['target'].replace('_', ' ')}"
        if kind == "higher_than":
            ref = sc.point(ck["ref"])[2]
            top = max(sc.point(x)[2] for x in ck["points"])
            return top > ref, f"highest of {'/'.join(ck['points'])} {100 * (top - ref):+.0f} cm against {_name(ck['ref'])}"
        if kind == "all_above":
            ref = sc.point(ck["ref"])[2] + ck.get("tol_m", 0.0)
            low = min(sc.point(x)[2] for x in ck["points"])
            return low >= ref, f"lowest of {'/'.join(ck['points'])} {100 * (low - ref):+.0f} cm against {_name(ck['ref'])}"
        if kind == "hand_shape":
            shape = sc.body.pose[ck["hand"] + "_arm"].get("hand", "relaxed")
            return shape in ck["allowed"], f"{ck['hand']} hand is {shape}"
        if kind == "max_height":
            top = sc.point(ck["point"])[2] + ck.get("extent_m", 0.0)
            return top <= ck["max_m"], f"top of the {ck['point']} {top:.2f} m (limit {ck['max_m']} m)"
        if kind in ("near", "apart"):              # point / target may be lists: the closest pair counts
            pts = ck["point"] if isinstance(ck["point"], list) else [ck["point"]]
            tgs = ck["target"] if isinstance(ck["target"], list) else [ck["target"]]
            d, p_, t_ = min((_dist(sc.point(p), sc.point(t)), p, t) for p in pts for t in tgs)
            note = f"{p_.replace('_', ' ')} {d * 100:.0f} cm from {t_.replace('_', ' ')}"
            return (d <= ck["max_m"], note) if kind == "near" else (d >= ck["min_m"], note)
        if kind == "paired":                       # left and right move together (butterfly, breaststroke)
            axes = ck.get("axes", "xyz")
            bad, worst = [], 0.0
            for a_, b_ in ck["pairs"]:
                pa, pb = sc.point(a_), sc.point(b_)
                for ax in axes:
                    i = "xyz".index(ax)
                    d = abs(pa[i] - pb[i])
                    worst = max(worst, d)
                    if d > ck.get("max_m", 0.08):
                        bad.append(f"{a_}/{b_} {d * 100:.0f} cm apart in {ax}")
            return (not bad), ("; ".join(bad) or f"pairs level, largest difference {worst * 100:.0f} cm")
        if kind == "both_touch":
            c, r = _point_or_object(sc, ck["object"])
            gaps = [_dist(sc.point(x), c) - r for x in ck["points"]]
            ok = all(abs(g) <= ck.get("tol_m", 0.03) for g in gaps)
            return ok, ", ".join(f"{x.replace('_', ' ')} {100 * g:.0f} cm" for x, g in zip(ck["points"], gaps)) + " from the ball surface"
        if kind == "on_floor":
            zs = {c: min(sc.above_ground(p) for p in sc.body.foot_points(c[0])) for c in ck["feet"]}
            bad = [f"{c} {z * 100:.0f} cm up" for c, z in zs.items() if z > ck.get("tol_m", 0.03)]
            return (not bad), ("; ".join(bad) or "feet on the floor")
    except KeyError as e:
        return None, f"not measurable here ({e})"
    return None, f"unknown check {kind}"


def equipment_checks(sc, rules: Dict) -> List[Tuple[str, bool, str]]:
    """Does the asset's net / rim / ball / bat / mound match the official sizes?"""
    out = []
    cat = (sc.asset.get("athlete") or {}).get("category", "men")
    for eq in rules.get("equipment") or []:
        if "env" in eq:
            items = [e for e in sc.env if e.get("kind") == eq["env"]]
        elif "object" in eq:
            items = [o for o in sc.objects.values() if o.get("kind") == eq["object"]]
        elif eq.get("ground"):
            items = [sc.asset["ground"]] if sc.asset.get("ground") else []
        else:
            items = []
        for it in items:
            v = it.get(eq["field"])
            if v is None:
                continue
            want = eq.get("value")
            if isinstance(want, dict):
                want = want.get(cat)
            rng = eq.get("range")
            if isinstance(rng, dict):
                rng = rng.get(cat)
            lo, hi = rng or (want - eq.get("tol", 0.005), want + eq.get("above_tol", eq.get("tol", 0.005)))
            ok = lo <= float(v) <= hi
            out.append((eq["id"], ok, f"{eq['field']} {v} (official {lo:g}-{hi:g}, {rules['rulebook']['short']} {eq['rule']})"))
    return out


def evaluate(sc) -> Dict:
    """All official-rule results for one placed scene."""
    a = sc.asset
    rules = load_rules(a.get("sport", ""))
    if not rules:
        return {"rules": None, "fouls": [], "equipment": [], "errors": []}
    fouls = []
    errors = []
    for f in rules.get("fouls") or []:
        if not applies(f, a):
            continue
        ok, note = run_check(sc, f, rules)
        fouls.append({**f, "passed": ok, "note": note})
        if ok is False:
            errors.append(f"game rule {rules['rulebook']['short']} {f['rule']} ({f['title']}): {note}")
    eq = equipment_checks(sc, rules)
    errors += [f"equipment {i}: {n}" for i, ok, n in eq if not ok]
    return {"rules": rules, "fouls": fouls, "equipment": eq, "errors": errors}


def sport_summary(sport: str) -> str:
    r = load_rules(sport)
    if not r:
        raise SystemExit(f"no rules for {sport}")
    b = r["rulebook"]
    lines = [f"# {sport}: {b['title']}", "", b.get("url", ""), "", "## Dimensions", ""]
    for k, v in (r.get("dimensions") or {}).items():
        val = {kk: vv for kk, vv in v.items() if kk not in ("rule", "note")} if isinstance(v, dict) else v
        lines.append(f"- {k}: {json.dumps(val, ensure_ascii=False)} ({b['short']} {v.get('rule', '') if isinstance(v, dict) else ''})"
                     + (f" - {v['note']}" if isinstance(v, dict) and v.get("note") else ""))
    lines += ["", "## Scene", ""] + [f"- {s['text']} ({b['short']} {s['rule']})" for s in r.get("scene") or []]
    lines += ["", "## Fouls a picture can show", ""]
    for f in r.get("fouls") or []:
        ck = f.get("check")
        how = ("checked (" + ", ".join(c["kind"] for c in (ck if isinstance(ck, list) else [ck])) + ")") if ck else "text only"
        lines.append(f"- {b['short']} {f['rule']} {f['title']}: {f['text']} [{how}; techniques: {', '.join(f.get('techniques', []))}]")
    return "\n".join(lines) + "\n"

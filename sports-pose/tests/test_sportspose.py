import io
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
PIL = pytest.importorskip("PIL.Image")
import sportspose as sp  # noqa: E402
import fetch_refs as fr  # noqa: E402


def close(a, b, tol=0.02):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_frames_follow_the_documented_signs():
    H = 1.8
    L_ua, L_fa = sp.SEG["upper_arm"] * H, sp.SEG["forearm"] * H
    b = sp.Body({"r_arm": {"elev": 90, "plane": 0, "rot": 0, "elbow": 90}}, H)
    sh = b.points["r_shoulder"]
    assert close(b.points["r_elbow"], (sh[0], sh[1] - L_ua, sh[2]))           # abduction goes out to the right
    assert close(b.points["r_wrist"], (sh[0] + L_fa, sh[1] - L_ua, sh[2]))    # rot 0: forearm points forward
    b = sp.Body({"r_arm": {"elev": 90, "plane": 0, "rot": 90, "elbow": 90}}, H)
    assert b.points["r_wrist"][2] > b.points["r_elbow"][2] + 0.2               # external rotation: forearm up
    b = sp.Body({"l_arm": {"elev": 90, "plane": 0, "rot": 90, "elbow": 90}}, H)
    assert b.points["l_wrist"][2] > b.points["l_elbow"][2] + 0.2               # same for the left arm
    b = sp.Body({"r_arm": {"elev": 90, "plane": 90, "elbow": 0}}, H)
    assert b.points["r_wrist"][0] > 0.5                                        # plane 90: straight forward
    b = sp.Body({"r_leg": {"flex": 90, "abd": 0, "rot": 0, "knee": 90}}, H)
    k, a = b.points["r_knee"], b.points["r_ankle"]
    assert k[0] > 0.4 and abs(a[0] - k[0]) < 0.02 and a[2] < k[2] - 0.4        # thigh forward, shin down
    b = sp.Body({"trunk": {"flex": 30}}, H)
    assert b.points["neck"][0] > 0.2                                           # flexion leans forward
    b = sp.Body({"trunk": {"rot": 30}}, H)
    assert b.points["r_shoulder"][0] > 0.05                                    # rot + turns left
    b = sp.Body({"head": {"flex": -30}}, H)
    assert b.points["nose"][2] > sp.Body({}, H).points["nose"][2]              # flex - looks up
    b = sp.Body({"pelvis": {"yaw": 90}}, H)
    assert b.points["r_hip"][0] > 0.05                                         # yaw 90: facing +y
    assert close(sp.Body({"r_arm": {"elev": 0, "elbow": 90, "pron": 90}}).vecs["r_palm_normal"], (0, 0, -1))


def test_ankle_modes_put_the_sole_level():
    b = sp.Body({"pelvis": {"tilt": 30}, "r_leg": {"flex": 83, "knee": 90, "ankle": "flat"}})
    assert abs(b.vecs["r_foot"][2]) < 0.01
    b = sp.Body({"r_leg": {"flex": 0, "knee": 0, "ankle": "toes:30"}})
    assert abs(-b.vecs["r_foot"][2] - math.sin(math.radians(30))) < 0.01


def test_rom_catches_an_impossible_elbow_and_a_floating_foot():
    a = {"code": "T", "sport": "test", "pose": {"r_arm": {"elbow": -40}, "l_leg": {"flex": 60, "knee": 90}},
         "support": {"contacts": ["r_foot", "l_foot"]}}
    msgs = [m for lv, m in sp.validate(sp.Scene(a)) if lv == "error"]
    assert any("r_arm.elbow" in m for m in msgs)
    assert any("l_foot should touch the floor" in m for m in msgs)


def test_reach_puts_the_palm_on_the_ball():
    a = {"code": "T", "sport": "test", "pose": {"r_arm": {"elev": 120, "plane": 60, "elbow": 20, "reach": {"to": "ball"}}},
         "objects": [{"name": "ball", "kind": "ball", "diameter_m": 0.21, "at": "r_shoulder", "offset_m": [0.3, 0, 0.5]}]}
    sc = sp.Scene(a)
    assert abs(sc.reach_gap("r_arm", {"to": "ball"})) < 0.02
    assert not [m for lv, m in sp.validate(sc) if lv == "error"]


def test_mound_ground_moves_the_floor():
    a = {"code": "T", "sport": "test", "ground": {"kind": "mound", "top_x_m": 0.0, "slope": 1 / 12, "drop_m": 0.254}}
    sc = sp.Scene(a)
    assert sc.ground((1.2, 0, 0)) == pytest.approx(-0.1)
    assert sc.ground((9, 0, 0)) == pytest.approx(-0.254)
    assert sc.ground((-1, 0, 0)) == 0


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("lib")
    assets = [sp.load_asset(str(p)) for p in sp.asset_files()]
    results = {a["code"]: sp.build_one(a, out) for a in assets}
    sp.write_index(assets, out)
    sp.write_catalog(assets, out)
    return out, assets, results


def test_every_asset_passes_its_checks(built):
    _, assets, results = built
    assert len(assets) >= 20
    bad = {c: [m for lv, m in issues if lv == "error"] for c, (issues, _) in results.items()}
    assert not {c: m for c, m in bad.items() if m}


def test_asset_files_are_complete(built):
    _, assets, _ = built
    for a in assets:
        assert Path(a["_path"]).stem == a["code"]
        assert a["names"]["ko"] and a["names"]["en"], a["code"]
        assert a.get("rules") and a.get("sources") and a.get("cameras"), a["code"]
        ids = {s["id"] for s in a["sources"]}
        for r in a["rules"]:
            cited = [x.strip().split(" ")[0] for x in r.get("src", "").split(",")]
            assert any(c in ids or c == "rules" for c in cited), (a["code"], r["m"], r.get("src"))


def test_outputs_match_openpose_formats(built):
    out, assets, _ = built
    from PIL import Image
    a = assets[0]
    folder = out / a["sport"] / a["code"]
    for cam in a["cameras"]:
        img = Image.open(folder / f"openpose_{cam['name']}.png")
        assert list(img.size) == cam["size"]
        j = json.loads((folder / f"openpose_{cam['name']}.json").read_text())
        person = j["people"][0]
        assert len(person["pose_keypoints_2d"]) == 18 * 3
        assert len(person["hand_left_keypoints_2d"]) == 21 * 3 == len(person["hand_right_keypoints_2d"])
        assert (j["canvas_width"], j["canvas_height"]) == tuple(cam["size"])
        xs = person["pose_keypoints_2d"][0::3]
        assert max(xs) <= cam["size"][0]


def test_prompt_numbers_come_from_the_skeleton(built):
    out, assets, _ = built
    a = sp.load_asset("VOLLEYBALL_SPIKE_CONTACT")
    sc = sp.Scene(a)
    met = sp.Metrics(sc)
    text = (out / "volleyball" / "VOLLEYBALL_SPIKE_CONTACT" / "prompt.md").read_text()
    for h in ("1. SYSTEM_INDEX_CODE: #VOLLEYBALL_SPIKE_CONTACT", "2. ANATOMICAL_BONES", "3. OBJECT_INTERACTION",
              "4. CINEMATIC_CAMERA", "5. KINETIC_ENERGY", "{SUBJECT}", "{SETTING}"):
        assert h in text
    assert f"({met.get('r_elbow_flex'):.0f} deg flexion)" in text
    assert "{" + "lowest_z}" not in text                                   # templates were filled


def test_find_ranks_korean_and_english_names(built):
    out, _, _ = built
    rows = json.loads((out / "index.json").read_text(encoding="utf-8"))["assets"]
    assert sp.search("배구 스파이크 타점", rows)[0][1]["code"] == "VOLLEYBALL_SPIKE_CONTACT"
    assert sp.search("덩크", rows)[0][1]["code"] == "BASKETBALL_DUNK"
    assert sp.search("goalkeeper dive", rows)[0][1]["code"] == "SOCCER_GOALKEEPER_DIVE"
    top = [r["code"] for _, r in sp.search("투구", rows, 4)]
    assert top == ["BASEBALL_PITCH_LEG_LIFT", "BASEBALL_PITCH_FOOT_CONTACT", "BASEBALL_PITCH_MER", "BASEBALL_PITCH_RELEASE"]
    assert "CATALOG.md" in [p.name for p in out.iterdir()]


def test_sequence_keeps_phase_order():
    txt = sp.sequence_text("BASEBALL_PITCH", [sp.load_asset(str(p)) for p in sp.asset_files()])
    order = [txt.index(c) for c in ("#BASEBALL_PITCH_LEG_LIFT", "#BASEBALL_PITCH_FOOT_CONTACT", "#BASEBALL_PITCH_MER",
                                    "#BASEBALL_PITCH_RELEASE")]
    assert order == sorted(order)


def test_fetch_refs_keeps_only_free_licences(tmp_path, monkeypatch):
    assert fr.licence_ok("CC BY-SA 4.0") and fr.licence_ok("CC0") and fr.licence_ok("Public domain")
    assert not fr.licence_ok("CC BY-NC-SA 4.0") and not fr.licence_ok("CC BY-ND 2.0") and not fr.licence_ok("")
    api = {"query": {"pages": {
        "1": {"index": 1, "title": "File:Spike.jpg", "imageinfo": [{"thumburl": "https://x/1.jpg", "descriptionurl": "https://c/1",
              "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"},
                                                    "Artist": {"value": "<a href='u'>Kim</a>"}}}]},
        "2": {"index": 2, "title": "File:NoNC.jpg", "imageinfo": [{"thumburl": "https://x/2.jpg", "descriptionurl": "https://c/2",
              "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "CC BY-NC 2.0"}}}]}}}}

    def fake_get(url, timeout=30.0):
        return json.dumps(api).encode() if "api.php" in url else b"JPEGDATA"
    monkeypatch.setattr(fr, "_get", fake_get)
    kept = fr.fetch({"code": "VOLLEYBALL_SPIKE_CONTACT", "sport": "volleyball", "ref_query": "volleyball spike"},
                    tmp_path, 4, pause=0)
    assert [k["title"] for k in kept] == ["File:Spike.jpg"] and kept[0]["author"] == "Kim"
    assert (tmp_path / "volleyball" / "VOLLEYBALL_SPIKE_CONTACT" / "1.jpg").read_bytes() == b"JPEGDATA"
    credits = fr.write_attribution(tmp_path).read_text()
    assert "by Kim, CC BY-SA 4.0" in credits


def test_partners_grip_each_other_and_are_drawn(built):
    out, _, _ = built
    a = sp.load_asset("JUDO_KUMIKATA")
    sc = sp.Scene(a)
    b = sc.partners["B"]
    for limb in ("r_arm", "l_arm"):
        assert abs(sc.reach_gap(limb, a["pose"][limb]["reach"])) < 0.03
        assert abs(b.reach_gap(limb, b.asset["pose"][limb]["reach"])) < 0.03
    j = json.loads((out / "judo" / "JUDO_KUMIKATA" / "openpose_side.json").read_text())
    assert len(j["people"]) == 2


def test_bodies_may_not_pass_through_each_other():
    a = sp.load_asset("JUDO_KUMIKATA")
    a["partners"][0]["support"]["root_offset"] = [0.1, 0.0]   # partner standing inside the athlete
    msgs = [m for lv, m in sp.validate(sp.Scene(a)) if lv == "error"]
    assert any("bodies pass through each other" in m for m in msgs)


def test_swimmer_roll_and_water_relative_text():
    b = sp.Body({"pelvis": {"tilt": 90, "roll": -40}})
    assert b.points["r_shoulder"][2] > b.points["l_shoulder"][2] + 0.1     # roll -: right shoulder up
    sc = sp.Scene(sp.load_asset("SWIMMING_FREESTYLE_BREATH"))
    block = sp.prompt_text(sc, sp.validate(sc))["block"]
    left_arm = next(line for line in block.splitlines() if line.startswith("- Left arm"))
    assert "pointing forward" in left_arm and "below the water surface" in left_arm
    assert "above the floor" not in block


def test_block_and_pool_ground():
    sc = sp.Scene(sp.load_asset("SWIMMING_START_SET"))
    assert sc.ground((-0.74, 0, 0)) == pytest.approx(0.75)
    assert sc.ground((1.0, 0, 0)) == pytest.approx(-2.5)                  # past the block: the pool floor
    assert sc.body.points["pelvis"][2] > 1.2                                # crouched on top of the block

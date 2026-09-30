"""Each official-rule check must pass on the asset and fail when the pose commits the foul."""
import copy
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
pytest.importorskip("PIL.Image")
import gamerules as gr  # noqa: E402
import sportspose as sp  # noqa: E402

SPORTS = ("volleyball", "soccer", "baseball", "basketball", "tennis", "badminton", "fishing", "boxing")


def result(asset, rule_id):
    ev = gr.evaluate(sp.Scene(asset))
    hit = [f for f in ev["fouls"] if f["id"] == rule_id]
    assert hit, f"{rule_id} does not apply to {asset['code']}"
    return hit[0]["passed"], hit[0]["note"], ev


def variant(code, change):
    a = copy.deepcopy(sp.load_asset(code))
    change(a)
    return a


@pytest.mark.parametrize("sport", SPORTS)
def test_rulebooks_are_complete(sport):
    r = gr.load_rules(sport)
    assert r and r["rulebook"]["url"].startswith("http") and r["rulebook"]["short"]
    assert r["dimensions"] and r["scene"] and r["fouls"]
    for f in r["fouls"]:
        assert f["rule"] and f["title"] and f["text"] and f["techniques"], f
    assert "## Fouls a picture can show" in gr.sport_summary(sport)


def test_every_asset_obeys_the_official_rules():
    for p in sp.asset_files():
        ev = gr.evaluate(sp.Scene(sp.load_asset(str(p))))
        assert not ev["errors"], (p.stem, ev["errors"])


def test_net_contact_is_caught():
    ok, note, _ = result(sp.load_asset("VOLLEYBALL_BLOCK"), "net_contact")
    assert ok, note

    def closer(a):
        for e in a["environment"]:
            if e.get("kind") == "net":
                e["x_m"] = 0.12                    # net pushed into the blocker's chest
    ok, note, ev = result(variant("VOLLEYBALL_BLOCK", closer), "net_contact")
    assert ok is False and any("11.3.1" in e for e in ev["errors"])


def test_attack_in_the_opponents_space_is_caught():
    def net_behind_ball(a):
        for e in a["environment"]:
            if e.get("kind") == "net":
                e["x_m"] = 0.0                     # the ball is now completely past the net
    ok, _, _ = result(variant("VOLLEYBALL_SPIKE_CONTACT", net_behind_ball), "attack_own_space")
    assert ok is False


def test_double_contact_needs_both_hands_on_the_ball():
    ok, note, _ = result(sp.load_asset("VOLLEYBALL_OVERHEAD_SET"), "double_contact")
    assert ok, note

    def one_hand(a):
        a["pose"]["l_arm"].pop("reach")
        a["pose"]["l_arm"].update({"elev": 20, "elbow": 20})
    ok, _, _ = result(variant("VOLLEYBALL_OVERHEAD_SET", one_hand), "double_contact")
    assert ok is False


def test_handball_is_caught():
    ok, note, _ = result(sp.load_asset("SOCCER_JUMPING_HEADER"), "handball")
    assert ok, note

    def arm_to_ball(a):
        a["pose"]["r_arm"]["reach"] = {"to": "ball"}
    ok, _, _ = result(variant("SOCCER_JUMPING_HEADER", arm_to_ball), "handball")
    assert ok is False


def test_goalkeeper_must_handle_inside_the_area():
    def far_out(a):
        for e in a["environment"]:
            if e.get("name") == "goal_center":
                e["at"] = [-30.0, 0, 0]            # goal line 30 m behind: outside the 16.5 m area
    ok, _, _ = result(variant("SOCCER_GOALKEEPER_DIVE", far_out), "keeper_area")
    assert ok is False


def test_legal_guarding_position():
    ok, note, _ = result(sp.load_asset("BASKETBALL_DEFENSIVE_STANCE"), "legal_guarding")
    assert ok, note

    def turned_away(a):
        a["pose"]["pelvis"]["yaw"] = 80
    ok, note, _ = result(variant("BASKETBALL_DEFENSIVE_STANCE", turned_away), "legal_guarding")
    assert ok is False and "chest turned" in note


def test_equipment_must_match_the_rulebook():
    def low_net(a):
        for e in a["environment"]:
            if e.get("kind") == "net":
                e["height_m"] = 2.3
    ev = gr.evaluate(sp.Scene(variant("VOLLEYBALL_SPIKE_CONTACT", low_net)))
    assert any("net_height" in e for e in ev["errors"])

    def women(a):
        a["athlete"]["category"] = "women"         # a 2.43 m net is wrong for women (2.24 m)
    ev = gr.evaluate(sp.Scene(variant("VOLLEYBALL_SPIKE_CONTACT", women)))
    assert any("net_height" in e for e in ev["errors"])

    def big_ball(a):
        a["objects"][0]["diameter_m"] = 0.3
    ev = gr.evaluate(sp.Scene(variant("BASKETBALL_DUNK", big_ball)))
    assert any("ball_size" in e for e in ev["errors"])


def test_prompt_carries_the_rules():
    a = sp.load_asset("VOLLEYBALL_BLOCK")
    sc = sp.Scene(a)
    t = sp.prompt_text(sc, sp.validate(sc))
    assert "Legal under the FIVB rules" in t["block"] and "no part of the body touches the net" in t["block"]
    assert "player touching the net" in t["negative"]


def test_pitcher_pivot_foot_must_touch_the_rubber():
    ok, note, _ = result(sp.load_asset("BASEBALL_PITCH_LEG_LIFT"), "pivot_on_rubber")
    assert ok, note

    def off(a):
        a["support"]["root_xy"] = [a["support"]["root_xy"][0] + 0.6, a["support"]["root_xy"][1]]
    ok, _, _ = result(variant("BASEBALL_PITCH_LEG_LIFT", off), "pivot_on_rubber")
    assert ok is False


def test_batter_feet_must_be_in_the_box():
    ok, note, _ = result(sp.load_asset("BASEBALL_BAT_CONTACT"), "batters_box")
    assert ok, note

    def plate_far(a):
        for e in a["environment"]:
            if e.get("name") == "plate":
                e["at"] = [0.0, -2.5, 0.0]         # the box moves 1.75 m away from the feet
    ok, _, _ = result(variant("BASEBALL_BAT_CONTACT", plate_far), "batters_box")
    assert ok is False


def test_mound_must_follow_the_rulebook():
    def steep(a):
        a["ground"]["slope"] = 0.2
    ev = gr.evaluate(sp.Scene(variant("BASEBALL_PITCH_RELEASE", steep)))
    assert any("mound_slope" in e for e in ev["errors"])

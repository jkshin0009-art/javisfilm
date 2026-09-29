import http.server
import json
import re
import sys
import threading
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import h3_scene as hs  # noqa: E402

EX = ROOT / "examples"


def build(scene="S01_diner.yaml", cast="cast.yaml", override=None):
    chars, locs = hs.load_cast(EX / cast)
    scene = hs.load_scene(EX / scene, chars, locs, override)
    return {c.id: hs.build_clip(scene, c, chars) for c in scene.clips}


def write(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def small_cast(n_chars=2, voices=0):
    chars = []
    for i in range(n_chars):
        c = {"id": f"P{i}", "name": f"Person{i}", "slot": i + 1, "look": f"a person number {i}",
             "short": f"person {i}", "sheet": f"p{i}.png"}
        if i < voices:
            c["voice"] = f"p{i}.wav"
        chars.append(c)
    return {"characters": chars,
            "locations": [{"id": "room", "look": "a small white room", "short": "the room", "image": "room.png", "slot": 9}]}


def run_scene(tmp_path, cast, clips, **scene_extra):
    cast_p = write(tmp_path, "cast.yaml", cast)
    scene = {"scene": "T", "location": "room", "clips": clips, **scene_extra}
    scene_p = write(tmp_path, "scene.yaml", scene)
    chars, locs = hs.load_cast(cast_p)
    sc = hs.load_scene(scene_p, chars, locs)
    return [hs.build_clip(sc, c, chars) for c in sc.clips]


# ------------------------------------------------------------------ example scene


def test_example_builds_without_errors():
    for cid, res in build().items():
        assert res.errors == [], (cid, res.errors)


def test_sections_in_official_order():
    res = build()["C01"]
    names = re.findall(r"^(\w+):$", res.prompt, re.M)
    assert names == list(hs.SECTIONS)


def test_picture_labels_match_loaded_slots():
    for res in build().values():
        loaded = {int(p["prompt_label"].split()[1].rstrip(">")) for p in res.manifest["pictures"]}
        used = {int(n) for n in re.findall(r"<Picture (\d+)>", res.prompt)}
        assert used <= loaded


def test_fixed_slots_keep_cast_numbers():
    res = build()["C03"]  # C, D, F on screen, A and B loaded but absent
    slots = {p["what"].split(": ")[1]: p["extender_slot"] for p in res.manifest["pictures"]}
    assert slots["Sora"] == 3 and slots["Dohyun"] == 6 and slots["diner"] == 7
    assert "<Picture 3>" in res.prompt and "<Picture 1>" not in res.prompt  # A is loaded, not described (unused=omit)


def test_speaker_ids_follow_first_vocal_event():
    res = build()["C02"]
    assert res.manifest["speakers"] == {"S1": "Junho", "S2": "Minji"}
    assert "<Subject 2> (S1)" in res.prompt and "<Subject 1> (S2)" in res.prompt


def test_korean_only_inside_dialogue():
    for res in build().values():
        assert not hs._hangul_outside_dialogue(res.prompt)


def test_wide_six_person_shot_gets_costume_note():
    res = build()["C01"]
    assert any("identity will come from costume" in n for n in res.notes)


def test_define_absent_marks_offscreen_people():
    res = build("EXP_multicast.yaml", "EXP_cast_template.yaml")["X3c"]
    assert res.prompt.count("does not appear in this clip") == 4
    sd = hs.split_sections(res.prompt)["retention_analysis"]
    assert "<Subject 3>" not in sd  # absent people are not in retention_analysis


def test_load_clip_only_loads_on_screen_people():
    res = build("EXP_multicast.yaml", "EXP_cast_template.yaml")["X3a"]
    assert [p["extender_slot"] for p in res.manifest["pictures"]] == [1, 2]
    assert all(p["load_as"].startswith("local") for p in res.manifest["pictures"])


def test_compact_policy_renumbers_contiguously():
    res = build(override=hs.Policy(slots="compact", load="clip"))["C03"]
    labels = [int(p["prompt_label"].split()[1].rstrip(">")) for p in res.manifest["pictures"]]
    assert labels == list(range(1, len(labels) + 1))


def test_location_without_image_uses_plain_text():
    res = build("EXP_multicast.yaml", "EXP_cast_template.yaml")["X1"]
    assert "a plain photo studio" in res.prompt
    assert all("location" not in p["what"] for p in res.manifest["pictures"])


# ------------------------------------------------------------------ validation


def test_nine_pictures_fit_and_slots_stay_in_range(tmp_path):
    cast = small_cast(8)  # slots 1-8, room in slot 9
    clips = [{"id": "c1", "duration": 6, "shots": [{"framing": "wide", "cast": [f"P{i}" for i in range(8)]}]}]
    res = run_scene(tmp_path, cast, clips)
    assert res[0].errors == [] and len(res[0].manifest["pictures"]) == 9
    cast["characters"].append({"id": "P8", "name": "P8", "slot": 10, "look": "x", "short": "x"})
    with pytest.raises(hs.SceneError):
        run_scene(tmp_path, cast, clips)
    cast["characters"].pop()
    with pytest.raises(hs.SceneError):
        run_scene(tmp_path, cast, clips, group_plate={"image": "g.png", "slot": 10})


def test_slot_collision_is_an_error(tmp_path):
    cast = small_cast(2)
    cast["locations"][0]["slot"] = 1  # same slot as P0
    clips = [{"id": "c1", "duration": 6, "shots": [{"framing": "medium", "cast": ["P0", "P1"]}]}]
    res = run_scene(tmp_path, cast, clips)[0]
    assert any("slot 1 is used by both" in e for e in res.errors)


def test_more_than_three_voices_is_an_error(tmp_path):
    lines = [{"who": f"P{i}", "text": "hi", "lang": "English"} for i in range(4)]
    clips = [{"id": "c1", "duration": 12, "shots": [{"framing": "wide", "cast": [f"P{i}" for i in range(4)], "lines": lines}]}]
    res = run_scene(tmp_path, small_cast(4, voices=4), clips)[0]
    assert any("at most 3" in e for e in res.errors)
    assert any("speakers in one clip" in w for w in res.warnings)


def test_bad_timing_is_an_error(tmp_path):
    clips = [{"id": "c1", "duration": 6, "shots": [
        {"framing": "medium", "cast": ["P0"]},
        {"at": 4, "framing": "close-up", "cast": ["P0"]},
        {"at": 3, "framing": "close-up", "cast": ["P1"]},
    ]}]
    res = run_scene(tmp_path, small_cast(2), clips)[0]
    assert any("not after shot" in e for e in res.errors)
    clips = [{"id": "c1", "duration": 20, "shots": [{"framing": "medium", "cast": ["P0"]}]}]
    res = run_scene(tmp_path, small_cast(2), clips)[0]
    assert any("outside 4-15s" in e for e in res.errors)


def test_unknown_placeholder_and_offscreen_speaker(tmp_path):
    clips = [{"id": "c1", "duration": 6, "shots": [
        {"framing": "medium", "cast": ["P0"], "action": "{P1} waves",
         "lines": [{"who": "P1", "text": "hello", "lang": "English"}]}]}]
    res = run_scene(tmp_path, small_cast(2), clips)[0]
    assert any("not in the shot cast" in e for e in res.errors)
    clips[0]["shots"][0]["lines"][0]["offscreen"] = True
    res = run_scene(tmp_path, small_cast(2), clips)[0]
    assert res.errors == [] and "(S1) off-screen" in res.prompt


def test_crowded_medium_shot_warns(tmp_path):
    clips = [{"id": "c1", "duration": 6, "shots": [{"framing": "medium", "cast": ["P0", "P1", "P2", "P3"]}]}]
    res = run_scene(tmp_path, small_cast(4), clips)[0]
    assert any("identity-critical faces" in w for w in res.warnings)


def test_long_line_in_short_shot_warns(tmp_path):
    clips = [{"id": "c1", "duration": 4, "shots": [{"framing": "close-up", "cast": ["P0"], "lines": [
        {"who": "P0", "lang": "Korean", "text": "이 대사는 사 초 안에 도저히 다 말할 수 없을 만큼 아주 길고 긴 문장입니다 정말로요"}]}]}]
    res = run_scene(tmp_path, small_cast(1), clips)[0]
    assert any("needs about" in w for w in res.warnings)


# ------------------------------------------------------------------ LLM expansion


def test_compare_description_catches_broken_labels():
    draft = "Style.\n[Shot 1] <Subject 1> waves. <Subject 1> (S1) says, <d>[Korean] 안녕.</d>"
    good = draft.replace("waves.", "waves slowly with a warm smile under soft window light." * 30)
    assert hs.compare_description(draft, good) == []
    bad = good.replace("<Subject 1> waves", "<Subject 2> waves")
    assert any("labels changed" in p for p in hs.compare_description(draft, bad))
    assert any("dialogue" in p for p in hs.compare_description(draft, good.replace("안녕.", "안녕하세요.")))
    assert any("Korean" in p for p in hs.compare_description(draft, good + " 한국어"))


class _Mock(http.server.BaseHTTPRequestHandler):
    reply = ""
    calls = 0

    def log_message(self, *a):
        pass

    def do_POST(self):
        type(self).calls += 1
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
        out = json.dumps({"choices": [{"message": {"content": type(self).reply}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


@pytest.fixture
def mock_llm():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _Mock.calls = 0
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_llm_expansion_accepted(mock_llm):
    _, url = mock_llm
    res = build()["C01"]
    draft = hs.split_sections(res.prompt)["detailed_description"]
    extra = " The warm light glints off the chrome counter and steam rises from the bowls." * 12
    _Mock.reply = "<think>plan</think>" + draft.replace("[Shot 2]", extra.strip() + "\n[Shot 2]")
    hs.llm_expand(res, url, "GUIDE")
    assert "steam rises" in res.prompt
    assert any("expanded by the local LLM" in n for n in res.notes)
    assert list(hs.split_sections(res.prompt)) == list(hs.SECTIONS)


def test_llm_expansion_rejected_falls_back(mock_llm):
    _, url = mock_llm
    res = build()["C01"]
    before = res.prompt
    _Mock.reply = "She walks in and everyone looks at her."  # labels, shots and dialogue dropped
    hs.llm_expand(res, url, "GUIDE")
    assert res.prompt == before
    assert _Mock.calls == 2
    assert any("broke the rules twice" in w for w in res.warnings)


def test_cli_build_writes_files(tmp_path):
    rc = hs.main(["build", str(EX / "S01_diner.yaml"), "--cast", str(EX / "cast.yaml"), "--out", str(tmp_path)])
    assert rc == 0
    for cid in ("C01", "C02", "C03"):
        assert (tmp_path / "S01" / f"{cid}.prompt.txt").read_text(encoding="utf-8").startswith("subject_definitions:")
        assert json.loads((tmp_path / "S01" / f"{cid}.refs.json").read_text(encoding="utf-8"))["clip"] == cid
    assert (tmp_path / "S01" / "report.md").exists()
    rc = hs.main(["check", str(EX / "S01_diner.yaml"), "--cast", str(EX / "cast.yaml"), "--check-files"])
    assert rc == 1  # example asset files do not exist in the repo

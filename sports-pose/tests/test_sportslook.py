"""sportslook: panel text -> asset, camera, filled prompt, switch and log. Standard library only."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import sportslook as sl  # noqa: E402

LIB = sl.Library(HERE / "library")

FOUND = {
    "태권도 선수가 상대 몸통에 돌려차기를 찬다": "TAEKWONDO_ROUNDHOUSE_KICK",
    "민수가 뒤차기로 상대를 공격한다, 측면 샷": "TAEKWONDO_BACK_KICK",
    "배구 스파이크 타점, 네트 위": "VOLLEYBALL_SPIKE_CONTACT",
    "투수가 공을 던지는 순간": "BASEBALL_PITCH_RELEASE",
    "그녀가 자유형으로 숨을 쉰다": "SWIMMING_FREESTYLE_BREATH",
    "평영으로 헤엄치다 숨을 쉰다": "SWIMMING_BREASTSTROKE_BREATH",
    "유도 업어치기": "JUDO_SEOI_NAGE",
    "업어치기 한판, 상대가 매트에 떨어진다": "JUDO_IPPON_LANDING",
    "레프트 훅이 턱에 꽂힌다": "BOXING_LEAD_HOOK",
    "권투 선수의 잽": "BOXING_JAB",
    "레슬링 양다리 태클": "WRESTLING_DOUBLE_LEG",
    "낚시꾼이 고기를 걸고 버틴다": "FISHING_FIGHT",
    "낚싯대를 던진다": "FISHING_CAST_RELEASE",
    "테니스 서브": "TENNIS_SERVE_CONTACT",
    "배드민턴 점프 스매시": "BADMINTON_JUMP_SMASH",
    "덩크슛": "BASKETBALL_DUNK",
    "타자가 공을 친다": "BASEBALL_BAT_CONTACT",
    "a goalkeeper dives to save": "SOCCER_GOALKEEPER_DIVE",
    "he throws a roundhouse kick": "TAEKWONDO_ROUNDHOUSE_KICK",
}
# everyday and film-set sentences that must not pull in a sports pose
NOTHING = ["민지가 카페에서 커피를 마신다", "Two people cross the road at night", "토스트를 먹는다", "배구 경기장 전경",
           "공원에서 공을 던지며 논다", "배우 블로킹을 맞춘다", "다들 파이팅!", "캐스팅 회의 장면", "그가 양다리를 걸쳤다",
           "기본 자세로 서 있다", "fish on the table", "wide shot of the front set", "ready position for the next shot",
           "the pitch meeting", "그녀가 훅 들어온다", "아이가 공 놓는 순간", "잽싸게 달려간다", "다이빙대 위에 선다"]


@pytest.mark.parametrize("text,code", FOUND.items())
def test_panel_text_finds_the_asset(text, code):
    got = LIB.match(text)
    assert got and got[0][1] == code, got


@pytest.mark.parametrize("text", NOTHING)
def test_other_scenes_find_nothing(text):
    assert LIB.match(text) == []


def test_every_asset_has_agent_data():
    for code in LIB.rows:
        a = LIB.agent(code)
        assert a["prompt"].startswith("{SUBJECT}") and "{SETTING}" in a["prompt"] and a["block"] and a["negative"]
        for cam in a["cameras"]:
            assert (Path(a["_dir"]) / cam["openpose_png"]).is_file()
        for p in a["partners"]:
            assert f"{{PARTNER_{p['id']}}}" in a["prompt"]


def test_pack_fills_the_prompt_and_picks_the_camera():
    p = LIB.pack("태권도 돌려차기, 로우앵글 와이드", subject="a young man in a white dobok",
                 setting="Olympic arena, blue mat.", partners={"B": "a tall woman with a ponytail"})
    assert p["code"] == "TAEKWONDO_ROUNDHOUSE_KICK" and p["camera"] == "low_cinema" and p["unfilled"] == []
    assert p["prompt"].startswith("a young man in a white dobok, ") and "a tall woman with a ponytail" in p["prompt"]
    assert Path(p["openpose_png"]).is_file() and p["size"] == [1344, 768]
    assert "#TAEKWONDO_ROUNDHOUSE_KICK" in p["guide"] and "word for word" in p["guide"]
    assert LIB.pack("배구 스파이크")["camera"] == LIB.agent(LIB.pack("배구 스파이크")["code"])["cameras"][0]["name"]
    assert LIB.pack("투수가 공을 던지는 순간")["motion"].startswith("{SUBJECT}, in one continuous movement.")
    assert LIB.pack("카페에서 대화") is None


def test_hook_switch_and_log(tmp_path):
    h = sl.Hook(tmp_path, library=HERE / "library")
    assert h.mode("prompt") == "off" and h.lookup("prompt", "유도 업어치기") is None     # no switch file: off
    (tmp_path / "sports_modes.json").write_text('{"default": "observe"}', encoding="utf-8")
    assert h.lookup("prompt", "유도 업어치기", panel="p01") is None                       # observe: log only
    (tmp_path / "sports_modes.json").write_text('{"default": "off", "prompt": "act"}', encoding="utf-8")
    assert h.lookup("prompt", "유도 업어치기", panel="p02")["code"] == "JUDO_SEOI_NAGE"
    assert h.mode("pose") == "off"
    (tmp_path / "sports_modes.json").write_text("{broken", encoding="utf-8")
    assert h.mode("prompt") == "off"
    rows = [json.loads(x) for x in h.log_path.read_text(encoding="utf-8").splitlines()]
    assert [r["mode"] for r in rows] == ["observe", "act"] and all("text" not in r for r in rows)
    assert "| prompt | 2 | 2 | 0 |" in sl.report(h.log_path)
    bad = sl.Hook(tmp_path, library=tmp_path / "missing")
    (tmp_path / "sports_modes.json").write_text('{"default": "act"}', encoding="utf-8")
    assert bad.lookup("prompt", "유도 업어치기") is None                                   # errors never reach the caller


def test_copied_module_reads_the_library_from_the_env(tmp_path, monkeypatch):
    shutil.copy(HERE / "sportslook.py", tmp_path / "sportslook.py")
    (tmp_path / "manifest.json").write_text(json.dumps(
        {"panels": [{"id": 1, "description": "유도 업어치기"}, {"id": 2, "description": "카페에서 대화"},
                    {"id": 3, "visual": "배구 스파이크 타점"}]}, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "SPORTS_POSE_LIBRARY": str(HERE / "library"), "PYTHONIOENCODING": "utf-8"}
    out = subprocess.run([sys.executable, str(tmp_path / "sportslook.py"), "scan", str(tmp_path / "manifest.json")],
                         capture_output=True, text=True, encoding="utf-8", env=env, cwd=tmp_path)
    assert out.returncode == 0, out.stderr
    assert "JUDO_SEOI_NAGE" in out.stdout and "panels 3, with a sports asset 2" in out.stdout
    out = subprocess.run([sys.executable, str(tmp_path / "sportslook.py"), "scan", str(tmp_path / "manifest.json"),
                          "--keys", "visual"], capture_output=True, text=True, encoding="utf-8", env=env, cwd=tmp_path)
    assert "panels 1, with a sports asset 1" in out.stdout and "VOLLEYBALL_SPIKE_CONTACT" in out.stdout

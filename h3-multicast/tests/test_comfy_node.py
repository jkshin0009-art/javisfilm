import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import h3_scene as hs  # noqa: E402


def _node_module():
    spec = importlib.util.spec_from_file_location("h3_scene_node", ROOT / "comfyui_node" / "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    assert hs.main(["build", str(ROOT / "examples" / "EXP_multicast.yaml"), "--cast",
                    str(ROOT / "examples" / "EXP_cast_template.yaml"), "--out", str(out)]) == 0
    return out / "EXP"


def test_pack_has_every_prompt_in_order(built):
    node = _node_module()
    pack, settings = node.load_scene_pack(str(built))
    assert pack["type"] == "H3_PROMPT_PACK" and pack["count"] == 8
    assert pack["prompts"][0] == (built / "X1.prompt.txt").read_text(encoding="utf-8")
    assert settings.splitlines()[0].startswith("card 1: X1  6s  seed 1001")


def test_pack_subset_follows_the_given_order(built):
    node = _node_module()
    pack, settings = node.load_scene_pack(f'"{built}"', "X5b, X5a")
    assert pack["count"] == 2
    assert "<Video 1>" in pack["prompts"][0] and "<Video 1>" not in pack["prompts"][1]
    assert settings.splitlines()[1].startswith("card 2: X5a")
    with pytest.raises(ValueError):
        node.load_scene_pack(str(built), "X9")


def test_pack_refuses_clips_with_errors(built, tmp_path):
    node = _node_module()
    bad = tmp_path / "EXP"
    bad.mkdir()
    order = json.loads((built / "order.json").read_text(encoding="utf-8"))
    order["clips"][0]["ok"] = False
    (bad / "order.json").write_text(json.dumps(order), encoding="utf-8")
    for p in built.glob("*.prompt.txt"):
        (bad / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="have errors"):
        node.load_scene_pack(str(bad))
    pack, _ = node.load_scene_pack(str(bad), "X2")
    assert pack["count"] == 1


def test_is_changed_tracks_prompt_edits(built):
    node = _node_module().H3ScenePromptPack
    before = node.IS_CHANGED(str(built))
    p = built / "X1.prompt.txt"
    text = p.read_text(encoding="utf-8")
    p.write_text(text + " ", encoding="utf-8")
    try:
        assert node.IS_CHANGED(str(built)) != before
    finally:
        p.write_text(text, encoding="utf-8")


def test_signature_matches_the_extender(built):
    ext = os.environ.get("EXTENDER_DIR")
    if not ext or not (Path(ext) / "prompt_bridge.py").exists():
        pytest.skip("set EXTENDER_DIR to a ComfyUI_MiniMax_H3_Extender folder")
    spec = importlib.util.spec_from_file_location("ext_prompt_bridge", Path(ext) / "prompt_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    pack, _ = _node_module().load_scene_pack(str(built))
    assert bridge.PROMPT_PACK_TYPE == pack["type"]
    assert bridge._prompt_pack_signature(pack["prompts"]) == pack["signature"]
    assert bridge._pack_prompts(pack["prompts"]) == pack["prompts"]

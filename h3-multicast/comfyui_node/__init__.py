"""ComfyUI node: feed h3_scene.py prompts straight into the MiniMax H3 Extender.

Put this folder in ComfyUI/custom_nodes (copy it, or link it so a git pull
updates it), restart ComfyUI, then connect

    H3 Scene Prompt Pack  --prompt_pack-->  MiniMax H3 Extender (prompt_pack input)

The Extender creates one clip card per prompt and fills in the prompts. It does
not take durations or seeds from a pack, so the node also returns
`card_settings`: the duration, seed and Motion Context for each card, to set by
hand (connect it to any text preview node).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACK_TYPE = "H3_PROMPT_PACK"  # socket type of the Extender's own Prompt Pack Bridge


def _signature(prompts: list[str]) -> str:
    # same recipe as the Extender's prompt_bridge._prompt_pack_signature
    raw = json.dumps(list(prompts), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _folder(scene_folder: str) -> Path:
    return Path(str(scene_folder).strip().strip('"'))


def load_scene_pack(scene_folder: str, clips: str = "") -> tuple[dict, str]:
    folder = _folder(scene_folder)
    order_file = folder / "order.json"
    if not order_file.exists():
        raise ValueError(f"H3 Scene Prompt Pack: {order_file} not found. Run h3_scene.py build first.")
    data = json.loads(order_file.read_text(encoding="utf-8"))
    entries = list(data.get("clips") or [])
    wanted = [c.strip() for c in str(clips or "").replace(";", ",").split(",") if c.strip()]
    if wanted:
        by_id = {e["clip"]: e for e in entries}
        missing = [c for c in wanted if c not in by_id]
        if missing:
            raise ValueError(f"H3 Scene Prompt Pack: unknown clip id(s) {missing}; known: {list(by_id)}")
        entries = [by_id[c] for c in wanted]
    broken = [e["clip"] for e in entries if not e.get("ok", True)]
    if broken:
        raise ValueError(f"H3 Scene Prompt Pack: {broken} have errors in report.md; fix the scene file and rebuild.")
    if not entries:
        raise ValueError("H3 Scene Prompt Pack: no clips selected.")
    prompts = [(folder / e["prompt_file"]).read_text(encoding="utf-8") for e in entries]
    pack = {
        "type": PACK_TYPE,
        "version": 1,
        "source": f"h3_scene {data.get('scene', '')}".strip(),
        "count": len(prompts),
        "prompts": prompts,
        "signature": _signature(prompts),
    }
    lines = []
    for i, e in enumerate(entries, start=1):
        seed = e.get("seed")
        lines.append(f"card {i}: {e['clip']}  {float(e['duration_s']):g}s  seed {seed if seed is not None else 'any'}  "
                     f"Motion Context {e.get('motion_context', 'OFF')}  refs: {e['clip']}.refs.txt")
    return pack, "\n".join(lines)


class H3ScenePromptPack:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_folder": ("STRING", {
                    "default": "",
                    "tooltip": "Folder written by h3_scene.py build, e.g. ...\\h3-multicast\\out\\S01 (it has order.json).",
                }),
            },
            "optional": {
                "clips": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated clip ids in card order, e.g. X1,X2,X3b. Empty = every clip in scene order.",
                }),
            },
        }

    RETURN_TYPES = (PACK_TYPE, "STRING", "INT")
    RETURN_NAMES = ("prompt_pack", "card_settings", "count")
    FUNCTION = "load"
    CATEGORY = "MiniMax H3"

    @classmethod
    def IS_CHANGED(cls, scene_folder, clips=""):
        # re-read when the generator rewrites the folder
        folder = _folder(scene_folder)
        h = hashlib.sha256(str(clips).encode("utf-8"))
        for p in sorted(folder.glob("*.prompt.txt")) + [folder / "order.json"]:
            if p.exists():
                h.update(p.name.encode("utf-8"))
                h.update(p.read_bytes())
        return h.hexdigest()

    def load(self, scene_folder, clips=""):
        pack, settings = load_scene_pack(scene_folder, clips)
        return (pack, settings, int(pack["count"]))


NODE_CLASS_MAPPINGS = {"H3ScenePromptPack": H3ScenePromptPack}
NODE_DISPLAY_NAME_MAPPINGS = {"H3ScenePromptPack": "H3 Scene Prompt Pack (javisfilm)"}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

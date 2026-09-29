#!/usr/bin/env python3
"""Diagnose and preview ComfyUI-BubbleText on your own images, without ComfyUI.

It imports the node's own code from your ComfyUI install, so what you see is
what the node does.

    python bubble_doctor.py fonts    --node-dir <ComfyUI>/custom_nodes/ComfyUI-BubbleText --text "대사"
    python bubble_doctor.py workflow --node-dir ... <workflow.json or folder> ...
    python bubble_doctor.py scan     --node-dir ... --in <images> --out out/scan
    python bubble_doctor.py render   --node-dir ... --in <images> --out out/render --text "대사" --font Jua-Regular.ttf

Problems it looks for:
- Korean (or any) text in a font that has no glyphs for it -> boxes instead of letters.
- Dark areas (hair, clothes, night sky) taken as "black bubbles": the node
  paints them flat and writes white text there, and a single line of text gets
  split between the real bubble and the dark area. The README calls black
  bubbles a fallback, but find_bubbles() always adds them; --fix-dark (and
  patch_bubbletext.py) use them only when no white bubble is found.
- The node's "bubble mask" output wired to a preview/save node: it is an empty
  (black) mask whenever no bubble is found.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path

import numpy as np

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
HANGUL = range(0xAC00, 0xD7A4)
SETTING_NAMES = ["enabled", "text", "font", "uppercase", "max_font_size", "reading_order",
                 "erase_ai_text", "text_color", "margin", "white_threshold", "prompt_style"]
NODE_TYPES = {"SpeechBubblePrompt", "SpeechBubbleRender", "SpeechBubbleTextAuto"}
IMAGE_SINKS = {"PreviewImage", "SaveImage", "Image Save", "SaveImageWebsocket"}


# --------------------------------------------------------------------------- loading the node


class _StubTensor(np.ndarray):
    def cpu(self):
        return self

    def numpy(self):
        return np.asarray(self)


def _install_torch_stub() -> None:
    """render_bubbles only needs zeros/from_numpy/stack; enough to run it without torch."""
    t = types.ModuleType("torch")
    t.__stub__ = True
    t.float32 = np.float32
    t.zeros = lambda shape, dtype=None: np.zeros(shape, np.float32).view(_StubTensor)
    t.from_numpy = lambda a: np.asarray(a).view(_StubTensor)
    t.stack = lambda xs: np.stack([np.asarray(x) for x in xs]).view(_StubTensor)
    sys.modules["torch"] = t


def load_node(node_dir: str | Path):
    node_dir = Path(node_dir)
    if not (node_dir / "bubble_text.py").exists():
        raise SystemExit(f"bubble_text.py not found in {node_dir}")
    try:
        import torch  # noqa: F401
    except ImportError:
        _install_torch_stub()
    import importlib.util

    # a module per folder, so an installed copy and a patched copy can be compared side by side
    name = f"bubble_text_{abs(hash(str(node_dir.resolve())))}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, node_dir / "bubble_text.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def to_tensor(rgb: np.ndarray):
    import torch

    arr = (rgb.astype(np.float32) / 255.0)[None]
    return arr.view(_StubTensor) if getattr(torch, "__stub__", False) else torch.from_numpy(arr)


def from_tensor(t) -> np.ndarray:
    return (np.asarray(t.cpu().numpy()) * 255.0).round().clip(0, 255).astype(np.uint8)


def read_rgb(path: Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"))


def save_rgb(rgb: np.ndarray, path: Path) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(path)


def get_text(args) -> str:
    """--text-file wins over --text; the file may have a BOM (PowerShell 5.1 writes one)."""
    if getattr(args, "text_file", None):
        return Path(args.text_file).read_text(encoding="utf-8-sig").strip()
    return getattr(args, "text", "") or ""


def images_in(p: Path) -> list[Path]:
    if p.is_file():
        return [p]
    return sorted(x for x in p.iterdir() if x.suffix.lower() in IMAGE_EXT)


# --------------------------------------------------------------------------- fonts


def font_cover(bt, path: str) -> tuple[int, set[int] | None]:
    cps = bt.font_codepoints(path)
    if cps is None:
        return -1, None
    return sum(1 for c in HANGUL if c in cps), cps


def missing_chars(text: str, cps: set[int] | None, bt) -> list[str]:
    if cps is None:
        return []
    fallback = set()
    for fp in bt.FALLBACK_FONTS:
        fc = bt.font_codepoints(fp) if Path(fp).exists() else None
        if fc:
            fallback |= fc
    return sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cps and ord(ch) not in fallback})


def cmd_fonts(args) -> int:
    bt = load_node(args.node_dir)
    args.text = get_text(args)
    fonts = bt.available_fonts()
    if not fonts:
        print("the node sees no fonts at all")
        return 1
    print(f"fonts the node offers ({len(fonts)}):")
    bad = 0
    for name, path in fonts.items():
        n, cps = font_cover(bt, path)
        cover = "fontTools missing, cannot check" if n < 0 else f"Hangul {n}/{len(HANGUL)}"
        line = f"  {name:32s} {cover}"
        if args.text and cps is not None:
            miss = missing_chars(args.text, cps, bt)
            line += "  OK for the text" if not miss else f"  MISSING {len(miss)}: {''.join(miss[:20])}"
            bad += bool(miss)
        print(line)
    if args.text and bad == len(fonts):
        print("\nno font can draw this text: copy a Korean .ttf/.otf into " + str(Path(args.node_dir) / "fonts"))
        return 1
    return 0


# --------------------------------------------------------------------------- workflows


def _ui_nodes(data: dict):
    """(node, links_by_id) for UI-format workflows, including nodes inside subgraphs."""
    links = {}
    for ln in data.get("links") or []:
        if isinstance(ln, list) and len(ln) >= 5:
            links[ln[0]] = {"from": ln[1], "from_slot": ln[2], "to": ln[3], "to_slot": ln[4]}
        elif isinstance(ln, dict):
            links[ln.get("id")] = {"from": ln.get("origin_id"), "from_slot": ln.get("origin_slot"),
                                   "to": ln.get("target_id"), "to_slot": ln.get("target_slot")}
    nodes = list(data.get("nodes") or [])
    for sg in (data.get("definitions") or {}).get("subgraphs") or []:
        sub_nodes, sub_links = _ui_nodes(sg)
        nodes += sub_nodes
        links.update(sub_links)
    return nodes, links


def analyse_workflow(path: Path, bt=None) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: cannot read JSON ({exc})"]
    out: list[str] = []
    fonts = bt.available_fonts() if bt else {}
    if isinstance(data, dict) and "nodes" in data:
        nodes, links = _ui_nodes(data)
        by_id = {n.get("id"): n for n in nodes}
        for n in nodes:
            if n.get("type") not in NODE_TYPES:
                continue
            head = f"{path.name}: node {n.get('id')} {n.get('type')}"
            vals = n.get("widgets_values") or []
            if isinstance(vals, dict):
                vals = list(vals.values())
            settings = dict(zip(SETTING_NAMES, vals)) if vals else {}
            if settings:
                out.append(head + ": " + ", ".join(f"{k}={v!r}" for k, v in settings.items()))
            else:
                out.append(head + " (settings come from the Prompt node)")
            text, font = str(settings.get("text", "")), settings.get("font")
            if settings and not settings.get("enabled", True):
                out.append(f"  ! {head}: enabled is OFF, the node passes the image through untouched")
            if text and any(0xAC00 <= ord(c) <= 0xD7A3 for c in text) and bt is not None:
                path_font = fonts.get(font)
                if not path_font:
                    out.append(f"  ! font {font!r} is not installed on this machine")
                else:
                    n_h, _ = font_cover(bt, path_font)
                    if n_h == 0:
                        out.append(f"  ! Korean text with font {font!r}, which has no Hangul glyphs: letters become boxes")
            for o in n.get("outputs") or []:
                if o.get("type") != "MASK":
                    continue
                for lid in o.get("links") or []:
                    tgt = by_id.get((links.get(lid) or {}).get("to"))
                    ttype = (tgt or {}).get("type", "?")
                    out.append(f"  - bubble mask -> node {(tgt or {}).get('id')} {ttype}")
                    if ttype in IMAGE_SINKS or ttype in ("MaskToImage", "MaskPreview", "MaskPreview+"):
                        out.append("  ! the bubble mask is shown/saved as an image: it is black wherever no bubble "
                                   "was found. Connect the IMAGE output (first one) to the preview/save node")
    elif isinstance(data, dict):  # API format
        for nid, n in data.items():
            if isinstance(n, dict) and n.get("class_type") in NODE_TYPES:
                out.append(f"{path.name}: node {nid} {n['class_type']}: " + json.dumps(n.get("inputs", {}), ensure_ascii=False)[:400])
    return out


def cmd_workflow(args) -> int:
    bt = load_node(args.node_dir) if args.node_dir else None
    files: list[Path] = []
    for p in args.paths:
        p = Path(p)
        files += [p] if p.is_file() else sorted(p.rglob("*.json"))
    hits = 0
    for f in files:
        lines = analyse_workflow(f, bt)
        if lines:
            hits += 1
            print("\n".join(lines))
    if not hits:
        print(f"no BubbleText nodes in {len(files)} JSON file(s)")
    return 0


def fix_workflow(src: Path, dst: Path, font: str | None, max_size: int | None, margin: float | None,
                 uppercase: bool | None) -> list[str]:
    """Write a copy of a UI workflow with new BubbleText settings. The original is never touched."""
    data = json.loads(src.read_text(encoding="utf-8"))
    if not (isinstance(data, dict) and "nodes" in data):
        raise SystemExit(f"{src.name}: only UI-format workflows (saved from the ComfyUI menu) are supported")
    nodes, _ = _ui_nodes(data)
    changed = []
    index = {name: i for i, name in enumerate(SETTING_NAMES)}
    for n in nodes:
        vals = n.get("widgets_values")
        if n.get("type") not in NODE_TYPES or not isinstance(vals, list) or len(vals) < 10:
            continue
        before = list(vals)
        for key, value in (("font", font), ("max_font_size", max_size), ("margin", margin), ("uppercase", uppercase)):
            if value is not None:
                vals[index[key]] = value
        if vals != before:
            changed.append(f"node {n.get('id')} {n['type']}: " + ", ".join(
                f"{k} {before[index[k]]!r} -> {vals[index[k]]!r}" for k in ("font", "max_font_size", "margin", "uppercase")
                if before[index[k]] != vals[index[k]]))
    if dst.resolve() == src.resolve():
        raise SystemExit("refusing to overwrite the original workflow; give a different output path")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def cmd_fix_workflow(args) -> int:
    if args.max_size is not None and not 10 <= args.max_size <= 300:
        print("max font size must be 10-300 (the node's own limits)")
        return 1
    changed = fix_workflow(Path(args.src), Path(args.dst), args.font, args.max_size, args.margin,
                           False if args.no_uppercase else None)
    print("\n".join(changed) if changed else "no BubbleText node settings changed")
    print(f"wrote {args.dst} (original untouched). Open it in ComfyUI to use it.")
    return 0


# --------------------------------------------------------------------------- scan / render


def dark_fallback(bt):
    """find_bubbles as the README describes it: black bubbles only when there is no white one."""
    orig = bt.find_bubbles

    def find(rgb, threshold):
        found = orig(rgb, threshold)
        white = [b for b in found if not b["dark"]]
        return white if white else found

    return find


def fill_order(bt, bubbles, n_texts, img_h, order):
    """Which bubbles the node would write into, in order (mirrors render_bubbles)."""
    lettered = [b for b in bubbles if b["letters"] >= 4]
    if n_texts == 1 and len(lettered) > 1:
        return bt.reading_order(lettered[:4], img_h, order)
    return bt.reading_order(bubbles[:n_texts], img_h, order)


def overlay(rgb: np.ndarray, bubbles, chosen) -> np.ndarray:
    """Outline every detected bubble (green white, red black) and number the ones that get text."""
    from PIL import Image, ImageDraw
    from scipy import ndimage

    arr = rgb.copy()
    marks = []
    for b in bubbles:
        ox, oy = b["offset"]
        edge = b["filled"] & ~ndimage.binary_erosion(b["filled"], iterations=3)
        ys, xs = np.nonzero(edge)
        color = (230, 40, 40) if b["dark"] else (40, 200, 60)
        arr[ys + oy, xs + ox] = color
        for k, c in enumerate(chosen, start=1):
            if c is b:
                marks.append((b["center"], color, k))
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    for (cx, cy), color, k in marks:
        draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=color)
        draw.text((cx - 5, cy - 8), str(k), fill=(255, 255, 255))
    return np.asarray(img)


def describe(bubbles) -> str:
    parts = []
    for b in bubbles:
        kind = "BLACK" if b["dark"] else "white"
        parts.append(f"{kind}(area {b['area']}, letters {b['letters']}, paper {b['paper']:.0f})")
    return ", ".join(parts) or "none"


def cmd_scan(args) -> int:
    bt = load_node(args.node_dir)
    args.text = get_text(args)
    out = Path(args.out)
    n_texts = max(1, len(bt.split_texts(args.text))) if args.text else 1
    problems = 0
    for p in images_in(Path(args.inp)):
        rgb = read_rgb(p)
        bubbles = bt.find_bubbles(rgb, args.threshold)
        chosen = fill_order(bt, bubbles, n_texts, rgb.shape[0], bt.READING_LTR)
        white = [b for b in bubbles if not b["dark"]]
        dark = [b for b in bubbles if b["dark"]]
        notes = []
        if not bubbles:
            notes.append("no bubble found: the node leaves this image as it is (lower --threshold if the bubble is greyish)")
        if white and dark:
            notes.append(f"{len(dark)} dark area(s) taken as black bubbles next to a white bubble: likely hair/clothes; "
                         "patch_bubbletext.py fixes this (render shows it as 'fixed')")
        if any(b["dark"] for b in chosen):
            notes.append("text would be written into a dark area")
        if len(chosen) > n_texts:
            notes.append(f"one text will be split across {len(chosen)} bubbles")
        problems += bool(notes)
        save_rgb(overlay(rgb, bubbles, chosen), out / f"{p.stem}__scan.png")
        print(f"{p.name}: {len(bubbles)} bubble(s): {describe(bubbles)}")
        for n in notes:
            print(f"   ! {n}")
    print(f"\noverlays in {out} (green = white bubble, red = black bubble, number = fill order)")
    return 1 if problems else 0


def auto_max_size(h: int, w: int) -> int:
    return int(max(64, min(300, round(0.12 * min(h, w)))))


def render_one(bt, rgb, text, font, max_size, margin, threshold, fix_dark, uppercase):
    cfg = dict(activado=True, texto=text, fuente=font, mayusculas=uppercase, tamano_maximo=int(max_size),
               orden_lectura=bt.READING_LTR, borrar_texto_ia=True, color_texto="auto", margen=float(margin),
               umbral_blanco=int(threshold))
    orig = bt.find_bubbles
    if fix_dark:
        bt.find_bubbles = dark_fallback(bt)
    try:
        img, mask = bt.render_bubbles(to_tensor(rgb), cfg)
    finally:
        bt.find_bubbles = orig
    return from_tensor(img[0]), np.asarray(mask[0].cpu().numpy())


def areas(rgb: np.ndarray, mask: np.ndarray) -> str:
    """How many areas received text, and how many of them were dark."""
    from scipy import ndimage

    labels, n = ndimage.label(mask > 0)
    if n == 0:
        return "no text written (no bubble found)"
    lum = rgb.mean(axis=2)
    dark = sum(1 for k in range(1, n + 1) if np.median(lum[labels == k]) < 128)
    return f"text in {n} area(s)" + (f", {dark} of them dark" if dark else "")


def cmd_render(args) -> int:
    bt = load_node(args.node_dir)
    args.text = get_text(args)
    if not args.text:
        print("give the bubble text with --text or --text-file")
        return 1
    fonts = bt.available_fonts()
    if args.font not in fonts:
        print(f"font {args.font!r} is not one the node offers: {', '.join(fonts)}")
        return 1
    miss = missing_chars(args.text, bt.font_codepoints(fonts[args.font]), bt)
    if miss:
        print(f"warning: {args.font} has no glyphs for {''.join(miss[:20])}")
    out = Path(args.out)
    for p in images_in(Path(args.inp)):
        rgb = read_rgb(p)
        h, w = rgb.shape[:2]
        size = auto_max_size(h, w) if args.max_size == "auto" else int(args.max_size)
        as_is, m1 = render_one(bt, rgb, args.text, args.current_font or args.font, args.current_max_size,
                               args.current_margin, args.threshold, False, args.uppercase)
        fixed, m2 = render_one(bt, rgb, args.text, args.font, size, args.margin, args.threshold, True, args.uppercase)
        save_rgb(as_is, out / f"{p.stem}__1_as_is.png")
        save_rgb(fixed, out / f"{p.stem}__2_fixed.png")
        strip = np.concatenate([rgb, as_is, fixed], axis=1)
        save_rgb(strip, out / f"{p.stem}__compare.png")
        print(f"{p.name}: as-is {areas(rgb, m1)} | fixed (max {size}, margin {args.margin}) {areas(rgb, m2)}")
    print(f"\nimages in {out}: __compare.png = original | as-is | fixed")
    return 0


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fonts", help="which fonts the node sees and whether they can draw the text")
    f.add_argument("--node-dir", required=True)
    f.add_argument("--text", default="")
    f.add_argument("--text-file", help="UTF-8 file with the bubble text (safer than --text on Windows PowerShell 5.1)")

    w = sub.add_parser("workflow", help="BubbleText settings and wiring in workflow JSON files")
    w.add_argument("--node-dir")
    w.add_argument("paths", nargs="+")

    s = sub.add_parser("scan", help="show which areas the node takes as bubbles")
    s.add_argument("--node-dir", required=True)
    s.add_argument("--in", dest="inp", required=True)
    s.add_argument("--out", default="out/scan")
    s.add_argument("--threshold", type=int, default=195)
    s.add_argument("--text", default="", help="the bubble text (blank line = next bubble), to predict splitting")
    s.add_argument("--text-file")

    r = sub.add_parser("render", help="write the text as the node would: as-is vs fixed")
    r.add_argument("--node-dir", required=True)
    r.add_argument("--in", dest="inp", required=True)
    r.add_argument("--out", default="out/render")
    r.add_argument("--text", default="")
    r.add_argument("--text-file")
    r.add_argument("--font", required=True, help="font for the fixed version (a Korean font for Korean text)")
    r.add_argument("--max-size", default="auto", help="max font size for the fixed version, or auto (12%% of the short side)")
    r.add_argument("--margin", type=float, default=0.12)
    r.add_argument("--threshold", type=int, default=195)
    r.add_argument("--uppercase", action="store_true")
    r.add_argument("--current-font", help="font your workflow uses now (default: same as --font)")
    r.add_argument("--current-max-size", type=int, default=64)
    r.add_argument("--current-margin", type=float, default=0.08)

    x = sub.add_parser("fix-workflow", help="copy a workflow with new BubbleText settings (original untouched)")
    x.add_argument("src")
    x.add_argument("dst")
    x.add_argument("--font")
    x.add_argument("--max-size", type=int)
    x.add_argument("--margin", type=float)
    x.add_argument("--no-uppercase", action="store_true")

    args = ap.parse_args(argv)
    return {"fonts": cmd_fonts, "workflow": cmd_workflow, "scan": cmd_scan, "render": cmd_render,
            "fix-workflow": cmd_fix_workflow}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

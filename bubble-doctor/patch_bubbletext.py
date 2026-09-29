#!/usr/bin/env python3
"""Make ComfyUI-BubbleText use black bubbles only as a fallback, as its README says.

find_bubbles() always adds dark flat areas that contain a few holes (hair,
clothes, a night sky with stars) as "black bubbles", even when a white bubble
was found. The node then paints them flat, writes white text into them, and
splits a single line of text between the real bubble and the dark area.
This changes one line so black bubbles are searched only when no white bubble
exists.

    python patch_bubbletext.py status --node-dir <ComfyUI>/custom_nodes/ComfyUI-BubbleText
    python patch_bubbletext.py apply  --node-dir ...
    python patch_bubbletext.py revert --node-dir ...

The original file is kept as bubble_text.py.orig. Revert before updating the
node with ComfyUI Manager or git pull, then apply again. Restart ComfyUI after
apply or revert.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ORIGINAL = "    dark = scan_bubbles(rgb, (mx <= 255 - white_threshold + 10) & flat, dark_paper=True)\n"
PATCHED = ("    # javisfilm bubble-doctor: black bubbles only as a fallback, as the README describes\n"
           "    dark = [] if white else scan_bubbles(rgb, (mx <= 255 - white_threshold + 10) & flat, dark_paper=True)\n")


def read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:  # keep \r\n as it is
        return fh.read()


def write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def eol(text: str, src: str) -> str:
    return text.replace("\n", "\r\n") if "\r\n" in src else text


def state(src: str) -> str:
    flat = src.replace("\r\n", "\n")
    if PATCHED in flat:
        return "patched"
    if flat.count(ORIGINAL) == 1:
        return "original"
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("status", "apply", "revert"))
    ap.add_argument("--node-dir", required=True)
    args = ap.parse_args(argv)

    target = Path(args.node_dir) / "bubble_text.py"
    backup = target.with_name("bubble_text.py.orig")
    if not target.exists():
        print(f"not found: {target}")
        return 2
    src = read(target)
    st = state(src)

    if args.command == "status":
        print(f"{target}: {st}" + (f" (backup {backup.name} present)" if backup.exists() else ""))
        return 0 if st != "unknown" else 1

    if args.command == "apply":
        if st == "patched":
            print("already patched")
            return 0
        if st == "unknown":
            print("this version of bubble_text.py does not contain the expected line; nothing changed. "
                  "Send the find_bubbles() function to the analyst.")
            return 1
        if not backup.exists():
            shutil.copyfile(target, backup)
        write(target, src.replace(eol(ORIGINAL, src), eol(PATCHED, src)))
        print(f"patched {target} (backup: {backup.name}). Restart ComfyUI.")
        return 0 if state(read(target)) == "patched" else 1

    # revert
    if backup.exists():
        shutil.copyfile(backup, target)
        backup.unlink()
        print(f"restored {target} from {backup.name}. Restart ComfyUI.")
        return 0
    if st == "patched":
        write(target, src.replace(eol(PATCHED, src), eol(ORIGINAL, src)))
        print(f"reverted {target} in place. Restart ComfyUI.")
        return 0
    print("nothing to revert")
    return 0


if __name__ == "__main__":
    sys.exit(main())

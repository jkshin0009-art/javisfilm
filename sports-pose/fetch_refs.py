"""fetch_refs: download reference photos for the pose assets from Wikimedia Commons.

Run it on a PC that can reach commons.wikimedia.org. For each asset it searches Commons with
the asset's `ref_query`, keeps only licences that allow use in a film production with credit
(public domain, CC0, CC BY, CC BY-SA; anything NC or ND is skipped), and saves

  refs/<sport>/<CODE>/<n>.<ext>   the image (1024 px wide thumbnail)
  refs/<sport>/<CODE>/refs.json   title, page, author, licence for every image
  refs/ATTRIBUTION.md             one credit line per image, ready to paste into the end credits

The photos are for looking at (a person, the prompt agent, or a pose detector checking a
generated image against a real one). The pose itself comes from the asset, not the photo.

  python fetch_refs.py                      all assets, 4 photos each
  python fetch_refs.py VOLLEYBALL_BLOCK -n 8
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sportspose as sp  # noqa: E402

API = "https://commons.wikimedia.org/w/api.php"
UA = "javisfilm-sports-pose/1.0 (reference photo collection for pose assets)"
FREE = re.compile(r"^(public domain|pd\b|cc0|cc[ -]by(-sa)?[ -]?\d)", re.I)


def licence_ok(name: str) -> bool:
    n = (name or "").strip()
    if not n or re.search(r"\bN[CD]\b|noncommercial|no ?deriv", n, re.I):
        return False
    return bool(FREE.match(n))


def _text(v: Optional[str]) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", v or ""))).strip()


def _get(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def search(query: str, limit: int) -> List[Dict]:
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
              "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": str(limit), "prop": "imageinfo",
              "iiprop": "url|extmetadata|mime", "iiurlwidth": "1024"}
    data = json.loads(_get(API + "?" + urllib.parse.urlencode(params)).decode("utf-8"))
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        lic = _text((meta.get("LicenseShortName") or {}).get("value"))
        out.append({"title": p.get("title", ""), "page": info.get("descriptionurl", ""),
                    "url": info.get("thumburl") or info.get("url", ""), "mime": info.get("mime", ""),
                    "author": _text((meta.get("Artist") or {}).get("value")) or "unknown",
                    "licence": lic, "licence_url": _text((meta.get("LicenseUrl") or {}).get("value")),
                    "free": licence_ok(lic)})
    return out


def fetch(asset: Dict, out: Path, n: int, pause: float = 1.0) -> List[Dict]:
    q = asset.get("ref_query") or " ".join([asset.get("sport", ""), asset.get("technique", "")]).replace("_", " ")
    found = [x for x in search(q, max(20, n * 5)) if x["free"] and x["url"]]
    folder = out / asset.get("sport", "misc") / asset["code"]
    folder.mkdir(parents=True, exist_ok=True)
    kept = []
    for i, x in enumerate(found[:n], 1):
        ext = {"image/png": ".png", "image/webp": ".webp"}.get(x["mime"], ".jpg")
        path = folder / f"{i}{ext}"
        path.write_bytes(_get(x["url"]))
        kept.append({**x, "file": str(path.relative_to(out)).replace("\\", "/")})
        time.sleep(pause)                          # be polite to the Commons servers
    (folder / "refs.json").write_text(json.dumps({"code": asset["code"], "query": q, "images": kept},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return kept


def write_attribution(out: Path) -> Path:
    lines = ["# Reference photo credits (Wikimedia Commons)", ""]
    for f in sorted(out.rglob("refs.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for x in d["images"]:
            lines.append(f"- {x['file']}: \"{x['title'].replace('File:', '')}\" by {x['author']}, "
                         f"{x['licence']} ({x['licence_url'] or 'see page'}), {x['page']}")
    p = out / "ATTRIBUTION.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="fetch_refs")
    ap.add_argument("codes", nargs="*")
    ap.add_argument("-n", type=int, default=4, help="photos per asset")
    ap.add_argument("--out", default=str(HERE / "refs"))
    ap.add_argument("--pause", type=float, default=1.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    assets = [sp.load_asset(c) for c in a.codes] if a.codes else [sp.load_asset(str(p)) for p in sp.asset_files()]
    total = 0
    for x in assets:
        try:
            kept = fetch(x, out, a.n, a.pause)
        except OSError as e:
            print(f"{x['code']:34s} failed: {e}")
            continue
        total += len(kept)
        print(f"{x['code']:34s} {len(kept)} photos")
    print(f"{total} photos -> {out}; credits: {write_attribution(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

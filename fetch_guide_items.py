"""
Download Coral Island item JSON from koenigderluegner/coral-island-guide
and resolve English display names via Localization/Game/en/Game.json.

Outputs (default base: data/guide-items/):
  items/ one JSON per item (same content as upstream database/items/)
  items_summary.json  full items.json array from the guide
  item_names_en.json  { "<item_id>": { "name", "description", "displayNameKey", ... } }
  Game_en.json        cached localization file (large)

Usage:
  python fetch_guide_items.py  python fetch_guide_items.py --out-dir ./my-data  python fetch_guide_items.py --max-items 50 # smoke test

Requirements: Python 3.6+ (stdlib only)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional, Tuple

REPO_RAW = (
    "https://raw.githubusercontent.com/koenigderluegner/coral-island-guide/main"
)
ITEMS_JSON = f"{REPO_RAW}/packages/guide/src/assets/live/database/items.json"
GAME_EN_JSON = (
    f"{REPO_RAW}/pak-assets/live/ProjectCoral/Content/Localization/Game/en/Game.json"
)


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "coralmuseum-fetch-guide-items/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def load_json_url(url: str) -> Any:
    return json.loads(fetch_url(url).decode("utf-8"))


def resolve_loc(game: dict, key: str) -> str:
    """Resolve a key like DT_InventoryItems.item_100001_name using Game.json."""
    if not key or "." not in key:
        return key
    ns, rest = key.split(".", 1)
    table = game.get(ns)
    if isinstance(table, dict) and rest in table:
        val = table[rest]
        return val if isinstance(val, str) else key
    return key


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_json(path: str, obj: Any, readable: bool = True) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        if readable:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def item_detail_url(item_id: str) -> str:
    safe = item_id.lower()
    return f"{REPO_RAW}/packages/guide/src/assets/live/database/items/{safe}.json"


def download_one_item(
    item_id: str, out_path: str
) -> Tuple[str, Optional[str]]:
    try:
        raw = fetch_url(item_detail_url(item_id))
    except urllib.error.HTTPError as e:
        return item_id, f"HTTP {e.code}"
    except Exception as e:
        return item_id, str(e)
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as e:
        return item_id, f"JSON: {e}"
    ensure_dir(os.path.dirname(out_path) or ".")
    with open(out_path, "wb") as f:
        f.write(raw)
    return item_id, None


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch guide item JSON + English names.")
    ap.add_argument(
        "--out-dir",
        default=os.path.join("data", "guide-items"),
        help="Output directory (default: data/guide-items)",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Parallel downloads for per-item JSON (default: 8)",
    )
    ap.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="If >0, only fetch this many items (for testing)",
    )
    ap.add_argument(
        "--skip-game-json",
        action="store_true",
        help="Do not re-download Game_en.json if it already exists",
    )
    args = ap.parse_args()

    base = os.path.abspath(args.out_dir)
    items_dir = os.path.join(base, "items")
    game_path = os.path.join(base, "Game_en.json")
    summary_path = os.path.join(base, "items_summary.json")
    names_path = os.path.join(base, "item_names_en.json")

    ensure_dir(items_dir)

    if args.skip_game_json and os.path.isfile(game_path):
        with open(game_path, "r", encoding="utf-8") as f:
            game = json.load(f)
    else:
        print("Downloading English localization (Game.json)…", flush=True)
        game_raw = fetch_url(GAME_EN_JSON)
        with open(game_path, "wb") as f:
            f.write(game_raw)
        game = json.loads(game_raw.decode("utf-8"))

    print("Downloading items summary…", flush=True)
    items = load_json_url(ITEMS_JSON)
    if not isinstance(items, list):
        print("Unexpected items.json shape", file=sys.stderr)
        return 1

    if args.max_items > 0:
        items = items[: args.max_items]

    write_json(summary_path, items)

    ids = [it["id"] for it in items if isinstance(it, dict) and "id" in it]

    print(f"Fetching {len(ids)} per-item JSON files into {items_dir} …", flush=True)
    errors: Dict[str, str] = {}
    futures = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for iid in ids:
            out_p = os.path.join(items_dir, f"{iid.lower()}.json")
            futures.append(ex.submit(download_one_item, iid, out_p))
        done = 0
        for fut in as_completed(futures):
            iid, err = fut.result()
            done += 1
            if err:
                errors[iid] = err
            if done % 200 == 0 or done == len(futures):
                print(f"  … {done}/{len(futures)}", flush=True)

    if errors:
        err_path = os.path.join(base, "download_errors.json")
        write_json(err_path, errors)
        print(f"Warning: {len(errors)} item downloads failed; see {err_path}", flush=True)

    names: Dict[str, Dict[str, Any]] = {}
    for it in items:
        if not isinstance(it, dict) or "id" not in it:
            continue
        iid = it["id"]
        dkey = it.get("displayName") or ""
        desc_key = it.get("description") or ""
        names[iid] = {
            "name": resolve_loc(game, dkey) if isinstance(dkey, str) else dkey,
            "description": resolve_loc(game, desc_key)
            if isinstance(desc_key, str)
            else desc_key,
            "displayNameKey": dkey,
            "descriptionKey": desc_key,
        }

    write_json(names_path, names)
    print(f"Wrote {names_path} ({len(names)} entries)", flush=True)
    print(f"Done. Output root: {base}", flush=True)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

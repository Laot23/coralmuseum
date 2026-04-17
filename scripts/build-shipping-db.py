"""
Build shipping-items.json for the web app.

Generates a JSON list of all shippable items (with quality variants) from the
guide data. The browser loads this and merges it with the save file's shipping
data so that items the player hasn't shipped yet still appear as "Not Shipped".

Usage:
    python scripts/build-shipping-db.py
"""

from __future__ import annotations

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT, "data", "guide-items")
OUT_PATH = os.path.join(ROOT, "web", "public", "data", "shipping-items.json")

EXCLUDE_CATEGORIES = {
    "Quest", "Test", "TBD", "None", "ItemUpgrade",
    "Wallpapers", "Window", "Floors",
}

QUALITY_SUFFIXES = {
    "bronze": "-a",
    "silver": "-b",
    "gold": "-c",
    "osmium": "-d",
}


def main() -> int:
    names_path = os.path.join(DATA_DIR, "item_names_en.json")
    summary_path = os.path.join(DATA_DIR, "items_summary.json")

    for p in (names_path, summary_path):
        if not os.path.exists(p):
            print(f"Missing: {p}\nRun fetch_guide_items.py first.", file=sys.stderr)
            return 1

    with open(names_path, "r", encoding="utf-8") as f:
        names = json.load(f)
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    result: list[dict] = []
    base_count = 0
    variant_count = 0

    for entry in summary:
        if not isinstance(entry, dict) or "id" not in entry:
            continue

        cat = entry.get("inventoryCategory", "")
        sell = entry.get("sellPrice", 0)

        if cat in EXCLUDE_CATEGORIES:
            continue
        # Skip unresolved hex-ID categories
        if len(cat) == 32 and all(c in "0123456789ABCDEFabcdef" for c in cat):
            continue
        if sell <= 0:
            continue

        iid = entry["id"]
        name_info = names.get(iid, {})
        name = name_info.get("name", iid) if isinstance(name_info, dict) else str(name_info)
        icon = entry.get("iconName", "")
        qualities = entry.get("qualities", {})

        base_count += 1
        result.append({
            "id": iid,
            "name": name,
            "category": cat,
            "iconName": icon,
            "sellPrice": sell,
        })

        for qual_name, suffix in QUALITY_SUFFIXES.items():
            if qual_name in qualities:
                q = qualities[qual_name]
                variant_count += 1
                result.append({
                    "id": f"{iid}{suffix}",
                    "name": name,
                    "category": cat,
                    "iconName": icon,
                    "sellPrice": q.get("sellPrice", sell),
                    "quality": qual_name,
                })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"Wrote {OUT_PATH}")
    print(f"  {base_count} base items + {variant_count} quality variants = {len(result)} total")
    print(f"  {size_kb:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

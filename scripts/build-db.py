"""
Build museum-items.json for the web app.

Merges item_names_en.json, items_summary.json, and per-item fish/bug/ocean
detail into a single compact JSON file consumed by the browser.

Usage:
    python scripts/build-db.py
"""

from __future__ import annotations

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT, "data", "guide-items")
OUT_PATH = os.path.join(ROOT, "web", "public", "data", "museum-items.json")


def _bools_to_list(obj: dict) -> list[str]:
    return [k for k, v in obj.items() if v]


def _compact_spawn(settings: list[dict]) -> list[dict]:
    out = []
    for s in settings:
        out.append({
            "location": s.get("spawnLocation", []),
            "time": _bools_to_list(s.get("spawnTime", {})),
            "season": _bools_to_list(s.get("spawnSeason", {})),
            "weather": _bools_to_list(s.get("spawnWeather", {})),
        })
    return out


def main() -> int:
    names_path = os.path.join(DATA_DIR, "item_names_en.json")
    summary_path = os.path.join(DATA_DIR, "items_summary.json")
    items_dir = os.path.join(DATA_DIR, "items")

    for p in (names_path, summary_path, items_dir):
        if not os.path.exists(p):
            print(f"Missing: {p}\nRun fetch_guide_items.py first.", file=sys.stderr)
            return 1

    with open(names_path, "r", encoding="utf-8") as f:
        names = json.load(f)
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    items_by_id: dict[str, dict] = {}
    for entry in summary:
        if not isinstance(entry, dict) or "id" not in entry:
            continue
        iid = entry["id"]
        name_info = names.get(iid, {})
        rec: dict = {
            "id": iid,
            "name": name_info.get("name", iid) if isinstance(name_info, dict) else str(name_info),
            "description": name_info.get("description", "") if isinstance(name_info, dict) else "",
            "category": entry.get("inventoryCategory", ""),
            "displayKey": entry.get("displayKey", ""),
            "sellPrice": entry.get("sellPrice", 0),
            "iconName": entry.get("iconName", ""),
            "tags": entry.get("tags", []),
        }
        items_by_id[iid] = rec

    fish_count = 0
    bug_count = 0
    ocean_count = 0
    for fname in os.listdir(items_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(items_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                detail = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        iid = detail.get("item", {}).get("id")
        if not iid or iid not in items_by_id:
            continue

        rec = items_by_id[iid]

        # Drop sources (coffers for artifacts, fossil nodes for fossils)
        chances = detail.get("chanceAsProcessResult", [])
        if chances:
            sources = []
            for entry in chances:
                inp = entry.get("input", {})
                src_id = inp.get("id", "")
                src_icon = inp.get("iconName", "")
                src_name_info = names.get(src_id, {})
                src_name = (src_name_info.get("name", src_id)
                            if isinstance(src_name_info, dict) else str(src_name_info))
                shop = entry.get("shop", {})
                for oc in entry.get("outputChanges", []):
                    chance = oc.get("chance", 0)
                    if chance > 0:
                        sources.append({
                            "sourceId": src_id,
                            "sourceName": src_name,
                            "sourceIcon": src_icon,
                            "chance": chance,
                            "shop": shop.get("displayName", ""),
                        })
            if sources:
                sources.sort(key=lambda s: -s["chance"])
                rec["sources"] = sources

        if "fish" in detail and detail["fish"]:
            fish = detail["fish"]
            rec["fish"] = {
                "rarity": fish.get("rarity", ""),
                "size": fish.get("fishSize", ""),
                "pattern": fish.get("pattern", ""),
                "difficulty": fish.get("difficulty", ""),
                "spawn": _compact_spawn(fish.get("spawnSettings", [])),
            }
            fish_count += 1

        if "insect" in detail and detail["insect"]:
            bug = detail["insect"]
            rec["bug"] = {
                "rarity": bug.get("rarity", ""),
                "spawn": [{
                    "location": bug.get("spawnLocation", []),
                    "time": _bools_to_list(bug.get("spawnTime", {})),
                    "season": _bools_to_list(bug.get("spawnSeason", {})),
                    "weather": _bools_to_list(bug.get("spawnWeather", {})),
                }],
            }
            bug_count += 1

        if "oceanCritter" in detail and detail["oceanCritter"]:
            oc = detail["oceanCritter"]
            rec["ocean"] = {
                "rarity": oc.get("rarity", ""),
                "spawn": [{
                    "location": oc.get("spawnLocation", []),
                    "time": _bools_to_list(oc.get("spawnTime", {})),
                    "season": _bools_to_list(oc.get("spawnSeason", {})),
                    "weather": _bools_to_list(oc.get("spawnWeather", {})),
                }],
            }
            ocean_count += 1

    result = list(items_by_id.values())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"Wrote {OUT_PATH}")
    print(f"  {len(result)} items, {fish_count} fish, {bug_count} bugs, {ocean_count} ocean critters")
    print(f"  {size_kb:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

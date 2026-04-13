"""
Coral Island — Museum Collection Extractor
==========================================
Reads a Coral Island .sav file and prints every museum category
with each item ID, optional English display name, and whether the
item has been donated (Yes / No).

Names come from item_names_en.json produced by fetch_guide_items.py
(default path: data/guide-items/item_names_en.json next to this script).

Usage:
    python extract_museum.py <path_to_save_file.sav>
    python extract_museum.py save.sav --names path/to/item_names_en.json
    python extract_museum.py save.sav --no-names

Example:
    python extract_museum.py DailySave_0.sav

Requirements: Python 3.6+  (no third-party packages needed)
"""

import argparse
import json
import os
import re
import sys
import zlib

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_NAMES_JSON = os.path.join(_SCRIPT_DIR, "data", "guide-items", "item_names_en.json")


# ---------------------------------------------------------------------------
# Step 1 – decompress the save file
# Coral Island .sav files are UE4 GVAS saves with zlib-compressed chunks.
# ---------------------------------------------------------------------------

def decompress_save(path: str) -> bytes:
    with open(path, "rb") as f:
        raw = f.read()

    out = bytearray()
    i = 0
    while i < len(raw) - 1:
        # zlib streams start with 0x78 followed by 0x01, 0x5E, 0x9C, or 0xDA
        if raw[i] == 0x78 and raw[i + 1] in (0x01, 0x5E, 0x9C, 0xDA):
            try:
                chunk = zlib.decompress(raw[i:])
                out.extend(chunk)
            except zlib.error:
                pass
        i += 1

    if not out:
        raise ValueError("No zlib data found — is this a valid Coral Island save?")
    return bytes(out)


# ---------------------------------------------------------------------------
# Step 2 – parse museumCollectionProgress
# Structure inside the decompressed data:
#   item_XXXXX\x00 <bool_byte> \x0b\x00\x00\x00 item_YYYYY\x00 ...
# The single byte immediately after the null-terminated item name is the
# donation flag: 0x01 = donated, 0x00 = not yet donated.
# ---------------------------------------------------------------------------

def parse_donation_map(data: bytes) -> dict:
    pos = data.find(b"museumCollectionProgress")
    if pos == -1:
        raise ValueError("'museumCollectionProgress' not found in save data.")

    region = data[pos : pos + 25_000]
    pattern = re.compile(rb"item_(\d+)\x00(.)")
    return {int(m.group(1)): bool(m.group(2)[0]) for m in pattern.finditer(region)}


# ---------------------------------------------------------------------------
# Step 3 – parse category membership
# The same region contains blocks like:
#   EC_DonationCategory::ARTIFACT ... item_50401 item_50402 ...
#   EC_DonationCategory::FOSSIL   ... item_50448 ...
# ---------------------------------------------------------------------------

def parse_categories(data: bytes) -> dict:
    pos = data.find(b"museumCollectionProgress")
    region = data[pos : pos + 25_000].decode("latin-1", errors="replace")

    segments = re.split(r"EC_DonationCategory::", region)
    categories = {}
    for seg in segments[1:]:
        cat_name = seg.split("\x00")[0].strip()
        item_ids = [int(x) for x in re.findall(r"item_(\d+)", seg[:3_000])]
        if cat_name and item_ids:
            categories[cat_name] = item_ids
    return categories


# ---------------------------------------------------------------------------
# Item display names (from coral-island-guide via fetch_guide_items.py)
# ---------------------------------------------------------------------------

def load_item_names(path: str) -> dict:
    """Return mapping item_id (e.g. 'item_50401') -> display name string."""
    if not path or not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    if not isinstance(raw, dict):
        return out
    for key, entry in raw.items():
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            out[key] = entry["name"]
        elif isinstance(entry, str):
            out[key] = entry
    return out


def _shorten(text: str, max_len: int) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Step 4 – print the results
# ---------------------------------------------------------------------------

def print_results(categories: dict, donation_map: dict, names: dict) -> None:
    total_items = 0
    total_donated = 0
    use_names = bool(names)
    name_w = 44

    for cat_name, item_ids in categories.items():
        donated_in_cat = sum(1 for i in item_ids if donation_map.get(i, False))
        total_items += len(item_ids)
        total_donated += donated_in_cat

        pct = donated_in_cat / len(item_ids) * 100 if item_ids else 0
        print()
        print(f"{'=' * 78}")
        print(f"  Category : {cat_name}")
        print(f"  Progress : {donated_in_cat} / {len(item_ids)}  ({pct:.1f}%)")
        print(f"{'=' * 78}")
        if use_names:
            print(f"  {'Item ID':<14} {'Name':<{name_w}} Donated")
            print(f"  {'-' * (14 + 1 + name_w + 1 + 7)}")
        else:
            print(f"  {'Item ID':<15} {'Donated'}")
            print(f"  {'-' * 25}")
        for item_id in item_ids:
            donated = donation_map.get(item_id, False)
            status = "Yes" if donated else "No"
            row_id = f"item_{item_id}"
            if use_names:
                label = names.get(row_id) or names.get(row_id.lower()) or ""
                label = _shorten(label, name_w) if label else "—"
                print(f"  {row_id:<14} {label:<{name_w}} {status}")
            else:
                print(f"  {row_id:<15} {status}")

    print()
    print("=" * 78)
    overall_pct = total_donated / total_items * 100 if total_items else 0
    print(f"  OVERALL MUSEUM COMPLETION")
    print(f"  {total_donated} / {total_items} items donated  ({overall_pct:.1f}%)")
    print("=" * 78)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Print Coral Island museum donation progress from a .sav file."
    )
    p.add_argument("save_path", help="Path to the Coral Island save (.sav)")
    p.add_argument(
        "--names",
        metavar="JSON",
        default=_DEFAULT_NAMES_JSON,
        help=(
            "Path to item_names_en.json (run fetch_guide_items.py first). "
            "Default: %(default)s"
        ),
    )
    p.add_argument(
        "--no-names",
        action="store_true",
        help="Do not load or show display names",
    )
    args = p.parse_args()

    save_path = args.save_path

    names = {}
    if not args.no_names:
        names = load_item_names(args.names)
        if not names:
            print(
                f"Note: no item names loaded (missing or empty: {args.names}). "
                f"Run: python fetch_guide_items.py\n",
                file=sys.stderr,
            )

    print(f"Reading: {save_path}")
    print("Decompressing save data...")
    data = decompress_save(save_path)
    print(f"Decompressed size: {len(data):,} bytes")

    print("Parsing museum collection...\n")
    donation_map = parse_donation_map(data)
    categories = parse_categories(data)

    if not categories:
        print("No museum categories found. Make sure you have visited the museum at least once in-game.")
        sys.exit(1)

    print_results(categories, donation_map, names)


if __name__ == "__main__":
    main()
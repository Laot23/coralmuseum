"""
Coral Island Save File - Shipping Tracker
Reads DailySave_1.sav and shows which items have been shipped and which haven't.

Usage:
    python coral_island_shipping.py
    python coral_island_shipping.py --save path/to/DailySave_1.sav
    python coral_island_shipping.py --shipped-only
    python coral_island_shipping.py --not-shipped-only
    python coral_island_shipping.py --csv
"""

import zlib
import struct
import re
import argparse
import csv
import sys
import os


# ── Item name lookup table (Coral Island internal IDs → display names) ──────
ITEM_NAMES = {
    # Crops - Spring
    "item_21001": "Potato",
    "item_21003": "Cauliflower",
    "item_21004": "Turnip",
    "item_21005": "Strawberry",
    "item_21006": "Melon",
    "item_21008": "Tomato",
    "item_21011": "Blueberry",
    "item_21014": "Eggplant",
    "item_21016": "Sweet Potato",
    "item_21021": "Pineapple",
    "item_21022": "Artichoke",
    "item_21023": "Wheat",
    "item_21024": "Rice",
    "item_21025": "Sugarcane",
    "item_21026": "Cotton",
    "item_21027": "Sunflower",
    "item_21029": "Canola",
    "item_21030": "Clover",
    "item_21031": "Lavender",
    "item_21035": "Bamboo Shoot",
    "item_21037": "Pumpkin",
    "item_21047": "Daffodil",
    "item_21048": "Tulip",
    "item_21049": "Cherry Blossom",
    "item_21054": "Violet",
    "item_21085": "Wasabi",
    # Crops - Summer
    "item_22001": "Pepper",
    "item_22002": "Corn",
    "item_22003": "Sunflower (Summer)",
    "item_22004": "Radish",
    "item_22005": "Grapes",
    "item_22007": "Starfruit",
    "item_22008": "Wheat (Summer)",
    "item_22010": "Mango",
    "item_22013": "Papaya",
    "item_22014": "Banana",
    "item_22015": "Durian",
    "item_22022": "Passion Fruit",
    "item_22023": "Dragonfruit",
    "item_22024": "Lychee",
    "item_22025": "Jackfruit",
    "item_22026": "Rambutan",
    "item_22027": "Longan",
    "item_22028": "Salak",
    "item_22030": "Pomelo",
    "item_22031": "Mangosteen",
    "item_22033": "Avocado",
    "item_22036": "Guava",
    "item_22037": "Coconut",
    "item_22038": "Coffee Bean",
    "item_22046": "Cacao",
    # Crops - Fall
    "item_23001": "Pumpkin (Fall)",
    "item_23002": "Broccoli",
    "item_23003": "Bok Choy",
    "item_23004": "Shiitake Mushroom",
    "item_23005": "Sweet Potato (Fall)",
    "item_23006": "Taro",
    "item_23007": "Ginseng",
    "item_23009": "Chili Pepper",
    "item_23010": "Yam",
    "item_23011": "Cabbage",
    "item_23012": "Amaranth",
    "item_23013": "Artichoke (Fall)",
    "item_23014": "Cranberry",
    "item_23016": "Soybean",
    "item_23019": "Garlic",
    "item_23021": "Onion",
    "item_23022": "Leek",
    "item_23023": "Lotus Root",
    "item_23024": "Lemongrass",
    "item_23025": "Anise",
    "item_23026": "Turmeric",
    "item_23027": "Cardamom",
    "item_23028": "Coriander",
    "item_23030": "Galangal",
    "item_23031": "Nutmeg",
    "item_23032": "Clove",
    "item_23033": "Star Anise",
    "item_23034": "Black Pepper",
    "item_23037": "Mangosteen (Fall)",
    "item_23040": "Bay Leaf",
    "item_23042": "Rosemary",
    "item_23048": "Wasabi Root",
    # Crops - Winter
    "item_24001": "Wintergreen Berry",
    "item_24002": "Snowdrop",
    "item_24006": "Holly",
    "item_24007": "Mistletoe",
    # Animal Products
    "item_31001": "Egg",
    "item_31002": "Large Egg",
    "item_31003": "Golden Egg",
    "item_31004": "Milk",
    "item_31005": "Large Milk",
    "item_31012": "Wool",
    "item_31014": "Angora Wool",
    "item_31016": "Silk",
    "item_31018": "Duck Egg",
    "item_31020": "Duck Feather",
    "item_31021": "Goat Milk",
    "item_32001": "Cheese",
    "item_32002": "Goat Cheese",
    "item_32003": "Cloth",
    "item_32004": "Butter",
    "item_32009": "Mayonnaise",
    "item_32011": "Duck Mayo",
    "item_32013": "Truffle Oil",
    "item_32015": "Honey",
    "item_32016": "Pickles",
    "item_32018": "Jam",
    # Crafted / Artisan
    "item_41041": "Salted Fish",
    "item_41042": "Smoked Fish",
    "item_41043": "Sashimi",
    "item_41044": "Fish Fillet",
    "item_41049": "Fried Fish",
    "item_41052": "Fish Steak",
    "item_41200": "Bread",
    "item_41202": "Cake",
    # Foraging
    "item_51102": "Wood",
    "item_51104": "Stone",
    "item_51106": "Coal",
    "item_51107": "Copper Ore",
    "item_51108": "Iron Ore",
    "item_51109": "Gold Ore",
    "item_51110": "Iridium Ore",
    "item_51300": "Mixed Seeds",
    "item_51301": "Ancient Seeds",
    "item_52102": "Fiber",
    "item_52103": "Hardwood",
    "item_52104": "Sap",
    "item_52107": "Resin",
    # Gems & Minerals
    "item_61009": "Amethyst",
    "item_61010": "Topaz",
    "item_61011": "Jade",
    "item_61012": "Aquamarine",
    "item_61013": "Ruby",
    "item_61014": "Emerald",
    "item_61015": "Diamond",
    "item_61016": "Prismatic Shard",
    "item_61017": "Quartz",
    "item_61022": "Fire Quartz",
    "item_61023": "Frozen Tear",
    "item_61028": "Earth Crystal",
    "item_61034": "Omni Geode",
    "item_61036": "Geode",
    "item_61037": "Frozen Geode",
    "item_61041": "Magma Geode",
    "item_62001": "Copper Bar",
    "item_62003": "Iron Bar",
    "item_62010": "Gold Bar",
    # Fish
    "item_71002": "Catfish",
    "item_71004": "Salmon",
    "item_71005": "Sardine",
    "item_71006": "Tuna",
    "item_71007": "Carp",
    "item_71009": "Pufferfish",
    "item_71010": "Eel",
    "item_71011": "Octopus",
    "item_71012": "Red Snapper",
    "item_71013": "Sturgeon",
    "item_71016": "Tiger Trout",
    "item_71018": "Largemouth Bass",
    "item_71020": "Midnight Carp",
    "item_71021": "Woodskip",
    "item_72030": "Squid",
    # Sea Critters
    "item_72032": "Sea Cucumber",
    "item_72033": "Nautilus Shell",
    "item_72034": "Coral",
    "item_72035": "Sea Urchin",
    "item_72039": "Oyster",
    "item_72043": "Clam",
    "item_72046": "Cockle",
    "item_72047": "Mussel",
    "item_72048": "Abalone",
    "item_72049": "Scallop",
    "item_72058": "Lobster",
    "item_72069": "Crab",
    "item_72075": "Crayfish",
    # Insects
    "item_131004": "Butterfly",
    "item_131008": "Beetle",
    "item_131012": "Grasshopper",
    "item_131016": "Dragonfly",
    "item_132007": "Cricket",
    # Tools / Special
    "item_65001": "Fiber",
    "item_65008": "Fishing Rod",
    "item_65011": "Bait",
    "item_65013": "Tackle",
    "item_65016": "Chest",
    "item_65017": "Furnace",
    "item_65018": "Bee House",
    "item_65019": "Keg",
    "item_65020": "Preserves Jar",
    "item_65027": "Recycling Machine",
    "item_65034": "Scarecrow",
    "item_65035": "Sprinkler",
    "item_65049": "Seed Maker",
    "item_65050": "Mayonnaise Machine",
    "item_65109": "Backpack",
    "item_65248": "Quality Fertilizer",
    "item_65306": "Speed-Gro",
    "item_65317": "Deluxe Fertilizer",
    "item_65340": "Ocean Fish Smoker",
    "item_65341": "Smoker",
    "item_65343": "Dehydrator",
    "item_10002": "Iridium Bar",
    "item_94067": "Solar Panel",
    "item_80065": "Eel (Smoked)",
    "item_80089": "Dried Fish",
}


def get_item_name(item_id: str) -> str:
    """Return a human-readable name for an item ID, or format the ID nicely."""
    base = item_id.split("-")[0]  # strip variant suffix like -a, -b, -1
    suffix = item_id[len(base):]  # e.g. "-a" or ""

    name = ITEM_NAMES.get(base)
    if name:
        if suffix:
            quality_map = {"-a": " (Bronze)", "-b": " (Silver)", "-c": " (Gold)",
                           "-d": " (Iridium)", "-1": " (Lv1)", "-2": " (Lv2)",
                           "-3": " (Lv3)", "-4": " (Lv4)"}
            name += quality_map.get(suffix, suffix)
        return name
    # Fall back to formatted ID
    return item_id


def load_all_decompressed(path: str) -> bytes:
    """Read the save file and concatenate all decompressed zlib chunks."""
    with open(path, "rb") as f:
        raw = f.read()

    relevant_offsets = []
    seen = set()
    for pat in [b"\x78\x9c", b"\x78\x01", b"\x78\xda", b"\x78\x5e"]:
        i = 0
        while True:
            idx = raw.find(pat, i)
            if idx == -1:
                break
            if idx not in seen:
                try:
                    d = zlib.decompress(raw[idx:])
                    if len(d) >= 10_000:
                        # Only keep chunks containing tracking data
                        if any(k in d for k in [b"itemTrackDataArray", b"shippedItems", b"totalShipped"]):
                            relevant_offsets.append((idx, d))
                    seen.add(idx)
                except Exception:
                    pass
            i = idx + 1

    relevant_offsets.sort(key=lambda x: x[0])
    return b"".join(d for _, d in relevant_offsets)


def parse_item_track_data(data: bytes) -> dict:
    """
    Parse itemTrackDataArray from decompressed UE4 save bytes.
    Returns dict of {item_id: totalShipped_count}.
    """
    results = {}
    idx = 0
    pattern = b"ItemId\x00\r\x00\x00\x00NameProperty\x00"

    while True:
        pos = data.find(pattern, idx)
        if pos == -1:
            break

        # After the pattern: \x0f\x00\x00\x00 (15) + \x00\x00\x00\x00\x00 (5) + <str_len:4> + <str>
        str_len_pos = pos + len(pattern) + 4 + 5
        if str_len_pos + 4 > len(data):
            break

        str_len = struct.unpack_from("<i", data, str_len_pos)[0]
        if not (1 <= str_len <= 60):
            idx = pos + 1
            continue

        item_start = str_len_pos + 4
        try:
            item_id = data[item_start: item_start + str_len - 1].decode("ascii")
        except Exception:
            idx = pos + 1
            continue

        if not item_id.startswith("item_"):
            idx = pos + 1
            continue

        # Find totalShipped IntProperty within next 300 bytes
        ts_pattern = b"totalShipped\x00\x0c\x00\x00\x00IntProperty\x00"
        ts_pos = data.find(ts_pattern, item_start, item_start + 300)
        if ts_pos == -1:
            idx = pos + 1
            continue

        # Value is at: len(ts_pattern) + 4 (size) + 4 (index) + 1 (tag) bytes after ts_pos
        val_pos = ts_pos + len(ts_pattern) + 4 + 4 + 1
        if val_pos + 4 <= len(data):
            value = struct.unpack_from("<i", data, val_pos)[0]
            results[item_id] = value

        idx = pos + 1

    return results


def parse_args():
    p = argparse.ArgumentParser(
        description="Coral Island Save File — Shipping Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--save", default="DailySave_1.sav",
        help="Path to the save file (default: DailySave_1.sav in current directory)"
    )
    p.add_argument("--shipped-only", action="store_true", help="Show only shipped items")
    p.add_argument("--not-shipped-only", action="store_true", help="Show only items never shipped")
    p.add_argument("--csv", action="store_true", help="Output as CSV to stdout")
    p.add_argument("--min-count", type=int, default=0,
                   help="Only show shipped items with at least this many shipped (default: 0)")
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.save):
        print(f"❌ Save file not found: {args.save}", file=sys.stderr)
        print("   Pass --save <path> to specify the location.", file=sys.stderr)
        sys.exit(1)

    print(f"📂 Reading: {args.save}", file=sys.stderr)
    data = load_all_decompressed(args.save)

    if not data:
        print("❌ No decompressed data found. Is this a valid Coral Island save?", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Parsing item tracking data...", file=sys.stderr)
    items = parse_item_track_data(data)

    if not items:
        print("❌ No item tracking data found.", file=sys.stderr)
        sys.exit(1)

    shipped = {k: v for k, v in items.items() if v > 0 and v >= args.min_count}
    not_shipped = {k: v for k, v in items.items() if v == 0}

    # ── CSV output ────────────────────────────────────────────────────────────
    if args.csv:
        writer = csv.writer(sys.stdout)
        writer.writerow(["Item ID", "Display Name", "Total Shipped", "Status"])
        if not args.not_shipped_only:
            for item_id, count in sorted(shipped.items()):
                writer.writerow([item_id, get_item_name(item_id), count, "Shipped"])
        if not args.shipped_only:
            for item_id in sorted(not_shipped):
                writer.writerow([item_id, get_item_name(item_id), 0, "Never Shipped"])
        return

    # ── Pretty console output ─────────────────────────────────────────────────
    total = len(items)
    print(f"\n{'═' * 60}")
    print(f"  🌴  CORAL ISLAND — Shipping Tracker")
    print(f"{'═' * 60}")
    print(f"  Total item types tracked : {total}")
    print(f"  Shipped (sold)           : {len(shipped)}")
    print(f"  Never shipped            : {len(not_shipped)}")
    print(f"{'═' * 60}\n")

    if not args.not_shipped_only:
        print(f"✅  SHIPPED ITEMS  ({len(shipped)} types)\n")
        print(f"  {'Item ID':<25} {'Name':<30} {'Total Shipped':>13}")
        print(f"  {'─'*25} {'─'*30} {'─'*13}")
        for item_id, count in sorted(shipped.items(), key=lambda x: -x[1]):
            name = get_item_name(item_id)
            print(f"  {item_id:<25} {name:<30} {count:>13,}")

    if not args.shipped_only and not args.not_shipped_only or args.not_shipped_only:
        if not args.shipped_only:
            print(f"\n❌  NEVER SHIPPED  ({len(not_shipped)} types)\n")
            print(f"  {'Item ID':<25} {'Name':<30}")
            print(f"  {'─'*25} {'─'*30}")
            for item_id in sorted(not_shipped):
                name = get_item_name(item_id)
                print(f"  {item_id:<25} {name:<30}")

    print(f"\n{'═' * 60}")
    print(f"  Done! Run with --csv to export, --help for options.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
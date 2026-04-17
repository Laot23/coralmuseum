import { getShippingItem, getItem } from "./db";

const QUALITY_LABELS: Record<string, string> = {
  bronze: " (Bronze)",
  silver: " (Silver)",
  gold: " (Gold)",
  osmium: " (Osmium)",
};

const SUFFIX_TO_QUALITY: Record<string, string> = {
  "-a": "bronze",
  "-b": "silver",
  "-c": "gold",
  "-d": "osmium",
};

/**
 * Resolve a shipping item ID to a display name.
 * Checks the shipping DB first, falls back to the museum DB, then raw ID.
 */
export function getShippingItemName(itemId: string): string {
  const shipItem = getShippingItem(itemId);
  if (shipItem) {
    const qual = shipItem.quality ? (QUALITY_LABELS[shipItem.quality] ?? "") : "";
    return shipItem.name + qual;
  }

  const exact = getItem(itemId);
  if (exact) return exact.name;

  const dashIdx = itemId.indexOf("-", 5);
  if (dashIdx > 0) {
    const base = itemId.substring(0, dashIdx);
    const suffix = itemId.substring(dashIdx);
    const qualName = SUFFIX_TO_QUALITY[suffix];
    const baseItem = getShippingItem(base) ?? getItem(base);
    if (baseItem) {
      const label = qualName ? (QUALITY_LABELS[qualName] ?? suffix) : suffix;
      return baseItem.name + label;
    }
  }

  return itemId;
}

/**
 * Get the base item ID (strip quality suffix) for icon lookups.
 */
export function getShippingBaseId(itemId: string): string {
  const dashIdx = itemId.indexOf("-", 5);
  return dashIdx > 0 ? itemId.substring(0, dashIdx) : itemId;
}

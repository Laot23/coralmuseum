import pako from "pako";

const ZLIB_SECOND_BYTES = new Set([0x01, 0x5e, 0x9c, 0xda]);

/**
 * UE4 GVAS saves contain multiple concatenated zlib streams.
 * Each starts with a 2-byte zlib header (0x78 + level byte) followed
 * by raw DEFLATE data.  pako.inflate() chokes on the trailing bytes
 * after each stream, so we use raw inflate (skipping the 2-byte header)
 * which cleanly stops at the DEFLATE stream boundary.
 */
export function decompressSave(buffer: ArrayBuffer): Uint8Array {
  const raw = new Uint8Array(buffer);
  const chunks: Uint8Array[] = [];

  for (let i = 0; i < raw.length - 1; i++) {
    if (raw[i] === 0x78 && ZLIB_SECOND_BYTES.has(raw[i + 1])) {
      try {
        const inf = new pako.Inflate({ raw: true });
        inf.push(raw.subarray(i + 2), true);
        if (inf.err === 0 && inf.result && inf.result.length > 0) {
          chunks.push(inf.result as Uint8Array);
        }
      } catch {
        // not a valid deflate stream at this offset
      }
    }
  }

  if (chunks.length === 0) {
    throw new Error("No zlib data found — is this a valid Coral Island save?");
  }

  const totalLen = chunks.reduce((s, c) => s + c.length, 0);
  const out = new Uint8Array(totalLen);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.length;
  }
  return out;
}

const ANCHOR = "museumCollectionProgress";
const WINDOW = 25_000;

function findAnchor(data: Uint8Array): number {
  const enc = new TextEncoder();
  const needle = enc.encode(ANCHOR);
  outer: for (let i = 0; i <= data.length - needle.length; i++) {
    for (let j = 0; j < needle.length; j++) {
      if (data[i + j] !== needle[j]) continue outer;
    }
    return i;
  }
  return -1;
}

export interface DonationMap {
  [itemId: string]: boolean;
}

export function parseDonationMap(data: Uint8Array): DonationMap {
  const pos = findAnchor(data);
  if (pos === -1) {
    throw new Error("'museumCollectionProgress' not found in save data.");
  }

  const end = Math.min(pos + WINDOW, data.length);
  const region = data.subarray(pos, end);
  const decoder = new TextDecoder("latin1");
  const text = decoder.decode(region);

  const map: DonationMap = {};
  const re = /item_(\d+)\x00(.)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const id = `item_${m[1]}`;
    const donated = m[2].charCodeAt(0) !== 0;
    map[id] = donated;
  }
  return map;
}

export interface CategoryData {
  name: string;
  itemIds: string[];
}

export interface ShippingMap {
  [itemId: string]: number;
}

/**
 * Parse itemTrackDataArray from decompressed UE4 save bytes.
 * Each tracked item has an ItemId (NameProperty) and a totalShipped (IntProperty).
 */
export function parseShippingData(data: Uint8Array): ShippingMap {
  const results: ShippingMap = {};
  const enc = new TextEncoder();
  const pattern = enc.encode("ItemId\x00\r\x00\x00\x00NameProperty\x00");
  const tsPattern = enc.encode("totalShipped\x00\x0c\x00\x00\x00IntProperty\x00");

  for (let i = 0; i < data.length - pattern.length; i++) {
    if (!matchBytes(data, i, pattern)) continue;

    const strLenPos = i + pattern.length + 4 + 5;
    if (strLenPos + 4 > data.length) break;

    const strLen = readInt32(data, strLenPos);
    if (strLen < 1 || strLen > 60) continue;

    const itemStart = strLenPos + 4;
    if (itemStart + strLen > data.length) continue;

    let itemId: string;
    try {
      itemId = new TextDecoder("ascii").decode(data.subarray(itemStart, itemStart + strLen - 1));
    } catch {
      continue;
    }
    if (!itemId.startsWith("item_")) continue;

    const searchEnd = Math.min(itemStart + 300, data.length - tsPattern.length);
    let tsPos = -1;
    for (let j = itemStart; j < searchEnd; j++) {
      if (matchBytes(data, j, tsPattern)) {
        tsPos = j;
        break;
      }
    }
    if (tsPos === -1) continue;

    const valPos = tsPos + tsPattern.length + 4 + 4 + 1;
    if (valPos + 4 <= data.length) {
      results[itemId] = readInt32(data, valPos);
    }
  }

  return results;
}

function matchBytes(data: Uint8Array, offset: number, needle: Uint8Array): boolean {
  if (offset + needle.length > data.length) return false;
  for (let j = 0; j < needle.length; j++) {
    if (data[offset + j] !== needle[j]) return false;
  }
  return true;
}

function readInt32(data: Uint8Array, offset: number): number {
  return (
    data[offset] |
    (data[offset + 1] << 8) |
    (data[offset + 2] << 16) |
    (data[offset + 3] << 24)
  );
}

export function parseCategories(data: Uint8Array): CategoryData[] {
  const pos = findAnchor(data);
  if (pos === -1) return [];

  const end = Math.min(pos + WINDOW, data.length);
  const region = data.subarray(pos, end);
  const decoder = new TextDecoder("latin1");
  const text = decoder.decode(region);

  const segments = text.split("EC_DonationCategory::");
  const categories: CategoryData[] = [];

  for (let i = 1; i < segments.length; i++) {
    const seg = segments[i];
    const nullIdx = seg.indexOf("\x00");
    const name = (nullIdx >= 0 ? seg.substring(0, nullIdx) : seg.substring(0, 20)).trim();
    const slice = seg.substring(0, 3000);
    const ids: string[] = [];
    const itemRe = /item_(\d+)/g;
    let im: RegExpExecArray | null;
    while ((im = itemRe.exec(slice)) !== null) {
      ids.push(`item_${im[1]}`);
    }
    if (name && ids.length > 0) {
      categories.push({ name, itemIds: ids });
    }
  }
  return categories;
}

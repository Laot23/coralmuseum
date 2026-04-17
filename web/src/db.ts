export interface SpawnData {
  location: string[];
  time: string[];
  season: string[];
  weather: string[];
}

export interface FishData {
  rarity: string;
  size: string;
  pattern: string;
  difficulty: string;
  spawn: SpawnData[];
}

export interface BugData {
  rarity: string;
  spawn: SpawnData[];
}

export interface DropSource {
  sourceId: string;
  sourceName: string;
  sourceIcon: string;
  chance: number;
  shop: string;
}

export interface MuseumItem {
  id: string;
  name: string;
  description: string;
  category: string;
  displayKey: string;
  sellPrice: number;
  iconName: string;
  tags: string[];
  fish?: FishData;
  bug?: BugData;
  ocean?: BugData;
  sources?: DropSource[];
}

export interface ShippingItem {
  id: string;
  name: string;
  category: string;
  iconName: string;
  sellPrice: number;
  quality?: string;
}

let itemsMap: Map<string, MuseumItem> | null = null;
let allItems: MuseumItem[] = [];
let shippingItemsList: ShippingItem[] = [];
let shippingItemsMap: Map<string, ShippingItem> | null = null;

export async function loadDatabase(): Promise<void> {
  if (itemsMap) return;
  const [museumResp, shippingResp] = await Promise.all([
    fetch(`${import.meta.env.BASE_URL}data/museum-items.json`),
    fetch(`${import.meta.env.BASE_URL}data/shipping-items.json`),
  ]);
  if (!museumResp.ok) throw new Error(`Failed to load item database: ${museumResp.status}`);
  const data: MuseumItem[] = await museumResp.json();
  allItems = data;
  itemsMap = new Map(data.map((it) => [it.id, it]));

  if (shippingResp.ok) {
    const shipData: ShippingItem[] = await shippingResp.json();
    shippingItemsList = shipData;
    shippingItemsMap = new Map(shipData.map((it) => [it.id, it]));
  }
}

export function getItem(id: string): MuseumItem | undefined {
  return itemsMap?.get(id);
}

export function getAllItems(): MuseumItem[] {
  return allItems;
}

export function getShippingItem(id: string): ShippingItem | undefined {
  return shippingItemsMap?.get(id);
}

export function getAllShippingItems(): ShippingItem[] {
  return shippingItemsList;
}

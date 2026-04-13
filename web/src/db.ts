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

let itemsMap: Map<string, MuseumItem> | null = null;
let allItems: MuseumItem[] = [];

export async function loadDatabase(): Promise<void> {
  if (itemsMap) return;
  const resp = await fetch("/data/museum-items.json");
  if (!resp.ok) throw new Error(`Failed to load item database: ${resp.status}`);
  const data: MuseumItem[] = await resp.json();
  allItems = data;
  itemsMap = new Map(data.map((it) => [it.id, it]));
}

export function getItem(id: string): MuseumItem | undefined {
  return itemsMap?.get(id);
}

export function getAllItems(): MuseumItem[] {
  return allItems;
}

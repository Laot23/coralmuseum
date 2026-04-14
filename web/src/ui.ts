import type { MuseumItem, SpawnData, DropSource } from "./db";
import type { CategoryData, DonationMap } from "./parser";
import { getItem } from "./db";

const ICON_BASE = "https://coral.guide/assets/live/items/icons/";

// ── State ──

type FilterMode = "all" | "missing" | "donated";
let currentFilter: FilterMode = "missing";
let searchQuery = "";
let donationMap: DonationMap = {};
let categories: CategoryData[] = [];
const expandedCategories = new Set<string>();
const expandedItems = new Set<string>();

// ── Helpers ──

function esc(s: string): string {
  const el = document.createElement("span");
  el.textContent = s;
  return el.innerHTML;
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function iconUrl(iconName: string): string {
  if (!iconName) return "";
  return `${ICON_BASE}${encodeURIComponent(iconName)}.webp`;
}

// ── Public API ──

export function showSection(id: string): void {
  for (const s of document.querySelectorAll("main > section")) {
    (s as HTMLElement).classList.add("hidden");
  }
  document.getElementById(id)?.classList.remove("hidden");
}

export function showError(msg: string): void {
  showSection("error-section");
  const el = document.getElementById("error-message");
  if (el) el.textContent = msg;
}

export function renderResults(cats: CategoryData[], donations: DonationMap): void {
  categories = cats;
  donationMap = donations;

  let totalItems = 0;
  let totalDonated = 0;
  for (const cat of cats) {
    totalItems += cat.itemIds.length;
    for (const id of cat.itemIds) {
      if (donations[id]) totalDonated++;
    }
  }

  const pct = totalItems > 0 ? Math.round((totalDonated / totalItems) * 100) : 0;

  const ring = document.getElementById("progress-ring") as SVGCircleElement | null;
  if (ring) {
    const circumference = 2 * Math.PI * 52;
    ring.style.strokeDasharray = `${circumference}`;
    ring.style.strokeDashoffset = `${circumference - (pct / 100) * circumference}`;
  }

  const pctEl = document.getElementById("progress-pct");
  if (pctEl) pctEl.textContent = `${pct}%`;

  const detail = document.getElementById("summary-detail");
  if (detail) detail.textContent = `${totalDonated} of ${totalItems} items donated`;

  for (const cat of cats) expandedCategories.add(cat.name);

  renderCategories();
  showSection("results-section");
}

export function setFilter(mode: FilterMode): void {
  currentFilter = mode;
  for (const btn of document.querySelectorAll(".filter-btn")) {
    const b = btn as HTMLElement;
    const m = b.dataset.filter;
    if (m === mode) {
      b.className = "filter-btn px-4 py-1.5 rounded-md text-sm font-semibold transition-colors " +
        (m === "missing"
          ? "bg-coral-400/20 text-coral-300"
          : m === "donated"
            ? "bg-emerald-900/30 text-emerald-400"
            : "bg-merino-800/40 text-merino-100");
    } else {
      b.className = "filter-btn px-4 py-1.5 rounded-md text-sm font-semibold transition-colors text-merino-300 hover:text-merino-100";
    }
  }
  renderCategories();
}

export function setSearch(query: string): void {
  searchQuery = query.toLowerCase().trim();
  renderCategories();
}

// ── Rendering ──

function matchesFilter(id: string): boolean {
  const donated = !!donationMap[id];
  if (currentFilter === "missing") return !donated;
  if (currentFilter === "donated") return donated;
  return true;
}

function matchesSearch(item: MuseumItem | undefined, id: string): boolean {
  if (!searchQuery) return true;
  if (item) {
    return (
      item.name.toLowerCase().includes(searchQuery) ||
      item.id.toLowerCase().includes(searchQuery) ||
      item.description.toLowerCase().includes(searchQuery)
    );
  }
  return id.toLowerCase().includes(searchQuery);
}

function renderCategories(): void {
  const container = document.getElementById("categories-container");
  if (!container) return;
  container.innerHTML = "";

  for (const cat of categories) {
    const filteredIds = cat.itemIds.filter((id) => {
      const item = getItem(id);
      return matchesFilter(id) && matchesSearch(item, id);
    });

    const totalInCat = cat.itemIds.length;
    const donatedInCat = cat.itemIds.filter((id) => donationMap[id]).length;
    const expanded = expandedCategories.has(cat.name);
    const complete = donatedInCat === totalInCat;

    const card = document.createElement("div");
    card.className = "category-card";

    card.innerHTML = `
      <div class="category-header" data-cat="${esc(cat.name)}">
        <div class="flex items-center gap-3">
          <svg class="w-5 h-5 text-bark transition-transform duration-200 ${expanded ? "rotate-90" : ""}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
          </svg>
          <span class="font-display font-bold text-bark text-lg">${esc(formatCategoryName(cat.name))}</span>
          ${complete ? `<span class="text-emerald-600 text-sm font-semibold">✓ Complete</span>` : ""}
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm font-semibold text-bark-light">${donatedInCat} / ${totalInCat}</span>
          <div class="w-28 h-2.5 bg-merino-200 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-500 ${complete ? "bg-emerald-500" : "bg-gold-400"}"
                 style="width: ${totalInCat > 0 ? (donatedInCat / totalInCat) * 100 : 0}%"></div>
          </div>
        </div>
      </div>
      ${expanded ? `<div class="category-body">${filteredIds.length > 0
        ? `<div class="item-grid">${filteredIds.map((id) => renderItemCard(id)).join("")}</div>`
        : `<div class="px-6 py-10 text-center text-bark-light/60 text-sm">No items match current filters</div>`
      }</div>` : ""}
    `;

    const header = card.querySelector(".category-header") as HTMLElement;
    header.addEventListener("click", () => {
      if (expandedCategories.has(cat.name)) {
        expandedCategories.delete(cat.name);
      } else {
        expandedCategories.add(cat.name);
      }
      renderCategories();
    });

    container.appendChild(card);
  }

  for (const toggle of container.querySelectorAll("[data-item-toggle]")) {
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = (toggle as HTMLElement).dataset.itemToggle!;
      if (expandedItems.has(id)) expandedItems.delete(id);
      else expandedItems.add(id);
      renderCategories();
    });
  }
}

function formatCategoryName(raw: string): string {
  return raw
    .replace(/_/g, " ")
    .split(" ")
    .map((w) => capitalize(w.toLowerCase()))
    .join(" ");
}

function renderItemCard(id: string): string {
  const item = getItem(id);
  const donated = !!donationMap[id];
  const name = item?.name || id;
  const hasDetail = !!(item?.fish || item?.bug || item?.ocean || item?.description || (item?.sources && item.sources.length > 0));
  const isExpanded = expandedItems.has(id);
  const icon = item?.iconName ? iconUrl(item.iconName) : "";

  const typeTag =
    item?.fish ? "Fish" :
    item?.bug ? "Bug" :
    item?.ocean ? "Ocean Critter" : "";

  return `
    <div class="item-card ${donated ? "item-donated" : "item-missing"}">
      <div class="item-card-main" ${hasDetail ? `data-item-toggle="${esc(id)}"` : ""}>
        <div class="item-icon-wrap">
          ${icon
            ? `<img src="${esc(icon)}" alt="${esc(name)}" class="item-icon" loading="lazy"
                   onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" />
               <div class="item-icon-fallback" style="display:none">?</div>`
            : `<div class="item-icon-fallback">?</div>`}
          ${donated
            ? `<div class="item-check">✓</div>`
            : ""}
        </div>
        <div class="item-info">
          <span class="item-name">${esc(name)}</span>
          <div class="item-meta">
            ${donated
              ? `<span class="badge badge-donated">Donated</span>`
              : `<span class="badge badge-missing">Missing</span>`}
            ${typeTag ? `<span class="badge badge-type">${esc(typeTag)}</span>` : ""}
          </div>
          ${!donated && item?.sellPrice ? `<span class="item-price">${item.sellPrice}g</span>` : ""}
        </div>
        ${hasDetail
          ? `<svg class="item-expand-icon ${isExpanded ? "rotate-180" : ""}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>`
          : ""}
      </div>
      ${isExpanded && item ? renderDetailPanel(item) : ""}
    </div>
  `;
}

function renderDetailPanel(item: MuseumItem): string {
  const parts: string[] = [];

  if (item.description) {
    parts.push(`<p class="detail-desc">${esc(item.description)}</p>`);
  }

  if (item.fish) {
    const f = item.fish;
    parts.push(`<div class="detail-chips">${[
      chip("Rarity", f.rarity, rarityColor(f.rarity)),
      chip("Size", f.size),
      chip("Pattern", f.pattern),
      chip("Difficulty", f.difficulty, difficultyColor(f.difficulty)),
    ].join("")}</div>`);
    parts.push(renderSpawnList(f.spawn));
  }

  if (item.bug) {
    parts.push(`<div class="detail-chips">${chip("Rarity", item.bug.rarity, rarityColor(item.bug.rarity))}</div>`);
    parts.push(renderSpawnList(item.bug.spawn));
  }

  if (item.ocean) {
    parts.push(`<div class="detail-chips">${chip("Rarity", item.ocean.rarity, rarityColor(item.ocean.rarity))}</div>`);
    parts.push(renderSpawnList(item.ocean.spawn));
  }

  if (item.sources && item.sources.length > 0) {
    parts.push(renderDropSources(item.sources));
  }

  return `<div class="detail-panel">${parts.join("")}</div>`;
}

function rarityColor(r: string): string {
  switch (r.toLowerCase()) {
    case "common": return "bg-bark/10 text-bark";
    case "uncommon": return "bg-emerald-100 text-emerald-700";
    case "rare": return "bg-blue-100 text-blue-700";
    case "epic": return "bg-purple-100 text-purple-700";
    case "legendary": return "bg-amber-100 text-amber-700";
    default: return "";
  }
}

function difficultyColor(d: string): string {
  switch (d.toLowerCase()) {
    case "easy": return "bg-emerald-100 text-emerald-700";
    case "medium": return "bg-amber-100 text-amber-700";
    case "hard": return "bg-coral-100 text-coral-700";
    case "very hard": return "bg-red-100 text-red-700";
    default: return "";
  }
}

function chip(label: string, value: string, colorClass?: string): string {
  if (!value) return "";
  const cls = colorClass || "bg-merino-200 text-bark";
  return `<span class="chip ${cls}"><span class="chip-label">${esc(label)}:</span> ${esc(value)}</span>`;
}

function spawnKey(s: SpawnData): string {
  return [
    s.season.slice().sort().join(","),
    s.time.slice().sort().join(","),
    s.weather.slice().sort().join(","),
  ].join("|");
}

function mergeSpawns(spawns: SpawnData[]): SpawnData[] {
  const map = new Map<string, SpawnData>();
  for (const s of spawns) {
    const k = spawnKey(s);
    const existing = map.get(k);
    if (existing) {
      const locs = new Set([...existing.location, ...s.location]);
      existing.location = [...locs];
    } else {
      map.set(k, { location: [...s.location], season: [...s.season], time: [...s.time], weather: [...s.weather] });
    }
  }
  return [...map.values()];
}

function renderSpawnList(spawns: SpawnData[]): string {
  if (spawns.length === 0) return "";
  const merged = mergeSpawns(spawns);
  if (merged.length === 1) return renderSpawn(merged[0]);
  return `<div class="spawn-options">${merged.map((s, i) =>
    `<div class="spawn-option">
      <div class="spawn-option-label">Option ${i + 1}</div>
      ${renderSpawnInner(s)}
    </div>`
  ).join("")}</div>`;
}

function renderSpawn(s: SpawnData): string {
  const rows: string[] = [];
  if (s.location.length) rows.push(chipRow("Location", s.location));
  if (s.season.length) rows.push(chipRow("Season", s.season.map(capitalize)));
  if (s.time.length) rows.push(chipRow("Time", s.time.map(capitalize)));
  if (s.weather.length) rows.push(chipRow("Weather", s.weather.map(capitalize)));
  if (rows.length === 0) return "";
  return `<div class="detail-chips">${rows.join("")}</div>`;
}

function renderSpawnInner(s: SpawnData): string {
  const rows: string[] = [];
  if (s.location.length) rows.push(chipRow("Location", s.location));
  if (s.season.length) rows.push(chipRow("Season", s.season.map(capitalize)));
  if (s.time.length) rows.push(chipRow("Time", s.time.map(capitalize)));
  if (s.weather.length) rows.push(chipRow("Weather", s.weather.map(capitalize)));
  if (rows.length === 0) return "";
  return `<div class="detail-chips mb-0">${rows.join("")}</div>`;
}

function chipRow(label: string, values: string[]): string {
  return `<span class="chip bg-merino-200 text-bark"><span class="chip-label">${esc(label)}:</span> ${values.map(esc).join(", ")}</span>`;
}

function renderDropSources(sources: DropSource[]): string {
  const rows = sources.map((s) => {
    const icon = s.sourceIcon ? iconUrl(s.sourceIcon) : "";
    const pct = s.chance < 1 ? s.chance.toFixed(2) : s.chance.toFixed(1);

    return `
      <div class="source-row">
        <div class="source-icon-wrap">
          ${icon
            ? `<img src="${esc(icon)}" alt="${esc(s.sourceName)}" class="source-icon" loading="lazy"
                   onerror="this.style.display='none'" />`
            : ""}
        </div>
        <div class="source-info">
          <span class="source-name">${esc(s.sourceName)}</span>
          ${s.shop ? `<span class="source-shop">@ ${esc(s.shop)}</span>` : ""}
        </div>
        <span class="source-pct">${pct}%</span>
      </div>
    `;
  });

  return `
    <div class="source-section">
      <div class="source-heading">Obtained from</div>
      ${rows.join("")}
    </div>
  `;
}

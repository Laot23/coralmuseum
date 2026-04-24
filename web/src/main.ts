import "./style.css";
import { loadDatabase } from "./db";
import { decompressSave, parseCategories, parseDonationMap, parseShippingData } from "./parser";
import {
  renderResults,
  renderShippingResults,
  setFilter,
  setSearch,
  setShippingFilter,
  setShippingSearch,
  showError,
  showSection,
  switchTab,
  type TabId,
} from "./ui";

// ── Elements ──

const dropZone = document.getElementById("drop-zone")!;
const fileInput = document.getElementById("file-input") as HTMLInputElement;
const errorRetry = document.getElementById("error-retry")!;
const uploadAnother = document.getElementById("upload-another")!;
const searchInput = document.getElementById("search-input") as HTMLInputElement;
const shippingSearchInput = document.getElementById("shipping-search-input") as HTMLInputElement;

// ── Upload handling ──

function handleFile(file: File): void {
  showSection("loading-section");

  const reader = new FileReader();
  reader.onload = async () => {
    try {
      await loadDatabase();
      const buffer = reader.result as ArrayBuffer;
      const data = decompressSave(buffer);
      const donations = parseDonationMap(data);
      const categories = parseCategories(data);
      const shipping = parseShippingData(data);

      const hasMuseum = categories.length > 0;
      const hasShipping = Object.keys(shipping).length > 0;

      if (!hasMuseum && !hasShipping) {
        showError(
          "No museum or shipping data found. Make sure you have visited the museum or shipped items at least once in-game."
        );
        return;
      }

      if (hasMuseum) renderResults(categories, donations);
      if (hasShipping) renderShippingResults(shipping);

      showSection("results-section");
      switchTab(hasMuseum ? "museum" : "shipping");
    } catch (e) {
      showError(e instanceof Error ? e.message : String(e));
    }
  };
  reader.onerror = () => showError("Failed to read the file.");
  reader.readAsArrayBuffer(file);
}

// Click to browse
dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (file) handleFile(file);
});

// Drag and drop
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("border-coral-400", "bg-merino-950/60");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("border-coral-400", "bg-merino-950/60");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("border-coral-400", "bg-merino-950/60");
  const file = e.dataTransfer?.files[0];
  if (file) handleFile(file);
});

// Retry / upload another
function resetToUpload(): void {
  fileInput.value = "";
  searchInput.value = "";
  shippingSearchInput.value = "";
  showSection("upload-section");
}

errorRetry.addEventListener("click", resetToUpload);
uploadAnother.addEventListener("click", resetToUpload);

// ── Top-level tabs ──

for (const btn of document.querySelectorAll(".tab-btn")) {
  btn.addEventListener("click", () => {
    const tab = (btn as HTMLElement).dataset.tab as TabId;
    switchTab(tab);
    (window as any).goatcounter?.count({ path: `tab-${tab}`, title: `Tab: ${tab}`, event: true });
  });
}

// ── Museum Filters ──

for (const btn of document.querySelectorAll(".filter-btn")) {
  btn.addEventListener("click", () => {
    const mode = (btn as HTMLElement).dataset.filter as "all" | "missing" | "donated";
    setFilter(mode);
  });
}

// ── Shipping Filters ──

for (const btn of document.querySelectorAll(".ship-filter-btn")) {
  btn.addEventListener("click", () => {
    const mode = (btn as HTMLElement).dataset.shipFilter as "all" | "shipped" | "not-shipped";
    setShippingFilter(mode);
  });
}

// ── Search ──

let searchTimeout: ReturnType<typeof setTimeout>;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => setSearch(searchInput.value), 150);
});

let shippingSearchTimeout: ReturnType<typeof setTimeout>;
shippingSearchInput.addEventListener("input", () => {
  clearTimeout(shippingSearchTimeout);
  shippingSearchTimeout = setTimeout(() => setShippingSearch(shippingSearchInput.value), 150);
});

import "./style.css";
import { loadDatabase } from "./db";
import { decompressSave, parseCategories, parseDonationMap } from "./parser";
import { renderResults, setFilter, setSearch, showError, showSection } from "./ui";

// ── Elements ──

const dropZone = document.getElementById("drop-zone")!;
const fileInput = document.getElementById("file-input") as HTMLInputElement;
const errorRetry = document.getElementById("error-retry")!;
const uploadAnother = document.getElementById("upload-another")!;
const searchInput = document.getElementById("search-input") as HTMLInputElement;

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

      if (categories.length === 0) {
        showError(
          "No museum categories found. Make sure you have visited the museum at least once in-game."
        );
        return;
      }

      renderResults(categories, donations);
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
  showSection("upload-section");
}

errorRetry.addEventListener("click", resetToUpload);
uploadAnother.addEventListener("click", resetToUpload);

// ── Filters ──

for (const btn of document.querySelectorAll(".filter-btn")) {
  btn.addEventListener("click", () => {
    const mode = (btn as HTMLElement).dataset.filter as "all" | "missing" | "donated";
    setFilter(mode);
  });
}

// ── Search ──

let searchTimeout: ReturnType<typeof setTimeout>;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => setSearch(searchInput.value), 150);
});

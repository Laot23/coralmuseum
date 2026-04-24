# Coral Museum Tracker

A browser-based tracker for [Coral Island](https://store.steampowered.com/app/1158160/Coral_Island/) that shows your museum donation progress and shipping checklist. Upload your save file and see exactly what you've donated, what's missing, and what you've shipped — no data ever leaves your browser.

**Live site:** https://laot23.github.io/coralmuseum/

---

## Features

- **Museum tab** — donation progress per category (fish, bugs, ocean, artifacts, etc.) with a progress ring, filters (all / donated / missing), and search
- **Shipping tab** — shipped vs. not-shipped items with the same filters and search
- **100% client-side** — save files are parsed entirely in your browser using the Unreal Engine GVAS format; nothing is uploaded to a server
- **No login required** — just drop in your `.sav` file

---

## Usage

1. Open the [live site](https://tomk2.github.io/coralmuseum/)
2. Click **Upload Save File** and select your Coral Island `.sav` file
   - Default save location on Windows: `%LOCALAPPDATA%\CoralIsland\Saved\SaveGames\`
3. Browse the **Museum** and **Shipping** tabs

---

## Project Structure

```
coralmuseum/
├── web/                        # Vite + TypeScript front end
│   ├── src/
│   │   ├── main.ts             # App entry point
│   │   ├── parser.ts           # GVAS save file parser (runs in-browser)
│   │   ├── db.ts               # Loads static item JSON
│   │   ├── ui.ts               # DOM / UI logic
│   │   └── style.css           # Tailwind CSS
│   ├── public/data/
│   │   ├── museum-items.json   # Pre-built museum item database
│   │   └── shipping-items.json # Pre-built shipping item database
│   ├── index.html
│   ├── vite.config.ts          # base: "/coralmuseum/"
│   └── package.json
│
├── scripts/
│   ├── build-db.py             # Builds museum-items.json from guide data
│   └── build-shipping-db.py    # Builds shipping-items.json from guide data
│
├── data/guide-items/           # Downloaded guide + localization data
│
├── fetch_guide_items.py        # Fetches item data from coral-island-guide
├── extract_museum.py           # CLI: print museum state from a .sav file
├── coral_shipping.py           # CLI: print/export shipping state from a .sav file
│
└── .github/workflows/
    └── deploy.yml              # GitHub Pages deploy
```

---

## Python CLI Tools

These scripts parse save files from the command line — useful for quick checks or scripting.

### `extract_museum.py`

Print your museum donation state from a `.sav` file.

```bash
python extract_museum.py <path/to/save.sav>
```

### `coral_shipping.py`

Print or export your shipping progress from a `.sav` file.

```bash
python coral_shipping.py <path/to/save.sav>
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Build | Vite 6, TypeScript 5 |
| Styling | Tailwind CSS 3 |
| Decompression | pako (zlib/DEFLATE for UE save chunks) |
| Item data | [coral-island-guide](https://github.com/koenigderluegner/coral-island-guide) |
| Hosting | GitHub Pages |

---

## License

Item data is sourced from [coral-island-guide](https://github.com/koenigderluegner/coral-island-guide). Coral Island is developed by [Stairway Games](https://www.stairwaygames.com/).

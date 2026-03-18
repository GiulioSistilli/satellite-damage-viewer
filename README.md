# 🛰️ Satellite Damage Viewer

**Open-source conflict damage assessment using historical satellite imagery.**

> Compare ESRI Wayback Archive snapshots, detect structural changes, and identify fire scars, collapsed infrastructure, and flooding — all from a single HTML file. No server, no API key, no login required.

---

## Author & Maintainer

| | |
|---|---|
| **Author** | Giulio Sistilli |
| **GitHub** | [@GiulioSistilli](https://github.com/GiulioSistilli) |
| **Licence** | MIT — free to use, modify, distribute |
| **Contributions** | Open an issue or pull request — see [Contributing](#contributing) |

---

## Why This Exists

Standard satellite tile services (Google Maps, standard ESRI) always serve the **latest mosaic**. Comparing "before" and "after" dates on those services returns identical tiles, making automated change detection meaningless.

This tool uses the **[ESRI Wayback Archive](https://livingatlas.arcgis.com/wayback/)** — a free, public service that preserves every published version of the World Imagery basemap since 2014. Each Wayback release is a genuine timestamped snapshot at **0.3–0.5 m/pixel** resolution. Individual buildings, vehicles, and crater scars are visible. New releases are published every 2–4 weeks and the app fetches the live catalogue on startup, so it always reflects the latest available date.

---

## Features

| Feature | Detail |
|---|---|
| True historical comparison | ESRI Wayback archive — real snapshots, not the same tile twice |
| High resolution | 0.3–0.5 m/pixel — buildings, streets, vehicles all visible |
| Three view modes | Slider (drag divider), Side-by-side, Overlay |
| Automated damage detection | Fire/burn scars · Collapse/darkening · General change |
| Bounding boxes | Top 40 change zones labelled `#1`–`#40` by area |
| Image enhancement | Brightness, contrast, saturation controls |
| Orange tile filter | Automatically hides ESRI placeholder tiles (no imagery available) |
| NASA fire layer | VIIRS/MODIS thermal anomaly overlay — optional, date-selectable |
| 25+ preset locations | Iran, UAE, Saudi Arabia, Qatar, Oman, Israel, Yemen |
| Live catalogue refresh | Fetches ESRI release list on load — always shows latest dates |
| PNG export | Side-by-side annotated export with date labels |
| Zero install | Single HTML file, no build step, no dependencies |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/GiulioSistilli/satellite-damage-viewer.git
cd satellite-damage-viewer

# 2. Serve locally
#    Required for CORS — the ESRI catalogue fetch needs HTTP, not file://
python3 -m http.server 8080

# 3. Open
# Navigate to http://localhost:8080 in any modern browser
```

> **Chrome note:** if tiles still fail due to CORS in local development, launch Chrome with  
> `--disable-web-security --user-data-dir=/tmp/chrome-dev` (development only, never for regular browsing).

---

## Preset Locations

### 🇮🇷 Iran
Tehran · Isfahan (nuclear research area) · Kharg Island (main oil export terminal) · Bandar Abbas (principal naval base) · Natanz (uranium enrichment) · Fordow (underground enrichment) · Tabriz · Ahvaz (oil refinery region)

### 🇦🇪 UAE
Dubai city centre · Dubai International Airport · Abu Dhabi · Ruwais petrochemical complex

### 🇸🇦 Saudi Arabia
Riyadh · Jeddah · Abqaiq (world's largest oil processing plant) · Ras Tanura (largest oil export terminal) · NEOM / The Line

### 🇶🇦 Qatar
Doha · Ras Laffan LNG complex

### 🇴🇲 Oman
Salalah Port · Strait of Hormuz

### 🇮🇱 Israel · 🇾🇪 Yemen
Tel Aviv · Haifa · Hodeidah Port · Sanaa

---

## How It Works

### Imagery source — ESRI Wayback

The live release catalogue is fetched on startup:

```
https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json
```

Each entry maps to a WMTS tile endpoint:

```
https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/
  default028mm/MapServer/tile/{releaseNum}/{z}/{y}/{x}
```

If the catalogue fetch fails (offline or CORS blocked from `file://`), the app falls back to a hardcoded list of verified release numbers.

### Change detection pipeline

Runs entirely in the browser using the Canvas 2D API — no server-side processing:

```
Capture BEFORE tiles → Canvas A  (brightness/contrast/saturation applied)
Capture AFTER  tiles → Canvas B

Per-pixel analysis (three indices):
  Fire index    = (ΔRed↑ + ΔGreen↓) / 2        → burn scars, explosions
  Dark index    = brightness(A) − brightness(B)  → collapse, flooding
  Change mag    = mean(|ΔR| + |ΔG| + |ΔB|) / 3  → general change

Blob detection:
  3× downsampled binary mask → BFS connected components → bounding boxes
  Top 40 regions sorted by area, labelled #1–#40
```

### Architecture — two maps only

Each view mode uses exactly two Leaflet maps:

- `mapB` — BEFORE tiles, lives in left half of side-by-side panel
- `mapA` — AFTER tiles, lives in right half of side-by-side panel

The **slider** is a canvas screenshot of both maps — no third Leaflet instance needed.  
The **overlay** moves `mapA`'s DOM container into the overlay panel and draws a `L.imageOverlay` on top of it.

This design avoids the Leaflet `display:none` initialisation problem that causes blank maps when containers are hidden during setup.

---

## Repository Structure

```
satellite-damage-viewer/
├── index.html                          ← Full application (single file, no build)
├── README.md                           ← This file
├── CONTRIBUTING.md                     ← Contribution guide
├── python/
│   └── satellite_damage_detector.py    ← Python CLI for GeoTIFF / batch output
└── docs/
    └── user-guide.md                   ← Step-by-step usage guide
```

---

## Known Limitations

| Limitation | Detail |
|---|---|
| Wayback update lag | New snapshots publish every 2–4 weeks. Events in the last month may not yet have a new Wayback release. |
| Cloud cover | Optical imagery is blocked by clouds. For cloud-independent analysis use Sentinel-1 SAR via [Copernicus Browser](https://browser.dataspace.copernicus.eu). |
| Viewport-based detection | Detection analyses the current visible viewport, not a full geographic area. Zoom in close to a target site for best results. |
| No georeferenced output | The PNG export is a screenshot. For GIS workflows use the Python CLI which outputs GeoTIFF. |
| CORS on `file://` | Chrome blocks cross-origin requests when opening the file directly. Always serve via `python3 -m http.server`. |

---

## Extending the Project

### Add new Wayback releases

Fetch the live catalogue and extract new release numbers:

```bash
curl https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json \
  | python3 -m json.tool \
  | grep -E '"releaseDateLabel"'
```

### Add new preset locations

In `index.html`, add an entry to the `PRESETS` object:

```javascript
my_site: { lat: 25.100, lon: 55.200, z: 15 },
```

Then add a matching `<option>` to the preset `<select>`.

### Sentinel-1 SAR integration (cloud-independent)

SAR data from ESA works through clouds and at night. Free access:
- **Copernicus Browser**: https://browser.dataspace.copernicus.eu
- **ASF Vertex**: https://search.asf.alaska.edu

The Python CLI (`python/satellite_damage_detector.py`) can be extended to fetch Sentinel-1 GRD tiles via the Copernicus Data Space API and run the same change detection pipeline on radar backscatter.

---

## Data Sources & Attribution

| Source | Resolution | Licence |
|---|---|---|
| [ESRI World Imagery Wayback](https://livingatlas.arcgis.com/wayback/) | 0.3–0.5 m | Free, no commercial redistribution |
| [NASA GIBS](https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs) | 250–375 m | Public domain |
| [Leaflet.js](https://leafletjs.com) | — | BSD-2 |

ESRI World Imagery sources include Maxar, Airbus DS, USDA FSA, USGS, and the GIS User Community.

---

## Contributing

Contributions are very welcome. This project is intended to be a community tool for open-source conflict monitoring and geospatial journalism.

**Good first contributions:**
- Additional preset locations
- Updated Wayback release numbers as new snapshots publish
- Sentinel-1 SAR integration
- Copernicus/Sentinel-2 10 m true colour integration
- GeoJSON export of detected damage zones
- Better blob detection algorithm (morphological operations)
- Mobile/touch UX improvements

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Commit your changes with a clear message
4. Open a Pull Request with a description of what you changed and why

Please keep pull requests focused — one feature or fix per PR makes review much easier.

---

## Licence

MIT Licence — see `LICENSE` file for full terms.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software. Attribution appreciated but not required.

---

*Built by [Giulio Sistilli](https://github.com/GiulioSistilli) · Contributions welcome*

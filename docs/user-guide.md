# User Guide — Satellite Damage Viewer

*A step-by-step guide to detecting infrastructure damage using historical satellite imagery.*

---

## Table of Contents

1. [Getting started](#1-getting-started)
2. [Understanding the imagery source](#2-understanding-the-imagery-source)
3. [Choosing your location](#3-choosing-your-location)
4. [Selecting dates](#4-selecting-dates)
5. [Loading the maps](#5-loading-the-maps)
6. [View modes](#6-view-modes)
7. [Running damage detection](#7-running-damage-detection)
8. [Image enhancement](#8-image-enhancement)
9. [NASA fire layer](#9-nasa-fire-layer)
10. [Interpreting results](#10-interpreting-results)
11. [Exporting your analysis](#11-exporting-your-analysis)
12. [Tips for finding real damage](#12-tips-for-finding-real-damage)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Getting started

The tool is a single HTML file. To run it:

```bash
# In the project folder:
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser. Do **not** open the file directly with `file://` — this blocks the ESRI catalogue fetch due to browser CORS restrictions.

On startup the app automatically fetches the live Wayback release catalogue from ESRI. You will see a green notice in the sidebar once it loads. If you are offline or the fetch fails, a fallback list of verified release numbers is used instead.

---

## 2. Understanding the imagery source

### What is ESRI Wayback?

ESRI publishes a basemap called World Imagery, which is a mosaic of satellite and aerial photography at up to 0.3–0.5 metres per pixel — detailed enough to see individual cars and rooftops. Every time ESRI updates this basemap they archive the previous version in the **Wayback** service.

This means you can access genuinely different historical snapshots and compare them pixel by pixel. The catalogue currently goes back to early 2014, with new snapshots added every 2–4 weeks.

### Why not Google Maps or standard ESRI?

Those services only serve the **current** mosaic. If you request tiles from two different dates, you get the exact same image both times — so any change detection algorithm will find zero difference. Wayback solves this by serving each archived version under its own URL.

### What resolution can I expect?

At zoom level 14 (street level) you can see:
- Individual buildings and their footprints
- Large vehicles (trucks, planes, ships)
- Road markings and roundabouts
- Burn scars from fires
- Newly cleared land or rubble fields

At zoom level 16–17 you can see:
- Individual cars
- Rooftop damage
- Small craters
- Construction equipment

You cannot see people. The resolution limit is approximately 0.3–0.5 metres per pixel.

---

## 3. Choosing your location

### Using presets

The sidebar has a dropdown of 25+ preset locations across the Middle East, pre-tuned with appropriate zoom levels. Select one and the latitude, longitude, and zoom fields fill automatically.

Presets are grouped by country:
- **Iran** — capital, nuclear sites, oil infrastructure, naval bases
- **UAE** — Dubai, Abu Dhabi, petrochemical complexes
- **Saudi Arabia** — Riyadh, oil processing plants, NEOM
- **Qatar** — Doha, Ras Laffan LNG
- **Oman** — Salalah Port, Strait of Hormuz
- **Israel / Yemen** — Tel Aviv, Haifa, Hodeidah, Sanaa

### Manual coordinates

You can type any latitude and longitude directly. Useful for pinpointing a specific facility or impact site you have coordinates for from a news report.

### Zoom level

| Zoom | What you see |
|---|---|
| 10–11 | Entire city region |
| 12–13 | Neighbourhood level, large buildings |
| 14 | Street level — recommended starting point |
| 15–16 | Individual buildings clearly visible |
| 17–18 | Rooftop detail, small vehicles |

Start at zoom 13–14 to get an overview, then zoom in to zoom 16–17 once you identify something interesting.

---

## 4. Selecting dates

### How Wayback dates work

Each entry in the dropdown is a date when ESRI published an updated basemap. The most recent entry is **not today** — it is the last time ESRI published a new update, which happens every 2–4 weeks. This is expected behaviour, not a bug.

### Choosing a good before/after pair

For conflict damage analysis:
- Set **BEFORE** to a date before the event you are investigating
- Set **AFTER** to the most recent available date after the event

For the Iran/UAE conflict that began 28 February 2026:
- **BEFORE**: `2026-01-16` or earlier
- **AFTER**: `2026-02-26 ★ latest` (the most recent available at time of writing)

> **Important:** if you select the same date for both BEFORE and AFTER, the app will warn you — the tiles will be identical and damage detection will find nothing.

### Refreshing the catalogue

Click **↻ Refresh release list** in the sidebar to re-fetch the live catalogue. Do this if you opened the app a few weeks ago and want to check whether ESRI has published a newer snapshot.

---

## 5. Loading the maps

Click **↓ Load Maps**. The app will:

1. Show the side-by-side view briefly while Leaflet initialises both maps (this is intentional — it ensures maps load correctly)
2. Start streaming Wayback tiles for both dates
3. Switch to the view mode you had selected once tiles begin loading
4. Re-enable all buttons when ready

Tile loading continues in the background as you pan and zoom. You do not need to wait for every tile to appear before interacting with the map.

---

## 6. View modes

### Slider

The before image is on the left, the after image on the right. Drag the white divider handle left and right to reveal one or the other. Once you have run damage detection, the coloured overlay appears on the after (right) side.

This is the best mode for quick visual comparison — drag the slider across a building or landmark and watch it change between dates.

### Side by side

Both maps are shown simultaneously as equal panels, synchronized. Panning or zooming one map moves the other to match. The BEFORE date label appears on the left map, AFTER on the right.

This mode is best for examining two areas simultaneously without having to drag a slider.

### Overlay

Shows the AFTER map with the damage detection layer drawn on top. Each detected change zone is colour-coded and numbered. Use the **Overlay opacity** slider to blend the detection layer with the underlying imagery.

This mode only activates after you have run damage detection — the button will tell you if you switch to it too early.

---

## 7. Running damage detection

After loading maps, click **⚡ Run Damage Detection**. The app will:

1. Capture the current viewport from both the BEFORE and AFTER maps
2. Run per-pixel analysis across three change indices
3. Group changed pixels into blobs using connected-component analysis
4. Draw coloured bounding boxes around the top 40 largest change zones
5. Update the statistics panel

### What the colours mean

| Colour | Meaning |
|---|---|
| 🔴 Red | Fire index — red channel increased, green decreased. Typical of burn scars, explosions, and active fires. |
| 🔵 Blue | Dark index — overall brightness dropped. Typical of collapsed structures (rubble is darker than intact buildings), flooding, and burned-out areas. |
| 🟡 Amber | General change — significant pixel difference that doesn't match the fire or dark signatures. Covers construction, vegetation change, land use change. |
| 🟢 Green box | Bounding box around a flagged zone. `#1` is the largest detected region. |

### Sensitivity slider

The sensitivity slider controls the minimum pixel difference threshold before a pixel is flagged as changed.

- **Low (5–15):** flags very subtle changes — useful for detecting early-stage construction or small fires, but produces more false positives from cloud shadows, lighting differences between dates, and seasonal vegetation.
- **Medium (18–30):** recommended starting point. Balances sensitivity against noise.
- **High (40–80):** only flags dramatic changes — major fires, large collapsed areas. Reduces false positives significantly but may miss subtle damage.

If detection shows very low change (under 0.5%) the status bar will suggest adjustments.

### Detection only analyses what is visible

The algorithm captures whatever is currently in the viewport. To analyse a specific site, zoom into it first, then run detection. Panning or zooming after detection will not update the statistics — click Run again after repositioning.

---

## 8. Image enhancement

The three sliders in the sidebar apply a CSS filter to all map tiles:

| Slider | Effect |
|---|---|
| **Brightness** | Makes dark imagery easier to see. Push to 150–200% for night-edge tiles or hazy regions. |
| **Contrast** | Sharpens the difference between light and dark areas. Useful for seeing building shadows and edges more clearly. |
| **Saturation** | Increases colour vividness. Helps distinguish vegetation (green), bare earth (tan/brown), water (dark blue), and urban areas (grey). |

These filters are also applied to the canvas capture during damage detection — what you see is what gets analysed.

Click **Reset to defaults** to return to the calibrated defaults (120% brightness, 115% contrast, 130% saturation).

---

## 9. NASA fire layer

The optional NASA fire layer adds a semi-transparent overlay from NASA's GIBS service on top of both Wayback maps. It is separate from the damage detection — it shows low-resolution (250–375m) thermal or true-colour data from NASA satellites.

Available layers:

| Layer | What it shows | Best for |
|---|---|---|
| VIIRS Thermal Anomalies | Active fire hotspots in near-real-time | Finding active fires or recent explosion sites |
| MODIS Terra True Color | 250m true colour imagery | Cross-referencing with a different sensor |
| VIIRS NOAA-20 True Color | 375m true colour | Same, with a slightly different overpass time |

Set the NASA date to the day you want to look at, then select the layer. This is most useful for confirming whether a site that shows change in the Wayback comparison also had active thermal anomalies on a specific day.

---

## 10. Interpreting results

### What the numbers mean

- **Fire / burn %** — percentage of the visible viewport flagged as fire/burn index
- **Collapse / flood %** — percentage flagged as significant darkening
- **Total change %** — all flagged pixels combined
- **Zones flagged** — number of connected change regions, up to 40

A total change of under 1% usually means either the dates are too close together, the sensitivity is too high, or there genuinely was little change at that location. Between 5–20% typically reflects significant activity (construction, seasonal change, or damage). Above 20% in a dense urban area almost always indicates major structural events.

### Distinguishing damage from normal change

Not all flagged zones are damage. Common false positives:

| What you see | Likely cause |
|---|---|
| Large blue zones over water | Water surface changes with wind/sun angle between dates |
| Amber zones over farmland | Seasonal crop cycles |
| Red zones in desert | Shadow angle differences between seasons |
| Scattered noise across the whole image | Sensitivity too low — raise the threshold |
| Orange tiles (hidden automatically) | ESRI had no imagery update for that location in that release |

To distinguish real damage: zoom in to flagged zone `#1` and visually compare the before/after in slider mode. Real damage will show visible structural differences — missing buildings, rubble fields, black scorch marks, flooded streets.

---

## 11. Exporting your analysis

Click **↑ Export PNG** to save a side-by-side image with:
- BEFORE tiles on the left with date label
- AFTER tiles on the right with date label
- Damage detection overlay drawn on the after image (if detection was run)
- Location name and attribution footer

The export always captures the current viewport at full resolution. Zoom into the area of interest before exporting.

---

## 12. Tips for finding real damage

### For Iran conflict sites (post February 28, 2026)

1. Select a preset like **Kharg Island**, **Bandar Abbas**, or **Isfahan**
2. Set BEFORE to `2026-01-16` and AFTER to `2026-02-26 ★ latest`
3. Set zoom to 14–15
4. Click Load Maps
5. Run damage detection with sensitivity ~18
6. Check zone `#1` in slider mode — zoom to 16–17 to confirm

For nuclear/military sites that are typically obscured in commercial imagery, use the VIIRS Thermal Anomalies layer to look for heat signatures even where visual damage is unclear.

### For long-term change analysis

Pick dates 6–12 months apart for maximum visible change. ESRI updates its basemap with new imagery for different regions at different times — a location in Dubai may have been re-imaged in November while a location in Iran was last updated in June. The actual acquisition date of the underlying imagery may differ from the Wayback release date.

### Pair with SAR for cloud-penetrating analysis

When the region is cloud-covered (common over Iran in winter/spring), the optical Wayback imagery will show nothing — you'll see white cloud. For those cases, use Sentinel-1 SAR data from the [Copernicus Browser](https://browser.dataspace.copernicus.eu). SAR sees through clouds and at night, and change detection on SAR backscatter can detect collapsed buildings and flooded areas that optical imagery cannot.

---

## 13. Troubleshooting

### Maps don't load / stuck at "Loading maps…"

- Make sure you are running via `python3 -m http.server 8080`, not opening the file directly
- Check your browser console (F12) for CORS errors
- Try clicking **↻ Refresh release list** and loading again
- If a specific release shows no tiles, try an adjacent date — not all releases have updated imagery for every location

### Detection finds nothing (0% change)

- Check you haven't selected the same date for both BEFORE and AFTER (the app warns you)
- Try a wider date gap (e.g. 2024 vs 2026)
- Lower the sensitivity slider toward 10–12
- Make sure you're zoomed into a site with actual activity — open ocean or desert with no development will legitimately show no change

### Orange tiles visible

The orange/amber fill is ESRI's placeholder tile for releases where no updated imagery exists for that location. The app attempts to detect and hide these automatically by sampling the tile colour. If some slip through, try a different release date — pick one where the region was actively updated.

### Export is blank or black

This happens if you export immediately after loading before tiles have fully rendered. Wait a few seconds for tiles to appear on screen, then export. The export captures tiles from the live Leaflet map containers, which must be fully loaded.

### Slider shows no image

Switch to Side-by-side mode first to confirm tiles are loading correctly. Then switch back to Slider — the slider captures a screenshot of the side-by-side view, so both maps must be rendering. If side-by-side shows tiles correctly but slider is black, click Run Damage Detection (which re-triggers the capture) or reload the maps.

---

*Guide written by [Giulio Sistilli](https://github.com/GiulioSistilli) · Last updated March 2026*

"""
Satellite Damage Detector
=========================
Fetches before/after imagery from NASA GIBS API and uses OpenCV
to detect potential damage (fires, destroyed areas, flooding) by
comparing two dates over a region of interest.

Requirements:
    pip install requests opencv-python numpy Pillow matplotlib

Usage:
    python satellite_damage_detector.py

Default AOI: Tehran, Iran  (swap lat/lon for Dubai etc.)
"""

import requests
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION – edit these to change area / dates
# ─────────────────────────────────────────────────────────────────────────────

# Areas of Interest (lat_min, lat_max, lon_min, lon_max)
AREAS = {
    "Tehran, Iran":   (35.5,  36.0,  51.0, 51.7),
    "Dubai, UAE":     (25.0,  25.4,  55.1, 55.5),
    "Isfahan, Iran":  (32.5,  32.8,  51.5, 51.9),
}

# Choose your AOI
AOI_NAME   = "Tehran, Iran"

# Dates: before the conflict, and a recent date
DATE_BEFORE = "2026-02-20"   # Pre-conflict baseline
DATE_AFTER  = "2026-03-10"   # Post-strike

# NASA GIBS layer to use. Good options:
#   MODIS_Terra_CorrectedReflectance_TrueColor  (250m true color, daily)
#   VIIRS_NOAA20_Thermal_Anomalies_375m_All     (fire/heat detections)
#   MODIS_Terra_Land_Surface_Temp_Day           (land surface temperature)
LAYER      = "MODIS_Terra_CorrectedReflectance_TrueColor"
TILESET    = "250m"
ZOOM       = 7          # 0-9, higher = more tiles/detail (7 ≈ city level)

# ─────────────────────────────────────────────────────────────────────────────
# GIBS WMTS TILE FETCHER
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi"


def deg2tile(lat, lon, zoom):
    """Convert lat/lon to WMTS tile row/col for EPSG:4326."""
    n = 2 ** zoom
    col = int((lon + 180.0) / 360.0 * n)
    row = int((90.0 - lat) / 180.0 * n)
    return row, col


def fetch_tile(layer, tileset, zoom, row, col, date):
    """Fetch a single 256x256 WMTS tile as a numpy array."""
    params = {
        "Service":      "WMTS",
        "Request":      "GetTile",
        "Version":      "1.0.0",
        "layer":        layer,
        "tilematrixset": tileset,
        "TileMatrix":   zoom,
        "TileRow":      row,
        "TileCol":      col,
        "style":        "default",
        "TIME":         date,
        "Format":       "image/jpeg",
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    if resp.status_code == 200:
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return np.array(img)
    else:
        # Return grey tile if not available
        return np.full((256, 256, 3), 128, dtype=np.uint8)


def fetch_region(lat_min, lat_max, lon_min, lon_max, date, zoom=ZOOM):
    """Stitch multiple tiles together to cover a lat/lon bounding box."""
    row_min, col_min = deg2tile(lat_max, lon_min, zoom)
    row_max, col_max = deg2tile(lat_min, lon_max, zoom)

    rows = range(row_min, row_max + 1)
    cols = range(col_min, col_max + 1)

    print(f"  Fetching {len(rows)*len(cols)} tiles for {date}...")
    grid = []
    for r in rows:
        row_tiles = []
        for c in cols:
            tile = fetch_tile(LAYER, TILESET, zoom, r, c, date)
            row_tiles.append(tile)
        grid.append(np.hstack(row_tiles))
    return np.vstack(grid)


# ─────────────────────────────────────────────────────────────────────────────
# OPENCV DAMAGE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_damage(img_before, img_after):
    """
    Compare two images and detect significant changes that may indicate:
      - Fire / burn scars (increase in red channel, drop in green/NIR)
      - Destroyed structures (loss of texture / colour homogenisation)
      - Flooding (darkening in near-IR equivalent channels)

    Returns:
      diff_vis   – colour-coded difference heatmap
      mask       – binary mask of detected change regions
      contours   – list of contours around changed areas
    """
    # Resize both to same shape (in case tile count differs)
    h = min(img_before.shape[0], img_after.shape[0])
    w = min(img_before.shape[1], img_after.shape[1])
    b = cv2.resize(img_before, (w, h))
    a = cv2.resize(img_after,  (w, h))

    # Convert to float for arithmetic
    b_f = b.astype(np.float32)
    a_f = a.astype(np.float32)

    # ── 1. Overall change magnitude (all channels) ──────────────────────────
    diff = np.abs(a_f - b_f)
    change_magnitude = diff.mean(axis=2)   # (H, W)

    # ── 2. Fire/burn index: big increase in red, drop in green ──────────────
    red_gain   = a_f[:,:,0] - b_f[:,:,0]   # R increased  → fire/burn
    green_loss = b_f[:,:,1] - a_f[:,:,1]   # G decreased  → vegetation loss
    fire_index = np.clip((red_gain + green_loss) / 2, 0, 255)

    # ── 3. Darkening index (collapse, flooding) ──────────────────────────────
    brightness_before = b_f.mean(axis=2)
    brightness_after  = a_f.mean(axis=2)
    dark_index = np.clip(brightness_before - brightness_after, 0, 255)

    # ── 4. Threshold and clean up ────────────────────────────────────────────
    CHANGE_THRESH = 30.0   # pixels with > this mean-channel change flagged
    FIRE_THRESH   = 40.0
    DARK_THRESH   = 40.0

    mask_change = (change_magnitude > CHANGE_THRESH).astype(np.uint8) * 255
    mask_fire   = (fire_index       > FIRE_THRESH).astype(np.uint8)   * 255
    mask_dark   = (dark_index       > DARK_THRESH).astype(np.uint8)   * 255

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_change = cv2.morphologyEx(mask_change, cv2.MORPH_CLOSE, kernel)
    mask_fire   = cv2.morphologyEx(mask_fire,   cv2.MORPH_CLOSE, kernel)
    mask_dark   = cv2.morphologyEx(mask_dark,   cv2.MORPH_CLOSE, kernel)

    # Minimum region size filter (removes noise pixels)
    def remove_small(mask, min_area=200):
        nb, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        out = np.zeros_like(mask)
        for i in range(1, nb):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                out[labels == i] = 255
        return out

    mask_change = remove_small(mask_change)
    mask_fire   = remove_small(mask_fire)
    mask_dark   = remove_small(mask_dark)

    # ── 5. Build colour overlay ──────────────────────────────────────────────
    overlay = a.copy()
    # Fire/burns → red
    overlay[mask_fire > 0] = [220, 40, 40]
    # Darkening/collapse/flood → blue
    overlay[mask_dark > 0] = [40, 100, 220]
    # General change → yellow
    general = cv2.bitwise_and(mask_change,
                              cv2.bitwise_not(cv2.bitwise_or(mask_fire, mask_dark)))
    overlay[general > 0] = [230, 200, 30]

    # Alpha blend with after image
    diff_vis = cv2.addWeighted(a, 0.5, overlay, 0.5, 0)

    # Combined binary mask
    combined_mask = cv2.bitwise_or(mask_change, cv2.bitwise_or(mask_fire, mask_dark))

    # Contours for bounding boxes
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    return diff_vis, combined_mask, contours, mask_fire, mask_dark


def annotate_contours(image, contours, min_area=500):
    """Draw bounding boxes around detected change regions."""
    annotated = image.copy()
    count = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(annotated, (x, y), (x+w, y+h), (255, 255, 0), 2)
        cv2.putText(annotated, f"#{count+1}", (x, y-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
        count += 1
    return annotated, count


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    lat_min, lat_max, lon_min, lon_max = AREAS[AOI_NAME]

    print(f"\n{'='*60}")
    print(f"  Satellite Damage Detector")
    print(f"  AOI   : {AOI_NAME}")
    print(f"  Layer : {LAYER}")
    print(f"  Before: {DATE_BEFORE}   After: {DATE_AFTER}")
    print(f"{'='*60}\n")

    # ── Fetch imagery ──────────────────────────────────────────────────────
    print("[1/3] Fetching BEFORE image from NASA GIBS...")
    img_before = fetch_region(lat_min, lat_max, lon_min, lon_max, DATE_BEFORE)

    print("[2/3] Fetching AFTER image from NASA GIBS...")
    img_after  = fetch_region(lat_min, lat_max, lon_min, lon_max, DATE_AFTER)

    # ── Damage detection ───────────────────────────────────────────────────
    print("[3/3] Running OpenCV damage detection...")
    diff_vis, mask, contours, mask_fire, mask_dark = detect_damage(img_before, img_after)
    annotated, n_regions = annotate_contours(diff_vis, contours)

    print(f"\n  ✓ Detected {n_regions} significant change region(s)")

    # ── Plot results ───────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 4, figsize=(22, 6))
    fig.patch.set_facecolor("#0d1117")
    titles = [
        f"BEFORE  ({DATE_BEFORE})",
        f"AFTER   ({DATE_AFTER})",
        "Change Detection\n(overlay)",
        f"Annotated  [{n_regions} regions]",
    ]
    images = [img_before, img_after, diff_vis, annotated]

    for ax, title, img in zip(axes, titles, images):
        ax.imshow(img)
        ax.set_title(title, color="white", fontsize=9, pad=6)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_edgecolor("#30363d")

    # Legend
    legend_patches = [
        mpatches.Patch(color="#dc2828", label="Fire / burn scar"),
        mpatches.Patch(color="#2864dc", label="Darkening / collapse / flood"),
        mpatches.Patch(color="#e6c81e", label="General change"),
    ]
    axes[2].legend(handles=legend_patches, loc="lower left",
                   fontsize=7, facecolor="#161b22", labelcolor="white",
                   framealpha=0.85, edgecolor="#30363d")

    plt.suptitle(f"Satellite Damage Analysis  |  {AOI_NAME}  |  {DATE_BEFORE} → {DATE_AFTER}",
                 color="white", fontsize=11, y=1.01)
    plt.tight_layout()

    out_path = f"damage_analysis_{AOI_NAME.split(',')[0].replace(' ','_')}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"\n  Saved: {out_path}")
    plt.show()

    # ── Summary stats ──────────────────────────────────────────────────────
    total_px  = mask.shape[0] * mask.shape[1]
    fire_px   = np.count_nonzero(mask_fire)
    dark_px   = np.count_nonzero(mask_dark)
    change_px = np.count_nonzero(mask)
    print(f"\n  Change coverage : {change_px/total_px*100:.2f}% of AOI")
    print(f"  Fire/burn area  : {fire_px/total_px*100:.2f}% of AOI")
    print(f"  Dark/collapse   : {dark_px/total_px*100:.2f}% of AOI")
    print()


if __name__ == "__main__":
    main()

# Contributing to Satellite Damage Viewer

Thank you for your interest in contributing. This project is maintained by [Giulio Sistilli](https://github.com/GiulioSistilli) and is open to contributions from anyone.

---

## What We're Looking For

All contributions are welcome. Particularly useful:

- **New preset locations** — additional sites of geopolitical or strategic interest
- **Updated Wayback release numbers** — as ESRI publishes new snapshots
- **Sentinel-1 SAR integration** — cloud-independent analysis
- **Copernicus/Sentinel-2 integration** — free 10 m true colour imagery
- **GeoJSON export** — export detected damage zones as georeferenced polygons
- **Better blob detection** — morphological operations, watershed segmentation
- **Mobile UX improvements** — touch events, responsive layout
- **Performance improvements** — Web Workers for the detection pipeline
- **Bug fixes** — especially around tile loading and canvas capture

---

## How to Contribute

1. Fork the repository on GitHub
2. Create a feature branch: `git checkout -b feature/your-improvement`
3. Make your changes
4. Test locally via `python3 -m http.server 8080`
5. Open a Pull Request with a clear description of what changed and why

Please keep PRs focused — one feature or fix per PR makes review much faster.

---

## Code Style

- Plain HTML/CSS/JS — no build tools, no frameworks, no bundlers
- Keep everything in `index.html` unless adding a genuinely standalone utility
- Comment non-obvious logic, especially around Leaflet quirks
- Prefer clarity over cleverness

---

## Reporting Issues

Open a GitHub Issue with:
- What you were trying to do
- What happened instead
- Browser and OS
- Any console errors (F12 → Console)

---

*Maintained by [Giulio Sistilli](https://github.com/GiulioSistilli)*

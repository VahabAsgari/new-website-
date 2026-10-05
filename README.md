# Joveyra — website

Static site. No build step: open `index.html`, or serve the folder with any static host.

```
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Pages

| Page | Process | Purpose |
|---|---|---|
| `index.html` | Line engraving | The firm: method, people, stewardship, contact |
| `firm.html` | Cyanotype | Conduct and record — performance without numbers |
| `platform.html` | Cyanotype | The trading platform for the Middle East |

## The two processes

All imagery is public-domain museum material (The Met Open Access), re-printed in code
so every image obeys one rule:

- **Engraving** — the paper of the print becomes Joveyra blue, the ink becomes black.
  Only the engraved lines carry the image.
- **Cyanotype** — light becomes paper white, shadow becomes Prussian blue, with
  uneven exposure, grain and a brushed emulsion edge.

To add or change an image, edit the manifest in `tools/build_images.py` and run:

```
pip install opencv-python-headless numpy
python3 tools/build_images.py
```

## System

- Type: Antonio (display), EB Garamond (text), IBM Plex Mono (labels) — self-hosted in `assets/fonts`.
- Colour: engraving blue `#0f2160`, Prussian `#06204f`, paper `#e9edf6`, copper `#c47c4a` (details only).
- Motion: Lenis inertial scroll, images on a deeper parallax plane, slow reveals,
  cross-page view transitions. All motion is disabled under `prefers-reduced-motion`.

## Open items

- Persian edition (`FA`) — copy and typeface to be supplied.
- Contact addresses (`office@`, `platform@`) are placeholders.
- Platform name.
- Legal text to be reviewed by counsel before launch.

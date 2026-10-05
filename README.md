# Joveyra — website

Static site. No build step: open `index.html`, or serve the folder with any static host.

```
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Pages

| URL | Process | Purpose |
|---|---|---|
| `/` | Line engraving | The firm: how we work, people, careers problem, questions |
| `/firm/` | Cyanotype | Disclosure, principles, investor questions (no performance figures) |
| `/product/` | Cyanotype | The Joveyra Platform for the Middle East |

The home page opens with a short drawn film (Galileo's notebook of Jupiter's moons,
January 1610, becoming the Joveyra mark). It plays once per visit; click or Escape skips it.
The footer of `/` and `/firm/` carries a live engraving of Jupiter whose four moons move
at their real orbital periods.

## Images

All imagery is public domain, re-drawn in code by `tools/build_images.py`:

- **Engraving** — the print is reduced to its lines (two tones only), cut out of its paper,
  and its edges dissolve through an ordered dither. Lines are drawn in paper colour on ultramarine.
- **Cyanotype** — light becomes paper, shadow becomes Prussian blue, with uneven exposure,
  grain and a brushed emulsion edge.
- **Diagrams** (`tools/diagrams.py`) — Galileo's Jupiter observations, Kepler's nested solids,
  Huygens's cycloidal pendulum, Galton's board, a Persian star rosette, drawn from their geometry.

Sources are listed in `SOURCES` inside `tools/build_images.py`; put them in `tools/source/`
(not committed) and run:

```
pip install opencv-python-headless numpy
python3 tools/build_images.py
```

## System

- Type: Roboto Flex (variable; condensed widths for headings, normal for text), IBM Plex Mono
  for tags, Vazirmatn for Persian. All self-hosted in `assets/fonts`.
- Colour: ultramarine `#1424c4`, deep `#0b1675`, paper `#eceef4`; cyanotype pages use
  Prussian `#123b80` / `#06204f` on `#efeee8`.
- Motion: Lenis inertial scroll, dither development of plates on arrival, the opening film,
  the Jupiter footer. All of it is disabled under `prefers-reduced-motion`.

## Open items

- Persian edition (`FA`) — copy and typeface to be supplied.
- Contact addresses (`office@`, `platform@`) are placeholders.
- Platform name.
- Legal text to be reviewed by counsel before launch.

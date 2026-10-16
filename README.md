# OBEREK RUE

GitHub Pages site for the OBEREK RUE: open environmental monitoring for l'Albufera de València.

All page content lives in [`_data/rue.yml`](_data/rue.yml). Edit that file; `index.html` only handles layout.

- To publish a link under **Access**, add a `url:` to that item. Items without one show as "coming soon".
- The promo list is empty for now. Add items as shown in the comments in `rue.yml`.
- Logos shown on the page are web-sized copies in `assets/img/`. The original packs (`EU Emblem/`, `RURBANIVE logos & brandbook/`) are kept for reference and left out of the published site.

## Tutorials

Three tutorials live under [`tutorials/`](tutorials/) and share the layout in `_layouts/tutorial.html`:

| Page | For | Refreshed by |
|---|---|---|
| `tutorials/dashboard.md` | farmers, residents, everyone | `scripts/capture_screenshots.py` |
| `tutorials/live-data.md` | developers, AI agents | by hand (see below) |
| `tutorials/research.md` | researchers | `scripts/build_research_page.py` |

The dashboard data changes every day, so the screenshots and results are made by scripts, not by hand.
The scripts only read public data. They never write to the dashboard or the bucket.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install playwright pyyaml pillow boto3 pandas matplotlib rdflib requests nbformat nbclient ipykernel
playwright install chromium
```

**Screenshots (dashboard tutorial).** `python scripts/capture_screenshots.py` retakes every shot, or pass shot
names to retake only those (`python scripts/capture_screenshots.py kei-cards poll`). It overwrites the PNGs in
`assets/tutorials/img/dashboard/` and writes the marker positions and capture date to `_data/screenshots.yml`.
The page draws the numbered markers on top of the images, so they follow the new layout. To add a shot,
add it to `SHOTS` in the script and put `{% include shot.html id="…" caption="…" %}` on the page. The marker
numbers in the captions must match the order of the `markers` list.

**Research results.** `python scripts/build_research_page.py` runs `tutorials/code/rederive_dashboard.ipynb` against
live data and rewrites `_includes/research-notebook.md` and the figures. The notebook reads the metadata and ontology
published in [NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code); pass `--metadata` and
`--ontology` to try local copies instead.

**Live-data pictures.** `cd tutorials/code && python follow_station.py --once --out ../../assets/tutorials/img/live-data/southwest-6h.png`
redraws the six-hour picture (update the date and message count in its caption in `tutorials/live-data.md`). The animated GIF is a recording of 16 real one-minute checks; if you record a new
one, update the time, number of checks and image size in `_data/live_capture.yml`.

**Metadata, ontology and code.** These are not kept in this repository. They are published with the pipelines in
[NeverBlink-labs/oberek-code](https://github.com/NeverBlink-labs/oberek-code), with a snapshot of the code and the data on
Zenodo ([10.5281/zenodo.23418104](https://doi.org/10.5281/zenodo.23418104)). The tutorials link to both.

**Naming the data sources.** Use the names the dashboard's Help page uses: the weather data comes from the
**Tancat de l'Estell** station of **Fundació Assut** (part of the AVAMET network); it is the only weather station and
belongs to the South location. Flow data comes from the **Confederación Hidrográfica del Júcar (CHJ)**, water sensors from
**OBEREK / UPV**, satellite data from **Copernicus Sentinel-2**.

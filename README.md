# SPT3G Cutout Viewer

An interactive Dash web app for browsing, annotating, and analyzing multi-wavelength cutouts of SPT3G sources.  
The viewer is designed for use within the SPT collaboration, providing a fast and flexible way to explore cutouts 
from **SPT**, **MeerKAT**, and **SPIRE** data, along with SED fitting results and metadata.

---

## Features

- **Interactive Cutout Viewer** — Browse through individual sources with multi-band cutouts.  
- **Catalog Integration** — Search, filter, and highlight sources directly from the main catalog table.  
- **Map Linking** — Hover over a table row to highlight the corresponding source on the sky map; click to open the viewer page.  
- **Notes & Annotation** — Record and save per-source notes.  
- **Theme Switching** — Light and dark modes applied consistently across pages.   

[//]: # (---)

[//]: # (## Structure)

[//]: # ()
[//]: # (The app is modularized for maintainability and collaboration:)

[//]: # ()
[//]: # (```)

[//]: # (dash_spt3g_viewer/)

[//]: # (├── app.py                  # Entry point)

[//]: # (├── layouts/)

[//]: # (│   ├── home.py             # Map + catalog table)

[//]: # (│   ├── viewer.py           # Multi-band image viewer)

[//]: # (│   └── components/         # Reusable UI elements)

[//]: # (├── callbacks/)

[//]: # (│   ├── map_callbacks.py)

[//]: # (│   ├── viewer_callbacks.py)

[//]: # (│   └── shared_callbacks.py)

[//]: # (├── assets/                 # CSS, JS, and favicon)

[//]: # (├── data/                   # Example catalogs and cutouts)

[//]: # (└── utils/                  # Helper functions &#40;I/O, theming, etc.&#41;)

[//]: # (```)

[//]: # (---)

[//]: # (## Installation)

[//]: # ()
[//]: # (1. Clone the repository:)

[//]: # (   ```bash)

[//]: # (   git clone https://github.com/<your-username>/spt3g-cutout-viewer.git)

[//]: # (   cd spt3g-cutout-viewer)

[//]: # (   ```)

[//]: # ()
[//]: # (2. Create and activate a virtual environment:)

[//]: # (   ```bash)

[//]: # (   python -m venv venv)

[//]: # (   source venv/bin/activate   # &#40;or venv\\Scripts\\activate on Windows&#41;)

[//]: # (   ```)

[//]: # ()
[//]: # (3. Install dependencies:)

[//]: # (   ```bash)

[//]: # (   pip install -r requirements.txt)

[//]: # (   ```)

[//]: # ()
[//]: # (4. &#40;Optional&#41; Set environment variables for external data paths or API keys:)

[//]: # (   ```bash)

[//]: # (   export CUTOUT_DATA_PATH=/path/to/cutouts)

[//]: # (   ```)

---

## Usage

The app can be accessed [here](https://d16m38n1h1vao6.cloudfront.net/). Alternatively, to run the app locally:
```bash
python app.py
```

Then open your browser to [http://127.0.0.1:8050](http://127.0.0.1:8050).

[//]: # (---)

[//]: # ()
[//]: # (## Roadmap)

[//]: # ()
[//]: # (- [ ] User authentication &#40;per-user notes&#41;)

[//]: # (- [ ] Cloud backend &#40;Firebase or S3&#41;)

[//]: # (- [ ] Advanced filtering and cross-matching tools)

[//]: # (- [ ] MBB parameter visualization panel)

[//]: # (- [ ] Export annotated results to PDF/CSV)

---

## Acknowledgements

This app was developed as part of ongoing work within the **SPT collaboration**, incorporating data from **SPT**, 
**MeerKAT**, and **SPIRE**.  
Built with [Plotly Dash](https://dash.plotly.com/).
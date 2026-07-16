# `ml/` — Squat model training (Phase 5)

## Setup

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Editable install of the backend's `app` package — this is how ml/ imports
# backend/app/module_b's feature functions directly instead of re-implementing
# them (X1: runtime feature parity enforced by construction, not discipline).
pip install -e ../backend
```

Verify the install worked:

```bash
python3 -c "from app.module_b.core.features import FeatureVector; print(FeatureVector)"
```

`../backend/pyproject.toml` exists solely to make this editable install possible — it
does not replace `backend/requirements.txt` as the FastAPI app's own dependency list.

## macOS / Apple Silicon note (Stage 5.2)

MediaPipe Python's GPU delegate is Ubuntu-only. On macOS it errors. `extract_landmarks.py`
must use `delegate=CPU` (XNNPACK) — this is the correct and only path here, not a bug to
"fix" later.

## Report convention

Every `ml/reports/*.md` file embeds its figures inline
(`![caption](figures/whatever.png)`), not just links to the folder, so a report reads
correctly if copied straight into the FYP appendix. All figures go through
`scripts/plotting.py`'s `save_fig()` — fixed DPI (150), one shared style — no script
sets its own DPI/style ad hoc.

## Layout

```
ml/
├── config.yaml       # dataset paths (committed), model asset path, seeds
├── requirements.txt
├── docs/              # schema references
├── scripts/           # one script per pipeline stage
├── data/              # gitignored — landmarks cache, feature CSVs (regenerable)
├── artifacts/         # committed — *.joblib, feature_schema.json, label_map.json
└── reports/
    ├── figures/        # committed — all .png outputs
    └── *.md            # committed — DATA_AUDIT.md, SQUAT_*_REPORT.md, etc.
```

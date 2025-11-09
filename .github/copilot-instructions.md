## Repo overview

This repository builds a small desktop dashboard and forecasting pipeline for regional economic risk driven by socioeconomic CSV datasets and IBM watsonx.ai time-series models.

Key components
- UI (PyQt6): `main.py`, `ui/dashboard.py` — a desktop app that renders a Folium heatmap and Plotly charts from processed CSVs.
- Data preprocessing: `utils/preprocessing.py` and `models/predictor.py` (preprocessing logic is also present in `predictor.py`).
- Forecasting: `models/predictor.py` — uses `ibm_watsonx_ai` TS model client to forecast `risk_index` and saves CSV outputs.
- LLM summarization/inference client: `models/watsonx_client.py` — lightweight `requests` wrapper calling watsonx text-generation endpoints.
- Config: `utils/config.py` centralizes env names and `DATA_PATHS`.

Primary dataflow (what to look for)
- Raw CSVs: `data/*.csv` (examples: `federalEmploymentByCounty.csv`, `snapParticipationByCounty.csv`, `unemploymentByCounty.csv`, `costOfLivingByCounty.csv`).
- Preprocess & merge: `preprocess_data()` in `models/predictor.py` and helpers in `utils/preprocessing.py` create derived features and a `risk_index` per county/region.
- Forecast: `forecast_risk()` in `models/predictor.py` calls the IBM time-series model and writes predictions (default CSV: `predicted_regional_risk.csv`).
- UI reads processed CSVs (expected: `data/processed/regional_risk.csv`) and expects point columns `lat`, `lon`, and `risk_score` to render the heatmap.

Environment & secrets
- The project uses a `.env`/environment variables. Key names: `API_KEY`, `PROJECT_ID`, `ENDPOINT` (or `WATSONX_URL`), and optionally `IAM_TOKEN`.
- Config helper: `utils/config.py` — consult this file before changing env var names.

Patterns & conventions to follow when coding here
- Column normalization: code normalizes CSV headers (strip, lower, replace spaces/hyphens) and maps variants to canonical names such as `county`, `state`, `population`, `federal_employment`, `snap_households`, `unemployment_rate`, `cost_index`.
- Join keys: merges expect `county` + `state` (lowercased, whitespace-trimmed). If a file is missing those keys, the code logs and raises a KeyError.
- Encoding-tolerant CSV read: `predictor._read_csv_flexible()` tries multiple encodings and falls back to decoding with replacement — follow the same defensive pattern for new CSV readers.
- Logging: long-running/IO scripts log to files (`predictor.log`, `preprocessing.log`) — prefer adding messages to these logs for operational diagnosis.
- Fault tolerant API calls: `watsonx_client` uses requests with a Retry strategy; `models/predictor.py` also uses the official `ibm_watsonx_ai` client for time-series inference.

Quick dev workflows (discoverable/verified)
- Install dependencies:
```cmd
python -m pip install -r requirements.txt
```
- Run the desktop UI:
```cmd
python main.py
```
- Run preprocessing (standalone):
```cmd
python utils\preprocessing.py
```
- Run the predictor (preprocess + forecast):
```cmd
python models\predictor.py
```

Important integration notes / gotchas
- There is a reference to `FASTAPI_BASE_URL` in `main.py` but no FastAPI backend in this repo; do not assume a running backend unless added separately.
- Two different watsonx access patterns coexist: `models/predictor.py` uses `ibm_watsonx_ai` SDK while `models/watsonx_client.py` posts directly to a text-generation endpoint — be careful to reuse configuration and tokens (`API_KEY`, `IAM_TOKEN`) rather than duplicating secrets handling.
- UI expects `data/processed/regional_risk.csv` with `lat`,`lon`,`risk_score` — if your pipeline outputs different column names, add a small adaptor step in `utils/preprocessing.py` or `models/predictor.py`.

Files to check when debugging
- `predictor.log`, `preprocessing.log` — primary logs.
- `data/processed/` — processed CSV artifacts consumed by the UI.
- `requirements.txt` — GUI needs `PyQt6` and `PyQt6-WebEngine` (WebEngine required to render Folium/Plotly HTML).

If you modify data schemas
- Update the normalization map in `models/predictor.py::_normalize_and_map()` and add unit checks where `load_data()` or `preprocess_data()` validate required columns.

When in doubt, prefer small, observable changes that preserve existing CSV formats consumed by the UI. Ask for missing runtime details (e.g., backend endpoints or credentials) rather than hardcoding them.

---
If you want this merged differently (preserve an older `copilot-instructions.md`), paste the old content and I will merge it while preserving useful lines above.

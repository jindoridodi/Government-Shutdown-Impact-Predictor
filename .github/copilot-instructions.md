[//]: # (Auto-merged, concise guidance for AI coding agents)

## Repo snapshot

This repository builds a small desktop dashboard (PyQt6) and a forecasting pipeline that ingests county-level CSVs and produces a regional risk CSV used by the UI. Forecasting uses IBM watsonx time-series/LLM clients.

## What matters for contributors/agents

- Primary entry points: `main.py` (desktop UI), `models/predictor.py` (preprocess + forecast), `utils/data_processing.py` (helpers).
- Processed artifact consumed by UI: `data/processed/regional_risk.csv` with columns `lat`, `lon`, `risk_score` (UI depends on these names).
- Data sources: `data/*.csv` (examples: `federalEmploymentByCounty.csv`, `snapParticipationByCounty.csv`, `unemploymentByCounty.csv`, `costOfLivingByCounty.csv`).

## Quick commands (Windows cmd.exe)

Install deps

```cmd
python -m pip install -r requirements.txt
```

Run UI

```cmd
python main.py
```

Run preprocessing only

```cmd
python utils\data_processing.py
```

Run full predictor (preprocess + forecast)

```cmd
python models\predictor.py
```

## Dataflow & architecture (short)

- Raw CSVs -> normalization & merge (utils/data_processing.py, models/predictor.py) -> derived features and `risk_index` -> optional time-series forecast (models/watsonx_ts_client.py / ibm_watsonx_ai usage) -> write `data/processed/regional_risk.csv`.
- UI reads that processed CSV to render a Folium heatmap + Plotly charts inside a PyQt6 window.

## Project-specific conventions to follow

- Column normalization: code lowercases/strips headers and maps variants to canonical names. Keep new CSV readers tolerant to header variants.
- Join keys: merges rely on normalized `county` + `state` (lowercased, trimmed). Missing keys cause a KeyError — detect early and log clearly.
- Encoding-tolerant CSV reading: reuse the repo pattern that tries common encodings and falls back to replace-decoding when needed.
- Stable CSV schema for UI: do not rename `lat`, `lon`, `risk_score` without adding an adapter.

## Integration & external dependencies

- IBM watsonx: two access patterns exist —
	- SDK/time-series (used in `models/predictor.py` via `ibm_watsonx_ai`),
	- Direct HTTP client for text generation (`models/watsonx_client.py`) using requests + retry.
- Environment variables: check `utils/config.py`. Typical keys: `API_KEY`, `PROJECT_ID`, `ENDPOINT` / `WATSONX_URL`, and optionally `IAM_TOKEN`. Prefer loading via `utils/config.py` helpers.

## Logs and debugging

- Main logs: `predictor.log`, `preprocessing.log` (search root for `logger` usage). Add short, descriptive log messages for long-running jobs.
- When the UI shows empty map/charts, confirm `data/processed/regional_risk.csv` exists and contains expected columns.

## Files to inspect when changing behavior

- `main.py` — UI startup and environment references (note: `FASTAPI_BASE_URL` may be present but no backend is included).
- `models/predictor.py` — core preprocess + forecast orchestration; update normalization mapping here when schema changes.
- `utils/data_processing.py` — CSV helpers, normalization utilities.
- `models/watsonx_client.py` and `models/watsonx_ts_client.py` — networking and retries. Reuse their retry patterns for new API clients.

## Minimal guidance for AI edits

- Preserve CSV output names consumed by the UI unless you add a thin adapter.
- Reuse existing logging and CSV-reading patterns rather than introducing new I/O styles.
- Keep secrets out of the code; load them via `utils/config.py` / env vars.

## Next steps / if something is missing

If any runtime details are unclear (credentials, exact watsonx endpoints, or a missing backend), ask the repo owner — avoid hardcoding. If you want a longer agent doc (examples of common changes, unit tests, or CI), say so and I'll expand.

---
Please review this condensed version and tell me any sections you'd like expanded, or specific examples / commands to include.

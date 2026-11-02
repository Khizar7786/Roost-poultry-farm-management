---
tags:
  - time-series
  - poultry
  - tensorflow
  - xgboost
---

# Roost price forecast

## Model description

A hybrid model for Lahore farm-gate broiler prices. A 28-day-lookback LSTM
projects prices, and an XGBoost classifier estimates price direction and
confidence. The implementation runs inside the Roost Django backend.

Source repository: https://github.com/Khizar7786/Roost-poultry-farm-management.
Model revision paired with this application: **replace with the full commit SHA**.

## Files and usage

Distribute `lstm_model_28.keras`, `xgboost_clf.json`, `price_scaler.json`,
`metrics.json`, `prepared_history.csv`, and `manifest.json` together.
See the application's `docs/MODELS.md` for pinned downloads and loading.

Record the exact Python, TensorFlow/Keras, XGBoost, pandas, and NumPy
versions used for this release here before publishing.

## Data and evaluation

- Dataset source and attribution: **fill in the actual source and terms**.
- Training dates and train/test split: **fill in from the training run**.
- Last historical date bundled for inference: **read from `prepared_history.csv`**.
- Current recorded held-out direction accuracy: **0.80**, from `metrics.json`.
- Additional price-error metrics and evaluation procedure: **fill in from evaluation**.

Direction accuracy describes the classifier; it does not establish price
accuracy or future performance. The stored metric has not been independently
re-evaluated as part of the application API regression tests.

## Limitations

Forecasts advance from the bundled history's last date. The application
does not automatically ingest current prices. The model is specific to
the training market and feature definitions; new dates and market regimes
require updated data and evaluation.

## License and permissions

**Fill in the license for these weights and bundled history before making
this repository public.** Confirm dataset redistribution rights and any
upstream model terms. The application source's Apache 2.0 license does not
automatically establish permission to redistribute third-party data or models.
Set the model-card `license` metadata only after selecting the applicable terms.

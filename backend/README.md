# Roost — Backend

Django + Django REST Framework API for **Roost**, an AI-assisted
management system for broiler (meat chicken) farms. It handles auth,
farms/batches/feed/health/sales records, alerts, a role-aware
dashboard, and two real AI models: computer-vision chick counting and
a trained market price forecaster.

**Tech stack:** Django 5.2.18 LTS, Django REST Framework, JWT auth
(`djangorestframework-simplejwt`), SQLite, TensorFlow/Keras, XGBoost,
scikit-learn, pandas.

## Setup

Use Python 3.11. For a fresh checkout, model downloads, and full-stack
startup commands, see the [root README](../README.md) and
[model setup guide](../docs/MODELS.md).

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # optional — for /admin/
python manage.py runserver
```

The first price-prediction request lazily loads the LSTM/XGBoost
artifacts (~1-2s); every request after that is fast. Chick counting
needs outbound HTTPS access to `serverless.roboflow.com`.

The requirements use the plain `tensorflow` package for CPU inference.
The locally verified installation is Windows with Python 3.11; CI uses
Ubuntu with Python 3.11. For another platform, use the same requirements
with a compatible Python 3.11 interpreter and TensorFlow wheel.

### Environment variables

Defaults support local development. `ROBOFLOW_API_KEY` is required for
chick counting; the rest of the application can start without it.

| Variable | Default |
|---|---|
| `DJANGO_SECRET_KEY` | a dev-only fallback key (**set this in production**) |
| `DJANGO_DEBUG` | `1` |
| `DJANGO_ALLOWED_HOSTS` | `*` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` |
| `ROBOFLOW_WORKFLOW_URL` | `https://serverless.roboflow.com/fam-world/workflows/detect-count-and-visualize` |
| `ROBOFLOW_API_KEY` | empty — set your own key to enable chick counting |
| `ROBOFLOW_TIMEOUT_SECONDS` | `20` |
| `PRICE_FORECAST_CONF_THRESHOLD` | `0.70` — XGBoost predictions below this probability are flagged `low_confidence` |

`backend/.env.example` lists the configuration names. Django reads these
from the process environment; it does not automatically load a `.env` file.
Never put real keys in `.env.example`, source code, or the frontend.

Create a new key in your Roboflow workspace and revoke the previously
shared key there. From a PowerShell terminal in `backend/`, enter:

```powershell
$roboflowSecureKey = Read-Host "Paste your new Roboflow API key" -AsSecureString
$env:ROBOFLOW_API_KEY = [System.Net.NetworkCredential]::new("", $roboflowSecureKey).Password
.\venv\Scripts\python.exe manage.py runserver
```

The key applies to this terminal session and the server started from it.
Restart an existing backend after setting the variable. A missing key
returns a configuration error before sending an image to Roboflow.

## Regression checks

From `backend/`, run:

```powershell
.\venv\Scripts\python.exe manage.py test --noinput
```

These checks cover registration, JWT login/refresh, employee deactivation,
all three roles, farm isolation, vaccination/shed ownership, valid and
invalid feed quantities, stock changes between validation and saving,
rollback, and Roboflow configuration. They use Django's separate test
database and mock external calls, so they do not require API keys or model
downloads. The shared API suites are in `tests/`, with app-specific tests
in `accounts/tests.py`, `health/tests.py`, `batches/tests.py`,
`feed/tests.py`, and `ai_integration/tests.py`.

## The AI layer

`ai_integration/engine.py` exposes two functions —
`count_chicks(image_file)` and `predict_price(horizon_days)` — called
directly by `monitoring/views.py`.

```
ai_integration/
├── engine.py                          validation + dispatch (image decode, error → HTTP status mapping)
├── ml_artifacts/                       trained model files + manifest.json (size/MD5 per file, auto-generated)
├── scripts/
│   ├── retrain.py                      regenerates all price-model artifacts from an updated source CSV
│   └── data/agbro_broiler_prices_source.csv   the source dataset last used to train
└── inference/
    ├── roboflow_chick_counter.py       chick counting — hosted on Roboflow, called over HTTP
    ├── broiler_forecast.py             price forecasting — LSTM + XGBoost, runs in-process
    └── broiler_features.py             feature engineering + training pipeline for the price model
```

### Chick counting — hosted on Roboflow

`roboflow_chick_counter.py` base64-encodes the uploaded image and
POSTs it to a Roboflow workflow (`fam-world/detect-count-and-visualize`),
then normalizes the response into this app's standard `{count,
confidence, boxes, model_version, processing_time_ms}` shape. Roboflow
returns bounding boxes as center-x/y + width/height; these get
converted to top-left x/y/w/h to match the convention used everywhere
else in the app.

> **Note:** the response-parsing logic is tested against simulated
> response shapes and a mocked HTTP layer; if `serverless.roboflow.com`
> is unreachable from your network, this endpoint will fail outright.

### Price prediction — a real trained hybrid, runs in-process

`broiler_forecast.py` loads a trained 28-day-lookback LSTM (price
projection) and an XGBoost classifier (UP/DOWN direction + confidence)
from `ai_integration/ml_artifacts/`, and reproduces the day-by-day
iterative forecast loop the model was validated with — each day's
predicted price feeds into the next day's features. Held-out test
accuracy for the currently-shipped model is **80%** on direction.
`ai_integration/ml_artifacts/metrics.json` records that accuracy; the
historical cutoff comes from `prepared_history.csv`, not the metrics file.

The model carries its **own** historical market dataset
(`prepared_history.csv`) and forecasts the Lahore farm-gate market
price forward from its own last known date — it doesn't read any
individual farm's sales history, since a market-level forecast isn't
really about one farm's transactions.

**To retrain with newer data**, get an updated version of the source
CSV (same 26 columns as
`ai_integration/scripts/data/agbro_broiler_prices_source.csv` — `date`,
`lhr_farm`, `usdpkr`, `feed_price_50kg`, etc., extended with more
recent rows, no blank cells) and run:

```bash
python manage.py shell -c "
from ai_integration.scripts.retrain import main
main('/path/to/updated_source.csv')
"
```

This reruns the same training pipeline (same LSTM architecture, same
XGBoost hyperparameters, same feature engineering — see
`ai_integration/scripts/retrain.py` and
`ai_integration/inference/broiler_features.py`) and overwrites the five
runtime artifacts in `ai_integration/ml_artifacts/` plus `manifest.json`
(size + MD5 per file), which the loader checks automatically — you
never need to hand-edit any size/hash values. Restart the Django
process afterward to pick up the new model, since it's cached
in-process after first load.

**Why the model files are `.json`, not `.joblib`**: these artifacts
used to be pickled via `joblib`. On at least one real Windows setup,
the XGBoost pickle file failed to unpickle with a low-level "input
stream corrupted" error — despite being byte-for-byte identical (MD5
matched) and the installed xgboost version matching exactly what
trained it, which points to a platform-sensitivity bug in the
pickle/joblib layer rather than the model data itself. The classifier
now loads through XGBoost's own native serialization
(`Booster.save_model()`/`load_model()`), which is built to be portable
across platforms and library versions. The price scaler (previously a
pickled sklearn `MinMaxScaler`) is now a plain JSON dump of its two
fitted parameters, loaded by a ~10-line hand-written
`SimplePriceScaler` class — the transform itself is just `x * scale +
min`, simple enough not to need pickle at all. Both were verified to
produce bit-for-bit identical output to the original pickled versions
before the switch, and `joblib` is no longer a dependency.

Each artifact is loaded through a size + MD5 hash check against
`manifest.json`, so a corrupted or partially extracted file fails with
a specific, actionable message (which file, expected vs. actual) instead
of a raw low-level error. If that fires, it almost always means the
file got mangled after download — most commonly from extracting into a
cloud-synced folder (OneDrive/Dropbox can interfere with large binary
files mid-extraction) or an interrupted zip download. Fix: re-extract
into a plain local folder, or re-download the zip fresh.

## Full endpoint reference

| Method & Path | Who | Purpose |
|---|---|---|
| `POST /api/auth/register/` | anyone | create farm + owner account |
| `POST /api/auth/login/` | anyone | get JWT |
| `POST /api/auth/login/refresh/` | anyone (valid refresh token) | refresh JWT |
| `GET /api/auth/me/` | any logged-in user | current user profile |
| `POST /api/auth/employees/register/` | Owner | create an employee account |
| `GET /api/auth/employees/` | Owner | list your employees |
| `POST /api/auth/employees/<id>/deactivate/` | Owner | disable an employee |
| `GET /api/farms/mine/` | Owner/Employee | your farm's details |
| `GET/POST /api/farms/sheds/` | Owner/Employee (POST: Owner) | manage sheds |
| `GET/POST /api/batches/` | Owner/Employee (POST: Owner) | list/create flock batches |
| `GET/PUT/PATCH/DELETE /api/batches/<id>/` | Owner/Employee (write: Owner) | batch detail |
| `GET/POST /api/feed/stock/` | Owner/Employee (POST: Owner) | feed inventory |
| `GET/POST /api/feed/logs/` | Owner/Employee | log daily feed consumption |
| `GET/POST /api/health/vaccinations/` | Owner/Employee (POST: Owner) | vaccination schedule |
| `POST /api/health/vaccinations/<id>/administer/` | Owner/Employee | mark administered |
| `GET/POST /api/sales/` | **Owner only** | sales records |
| `GET/PUT/PATCH/DELETE /api/sales/<id>/` | **Owner only** | sale detail |
| `GET/POST /api/monitoring/counting-sessions/` | Owner/Employee | upload image → chick count (Roboflow) |
| `GET/POST /api/monitoring/mortality-events/` | Owner/Employee | manual mortality log |
| `GET /api/monitoring/price-predictions/` | **Owner only** | past forecasts |
| `POST /api/monitoring/price-predictions/trigger/` | **Owner only** | `{"horizon_days": 7}` → real LSTM+XGBoost forecast |
| `GET /api/alerts/` | Owner/Employee | alert feed (`?unacknowledged=true` filter) |
| `POST /api/alerts/<id>/acknowledge/` | Owner/Employee | acknowledge an alert |
| `POST /api/alerts/escalate-overdue/` | Owner/Employee | escalate overdue HIGH alerts (intended for a cron job) |
| `GET /api/dashboard/` | Owner/Employee | role-aware aggregated dashboard |
| `POST /api/chatbot/ask/` | any logged-in user | `{ "query": "..." }` |
| `GET /api/ai/status/` | any logged-in user | inference layer health |

### Price prediction response shape

```json
{
  "horizon_days": 7,
  "last_known_date": "2026-07-22",
  "last_known_price_pkr": 340.0,
  "model_accuracy": 0.80,
  "confidence_threshold": 0.7,
  "forecast": [
    {
      "day": 1, "date": "2026-07-16", "price_pkr": 293.36,
      "delta_pkr": -46.64, "delta_pct": -0.1372,
      "direction": "UP", "prob_up": 0.6797, "prob_down": 0.3203,
      "confidence": 0.6797, "low_confidence": true,
      "rsi14": 79.17, "macd_hist": 1.77,
      "events": ["High NDV risk", "RSI overbought", "Bullish momentum"]
    }
  ],
  "summary": {
    "up_days": 2, "down_days": 0, "uncertain_days": 3,
    "final_price_pkr": 305.37, "net_change_pkr": -34.63, "net_change_pct": -0.1019
  }
}
```

## App structure

```
accounts/       custom User model (role: OWNER/EMPLOYEE/ADMIN), auth endpoints, shared permissions
farms/          Farm, Shed
batches/        ChickBatch (age, mortality rate computed properties)
feed/           FeedStock, FeedConsumptionLog
health/         VaccinationRecord
sales/          SaleRecord (Owner-only)
monitoring/     CountingSession, MortalityEvent, PricePrediction
                — the views here call ai_integration.engine directly and persist results
alerts/         Alert (auto-created by other apps' business logic)
dashboard/      role-aware aggregation view, no models of its own
ai_integration/ engine.py + inference/ + ml_artifacts/ + scripts/retrain.py — the AI layer
chatbot/        keyword-matched FAQ responder — app features (chick counting, alerts, etc.)
                plus general poultry husbandry knowledge (vaccination schedule, feed
                program, common diseases, deworming). Swap for a real NLP/LLM service later.
```

## Permission model

Three roles — **Owner** (full access to their farm, staff management,
sales, price forecasts), **Employee** (daily operations: image
capture, feed logging, vaccination administration — no financial data,
no user management), **Admin** (system configuration, not farm
operational data).

`accounts/permissions.py` implements the split:
- `IsFarmOwner` — Owner only, scoped to their own farm.
- `IsFarmOwnerOrEmployeeReadOnly` — Owner gets full CRUD, Employee gets
  read-only, both restricted to their own farm.
- `IsFarmMember` — Owner or Employee, any method, own farm only — used
  for the specific actions employees are meant to do (image capture, feed
  logging, marking vaccinations administered, acknowledging alerts).

Every queryset in every view is filtered by the requesting user's
`farm_id` — there's no endpoint that returns another farm's data.

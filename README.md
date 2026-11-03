# Roost — Poultry Farm Management

Roost is a final-year project for managing broiler farms. A React frontend
connects to a Django REST API for farm records, batches, feed inventory,
vaccinations, mortality logs, sales, alerts, and staff accounts.

Chick counting calls a hosted Roboflow workflow. Market price forecasting
runs a trained LSTM and XGBoost classifier inside Django. Mortality is
logged manually. The chatbot uses a keyword-based FAQ service.

This monorepo also includes a standalone [chicken behavior pipeline](pipeline/README.md)
using YOLO and ByteTrack. The backend, frontend, and pipeline share this Git
repository; each component keeps its own dependencies and checks.

## Requirements

- Python **3.11**, Django **5.2.18 LTS**, and XGBoost **3.2.0** are the verified backend baseline.
- Node.js **22.12 or later in the 22.x series**, with npm.
- A Roboflow key and outbound HTTPS for chick counting.
- The separate price-model bundle for price forecasts. Other pages and the
  automated API tests can run without that bundle.

For a new isolated environment alongside an older installation, see
[environment alignment](docs/ENVIRONMENT.md).

The backend uses SQLite locally. Install dependencies from
[`backend/requirements.txt`](backend/requirements.txt) and
[`frontend/package-lock.json`](frontend/package-lock.json); virtual
environments and `node_modules` are excluded from source control.
The pipeline uses a separate Python environment under `pipeline/.venv`;
follow [its setup guide](pipeline/README.md) from the `pipeline/` directory.

## Run locally on Windows

Run these commands in PowerShell **from the repository root**, which
contains both `backend/` and `frontend/`:

```powershell
py -3.11 -m venv backend/venv
.\backend\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\backend\venv\Scripts\python.exe backend/manage.py migrate
$env:DJANGO_SECRET_KEY = (& .\backend\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))")
.\backend\venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

In a second PowerShell terminal, from the repository root:

```powershell
# On a fresh checkout, create the local frontend configuration.
Copy-Item frontend/.env.example frontend/.env
Set-Location frontend
npm.cmd ci
npm.cmd run dev -- --configLoader native --host 127.0.0.1 --port 5173 --strictPort
```

Open **http://localhost:5173**. The API runs on **http://localhost:8000**;
the backend root is not a landing page. Django administration is at
**http://localhost:8000/admin/**.

On macOS/Linux, create a Python 3.11 virtual environment with
`python3.11 -m venv backend/.venv`, use `backend/.venv/bin/python` in place
of the Windows interpreter path, and use `npm` in place of `npm.cmd`.

## Configuration

[`backend/.env.example`](backend/.env.example) lists backend variables.
Django reads the **process environment**; copying that template into a
`.env` file alone does not load it. Export the values in the same terminal
that starts Django, or configure them in your hosting service.

[`frontend/.env.example`](frontend/.env.example) is a Vite template. Copy
it to `frontend/.env` on a fresh checkout. Vite loads that file, and its
`VITE_` variables become public browser configuration. Store API keys only
in the backend environment.

To enable chick counting, obtain a new key from your own Roboflow
workspace. Before starting Django in the backend terminal:

```powershell
$roboflowSecureKey = Read-Host "Paste your Roboflow API key" -AsSecureString
$env:ROBOFLOW_API_KEY = [System.Net.NetworkCredential]::new("", $roboflowSecureKey).Password
```

Restart Django after changing environment variables. A missing Roboflow
key produces a configuration error for chick counting while the rest of
the application remains available.

## Accounts and roles

| Role | Registration | Access |
|---|---|---|
| Farm Owner | **Register your farm** in the frontend | Own farm, staff management, sales, forecasts, and daily operations |
| Farm Employee | Owner uses **Staff → Add employee** | Own farm's daily operations; no sales, forecasts, or staff management |
| System Admin | Django superuser setup and explicit `ADMIN` role | Django administration; no owner-only farm endpoints |

All farm data belongs to the logged-in user's farm. The backend enforces
permissions independently of the frontend navigation.

For optional administration, run `createsuperuser` using `backend/manage.py`.
The current user model defaults to `EMPLOYEE`, so explicitly assign the
`ADMIN` role to that superuser through Django administration. Superuser
flags and the application's role are separate fields. Do not commit a
database or create shared default passwords for a public demo.

To reset a password, run from the repository root:

```powershell
.\backend\venv\Scripts\python.exe backend/manage.py changepassword YOUR_USERNAME
```

## Automated checks

From the repository root:

```powershell
.\backend\venv\Scripts\python.exe backend/manage.py test backend --top-level-directory backend --noinput
.\backend\venv\Scripts\python.exe -m pip check
.\backend\venv\Scripts\python.exe backend/manage.py check
.\backend\venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
```

The explicit `backend` discovery directory keeps the API suite separate
from the standalone pipeline when running from the monorepo root.

The API suite covers registration, JWT login and refresh, deactivation,
roles, farm isolation, vaccination/shed ownership, feed validation, atomic
stock deduction and rollback, and Roboflow configuration. Tests use a
separate test database and mock external AI calls. Model downloads, real
API keys, and the development database are not required.

Build the frontend from `frontend/`:

```powershell
npm.cmd run build -- --configLoader native
```

The [GitHub Actions workflow](.github/workflows/ci.yml) runs three independent
jobs on pushes and pull requests: backend checks, the frontend build, and
pipeline dependency checks and unit tests. Run the pipeline suite from its
own directory and environment:

```powershell
Set-Location pipeline
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A browser end-to-end test suite is not included. Live Roboflow inference and
forecast quality require separate verification with the configured service/model bundle.

## Project layout

```text
backend/                  Django apps, REST API, migrations, API tests
backend/ai_integration/    Inference code and retraining scripts
frontend/                 React UI, Vite, Tailwind, npm lockfile
pipeline/                 Standalone YOLO/ByteTrack source, configuration, and tests
pipeline/dataset/         Dataset card, attribution, license, and YAML; binaries on Hugging Face
docs/MODELS.md            Model upload, download, and integrity instructions
docs/PUBLISHING.md        GitHub/Hugging Face publishing steps
LICENSE                   Apache License 2.0 for the Roost application and root documentation
LICENSES.md               License scopes for application, pipeline, and dataset
NOTICE                    Attribution for original project code
```

See the [backend guide](backend/README.md) for endpoint details and the
[frontend guide](frontend/README.md) for the UI structure. The
[pipeline guide](pipeline/README.md) covers behavior detection, training, and
its separate environment.

## Models and publishing

All application and pipeline source lives in this GitHub monorepo. Price-model
artifacts and behavior-detector weights belong in Hugging Face model repositories;
images and annotations belong in a Hugging Face dataset repository.
Follow [price-model setup](docs/MODELS.md), the [dataset card](pipeline/dataset/README.md),
and the [publishing guide](docs/PUBLISHING.md) for the corresponding paths and notices.

## License

The Roost application and root documentation use [Apache License 2.0](LICENSE).
The standalone pipeline uses [AGPL-3.0-only](pipeline/LICENSE). The source dataset
is identified as [CC BY 4.0](pipeline/dataset/LICENSE), with its notices and
modification record preserved under `pipeline/dataset/`.
See [LICENSES.md](LICENSES.md) for the component scopes and [NOTICE](NOTICE)
for attribution. Dependencies and separately published model bundles retain
their own terms; record weight and data provenance in their model cards.

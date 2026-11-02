# Backend environment alignment

The supported baseline is **Python 3.11 + Django 5.2.18 LTS**.
`backend/requirements.txt` pins Django exactly. The former Django 6.0.7
installation is not the validation baseline. XGBoost is pinned to 3.2.0,
TensorFlow to 2.21.0, and pandas to 3.1.0 for the current price-model stack.

## Clean installation on Windows

Run from the application root (the directory containing `backend/` and
`frontend/`). These commands create a separate environment; they preserve
any existing `backend/venv`, `backend/venv_old`, database, and model files.
Use a new, empty `backend/.venv` directory. If it already exists, choose
another unused environment name in these commands. Use the explicit
interpreter path even if your terminal already says `(venv)`.

```powershell
py -3.11 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install --upgrade pip
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\backend\.venv\Scripts\python.exe -m pip check
.\backend\.venv\Scripts\python.exe -c "import sys, django; print(sys.version); print(django.get_version()); assert django.get_version() == '5.2.18'"
.\backend\.venv\Scripts\python.exe backend/manage.py check
.\backend\.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\backend\.venv\Scripts\python.exe backend/manage.py test --noinput
```

After the checks, use this same interpreter for `migrate` and `runserver`
following the root README. Activation is optional. On Linux/macOS use
`python3.11 -m venv backend/.venv` and `backend/.venv/bin/python`.

CI installs the same requirements under Python 3.11, explicitly asserts
Django 5.2.18, runs `pip check`, and runs the Django checks and tests. The API
tests use a separate test database and mock remote AI calls. Forecast model
loading is a separate local check and requires the model bundle.

If pip reports no matching versions and your machine has `PIP_NO_INDEX=1`,
remove that setting in the terminal used for installation, or supply your
organization's approved package index. The public packages are on PyPI.

The independent chicken behavior pipeline has its own environment and
requirements. Do not install its PyTorch dependencies into this Django venv.

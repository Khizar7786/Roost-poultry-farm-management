# Price-model bundle

The GitHub monorepo contains application and behavior-pipeline source. This
guide covers the price-model bundle; behavior weights and dataset publishing
are documented in [the publishing guide](PUBLISHING.md) and
[the pipeline guide](../pipeline/README.md).
Publish the trained price-model bundle separately as a Hugging Face **model** repository.
The Hugging Face repository stores artifacts; uploading them does not
deploy the Django backend or automatically provide a working inference API.

## Required files

Upload these six files from `backend/ai_integration/ml_artifacts/` together:

| File | Purpose |
|---|---|
| `lstm_model_28.keras` | Trained price projection model |
| `xgboost_clf.json` | Trained direction classifier |
| `price_scaler.json` | Fitted price-scaling parameters |
| `metrics.json` | Recorded held-out direction accuracy |
| `prepared_history.csv` | Historical features required at inference time |
| `manifest.json` | Expected sizes and MD5 hashes for the five runtime artifacts |

The scaler and history are required, even though they are not model
weights. Keep the bundle from one training run together. Django loads it
from that local directory and checks files against the manifest. MD5 is
used to detect accidental file corruption, not to authenticate a publisher.
Download only from your trusted repository and pin its commit SHA.

## Upload your bundle

All commands below are PowerShell commands run **from the repository root**
after setting up `backend/venv` and its requirements:

```powershell
.\backend\venv\Scripts\python.exe -m pip install --upgrade huggingface_hub
.\backend\venv\Scripts\hf.exe auth login
$modelRepo = "YOUR_HF_USERNAME/roost-price-forecast"
.\backend\venv\Scripts\hf.exe repos create $modelRepo --private
.\backend\venv\Scripts\hf.exe upload $modelRepo ./backend/ai_integration/ml_artifacts .
```

`YOUR_HF_USERNAME` is a placeholder; no Hugging Face model repository is
configured in this source checkout. Replace it with your account name.
Keep authentication in the CLI's credential store or backend environment,
never in source code or a `VITE_` variable.

Create a model-card `README.md` in that Hugging Face repository. Start from
[`MODEL_CARD_TEMPLATE.md`](MODEL_CARD_TEMPLATE.md), then fill in the actual
repository links, dataset provenance, evaluation split, and rights to the
weights and data. Keep the repository private while those terms are unresolved.

After uploading, copy the full 40-character model commit SHA from its
history. Put that SHA and the model repository ID in the published project
instructions so a GitHub code version can be paired with its model version.

## Download after cloning the application

If needed, install `huggingface_hub` using the command above. Authenticate
with `hf.exe auth login` when the model repository is private, then run:

```powershell
$modelRepo = "YOUR_HF_USERNAME/roost-price-forecast"
$modelRevision = "FULL_40_CHARACTER_MODEL_COMMIT_SHA"
.\backend\venv\Scripts\hf.exe download $modelRepo lstm_model_28.keras xgboost_clf.json price_scaler.json metrics.json prepared_history.csv manifest.json --revision $modelRevision --local-dir ./backend/ai_integration/ml_artifacts
```

Both values are placeholders until the model is published. Use the actual
repository ID and commit SHA. On macOS/Linux, use the `hf` executable from
your active environment instead of the Windows `.exe` path.

With the backend requirements installed, validate the bundle and perform
a one-day inference without creating farm records:

```powershell
.\backend\venv\Scripts\python.exe backend/manage.py shell -c "from ai_integration.engine import predict_price; result = predict_price(1); print('Forecast loaded; history ends:', result['last_known_date'])"
```

Restart Django after replacing artifacts because the forecast engine is
cached in memory. If an integrity check fails, download the pinned bundle
again; do not bypass the manifest or mix artifacts from different runs.

## Retraining and evaluation

The original training CSV is excluded from GitHub. Obtain an authorized
copy of the documented source data and run the retraining steps in the
[backend guide](../backend/README.md). Retraining produces five runtime
artifacts plus the manifest; publish them together as a new model version.

The current `metrics.json` records **0.80 direction classification
accuracy**. This is a stored training-run metric, not a new independent
evaluation or a claim of 80% price accuracy. Forecasts advance from the
last date in the bundled historical data; they do not fetch current market
prices automatically.

Chick counting currently uses a hosted Roboflow workflow and requires
`ROBOFLOW_API_KEY`. The price bundle does not contain chick-counting weights.

## References

- [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli)
- [Hugging Face model cards](https://huggingface.co/docs/hub/model-cards)

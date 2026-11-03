# Chicken Behavior Detection Pipeline

Detect chickens with Ultralytics YOLO, track them with ByteTrack, and write
annotated video plus a CSV of movement-based behavior flags. This standalone
component lives under `pipeline/` in the Roost monorepo and uses its own Python
venv, requirements, and tests. The application guides are in [the root README](../README.md).

## Environment

Use **Python 3.11**. The requirements match the current environment:
Ultralytics 8.4.75, PyTorch 2.5.1, Torchvision 0.20.1, OpenCV 4.11.0.86,
and NumPy 2.4.6. From the monorepo root, run `Set-Location pipeline` first.
Then run these PowerShell commands from `pipeline/`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Existing CUDA 12.1 builds `torch==2.5.1+cu121` and
`torchvision==0.20.1+cu121` also satisfy the requirements. CPU is the default
for inference and all three training entry points. Choose GPU `0` explicitly
only after installing a suitable CUDA PyTorch build.

ByteTrack now comes from Ultralytics. The old mandatory BoxMOT 10 package
required NumPy 1.24.4 and Torchvision below 0.18, conflicting with the current
environment. It is no longer required. If reusing the old `venv` rather than
creating `.venv`, remove that unused package before checking dependencies:

```powershell
.\venv\Scripts\python.exe -m pip uninstall boxmot
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
```

`tracker.type` supports `bytetrack`. Unknown tracker names fail explicitly;
the previous incomplete DeepOCSort/StrongSort adapters are no longer exposed.
The thresholds in `tracker/bytetrack.yaml` are now actually applied.

## Dataset and model setup

`config.yaml` points at the committed `dataset/data.yaml`. Restore your image
and YOLO label files using [the dataset guide](dataset/README.md). The trainer
rejects missing or empty train/validation directories before loading weights.
A clean code checkout intentionally excludes the image and model binaries.

The dataset guide is also the Hugging Face dataset card. It preserves the
[source attribution](dataset/ATTRIBUTION.md), [CC BY 4.0 license](dataset/LICENSE),
[modification record](dataset/MODIFICATIONS.md), and original Roboflow notices.
The working validation set contains the original validation and test filenames
combined; it has no separate test split. Include all these notices when
redistributing data. See the dataset card for the exact upload layout.

The configured inference weights path is
`runs/detect/runs/train/chicken_yolov8s/weights/best.pt`, relative to `pipeline/`.
Download the trained weights from the corresponding Hugging Face **model**
repository before inference, then set `model.weights` or pass `--weights`.
Record that model repository ID and pinned revision when publishing the weights.

## Train

Edit the training options in `config.yaml`, then run:

```powershell
.\.venv\Scripts\python.exe train/train.py --config config.yaml
```

The trainer honors `model.device`, `model.pretrained_base`, and the complete
`training` section. CPU-safe defaults use zero workers, no AMP, and no image
cache. Ultralytics downloads the pretrained base model on first use if it
is not already available. Completed runs print the actual best-weights path,
including any automatically incremented run directory.

The argument-based alternatives remain available:

```powershell
.\.venv\Scripts\python.exe train.py --data dataset/data.yaml --device cpu
.\.venv\Scripts\python.exe trainRTDETR.py --data dataset/data.yaml --device cpu
```

The RT-DETR entry point uses Ultralytics' `RTDETR` class.

## Run inference

```powershell
.\.venv\Scripts\python.exe main.py --input farm_footage.mp4 --output output/annotated.mp4
# Override the configured trained model:
.\.venv\Scripts\python.exe main.py --input farm_footage.mp4 --weights models/chicken.pt
```

Paths inside `config.yaml` resolve relative to that file. CLI input, output,
and weight overrides resolve relative to your terminal's working directory.
The default configuration is found beside `main.py`, even from another
working directory. Results go to the chosen video output and the configured
CSV path (`output/behavior_log.csv`).

| Flag | Rule |
| --- | --- |
| Normal | No higher-priority rule applies |
| Huddling | Mean distance to up to K nearest other chickens is below the configured threshold |
| Possibly ill | Low movement for the complete configured window (30 seconds by default) |
| Possibly dead | Near-zero movement for the complete configured window (160 seconds by default) |

These are movement-based review flags, not diagnoses. The full configured
history is retained, and the possibly-dead rule takes priority over illness
and huddling. Thresholds depend on camera scale and frame rate.

## Tests and CI

The unittest suite covers portable configuration, CPU defaults, dataset
validation, configured training arguments, real ByteTrack identity/aging,
tracker thresholds, behavior timing and priority, trajectory eviction, and
CSV intervals. It needs no real dataset, model download, or GPU. Training is
mocked in unit tests; full training and model accuracy require your dataset.
The `pipeline` job in the [root GitHub workflow](../.github/workflows/ci.yml)
installs CPU dependencies, runs `pip check`, and executes the suite under
Python 3.11 on pushes and pull requests. Its working directory is `pipeline/`.

## What to publish

| Destination | Files |
| --- | --- |
| GitHub monorepo (`pipeline/`) | Python source, tests, configuration YAMLs, requirements, README, LICENSE, NOTICE, and dataset notices; CI lives in the root workflow |
| Hugging Face model repository | Trained `.pt`/exported model files and a model card with provenance, metrics, and license |
| Hugging Face dataset repository | Images, YOLO annotations, splits, dataset card, and source attribution/license |
| Local only | Virtual environments, caches, raw/private footage, generated videos/CSVs, run directories, private notes, secrets |

The `.gitignore` preserves local data and models while excluding them from
new commits. Before publishing, inspect `git status` and staged changes;
ignore rules do not remove files already tracked by Git.

## License

This pipeline is distributed under **GNU AGPL version 3 only**; see
[LICENSE](LICENSE) and [NOTICE](NOTICE). Ultralytics retains its own notices.
The Roost application uses Apache 2.0; see the [monorepo license scopes](../LICENSES.md).
Datasets and model weights require their own license/provenance records.

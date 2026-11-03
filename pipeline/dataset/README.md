---
license: cc-by-4.0
pretty_name: Combined Dataset - FYP working copy
size_categories:
  - 10K<n<100K
task_categories:
  - object-detection
---

# Combined Dataset: chicken detection

This is the FYP working copy of **Combined Dataset, version 1**, exported from
[the Roboflow source project](https://universe.roboflow.com/muhammads-workspace-a0tjd/combined-dataset-uqmyy/dataset/1).
It contains **11,954 images** with one YOLO class, **`0 = chicken`**.

## Credit and license

Credit the source contributor identified by Roboflow workspace
`muhammads-workspace-a0tjd`, project `combined-dataset-uqmyy`, version 1.
The supplied export does not name an individual creator. Read the complete
[source credit](ATTRIBUTION.md), [original provider notice](README.dataset.txt),
and [original export notice](README.roboflow.txt).

The dataset is supplied under **Creative Commons Attribution 4.0 International**:
[license summary](https://creativecommons.org/licenses/by/4.0/),
[legal terms](https://creativecommons.org/licenses/by/4.0/legalcode.en), and
[local license text](LICENSE). Keep attribution, supplied notices, the license,
and change history with redistributed data. Do not imply source endorsement.
The pipeline and Roost application have separate code licenses.

## Current splits and modification history

| Split | Images | Labels |
| --- | ---: | ---: |
| Training (`train/`) | 9,563 | 9,563 |
| Validation (`valid/`) | 2,391 | 2,391 |
| Separate test split | 0 | 0 |

The original archive has **9,563 train / 1,195 validation / 1,196 test** images.
The current validation filenames match the original validation and test sets
combined, for both images and annotations. This working copy therefore has
**no independent test split**. See [MODIFICATIONS.md](MODIFICATIONS.md) for the
observed merge, upstream preprocessing, and FYP configuration changes. Image
and label contents have not been fully compared against the archive.

The upstream notice records auto-orientation with EXIF orientation removal,
stretch resizing to 512 x 512, and no augmentation during the export. Retain
that supplied processing history when making further changes.

## Format and setup

```text
dataset/
  README.md
  ATTRIBUTION.md
  LICENSE
  MODIFICATIONS.md
  README.dataset.txt
  README.roboflow.txt
  data.yaml
  upstream/data.yaml
  train/images/*.jpg
  train/labels/*.txt
  valid/images/*.jpg
  valid/labels/*.txt
```

The training scripts expect this YOLO layout. Each label row is
`class cx cy width height`, with normalized coordinates in `[0, 1]`.
The active `data.yaml` has paths relative to that file and deliberately omits
an optional `path` key. Missing or empty train/validation image directories
are rejected before model loading. See `upstream/data.yaml` for the untouched
source configuration, which describes the original three-split export.

## GitHub and Hugging Face

Commit this card, configuration, license, attribution, modification record,
and original notice files to the GitHub code repository. The `.gitignore`
excludes image/annotation directories, dataset archives, and generated caches.

For Hugging Face, create a separate **dataset** repository and copy the
**contents** of this working `dataset/` directory into its root, including
`train/`, `valid/`, this `README.md`, all notice/license files, and `upstream/`.
The YAML front matter above records `license: cc-by-4.0`. Keep the original
credits and append any additional changes to `MODIFICATIONS.md` before a new
release. Model weights go to a separate **model** repository.

This card describes the current working copy. If publishing the original ZIP
instead, preserve its original three splits and update the card's counts and
modification description to match that release. Do not label the merged
validation copy as an unchanged original export.

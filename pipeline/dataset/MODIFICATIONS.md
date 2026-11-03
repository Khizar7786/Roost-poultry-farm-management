# Dataset modification record

Recorded **2026-11-02** against `Combined Dataset.Beahvdeetection.zip`.
The dates of earlier changes to the working data are not recorded.

## Upstream processing retained from the supplied notice

`README.roboflow.txt` states that the export has 11,954 images, YOLOv8
annotations, auto-oriented pixel data with EXIF orientation removed, and
images stretched to **512 x 512**. It states that no image augmentation
techniques were applied during that export. Keep that original notice with
redistributions; these statements describe the upstream export.

## Observed split changes in the working copy

| Split | Original archive images | Current working-copy images |
| --- | ---: | ---: |
| Training | 9,563 | 9,563 |
| Validation | 1,195 | 2,391 |
| Test | 1,196 | 0 |
| Total | 11,954 | 11,954 |

The current training image and label filename sets match the original training
sets. The current validation image and label filename sets match the union of
the original validation and test sets. This records an observed merge of the
original validation and test splits, performed before this documentation update.
There is no separate test split in this working copy. Metrics on this merged
validation set must not be described as results on an untouched test split.

These comparisons check filenames and counts. The image pixels and annotation
contents have not been fully compared with the archive; this record does not
claim they are byte-identical or that no other historical changes occurred.

## FYP configuration and documentation changes

On 2026-11-02, the FYP configuration was made portable:

- `train: ../train/images` became `train: train/images`.
- `val: ../valid/images` became `val: valid/images`.
- The active YAML omits `test: ../test/images` because this working copy has
  no separate test folder. The original configuration is retained under
  `upstream/data.yaml`.
- The class remains `0 = chicken`; the Roboflow source and CC BY 4.0 metadata
  are retained.
- The original notice files were restored and attribution, the full license
  text, and this modification record were added. This documentation update
  did not edit, move, or remove images or annotations.

The source ZIP contains three identical `data.yaml` entries; one unmodified
copy is retained in `upstream/data.yaml`.

Append future filtering, annotation corrections, resizing, augmentations,
merges, re-splitting, or other changes here with their date and scope. Keep
previous entries and the original source notices in every redistributed copy.

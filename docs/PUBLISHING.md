# Publish the monorepo, datasets, and models

All FYP source lives in one GitHub repository:
https://github.com/Khizar7786/Roost-poultry-farm-management.
It contains `backend/`, `frontend/`, and the standalone `pipeline/` component.
Each component has its own dependencies and checks.

## File destinations

| Destination | Contents |
| --- | --- |
| This GitHub monorepo | Backend/frontend/pipeline source, tests, configuration, requirements and npm lockfile, root workflow, docs, licenses, dataset card and source notices |
| Hugging Face price-model repository | The six-file price bundle described in [MODELS.md](MODELS.md), plus its completed model card |
| Hugging Face behavior-model repository | Selected trained `.pt`/exported weights and a model card with source, evaluation, applicable license, and pinned version |
| Hugging Face dataset repository | Images, YOLO annotations, split folders, and all dataset attribution/license/modification files |
| Local only | Python environments, `node_modules`, databases, account records, real environment files, uploads, private footage, generated outputs, and caches |

The root and pipeline `.gitignore` files exclude binary model files, dataset
images and annotations, archives, footage, environments, and runtime data.
These rules preserve files locally. They do not remove files already tracked
by Git. Inspect `git status`, `git diff --cached --stat`, and the staged diff
before each public push.

## GitHub updates

The repository is already initialized and `origin` points to the URL above.
Run from the repository root:

```powershell
git status --short
git add .
git diff --cached --stat
git diff --cached
git commit -m "Describe the source change"
git push origin main
```

Keep all three components in this repository. Create Python environments
individually in `backend/` and `pipeline/`, and install frontend dependencies
from `frontend/package-lock.json`.

The source licenses are scoped by component: Apache 2.0 for Roost,
AGPL-3.0-only for the standalone pipeline, and CC BY 4.0 for the identified
chicken dataset. Read [LICENSES.md](../LICENSES.md) and [NOTICE](../NOTICE).
Third-party dependencies and model releases retain their own terms.

Configure the replacement Roboflow key outside source and revoke any old
shared key in your Roboflow account. Databases containing registered users
and password hashes belong outside public Git history.

## Hugging Face artifacts

For price forecasting, upload all six runtime files together using
[MODELS.md](MODELS.md). Complete [the price-model card](MODEL_CARD_TEMPLATE.md)
with the weights license and bundled history's redistribution terms before
making that model repository public.

For chicken behavior detection, select the trained detector weights from the
training run and upload them to a separate Hugging Face **model** repository.
Record its architecture, class mapping, training-data source, evaluation split
and metrics, upstream terms, and applicable weights license in its model card.
Model binaries remain outside Git; download them into `pipeline/` and configure
`model.weights` or `--weights` using [the pipeline guide](../pipeline/README.md).

For the dataset, copy the contents of your populated `pipeline/dataset/`
folder into the root of a Hugging Face **dataset** repository. Include
`README.md`, `ATTRIBUTION.md`, `LICENSE`, `MODIFICATIONS.md`, the two original
Roboflow notices, `data.yaml`, `upstream/`, and the image/label split folders.
The GitHub checkout contains the metadata only; restore image and label files
from your authorized dataset copy before preparing that upload.

The [dataset card](../pipeline/dataset/README.md) describes the FYP working
copy: 9,563 training and 2,391 validation images, with the source validation
and test filenames combined. It has no separate test split. Preserve the
source credit, CC BY 4.0 terms, and modification record with redistributions.

After creating the Hugging Face repositories, put their actual IDs and pinned
commit revisions in the corresponding setup guides and cards. No artifact
repository ID is assumed by the source code.

## Automated checks

[The root workflow](../.github/workflows/ci.yml) runs three independent jobs on
pushes and pull requests with read-only repository permissions:

- Backend: Python 3.11, the pinned Django baseline, dependency consistency,
  configuration and migration checks, and API tests.
- Frontend: Node 22, `npm ci`, and the production build.
- Pipeline: Python 3.11, CPU PyTorch, dependency consistency, and unit tests
  from the `pipeline/` directory.

The checks use no real model files, dataset images, or API keys. Uploading
source and artifacts is separate from deploying a publicly accessible app.

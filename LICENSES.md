# License scopes

This monorepo contains independently documented components with different licenses.

| Scope | License | Text and notices |
| --- | --- | --- |
| Roost application: `backend/`, `frontend/`; root documentation, `docs/`, and root CI configuration | Apache-2.0 | [LICENSE](LICENSE), [NOTICE](NOTICE) |
| Standalone behavior pipeline: source, tests, configuration, and documentation under `pipeline/`, except the dataset notices below | AGPL-3.0-only | [pipeline/LICENSE](pipeline/LICENSE), [pipeline/NOTICE](pipeline/NOTICE) |
| Chicken dataset identified by the supplied export, plus its source and license notices under `pipeline/dataset/` | CC-BY-4.0 | [dataset license](pipeline/dataset/LICENSE), [attribution](pipeline/dataset/ATTRIBUTION.md), [modifications](pipeline/dataset/MODIFICATIONS.md) |
| Third-party dependencies, externally hosted models, and separately published weights or price history | Their respective upstream or release-specific terms | Dependency notices and the corresponding model/dataset cards |

The root Apache license describes the Roost application and root materials;
it does not replace the AGPL pipeline license or the dataset's CC BY notices.
The pipeline keeps its own environment and entry points. Adding its source to
this repository does not combine its runtime dependencies with the Django backend.

Dataset binaries and model weights are excluded from Git. Preserve their source
credit and applicable notices when publishing them on Hugging Face. For the price
bundle, document the weights license and bundled history's redistribution terms
in its model card.

"""
AI inference entry points, called directly by `monitoring/views.py`.

- `count_chicks` — real inference via a hosted Roboflow workflow (UC-01).
- `predict_price` — real inference via a trained LSTM + XGBoost hybrid,
  running in-process (UC-03).

See `ai_integration/inference/` for the implementations:
- `roboflow_chick_counter.py`: calls Roboflow's hosted detection workflow.
- `broiler_forecast.py` / `broiler_features.py`: the real trained price
  forecast model and its feature pipeline.

Note: behaviour detection (UC-06) was removed — it was only ever a local
computer-vision heuristic standing in for a trained model that was never
available, and has been dropped from the product entirely rather than
kept as a placeholder.
"""

from __future__ import annotations

from PIL import Image, UnidentifiedImageError

from .inference import broiler_forecast
from .inference import roboflow_chick_counter

MIN_IMAGE_DIMENSION = 32


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _load_image(image_file) -> Image.Image:
    try:
        image_file.seek(0)
    except (AttributeError, ValueError):
        pass
    try:
        img = Image.open(image_file)
        img.load()
        return img
    except (UnidentifiedImageError, OSError) as exc:
        # UC-01 alt. flow: poor / unreadable image -> ask for re-capture.
        raise AIServiceError("Could not read this image — please re-capture and try again.") from exc


def count_chicks(image_file) -> dict:
    img = _load_image(image_file)
    if img.width < MIN_IMAGE_DIMENSION or img.height < MIN_IMAGE_DIMENSION:
        raise AIServiceError("Image resolution is too low for a reliable count — please re-capture.")

    try:
        image_file.seek(0)
    except (AttributeError, ValueError):
        pass
    image_bytes = image_file.read() if hasattr(image_file, "read") else image_file

    try:
        return roboflow_chick_counter.count_from_image_bytes(image_bytes)
    except roboflow_chick_counter.RoboflowError as exc:
        raise AIServiceError(str(exc), status_code=502) from exc


def predict_price(horizon_days: int = 10) -> dict:
    if not 1 <= horizon_days <= 30:
        raise AIServiceError("horizon_days must be between 1 and 30.")
    try:
        return broiler_forecast.forecast(horizon_days)
    except Exception as exc:  # model file missing, bad artifact, etc.
        raise AIServiceError(f"Price forecast failed: {exc}", status_code=502) from exc


def health_check() -> bool:
    """Kept for API compatibility with the status endpoint / frontend."""
    return True


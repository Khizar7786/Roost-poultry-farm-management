"""
Chick counting (UC-01) — real inference via a hosted Roboflow workflow.

Unlike the earlier placeholder heuristic, this calls an actual trained
detection model hosted by Roboflow ("fam-world/detect-count-and-visualize"),
so counts and bounding boxes come from a real object-detection model, not
a local approximation.

IMPORTANT — one thing to verify once you have live network access:
Roboflow Workflows let you name your own output blocks, so the exact
JSON keys in the response depend on how that specific workflow was
built. This module was written from Roboflow's documented conventions
for a detect → count → visualize workflow (`predictions`, `count_objects`
/ `count`, `output_image`) and tries several fallback key names — but it
was **not possible to test against the live endpoint** in the sandbox
this was built in (`serverless.roboflow.com` isn't reachable there; the
network egress proxy returns `host_not_allowed`). Run one real request
via `test_roboflow_response_shape()` below (or just hit the endpoint
yourself and compare) and adjust `_extract_predictions()` if the actual
keys differ from what's assumed here.

Roboflow's object-detection predictions are given as **center** x/y +
width/height; `_normalize_box()` converts that to the top-left-corner
x/y/w/h convention the rest of this app (and the frontend's bounding-box
overlay) uses everywhere else.
"""

import base64
import time

import requests
from django.conf import settings

WORKFLOW_URL = getattr(
    settings,
    "ROBOFLOW_WORKFLOW_URL",
    "https://serverless.roboflow.com/fam-world/workflows/detect-count-and-visualize",
)
REQUEST_TIMEOUT_SECONDS = getattr(settings, "ROBOFLOW_TIMEOUT_SECONDS", 20)


class RoboflowError(Exception):
    pass


def count_from_image_bytes(image_bytes: bytes) -> dict:
    api_key = getattr(settings, "ROBOFLOW_API_KEY", "").strip()
    if not api_key:
        raise RoboflowError(
            "Chick counting is not configured. Set ROBOFLOW_API_KEY in the backend "
            "server's environment and restart the server."
        )

    started = time.monotonic()

    encoded = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "api_key": api_key,
        "inputs": {"image": {"type": "base64", "value": encoded}},
    }

    try:
        response = requests.post(WORKFLOW_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError as exc:
        if "NameResolutionError" in str(exc) or "getaddrinfo failed" in str(exc):
            raise RoboflowError(
                "Could not reach the chick-counting service: your computer can't resolve "
                "serverless.roboflow.com right now, meaning it's a network/DNS issue on this "
                "machine, not the app. Check: (1) you're actually connected to the internet — try "
                "opening any website, (2) if you're on a VPN or campus network, try disabling it or "
                "switching networks, (3) try `ipconfig /flushdns` in a terminal, then retry. If it "
                "worked before and stopped without you changing anything, it's most likely a "
                "temporary network/DNS blip rather than something to fix in the code."
            ) from exc
        raise RoboflowError(f"Could not reach the chick-counting service: {exc}") from exc
    except requests.RequestException as exc:
        raise RoboflowError(f"Could not reach the chick-counting service: {exc}") from exc

    if response.status_code != 200:
        raise RoboflowError(
            f"Chick-counting service returned {response.status_code}: {response.text[:300]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RoboflowError("Chick-counting service returned a non-JSON response.") from exc

    predictions, image_dims, raw_count = _extract_predictions(data)
    boxes = [_normalize_box(p) for p in predictions]

    count = raw_count if raw_count is not None else len(boxes)
    avg_confidence = round(sum(b["confidence"] for b in boxes) / len(boxes), 3) if boxes else 0.0

    return {
        "count": count,
        "confidence": avg_confidence,
        "boxes": boxes,
        "model_version": "roboflow:fam-world/detect-count-and-visualize",
        "processing_time_ms": int((time.monotonic() - started) * 1000),
    }


def _extract_predictions(data: dict):
    """Best-effort parsing of a Roboflow Workflow response. Returns
    (predictions_list, image_dims_or_none, explicit_count_or_none).

    Tries, in order:
    1. outputs[0]["predictions"]["predictions"] + outputs[0]["count_objects"|"count"]
    2. outputs[0]["predictions"] as a bare list
    3. scans outputs[0]'s values for anything list-of-dicts-with-x/y/width/height
    """
    outputs = data.get("outputs")
    if not outputs or not isinstance(outputs, list):
        raise RoboflowError(f"Unexpected response shape from Roboflow (no 'outputs' list): {data!r:.300}")

    block = outputs[0]
    if not isinstance(block, dict):
        raise RoboflowError(f"Unexpected 'outputs[0]' shape from Roboflow: {block!r:.300}")

    explicit_count = None
    for count_key in ("count_objects", "count", "object_count"):
        if count_key in block and isinstance(block[count_key], (int, float)):
            explicit_count = int(block[count_key])
            break

    predictions_field = block.get("predictions")
    image_dims = None

    if isinstance(predictions_field, dict):
        image_dims = predictions_field.get("image")
        preds = predictions_field.get("predictions")
        if isinstance(preds, list):
            return preds, image_dims, explicit_count

    if isinstance(predictions_field, list):
        return predictions_field, image_dims, explicit_count

    # Fallback: scan every value in the output block for a list of
    # dicts that look like detection predictions.
    for value in block.values():
        candidate = value.get("predictions") if isinstance(value, dict) else value
        if isinstance(candidate, list) and candidate and _looks_like_prediction(candidate[0]):
            return candidate, value.get("image") if isinstance(value, dict) else None, explicit_count

    if explicit_count is not None:
        # We at least know the count even if we can't locate box geometry.
        return [], None, explicit_count

    raise RoboflowError(
        "Could not find a predictions list in the Roboflow response. "
        "The workflow's output block names may differ from what this integration "
        f"expects — inspect the raw response and adjust `_extract_predictions()`. Raw keys: {list(block.keys())}"
    )


def _looks_like_prediction(item) -> bool:
    return isinstance(item, dict) and {"x", "y", "width", "height"}.issubset(item.keys())


def _normalize_box(prediction: dict) -> dict:
    """Roboflow gives center x/y + width/height; convert to the
    top-left x/y/w/h convention used elsewhere in this app."""
    cx = float(prediction.get("x", 0))
    cy = float(prediction.get("y", 0))
    w = float(prediction.get("width", 0))
    h = float(prediction.get("height", 0))
    confidence = float(prediction.get("confidence", 0.5))
    return {
        "x": round(cx - w / 2, 2),
        "y": round(cy - h / 2, 2),
        "w": round(w, 2),
        "h": round(h, 2),
        "confidence": round(confidence, 3),
    }

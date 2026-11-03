"""
Visualizer
----------
Draws bounding boxes, IDs, and behavior labels onto frames using OpenCV.

Behavior → color mapping (BGR):
  NORMAL        → green   (0, 200, 80)
  HUDDLING      → blue    (220, 140, 0)
  POSSIBLY_ILL  → yellow  (0, 210, 255)
  POSSIBLY_DEAD → red     (0, 50, 220)
"""

import cv2
import numpy as np
from behavior.classifier import Behavior

# BGR colors per behavior
BEHAVIOR_COLORS: dict[Behavior, tuple[int, int, int]] = {
    Behavior.NORMAL:        (80,  200,  0),
    Behavior.HUDDLING:      (200, 130,  0),
    Behavior.POSSIBLY_ILL:  (0,   200, 240),
    Behavior.POSSIBLY_DEAD: (0,    40, 210),
}

BEHAVIOR_LABELS: dict[Behavior, str] = {
    Behavior.NORMAL:        "Normal",
    Behavior.HUDDLING:      "Huddling",
    Behavior.POSSIBLY_ILL:  "Possibly Ill",
    Behavior.POSSIBLY_DEAD: "Possibly Dead",
}


def draw_detections(
    frame: np.ndarray,
    detections: list[dict],
    behaviors: dict[int, Behavior],
) -> np.ndarray:
    """
    Draw bounding boxes + IDs + behavior labels on a frame.

    Args:
        frame:      BGR image (H, W, 3).
        detections: list of dicts with keys: id, x1, y1, x2, y2
        behaviors:  mapping of track_id → Behavior enum value

    Returns:
        Annotated BGR frame (copy).
    """
    out = frame.copy()

    for det in detections:
        tid  = int(det["id"])
        x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
        beh  = behaviors.get(tid, Behavior.NORMAL)
        color = BEHAVIOR_COLORS[beh]
        label = f"#{tid} {BEHAVIOR_LABELS[beh]}"

        # Box
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        # Label background pill
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
        pad = 4
        lx1, ly1 = x1, max(0, y1 - th - 2 * pad)
        lx2, ly2 = x1 + tw + 2 * pad, y1
        cv2.rectangle(out, (lx1, ly1), (lx2, ly2), color, -1)

        # Label text (dark on bright, white on dark)
        brightness = 0.299 * color[2] + 0.587 * color[1] + 0.114 * color[0]
        text_color = (20, 20, 20) if brightness > 140 else (240, 240, 240)
        cv2.putText(out, label, (lx1 + pad, ly2 - pad),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, text_color, 1, cv2.LINE_AA)

    return out


def draw_hud(
    frame: np.ndarray,
    frame_idx: int,
    fps: float,
    behavior_counts: dict[Behavior, int],
) -> np.ndarray:
    """
    Draw a HUD overlay in the top-left corner showing frame number,
    timestamp, and per-behavior chicken counts.
    """
    out = frame.copy()
    h, w = out.shape[:2]

    # Semi-transparent dark panel
    panel_h = 20 + 20 * (len(Behavior) + 2)
    overlay = out.copy()
    cv2.rectangle(overlay, (8, 8), (240, panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, out, 0.45, 0, out)

    ts = frame_idx / max(fps, 1e-6)
    lines = [
        f"Frame: {frame_idx:06d}",
        f"Time:  {int(ts//60):02d}:{ts%60:05.2f}",
        "─" * 22,
    ]
    for beh in Behavior:
        cnt = behavior_counts.get(beh, 0)
        lines.append(f"{BEHAVIOR_LABELS[beh]:<16}: {cnt}")

    for i, line in enumerate(lines):
        y = 24 + i * 20
        color = BEHAVIOR_COLORS.get(
            list(Behavior)[i - 3] if i >= 3 else Behavior.NORMAL,
            (200, 200, 200)
        ) if i >= 3 else (200, 200, 200)
        cv2.putText(out, line, (14, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, color, 1, cv2.LINE_AA)

    return out

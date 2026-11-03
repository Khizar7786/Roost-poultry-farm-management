"""
utils/overlay.py
────────────────
All OpenCV drawing helpers for the annotated output video.
"""

from __future__ import annotations
from collections import deque
from typing import Dict, List, Tuple
import cv2
import numpy as np

from behavior.analyzer import Behavior, BEHAVIOR_COLORS


def draw_detection(
    frame: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    chicken_id: int,
    behavior: Behavior,
    conf: float,
    cfg: dict,
) -> None:
    """Draw a bounding box with ID and behavior label."""
    color = BEHAVIOR_COLORS[behavior]
    thickness = cfg["output"]["box_thickness"]
    fs        = cfg["output"]["font_scale"]

    # Box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    # Label background + text
    label = f"ID:{chicken_id}  {behavior.value}"
    (tw, th), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, fs, 1
    )
    pad = 3
    lx1, ly1 = x1, y1 - th - 2 * pad
    lx2, ly2 = x1 + tw + 2 * pad, y1

    # Keep label inside frame
    if ly1 < 0:
        ly1, ly2 = y2, y2 + th + 2 * pad

    cv2.rectangle(frame, (lx1, ly1), (lx2, ly2), color, -1)
    cv2.putText(
        frame, label,
        (lx1 + pad, ly2 - pad - baseline),
        cv2.FONT_HERSHEY_SIMPLEX, fs,
        (255, 255, 255), 1, cv2.LINE_AA,
    )


def draw_trajectory(
    frame: np.ndarray,
    positions: deque,
    behavior: Behavior,
    max_len: int = 40,
) -> None:
    """Draw a fading motion trail for one chicken."""
    color = BEHAVIOR_COLORS[behavior]
    pts   = list(positions)[-max_len:]
    if len(pts) < 2:
        return

    for i in range(1, len(pts)):
        alpha = i / len(pts)
        c = tuple(int(v * alpha) for v in color)
        cv2.line(
            frame,
            (int(pts[i - 1][0]), int(pts[i - 1][1])),
            (int(pts[i][0]),     int(pts[i][1])),
            c, 1, cv2.LINE_AA,
        )


def draw_huddle_lines(
    frame: np.ndarray,
    pairs: List[Tuple[int, int]],
    positions: Dict[int, Tuple[float, float]],
) -> None:
    """Draw thin connecting lines between huddling chickens."""
    huddle_color = BEHAVIOR_COLORS[Behavior.HUDDLING]
    for a, b in pairs:
        if a in positions and b in positions:
            pa = (int(positions[a][0]), int(positions[a][1]))
            pb = (int(positions[b][0]), int(positions[b][1]))
            cv2.line(frame, pa, pb, huddle_color, 1, cv2.LINE_AA)


def draw_hud(
    frame: np.ndarray,
    frame_idx: int,
    fps: float,
    behavior_counts: Dict[Behavior, int],
) -> None:
    """Draw a semi-transparent HUD in the top-left corner."""
    h, w = frame.shape[:2]
    panel_w, panel_h = 260, 130
    overlay = frame.copy()

    cv2.rectangle(overlay, (8, 8), (8 + panel_w, 8 + panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    ts = frame_idx / max(fps, 1)
    cv2.putText(
        frame, f"Time: {int(ts // 60):02d}:{ts % 60:05.2f}  Frame: {frame_idx}",
        (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA,
    )

    y = 48
    for beh, count in behavior_counts.items():
        color = BEHAVIOR_COLORS[beh]
        cv2.circle(frame, (18, y - 4), 5, color, -1)
        cv2.putText(
            frame, f"{beh.value}: {count}",
            (28, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
            (220, 220, 220), 1, cv2.LINE_AA,
        )
        y += 20


def draw_alert_banner(frame: np.ndarray, message: str) -> None:
    """Red banner at the bottom for critical alerts."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 36), (w, h), (0, 0, 180), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.putText(
        frame, f"⚠  {message}",
        (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
        (255, 255, 255), 1, cv2.LINE_AA,
    )

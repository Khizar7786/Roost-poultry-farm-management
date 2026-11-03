"""
BehaviorLogger
--------------
Writes per-frame, per-chicken behavior events to a CSV file for
post-processing, alerts, or data export.

CSV columns:
  frame_idx, timestamp_sec, track_id, cx, cy, behavior, avg_displacement_px
"""

from __future__ import annotations
import csv
import os
from pathlib import Path
from behavior.classifier import Behavior


_COLUMNS = [
    "frame_idx",
    "timestamp_sec",
    "track_id",
    "cx",
    "cy",
    "behavior",
    "avg_displacement_px",
]


class BehaviorLogger:
    def __init__(self, csv_path: str, fps: float, log_interval_sec: float = 1.0):
        """
        Args:
            csv_path:          Output CSV file path.
            fps:               Video FPS (used to compute timestamp).
            log_interval_sec:  Only write a row once per this many seconds
                               per chicken (avoids huge files at 30fps).
        """
        self._csv_path        = Path(csv_path)
        self._fps             = max(fps, 1.0)
        self._log_interval    = max(1, int(log_interval_sec * fps))
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)

        self._file   = open(self._csv_path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=_COLUMNS)
        self._writer.writeheader()

        # Track last-logged frame per ID to enforce interval
        self._last_logged: dict[int, int] = {}

    # ------------------------------------------------------------------ #

    def log(
        self,
        frame_idx: int,
        track_id: int,
        cx: float,
        cy: float,
        behavior: Behavior,
        avg_displacement: float,
    ) -> None:
        last = self._last_logged.get(track_id, -999999)
        if frame_idx - last < self._log_interval:
            return

        self._writer.writerow({
            "frame_idx":           frame_idx,
            "timestamp_sec":       round(frame_idx / self._fps, 3),
            "track_id":            track_id,
            "cx":                  round(cx, 1),
            "cy":                  round(cy, 1),
            "behavior":            behavior.value,
            "avg_displacement_px": round(avg_displacement, 3),
        })
        self._last_logged[track_id] = frame_idx

    def flush(self) -> None:
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

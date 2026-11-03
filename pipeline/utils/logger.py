"""
utils/logger.py
───────────────
Writes per-frame behavior events to a CSV file.
"""

from __future__ import annotations
import csv
import os
from datetime import datetime
from typing import Dict, List
from behavior.analyzer import Behavior


class BehaviorLogger:
    def __init__(self, output_dir: str, video_name: str):
        os.makedirs(output_dir, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"{video_name}_{ts}_log.csv")
        self._file   = open(path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow([
            "frame", "time_sec", "chicken_id",
            "cx", "cy", "behavior",
        ])
        self.path = path

    def log(
        self,
        frame_idx: int,
        fps: float,
        detections: List,      # (id, cx, cy)
        behaviors: Dict[int, Behavior],
    ) -> None:
        t = frame_idx / max(fps, 1)
        for (cid, cx, cy) in detections:
            beh = behaviors.get(cid, Behavior.NORMAL)
            self._writer.writerow([frame_idx, f"{t:.3f}", cid, f"{cx:.1f}", f"{cy:.1f}", beh.value])

    def close(self) -> None:
        self._file.close()
        print(f"[Logger] Saved log → {self.path}")

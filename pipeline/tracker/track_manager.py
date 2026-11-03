"""Adapt Ultralytics ByteTrack results to the pipeline's track dictionaries."""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import yaml


class TrackManager:
    def __init__(self, tracker_type="bytetrack", config_path=None):
        if tracker_type.lower() != "bytetrack":
            raise ValueError("Supported tracker: bytetrack. Set tracker.type in config.yaml.")
        from ultralytics.trackers.byte_tracker import BYTETracker

        path = Path(config_path) if config_path else Path(__file__).with_name("bytetrack.yaml")
        with path.open(encoding="utf-8") as stream:
            settings = yaml.safe_load(stream)
        self._tracker = BYTETracker(SimpleNamespace(**settings))

    def update(self, yolo_results, frame):
        from ultralytics.engine.results import Boxes

        boxes = yolo_results.boxes
        if boxes is None:
            boxes = Boxes(np.empty((0, 6), dtype=np.float32), frame.shape[:2])
        # ByteTrack needs the numpy-backed Boxes API, including boolean slicing.
        tracks = self._tracker.update(boxes.cpu().numpy(), frame)
        results = []
        for row in tracks:
            x1, y1, x2, y2, track_id, confidence, class_id = row[:7]
            width, height = float(x2 - x1), float(y2 - y1)
            results.append({
                "id": int(track_id), "x1": float(x1), "y1": float(y1),
                "x2": float(x2), "y2": float(y2),
                "cx": float(x1 + width / 2), "cy": float(y1 + height / 2),
                "w": width, "h": height, "conf": float(confidence), "cls": int(class_id),
            })
        return results

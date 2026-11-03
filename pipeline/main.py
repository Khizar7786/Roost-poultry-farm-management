"""
main.py — Chicken Behavior Detection Pipeline
=============================================

Usage:
    python main.py --input VIDEO_PATH [--output OUTPUT_PATH] [--config config.yaml] [--weights WEIGHTS_PATH]

Example:
    python main.py --input farm_footage.mp4 --output output/annotated.mp4
    python main.py --input farm_footage.mp4 --weights runs/train/chicken_yolo26/weights/best.pt

The --weights flag overrides model.weights from config.yaml, so you can
quickly switch between trained models (e.g. YOLOv8 vs YOLO26) without
editing or duplicating config files.
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

# Local modules
from tracker.track_manager import TrackManager
from behavior.classifier   import BehaviorClassifier, Behavior
from behavior.logger       import BehaviorLogger
from utils.trajectory      import TrajectoryBuffer
from utils.config import DEFAULT_CONFIG, load_config
from utils.visualizer      import draw_detections, draw_hud


# ─────────────────────────────────────────────────────────────── #
#  Config helpers                                                  #
# ─────────────────────────────────────────────────────────────── #

def get(cfg: dict, *keys, default=None):
    """Safely traverse nested config dict."""
    node = cfg
    for k in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(k, default)
        if node is None:
            return default
    return node


# ─────────────────────────────────────────────────────────────── #
#  Main pipeline                                                   #
# ─────────────────────────────────────────────────────────────── #

def run(
    input_path:  str,
    output_path: str,
    config_path: str,
    weights_override: str | None = None,
) -> None:
    # ── Load config ──────────────────────────────────────────── #
    cfg = load_config(config_path)

    # ── YOLO model ───────────────────────────────────────────── #
    # CLI --weights wins over config.yaml's model.weights
    weights    = weights_override or get(cfg, "model", "weights", default="yolov8n.pt")
    confidence = get(cfg, "model", "confidence", default=0.45)
    iou        = get(cfg, "model", "iou",        default=0.5)
    imgsz      = get(cfg, "model", "imgsz",      default=640)
    device     = get(cfg, "model", "device",     default="cpu")

    print(f"\n[1/5] Loading YOLO model: {weights}")
    model = YOLO(weights)

    # ── Video input ──────────────────────────────────────────── #
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        sys.exit(f"[ERROR] Cannot open video: {input_path}")

    src_fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    fps_override = get(cfg, "video", "fps_override")
    fps        = float(fps_override) if fps_override else float(src_fps)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[2/5] Video: {width}×{height} @ {fps:.1f} fps  ({total_frames} frames)")

    # ── Video output ─────────────────────────────────────────── #
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    codec   = get(cfg, "video", "output_codec", default="mp4v")
    fourcc  = cv2.VideoWriter_fourcc(*codec)
    writer  = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # ── Tracker ──────────────────────────────────────────────── #
    tracker_type   = get(cfg, "tracker", "type",   default="bytetrack")
    tracker_config = get(cfg, "tracker", "config", default=None)
    print(f"[3/5] Initialising tracker: {tracker_type}")
    tracker = TrackManager(tracker_type, tracker_config)

    # ── Behavior engine ──────────────────────────────────────── #
    print(f"[4/5] Configuring behavior classifier")
    classifier = BehaviorClassifier(
        fps              = fps,
        huddle_k         = get(cfg, "behavior", "huddle_k_neighbors", default=3),
        huddle_dist_px   = get(cfg, "behavior", "huddle_dist_px",     default=120.0),
        ill_velocity_px  = get(cfg, "behavior", "ill_velocity_px",    default=8.0),
        ill_window_sec   = get(cfg, "behavior", "ill_window_sec",     default=30.0),
        dead_velocity_px = get(cfg, "behavior", "dead_velocity_px",   default=2.0),
        dead_window_sec  = get(cfg, "behavior", "dead_window_sec",    default=60.0),
    )

    trajectories  = TrajectoryBuffer(max_frames=classifier.history_frames)  # Retain the complete longest behavior window.

    # ── Logger ───────────────────────────────────────────────── #
    save_csv       = get(cfg, "logging", "save_csv",        default=True)
    csv_path       = get(cfg, "logging", "csv_path",        default="output/behavior_log.csv")
    log_interval   = get(cfg, "logging", "log_interval_sec", default=1.0)

    logger = BehaviorLogger(csv_path, fps, log_interval) if save_csv else None

    # ─────────────────────────────────────────────────────────── #
    #  Frame loop                                                  #
    # ─────────────────────────────────────────────────────────── #
    print(f"[5/5] Processing video …\n")

    frame_idx = 0
    with tqdm(total=total_frames, unit="frame", ncols=80) as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # ── YOLO inference ──────────────────────────────── #
            yolo_results = model(
                frame,
                conf    = confidence,
                iou     = iou,
                imgsz   = imgsz,
                device  = device,
                verbose = False,
            )[0]

            # ── Tracking ────────────────────────────────────── #
            tracks = tracker.update(yolo_results, frame)

            # ── Update trajectory buffer ─────────────────────── #
            active_ids      = []
            current_centers = {}
            for t in tracks:
                tid = t["id"]
                active_ids.append(tid)
                current_centers[tid] = (t["cx"], t["cy"])
                trajectories.update(tid, frame_idx, t["cx"], t["cy"])

            # ── Behavior classification ──────────────────────── #
            behaviors = classifier.classify_all(
                trajectories, active_ids, current_centers
            )

            # ── Logging ─────────────────────────────────────── #
            if logger:
                for tid in active_ids:
                    cx, cy  = current_centers[tid]
                    beh     = behaviors.get(tid, Behavior.NORMAL)
                    avg_d   = trajectories.average_displacement(tid, int(fps * 5))
                    logger.log(frame_idx, tid, cx, cy, beh, avg_d)

            # ── Behavior counts for HUD ──────────────────────── #
            counts: dict[Behavior, int] = {b: 0 for b in Behavior}
            for beh in behaviors.values():
                counts[beh] += 1

            # ── Draw output frame ────────────────────────────── #
            out_frame = draw_detections(frame, tracks, behaviors)
            out_frame = draw_hud(out_frame, frame_idx, fps, counts)
            writer.write(out_frame)

            frame_idx += 1
            pbar.update(1)

            # Flush CSV every 300 frames
            if logger and frame_idx % 300 == 0:
                logger.flush()

    # ─────────────────────────────────────────────────────────── #
    #  Cleanup                                                     #
    # ─────────────────────────────────────────────────────────── #
    cap.release()
    writer.release()
    if logger:
        logger.close()

    print(f"\n{'='*55}")
    print(f"  Done!")
    print(f"  Annotated video : {output_path}")
    if save_csv:
        print(f"  Behavior log    : {csv_path}")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────────────────────── #
#  Entry point                                                     #
# ─────────────────────────────────────────────────────────────── #

def parse_args():
    p = argparse.ArgumentParser(
        description="Chicken Behavior Detection — inference pipeline"
    )
    p.add_argument(
        "--input",  "-i", required=True,
        help="Path to input video file"
    )
    p.add_argument(
        "--output", "-o", default="output/annotated.mp4",
        help="Path to output annotated video (default: output/annotated.mp4)"
    )
    p.add_argument(
        "--config", "-c", default=str(DEFAULT_CONFIG),
        help="Path to config.yaml (default: config.yaml)"
    )
    p.add_argument(
        "--weights", "-w", default=None,
        help="Override model.weights from config.yaml (e.g. runs/train/chicken_yolo26/weights/best.pt)"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.input, args.output, args.config, args.weights)

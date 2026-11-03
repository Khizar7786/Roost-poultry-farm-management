"""
utils/calibrate.py
──────────────────
Helps you calibrate behavior thresholds for your specific
camera setup, resolution, and chicken size.

Run on a short reference clip where you KNOW the chickens are healthy:
    python utils/calibrate.py --video ref_clip.mp4

Prints suggested threshold values to paste into config.yaml.
"""

from __future__ import annotations
import argparse
import os
import sys
import yaml
import numpy as np
import cv2
from ultralytics import YOLO
from tqdm import tqdm


def calibrate(video_path: str, config_path: str = "config.yaml") -> None:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    weights = cfg["model"]["weights"]
    if not os.path.exists(weights):
        weights = cfg["model"]["pretrained_base"]

    model = YOLO(weights)
    cap   = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"Cannot open: {video_path}")

    fps   = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    box_sizes:      list[float] = []
    pairwise_dists: list[float] = []
    per_frame_vels: list[float] = []
    prev_centroids: dict[int, tuple] = {}

    pbar = tqdm(total=min(total, 900), desc="Calibrating")  # ~30s at 30fps

    for fi in range(min(total, 900)):
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=0.4, verbose=False,
                                device=cfg["model"]["device"])
        r = results[0]
        centroids = {}

        if r.boxes is not None and len(r.boxes):
            boxes = r.boxes.xyxy.cpu().numpy()
            ids   = r.boxes.id
            for i, (x1, y1, x2, y2) in enumerate(boxes):
                w = x2 - x1
                h = y2 - y1
                box_sizes.append(float((w + h) / 2))
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                tid = int(ids[i]) if ids is not None else i
                centroids[tid] = (cx, cy)

            # Pairwise distances this frame
            pts = list(centroids.values())
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    d = np.linalg.norm(np.array(pts[i]) - np.array(pts[j]))
                    pairwise_dists.append(d)

            # Velocity relative to previous frame
            for tid, (cx, cy) in centroids.items():
                if tid in prev_centroids:
                    px, py = prev_centroids[tid]
                    per_frame_vels.append(np.linalg.norm([cx - px, cy - py]))

        prev_centroids = centroids
        pbar.update(1)

    pbar.close()
    cap.release()

    if not box_sizes:
        print("[Calibrate] No detections found. Check your weights / video.")
        return

    avg_box   = float(np.median(box_sizes))
    avg_dist  = float(np.median(pairwise_dists)) if pairwise_dists else avg_box * 3
    p25_dist  = float(np.percentile(pairwise_dists, 25)) if pairwise_dists else avg_box * 1.5
    avg_vel   = float(np.median(per_frame_vels)) if per_frame_vels else 10.0
    p10_vel   = float(np.percentile(per_frame_vels, 10)) if per_frame_vels else 3.0

    # Suggested thresholds
    huddle_dist = round(p25_dist * 0.9, 1)
    ill_vel     = round(p10_vel  * 0.6, 1)
    dead_vel    = round(p10_vel  * 0.15, 1)

    print("\n" + "─" * 50)
    print("  Calibration Results")
    print("─" * 50)
    print(f"  Median chicken size (px):   {avg_box:.1f}")
    print(f"  Median pairwise distance:   {avg_dist:.1f} px")
    print(f"  25th pctile distance:       {p25_dist:.1f} px")
    print(f"  Median velocity / frame:    {avg_vel:.2f} px")
    print(f"  10th pctile velocity:       {p10_vel:.2f} px")
    print("─" * 50)
    print("\n  Suggested config.yaml values:\n")
    print(f"    huddle_distance_px:  {huddle_dist}")
    print(f"    ill_velocity_px:     {ill_vel}")
    print(f"    dead_velocity_px:    {dead_vel}")
    print()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Calibrate behavior thresholds")
    p.add_argument("--video",  required=True)
    p.add_argument("--config", default="config.yaml")
    args = p.parse_args()
    calibrate(args.video, args.config)

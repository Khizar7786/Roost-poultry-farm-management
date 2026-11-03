"""
train.py
--------
Fine-tune a YOLOv8 model on your chicken dataset.

Usage:
    python train.py --data dataset/data.yaml --epochs 100 --img 640

Dataset directory layout expected:
    dataset/
      data.yaml       (train: train/images, val: valid/images)
      train/images/   and train/labels/
      valid/images/   and valid/labels/

See dataset/README.md. Paths in data.yaml are relative to that file.
"""

import argparse
from pathlib import Path
from utils.config import PROJECT_ROOT, validate_dataset
from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLO for chicken detection")
    p.add_argument("--data",        type=str, default=str(PROJECT_ROOT / "dataset/data.yaml"),
                   help="Path to data.yaml")
    p.add_argument("--weights",     type=str, default="yolov8n.pt",
                   help="Starting weights (pretrained or custom .pt)")
    p.add_argument("--epochs",      type=int, default=100)
    p.add_argument("--img",         type=int, default=640,
                   help="Input image size")
    p.add_argument("--batch",       type=int, default=16)
    p.add_argument("--device",      type=str, default="cpu",
                   help="Training device: cpu | 0 (GPU) | mps")
    p.add_argument("--project",     type=str, default=str(PROJECT_ROOT / "runs/train"),
                   help="Output directory")
    p.add_argument("--name",        type=str, default="chicken_v1")
    p.add_argument("--patience",    type=int, default=20,
                   help="Early stopping patience (epochs)")
    return p.parse_args()


def main():
    args = parse_args()

    try:
        args.data = validate_dataset(args.data)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from error

    model = YOLO(args.weights)

    print(f"\n{'='*55}")
    print(f"  Training chicken detection model")
    print(f"  Base weights : {args.weights}")
    print(f"  Dataset      : {args.data}")
    print(f"  Epochs       : {args.epochs}")
    print(f"  Device       : {args.device}")
    print(f"{'='*55}\n")

    results = model.train(
        data        = args.data,
        epochs      = args.epochs,
        imgsz       = args.img,
        batch       = args.batch,
        device      = args.device,
        project     = args.project,
        name        = args.name,
        patience    = args.patience,

        # Stability / GPU settings
        workers     = 0,
        amp         = False,
        cache       = False,
        close_mosaic= 10,

        # Augmentations beneficial for farm footage
        hsv_h       = 0.015,
        hsv_s       = 0.5,
        hsv_v       = 0.4,
        degrees     = 10.0,
        translate   = 0.1,
        scale       = 0.5,
        flipud      = 0.1,
        fliplr      = 0.5,

        # Reduced for stability on 4GB VRAM
        mosaic      = 0.5,
        mixup       = 0.0,
    )

    best_weights = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"\n[✓] Training complete.")
    print(f"    Best weights saved to: {best_weights}")
    print(f"\n    Update config.yaml → model.weights to point at this file,")
    print(f"    then run: python main.py --input your_video.mp4\n")


if __name__ == "__main__":
    main()

from ultralytics import RTDETR
import argparse
from pathlib import Path
from utils.config import PROJECT_ROOT, validate_dataset

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data",     type=str, default=str(PROJECT_ROOT / "dataset/data.yaml"))
    p.add_argument("--weights",  type=str, default="rtdetr-l.pt")
    p.add_argument("--epochs",   type=int, default=80)
    p.add_argument("--img",      type=int, default=480)
    p.add_argument("--batch",    type=int, default=4)
    p.add_argument("--device",   type=str, default="cpu")
    p.add_argument("--project",  type=str, default=str(PROJECT_ROOT / "runs/rtdetr"))
    p.add_argument("--name",     type=str, default="chicken_rtdetr")
    p.add_argument("--patience", type=int, default=20)
    return p.parse_args()

def main():
    args = parse_args()

    try:
        args.data = validate_dataset(args.data)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from error

    print(f"\n{'='*55}")
    print(f"  Training RT-DETR — chicken detection")
    print(f"  Weights  : {args.weights}")
    print(f"  Dataset  : {args.data}")
    print(f"  Epochs   : {args.epochs}")
    print(f"{'='*55}\n")

    model = RTDETR(args.weights)
    model.train(
        data        = args.data,
        epochs      = args.epochs,
        imgsz       = args.img,
        batch       = args.batch,
        device      = args.device,
        project     = args.project,
        name        = args.name,
        patience    = args.patience,
        workers     = 0,
        amp         = False,
        cache       = False,
        close_mosaic= 10,
        hsv_h=0.015, hsv_s=0.5, hsv_v=0.4,
        degrees=10.0, translate=0.1, scale=0.5,
        flipud=0.1, fliplr=0.5,
    )

    best = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"\n[✓] Done. Best weights: {best}\n")

if __name__ == "__main__":
    main()

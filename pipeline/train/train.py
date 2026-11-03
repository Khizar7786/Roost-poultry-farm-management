"""Train YOLO using config.yaml: python train/train.py --config config.yaml."""
import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import DEFAULT_CONFIG, load_config, validate_dataset


def train(config):
    settings = config["training"]
    data_yaml = validate_dataset(settings["data_yaml"])
    # Missing data never triggers a model download.
    from ultralytics import YOLO

    model = YOLO(config["model"].get("pretrained_base", "yolov8s.pt"))
    model.train(
        data=data_yaml,
        epochs=settings.get("epochs", 100),
        imgsz=settings.get("imgsz", 640),
        batch=settings.get("batch", 8),
        device=config["model"].get("device", "cpu"),
        workers=settings.get("workers", 0),
        project=settings["project"],
        name=settings.get("name", "chicken_yolo"),
        amp=settings.get("amp", False),
        cache=settings.get("cache", False),
    )
    best = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"Training complete. Best weights: {best}")
    return best


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train chicken YOLO from configuration")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    try:
        train(load_config(args.config))
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error)) from error

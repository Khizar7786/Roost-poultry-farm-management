"""Portable configuration paths shared by training and inference."""
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config.yaml"


def load_config(path=DEFAULT_CONFIG):
    path = Path(path).expanduser().resolve()
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    # Configured filesystem paths are relative to config.yaml, not the shell.
    for section, key in (
        ("model", "weights"), ("training", "data_yaml"),
        ("training", "project"), ("tracker", "config"), ("logging", "csv_path"),
    ):
        value = config.get(section, {}).get(key)
        if value:
            config[section][key] = str((path.parent / value).resolve())
    config.setdefault("model", {}).setdefault("device", "cpu")
    return config


def validate_dataset(data_yaml):
    """Fail before loading weights if the local YOLO dataset is unavailable."""
    data_yaml = Path(data_yaml).expanduser().resolve()
    if not data_yaml.is_file():
        raise FileNotFoundError(f"Dataset YAML not found: {data_yaml}. See dataset/README.md.")
    with data_yaml.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict) or not data.get("names"):
        raise ValueError(f"Dataset YAML must define class names: {data_yaml}")
    root = Path(data.get("path") or data_yaml.parent)
    if not root.is_absolute():
        root = data_yaml.parent / root
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
    for split in ("train", "val"):
        entry = data.get(split)
        if not isinstance(entry, str) or not entry:
            raise ValueError(f"Dataset YAML must define a {split} image directory")
        images = (root / entry).resolve()
        if not images.is_dir() or not any(
            p.is_file() and p.suffix.lower() in extensions for p in images.rglob("*")
        ):
            raise FileNotFoundError(f"No {split} images found at {images}. See dataset/README.md.")
    return str(data_yaml)

"""
filter_detection_labels.py
--------------------------
Scans every .txt label file inside a given dataset directory
(train/labels and valid/labels by default) and removes any
segmentation lines, keeping only YOLO detection lines.

YOLO detection  → class_id cx cy w h          (exactly 5 values)
YOLO segmentation → class_id x1 y1 x2 y2 ...  (more than 5 values)

Usage:
    python filter_detection_labels.py
    python filter_detection_labels.py --dataset path/to/dataset --dry-run
"""

import os
import argparse
import shutil
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def is_detection_line(line: str) -> bool:
    """Return True only if the line is a valid YOLO detection label (5 values)."""
    parts = line.strip().split()
    return len(parts) == 5


def filter_label_file(filepath: Path, dry_run: bool = False) -> dict:
    """
    Filter a single label .txt file.
    Returns a stats dict: {kept, removed, path}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    kept = []
    removed = []

    for line in lines:
        stripped = line.strip()
        if not stripped:          # blank lines — skip them always
            continue
        if is_detection_line(stripped):
            kept.append(stripped + "\n")
        else:
            removed.append(stripped)

    if not dry_run and removed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(kept)

    return {"path": filepath, "kept": len(kept), "removed": len(removed)}


def backup_labels(label_dirs: list[Path], backup_root: Path):
    """Copy all label dirs to a backup location before modifying."""
    for label_dir in label_dirs:
        rel = label_dir.parent.name  # e.g. "train" or "valid"
        dest = backup_root / rel / "labels"
        if label_dir.exists():
            shutil.copytree(label_dir, dest, dirs_exist_ok=True)
            print(f"  Backed up {label_dir} → {dest}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Strip segmentation labels from YOLO .txt files.")
    parser.add_argument(
        "--dataset", default="dataset",
        help="Path to your dataset folder (default: ./dataset)"
    )
    parser.add_argument(
        "--splits", nargs="+", default=["train", "valid"],
        help="Sub-folder names to process (default: train valid)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without modifying any files"
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip creating a backup (not recommended)"
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset).resolve()
    if not dataset_root.exists():
        print(f"[ERROR] Dataset folder not found: {dataset_root}")
        return

    # Collect label directories
    label_dirs = []
    for split in args.splits:
        ld = dataset_root / split / "labels"
        if ld.exists():
            label_dirs.append(ld)
        else:
            print(f"[WARN] Label dir not found, skipping: {ld}")

    if not label_dirs:
        print("[ERROR] No label directories found. Check --dataset and --splits.")
        return

    # Backup first
    if not args.dry_run and not args.no_backup:
        backup_root = dataset_root / "_labels_backup"
        print(f"\n📦 Backing up labels to: {backup_root}")
        backup_labels(label_dirs, backup_root)

    # Process files
    total_kept = total_removed = total_files = 0
    files_changed = []

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}🔍 Scanning label files...\n")

    for label_dir in label_dirs:
        txt_files = sorted(label_dir.glob("*.txt"))
        print(f"  {label_dir.relative_to(dataset_root)} — {len(txt_files)} files")

        for txt_file in txt_files:
            stats = filter_label_file(txt_file, dry_run=args.dry_run)
            total_files += 1
            total_kept += stats["kept"]
            total_removed += stats["removed"]

            if stats["removed"] > 0:
                files_changed.append(stats)
                print(f"    {'[DRY RUN] ' if args.dry_run else ''}✂  {txt_file.name}: "
                      f"kept {stats['kept']} detection, removed {stats['removed']} segmentation line(s)")

    # Summary
    print(f"\n{'='*60}")
    print(f"{'[DRY RUN] ' if args.dry_run else ''}✅ Done!")
    print(f"   Files scanned  : {total_files}")
    print(f"   Files modified : {len(files_changed)}")
    print(f"   Lines kept     : {total_kept}  (detection)")
    print(f"   Lines removed  : {total_removed}  (segmentation)")
    if not args.dry_run and not args.no_backup:
        print(f"   Backup location: {backup_root}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
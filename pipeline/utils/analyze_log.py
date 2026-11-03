"""
utils/analyze_log.py
────────────────────
Post-process a CSV log produced by main.py.
Prints a summary and saves a per-chicken behavior timeline plot.

Usage:
    python utils/analyze_log.py --log output/myvideo_20240101_log.csv
"""

from __future__ import annotations
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


COLORS = {
    "Normal":        "#00c850",
    "Huddling":      "#ffa500",
    "Possibly Ill":  "#00c8ff",
    "Possibly Dead": "#dc0000",
}


def analyze(log_path: str) -> None:
    df = pd.read_csv(log_path)
    print(f"\n{'─'*60}")
    print(f"  Log: {log_path}")
    print(f"  Frames: {df['frame'].max()}   Chickens tracked: {df['chicken_id'].nunique()}")
    print(f"{'─'*60}")

    summary = (
        df.groupby(["chicken_id", "behavior"])
        .size()
        .unstack(fill_value=0)
    )
    print("\nFrames per behavior per chicken ID:")
    print(summary.to_string())

    # ── Timeline plot ─────────────────────────────────────────────────────────
    ids = sorted(df["chicken_id"].unique())
    fig, ax = plt.subplots(figsize=(14, max(4, len(ids) * 0.5 + 2)))

    for i, cid in enumerate(ids):
        sub = df[df["chicken_id"] == cid].sort_values("time_sec")
        for _, row in sub.iterrows():
            ax.barh(
                i, 1 / 30, left=row["time_sec"],
                color=COLORS.get(row["behavior"], "#888"),
                height=0.7, linewidth=0,
            )

    ax.set_yticks(range(len(ids)))
    ax.set_yticklabels([f"ID {c}" for c in ids])
    ax.set_xlabel("Time (seconds)")
    ax.set_title("Chicken Behavior Timeline")

    patches = [mpatches.Patch(color=c, label=l) for l, c in COLORS.items()]
    ax.legend(handles=patches, loc="upper right", fontsize=8)

    plt.tight_layout()
    out_path = log_path.replace(".csv", "_timeline.png")
    plt.savefig(out_path, dpi=120)
    print(f"\n[Plot] Saved timeline → {out_path}")
    plt.show()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True, help="Path to CSV log file")
    args = p.parse_args()
    analyze(args.log)

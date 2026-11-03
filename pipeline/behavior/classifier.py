"""
BehaviorClassifier
------------------
Rule-based classifier that maps per-chicken trajectory features and
frame-level neighbor distances to a Behavior label.

Behaviors (in priority order — highest wins):
  1. POSSIBLY_DEAD   — near-zero movement for a long window
  2. POSSIBLY_ILL    — low movement for a medium window
  3. HUDDLING        — current centroid is very close to K neighbors
  4. NORMAL          — default
"""

from __future__ import annotations
from enum import Enum
from math import ceil
import numpy as np
from utils.trajectory import TrajectoryBuffer


class Behavior(Enum):
    NORMAL        = "normal"
    HUDDLING      = "huddling"
    POSSIBLY_ILL  = "possibly_ill"
    POSSIBLY_DEAD = "possibly_dead"


class BehaviorClassifier:
    """
    Args:
        fps:                   Video frame rate (needed to convert seconds → frames).
        huddle_k:              Number of nearest neighbors to check for huddling.
        huddle_dist_px:        Max mean neighbor distance (px) to trigger huddling.
        ill_velocity_px:       Max mean displacement (px/frame) for "possibly ill".
        ill_window_sec:        Time window (s) for ill check.
        dead_velocity_px:      Max mean displacement (px/frame) for "possibly dead".
        dead_window_sec:       Time window (s) for dead check.
    """

    def __init__(
        self,
        fps: float,
        huddle_k: int              = 3,
        huddle_dist_px: float      = 120.0,
        ill_velocity_px: float     = 8.0,
        ill_window_sec: float      = 30.0,
        dead_velocity_px: float    = 2.0,
        dead_window_sec: float     = 60.0,
    ):
        self._fps              = max(fps, 1.0)
        self._huddle_k         = huddle_k
        self._huddle_dist_px   = huddle_dist_px
        self._ill_velocity_px  = ill_velocity_px
        self._ill_frames       = max(2, ceil(ill_window_sec * self._fps) + 1)
        self._dead_velocity_px = dead_velocity_px
        self._dead_frames      = max(2, ceil(dead_window_sec * self._fps) + 1)

    @property
    def history_frames(self):
        """Positions needed to cover the complete longest behavior window."""
        return max(self._ill_frames, self._dead_frames)

    # ------------------------------------------------------------------ #

    def classify_all(
        self,
        trajectories: TrajectoryBuffer,
        active_ids: list[int],
        current_centers: dict[int, tuple[float, float]],
    ) -> dict[int, Behavior]:
        """
        Classify every active chicken in the current frame.

        Args:
            trajectories:    Shared TrajectoryBuffer containing position history.
            active_ids:      IDs detected in the current frame.
            current_centers: {track_id: (cx, cy)} for the current frame only.

        Returns:
            {track_id: Behavior}
        """
        result: dict[int, Behavior] = {}

        # Pre-compute all current centroids for neighbor distance checks
        all_centers = np.array(
            [current_centers[tid] for tid in active_ids if tid in current_centers],
            dtype=float,
        )
        id_order = [tid for tid in active_ids if tid in current_centers]

        for tid in active_ids:
            result[tid] = self._classify_one(
                tid, trajectories, current_centers, all_centers, id_order
            )

        return result

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _classify_one(
        self,
        tid: int,
        trajectories: TrajectoryBuffer,
        current_centers: dict[int, tuple[float, float]],
        all_centers: np.ndarray,
        id_order: list[int],
    ) -> Behavior:

        # ── 1. Possibly dead (highest priority) ──────────────────────── #
        dead_disp = trajectories.average_displacement(tid, self._dead_frames)
        if dead_disp <= self._dead_velocity_px:
            # Only flag dead if we actually have enough history
            history = trajectories.get_positions(tid)
            if len(history) >= self._dead_frames:
                return Behavior.POSSIBLY_DEAD

        # ── 2. Possibly ill ──────────────────────────────────────────── #
        ill_disp = trajectories.average_displacement(tid, self._ill_frames)
        if ill_disp <= self._ill_velocity_px:
            history = trajectories.get_positions(tid)
            if len(history) >= self._ill_frames:
                return Behavior.POSSIBLY_ILL

        # ── 3. Huddling ──────────────────────────────────────────────── #
        if tid in current_centers and len(all_centers) > 1:
            cx, cy = current_centers[tid]
            this_pt = np.array([[cx, cy]])
            dists = np.linalg.norm(all_centers - this_pt, axis=1)
            # Exclude self by ID; another chicken may have the same center.
            dists_no_self = np.sort(dists[[other != tid for other in id_order]])
            if len(dists_no_self) > 0:
                k = min(self._huddle_k, len(dists_no_self))
                mean_neighbor_dist = float(np.mean(dists_no_self[:k]))
                if mean_neighbor_dist < self._huddle_dist_px:
                    return Behavior.HUDDLING

        return Behavior.NORMAL

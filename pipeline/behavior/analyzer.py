"""
behavior/analyzer.py
────────────────────
Rule-based behavior classifier.

For every tracked chicken (ID) it maintains a rolling position history
and computes three behaviors:
  - HUDDLING    : too close to neighbors
  - POSSIBLY_ILL: very low movement sustained over ill_window
  - POSSIBLY_DEAD: near-zero movement sustained over dead_window
  - NORMAL      : none of the above
"""

from __future__ import annotations
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional
import numpy as np


# ── Behavior labels ────────────────────────────────────────────────────────────

class Behavior(str, Enum):
    NORMAL        = "Normal"
    HUDDLING      = "Huddling"
    POSSIBLY_ILL  = "Possibly Ill"
    POSSIBLY_DEAD = "Possibly Dead"


# BGR colors for each behavior (used by the overlay)
BEHAVIOR_COLORS: Dict[Behavior, Tuple[int, int, int]] = {
    Behavior.NORMAL:        (0,   200,  80),   # green
    Behavior.HUDDLING:      (255, 165,   0),   # blue-ish
    Behavior.POSSIBLY_ILL:  (0,   200, 255),   # yellow
    Behavior.POSSIBLY_DEAD: (0,   0,   220),   # red
}


# ── Per-chicken state ──────────────────────────────────────────────────────────

@dataclass
class ChickenState:
    chicken_id: int
    positions: deque = field(default_factory=lambda: deque(maxlen=300))  # (cx, cy)
    behavior: Behavior = Behavior.NORMAL
    behavior_frame_count: int = 0       # frames current behavior has been active
    last_seen_frame: int = 0


# ── Analyzer ──────────────────────────────────────────────────────────────────

class BehaviorAnalyzer:
    """
    Call update(frame_idx, detections) every frame.
    detections: list of (chicken_id, cx, cy)

    Returns a dict {chicken_id: Behavior}
    """

    def __init__(self, cfg: dict, fps: float):
        b = cfg["behavior"]
        self.fps = fps

        # Huddling
        self.huddle_k          = int(b["huddle_k_neighbors"])
        self.huddle_dist       = float(b["huddle_distance_px"])
        self.huddle_min        = int(b["huddle_min_chickens"])

        # Ill / Dead
        self.ill_vel           = float(b["ill_velocity_px"])
        self.dead_vel          = float(b["dead_velocity_px"])
        self.ill_frames        = int(b["ill_window_sec"]  * fps)
        self.dead_frames       = int(b["dead_window_sec"] * fps)
        self.history_frames    = int(b["history_sec"]     * fps)

        self.states: Dict[int, ChickenState] = {}

    # ── public API ────────────────────────────────────────────────────────────

    def update(
        self,
        frame_idx: int,
        detections: List[Tuple[int, float, float]],
    ) -> Dict[int, Behavior]:
        """
        detections: [(id, cx, cy), ...]
        Returns  : {id: Behavior}
        """
        self._update_positions(frame_idx, detections)
        self._classify_behaviors(frame_idx)
        return {cid: s.behavior for cid, s in self.states.items()}

    def get_state(self, chicken_id: int) -> Optional[ChickenState]:
        return self.states.get(chicken_id)

    # ── position tracking ─────────────────────────────────────────────────────

    def _update_positions(
        self,
        frame_idx: int,
        detections: List[Tuple[int, float, float]],
    ) -> None:
        for (cid, cx, cy) in detections:
            if cid not in self.states:
                self.states[cid] = ChickenState(
                    chicken_id=cid,
                    positions=deque(maxlen=self.history_frames),
                )
            s = self.states[cid]
            s.positions.append((cx, cy))
            s.last_seen_frame = frame_idx

    # ── classification ────────────────────────────────────────────────────────

    def _classify_behaviors(self, frame_idx: int) -> None:
        # Only consider chickens seen in the last few frames
        active = {
            cid: s for cid, s in self.states.items()
            if frame_idx - s.last_seen_frame <= int(self.fps * 2)
        }

        # Current positions dict for neighbor calculations
        current_pos: Dict[int, np.ndarray] = {}
        for cid, s in active.items():
            if s.positions:
                current_pos[cid] = np.array(s.positions[-1], dtype=float)

        # Total active chickens (needed for huddling minimum)
        n_active = len(current_pos)

        for cid, s in active.items():
            behavior = self._classify_one(cid, s, current_pos, n_active)
            s.behavior = behavior

    def _classify_one(
        self,
        cid: int,
        state: ChickenState,
        current_pos: Dict[int, np.ndarray],
        n_active: int,
    ) -> Behavior:

        pos_history = list(state.positions)
        if len(pos_history) < 2:
            return Behavior.NORMAL

        # ── 1. Movement metrics ───────────────────────────────────────────────
        coords = np.array(pos_history, dtype=float)   # (T, 2)

        # Per-frame displacement
        displacements = np.linalg.norm(np.diff(coords, axis=0), axis=1)

        # Recent average velocity (last ill_frames / dead_frames window)
        def avg_vel(window: int) -> float:
            recent = displacements[-window:] if len(displacements) >= window else displacements
            return float(np.mean(recent)) if len(recent) > 0 else 0.0

        avg_vel_dead = avg_vel(self.dead_frames)
        avg_vel_ill  = avg_vel(self.ill_frames)

        # ── 2. Dead check (most severe — check first) ─────────────────────────
        if (
            len(pos_history) >= self.dead_frames
            and avg_vel_dead <= self.dead_vel
        ):
            return Behavior.POSSIBLY_DEAD

        # ── 3. Ill check ─────────────────────────────────────────────────────
        if (
            len(pos_history) >= self.ill_frames
            and avg_vel_ill <= self.ill_vel
        ):
            return Behavior.POSSIBLY_ILL

        # ── 4. Huddling check ────────────────────────────────────────────────
        if (
            cid in current_pos
            and n_active >= self.huddle_min
        ):
            me = current_pos[cid]
            others = [
                np.linalg.norm(me - pos)
                for oid, pos in current_pos.items()
                if oid != cid
            ]
            if others:
                others.sort()
                k_nearest = others[:self.huddle_k]
                if np.mean(k_nearest) < self.huddle_dist:
                    return Behavior.HUDDLING

        return Behavior.NORMAL

    # ── helpers ───────────────────────────────────────────────────────────────

    def get_huddling_pairs(
        self,
        current_pos: Dict[int, np.ndarray],
    ) -> List[Tuple[int, int]]:
        """Return pairs of IDs that are within huddle distance."""
        ids  = list(current_pos.keys())
        pairs = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                dist = float(np.linalg.norm(current_pos[a] - current_pos[b]))
                if dist < self.huddle_dist:
                    pairs.append((a, b))
        return pairs

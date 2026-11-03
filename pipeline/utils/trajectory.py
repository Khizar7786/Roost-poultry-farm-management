"""
TrajectoryBuffer
----------------
Maintains a rolling history of (cx, cy) positions for each tracked chicken ID.
Used by the behavior engine to compute velocity and displacement.
"""

from collections import deque
import numpy as np


class TrajectoryBuffer:
    """
    Stores per-ID position history as a fixed-length deque of (frame_idx, cx, cy) tuples.
    """

    def __init__(self, max_frames: int = 300):
        """
        Args:
            max_frames: Maximum number of frames to keep per ID.
                        At 30 fps, 300 frames = 10 seconds of history.
        """
        self._max_frames = max_frames
        # dict[int, deque[tuple[int, float, float]]]
        self._tracks: dict[int, deque] = {}

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def update(self, track_id: int, frame_idx: int, cx: float, cy: float) -> None:
        """Append a new position for the given track ID."""
        if track_id not in self._tracks:
            self._tracks[track_id] = deque(maxlen=self._max_frames)
        self._tracks[track_id].append((frame_idx, cx, cy))

    def get_positions(self, track_id: int) -> list[tuple[int, float, float]]:
        """Return the full position history as a list of (frame_idx, cx, cy)."""
        return list(self._tracks.get(track_id, []))

    def average_displacement(self, track_id: int, window_frames: int) -> float:
        """
        Mean Euclidean step distance over the last `window_frames` frames.
        Returns 0.0 if fewer than 2 positions are available.
        """
        positions = self.get_positions(track_id)
        if len(positions) < 2:
            return 0.0
        recent = positions[-window_frames:]
        dists = [
            np.hypot(recent[i][1] - recent[i - 1][1],
                     recent[i][2] - recent[i - 1][2])
            for i in range(1, len(recent))
        ]
        return float(np.mean(dists)) if dists else 0.0

    def all_ids(self) -> list[int]:
        return list(self._tracks.keys())

    def remove(self, track_id: int) -> None:
        """Remove a stale track ID."""
        self._tracks.pop(track_id, None)

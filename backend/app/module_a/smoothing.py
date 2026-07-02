"""One Euro Filter for smoothing noisy landmark coordinates over time.

Reference: Casiez et al., "1€ Filter: A Simple Speed-based Low-pass Filter
for Noisy Input in Interactive Systems" (blueprint §4.2).
"""

import math

from app.module_a.config import MIN_VISIBILITY


class OneEuroFilter:
    """Low-pass filter whose cutoff adapts to the signal's speed."""

    def __init__(
        self, min_cutoff: float = 1.0, beta: float = 0.5, d_cutoff: float = 1.0
    ):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x_prev: float | None = None
        self._dx_prev = 0.0
        self._t_prev: float | None = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x: float, t: float) -> float:
        if self._t_prev is None:
            self._x_prev = x
            self._t_prev = t
            return x

        dt = max(t - self._t_prev, 1e-6)
        self._t_prev = t

        dx = (x - self._x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self._dx_prev
        self._dx_prev = dx_hat

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self._x_prev
        self._x_prev = x_hat
        return x_hat


class LandmarkSmoother:
    """Runs one OneEuroFilter per landmark index per axis (x, y, z).

    Landmarks below MIN_VISIBILITY are not filtered — the last smoothed
    value is held instead, so a brief occlusion doesn't inject noise.
    """

    def __init__(self, num_landmarks: int = 33):
        self._filters: dict[tuple[int, str], OneEuroFilter] = {
            (i, axis): OneEuroFilter()
            for i in range(num_landmarks)
            for axis in ("x", "y", "z")
        }
        self._last: dict[int, dict] = {}

    def smooth_frame(
        self, timestamp_sec: float, world_landmarks: list[dict]
    ) -> list[dict]:
        smoothed = []
        for i, lm in enumerate(world_landmarks):
            visibility = lm.get("visibility", 0.0)
            if visibility < MIN_VISIBILITY and i in self._last:
                smoothed.append(self._last[i])
                continue

            point = {
                "x": self._filters[(i, "x")].filter(lm["x"], timestamp_sec),
                "y": self._filters[(i, "y")].filter(lm["y"], timestamp_sec),
                "z": self._filters[(i, "z")].filter(lm["z"], timestamp_sec),
                "visibility": visibility,
            }
            self._last[i] = point
            smoothed.append(point)
        return smoothed

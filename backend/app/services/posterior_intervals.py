"""Highest-density posterior intervals for one-dimensional sample arrays.

Every runner in this service reports ``hdi_low_94`` / ``hdi_high_94`` (and the
frontend labels the pair "94% HDI").  Before 2026-09-09 several of those sites
silently filled the fields with the 3rd/97th percentiles — an equal-tailed
interval (ETI), which coincides with the HDI only for symmetric posteriors and
is visibly wider on the skewed w, w_a, M_B or rd posteriors that dark-energy
and BAO-only runs produce.  This module is the single implementation those
sites now share, so the label and the number agree.

The algorithm is the standard sorted-sample search (the same one ArviZ's
``hdi`` uses for a 1-D unimodal input): among all windows holding
``floor(prob * n)`` consecutive sorted draws, take the narrowest.  For a
multimodal posterior it returns the narrowest *single* interval, which is the
honest 1-D fallback (a split HDI needs a density estimate and is out of scope).
"""

from __future__ import annotations

import math

import numpy as np

DEFAULT_HDI_PROB = 0.94


def hdi_interval(values, prob: float = DEFAULT_HDI_PROB) -> tuple[float, float]:
    """Return the narrowest interval containing ``prob`` of the finite draws.

    Non-finite draws are ignored.  With fewer than two finite draws the
    interval collapses to the available range (or NaNs when empty).
    """
    if not (0.0 < prob < 1.0):
        raise ValueError(f"prob must lie in (0, 1); got {prob}")
    x = np.sort(np.asarray(values, dtype=float).ravel())
    x = x[np.isfinite(x)]
    n = x.size
    if n == 0:
        return math.nan, math.nan
    if n == 1:
        return float(x[0]), float(x[0])
    # Window of floor(prob * n) sorted-index steps (ArviZ's convention, so the
    # two implementations agree to the last draw); the narrowest such window.
    span = int(math.floor(prob * n))
    if span < 1:
        span = 1
    if span >= n:
        return float(x[0]), float(x[-1])
    widths = x[span:] - x[: n - span]
    start = int(np.argmin(widths))
    return float(x[start]), float(x[start + span])


def equal_tailed_interval(values, prob: float = DEFAULT_HDI_PROB) -> tuple[float, float]:
    """Symmetric-tail credible interval (percentile based); kept for callers
    that explicitly want tail quantiles rather than the HDI."""
    x = np.asarray(values, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size == 0:
        return math.nan, math.nan
    tail = 100.0 * (1.0 - prob) / 2.0
    low, high = np.percentile(x, [tail, 100.0 - tail])
    return float(low), float(high)

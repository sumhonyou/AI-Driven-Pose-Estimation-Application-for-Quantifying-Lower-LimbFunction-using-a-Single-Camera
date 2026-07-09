"""Measurement-agreement statistics: ICC, Bland-Altman, Cohen's kappa.

This is a measurement-agreement problem (system hold-time vs a human-timed
reference), not a classifier-accuracy problem -- these three statistics are the
standard tools for that framing (blueprint plan doc, evaluation framing note).

No numpy/scipy/pingouin dependency: this project's requirements.txt has none of
them, and these formulas are simple closed-form sums over a small sample, so a
pure-Python implementation avoids adding a new dependency for three formulas.
"""

import math


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _sample_stdev(values: list[float]) -> float:
    """Sample standard deviation (n-1 denominator) -- Bland & Altman (1986) convention."""
    n = len(values)
    if n < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))


def icc_2_1(system: list[float], manual: list[float]) -> float:
    """Two-way random effects, single measurement, ABSOLUTE agreement: ICC(2,1).

    Reference: Shrout & Fleiss (1979), "Intraclass correlations: uses in
    assessing rater reliability". Chosen over ICC(3,1) ("consistency") because
    we care whether the system's seconds literally match a human's stopwatch
    seconds, not just whether they move proportionally together.

    n subjects (sessions/legs) x k=2 raters (system, manual). Returns a value
    in roughly [-1, 1]; 1.0 = perfect absolute agreement.
    """
    if len(system) != len(manual):
        raise ValueError("system and manual must be the same length")
    n = len(system)
    if n < 2:
        raise ValueError("need at least 2 subjects for ICC")
    k = 2

    rows = list(zip(system, manual))
    grand_mean = _mean(system + manual)
    row_means = [_mean(list(r)) for r in rows]
    col_means = [_mean(system), _mean(manual)]

    ss_total = sum((v - grand_mean) ** 2 for r in rows for v in r)
    ss_rows = k * sum((rm - grand_mean) ** 2 for rm in row_means)
    ss_cols = n * sum((cm - grand_mean) ** 2 for cm in col_means)
    ss_error = ss_total - ss_rows - ss_cols

    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1)) if (n - 1) * (k - 1) > 0 else 0.0

    denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    if abs(denom) < 1e-12:
        return 1.0 if abs(ms_rows - ms_error) < 1e-12 else 0.0
    return (ms_rows - ms_error) / denom


def bland_altman(system: list[float], manual: list[float]) -> dict:
    """Bias (mean difference) and 95% limits of agreement (Bland & Altman, 1986).

    `diff` is defined as system - manual: positive bias means the system tends
    to read longer than the human-timed reference.
    """
    if len(system) != len(manual):
        raise ValueError("system and manual must be the same length")
    if not system:
        raise ValueError("need at least 1 paired sample")

    diffs = [s - m for s, m in zip(system, manual)]
    bias = _mean(diffs)
    sd = _sample_stdev(diffs)
    return {
        "bias_sec": round(bias, 3),
        "sd_sec": round(sd, 3),
        "loa_lower_sec": round(bias - 1.96 * sd, 3),
        "loa_upper_sec": round(bias + 1.96 * sd, 3),
        "n": len(diffs),
    }


def cohens_kappa(system_labels: list[str], manual_labels: list[str]) -> float:
    """Unweighted Cohen's kappa (Cohen, 1960) for categorical band agreement."""
    if len(system_labels) != len(manual_labels):
        raise ValueError("system_labels and manual_labels must be the same length")
    n = len(system_labels)
    if n == 0:
        raise ValueError("need at least 1 paired label")

    categories = sorted(set(system_labels) | set(manual_labels))
    sys_counts = {c: 0 for c in categories}
    man_counts = {c: 0 for c in categories}
    agree = 0
    for s, m in zip(system_labels, manual_labels):
        sys_counts[s] += 1
        man_counts[m] += 1
        if s == m:
            agree += 1

    po = agree / n
    pe = sum(sys_counts[c] * man_counts[c] for c in categories) / (n * n)
    if abs(1 - pe) < 1e-12:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)

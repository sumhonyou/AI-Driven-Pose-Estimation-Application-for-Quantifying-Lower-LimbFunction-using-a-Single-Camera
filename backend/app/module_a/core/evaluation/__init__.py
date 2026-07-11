"""Measurement-agreement evaluation shared across Module A exercises.

Deliberately pure Python (no numpy/scipy/pandas) -- this project has no
dependency on a stats library, and ICC / Bland-Altman / Cohen's kappa are all
straightforward closed-form formulas over small samples. Used by both the SLS
(hold-time, seconds) and WBLT (distance cm / angle deg) replay harnesses --
the formulas are unit-agnostic, so callers label units in their own reports.
"""

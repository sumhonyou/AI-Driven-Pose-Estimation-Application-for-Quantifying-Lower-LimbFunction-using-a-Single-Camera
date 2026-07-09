"""Measurement-agreement evaluation for Module A (SLS replay harness).

Deliberately pure Python (no numpy/scipy/pandas) -- this project has no
dependency on a stats library, and ICC / Bland-Altman / Cohen's kappa are all
straightforward closed-form formulas over small samples.
"""

"""F4.17 / F4.18 -- Bland-Altman plots for Module A's two measurement-agreement
studies (SLS hold time, WBLT reach distance).

Neither figure existed anywhere in the project before this script -- the SLS and
WBLT evaluation reports quote bias/LoA numbers but never plotted them. This script
replays each corpus through the same real analysis + agreement functions the
reports use (`app.module_a.sls.analysis`, `app.module_a.wblt.analysis`,
`app.module_a.core.evaluation.agreement.bland_altman`), so the plotted bias and
limits are guaranteed to match the numbers already quoted in
SLS_EVALUATION_REPORT.md / WBLT_EVALUATION_REPORT.md rather than being recomputed
by a second, possibly-diverging path.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from plotting import save_fig

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
SLS_CORPUS = BACKEND_ROOT / "app" / "module_a" / "replay_corpus" / "sls"
WBLT_CORPUS = BACKEND_ROOT / "app" / "module_a" / "replay_corpus" / "wblt"


def _bland_altman_plot(
    means: list[float],
    diffs: list[float],
    bias: float,
    loa_lower: float,
    loa_upper: float,
    *,
    unit: str,
    title: str,
    fig_name: str,
) -> Path:
    fig, ax = plt.subplots()
    ax.scatter(means, diffs, color="#2b8cbe", s=50, zorder=3)
    ax.axhline(bias, color="#e6550d", lw=1.5, label=f"Bias = {bias:+.3f}{unit}")
    ax.axhline(
        loa_lower,
        color="gray",
        lw=1,
        linestyle="--",
        label=f"95% LoA = [{loa_lower:.3f}, {loa_upper:.3f}]{unit}",
    )
    ax.axhline(loa_upper, color="gray", lw=1, linestyle="--")
    ax.set_xlabel(f"Mean of system and manual reading ({unit})")
    ax.set_ylabel(f"Difference (system − manual, {unit})")
    ax.set_title(title)
    ax.legend(loc="best")
    return save_fig(fig, fig_name, figsize="single")


def plot_sls() -> Path:
    from app.module_a.core.evaluation.agreement import bland_altman
    from app.module_a.sls import analysis

    manifest = json.loads((SLS_CORPUS / "labels.json").read_text())
    system_holds, manual_holds = [], []
    for entry in manifest:
        frames = json.loads((SLS_CORPUS / entry["frames_file"]).read_text())
        result = analysis.analyze_leg(frames, entry["leg"])["metrics"]
        system_holds.append(result["holdSeconds"])
        manual_holds.append(entry["manual_hold_sec"])

    ba = bland_altman(system_holds, manual_holds)
    means = [(s + m) / 2 for s, m in zip(system_holds, manual_holds)]
    diffs = [s - m for s, m in zip(system_holds, manual_holds)]

    print(
        f"SLS: n={len(means)} bias={ba['bias']:.4f}s "
        f"LoA=[{ba['loa_lower']:.4f}, {ba['loa_upper']:.4f}]s"
    )
    return _bland_altman_plot(
        means,
        diffs,
        ba["bias"],
        ba["loa_lower"],
        ba["loa_upper"],
        unit="s",
        title="Bland-Altman -- SLS hold time\nSystem vs. simulated manual (stopwatch) reference",
        fig_name="bland_altman_sls_holdtime",
    )


def plot_wblt() -> Path:
    from app.module_a.core.evaluation.agreement import bland_altman
    from app.module_a.wblt import analysis
    from app.module_a.wblt.age_band import resolve_ageband_sex

    manifest = json.loads((WBLT_CORPUS / "labels.json").read_text())
    system_distances, manual_distances = [], []
    for entry in manifest:
        frames = json.loads((WBLT_CORPUS / entry["frames_file"]).read_text())
        result = analysis.analyze_attempt(
            frames,
            entry["leg"],
            entry["target_distance_cm"],
            entry["touched"],
            entry["exact_age"],
            entry["gender"],
        )
        if result["distance_cm"] is None:
            continue  # excluded exactly as the evaluation report excludes it
        system_distances.append(result["distance_cm"])
        manual_distances.append(entry["manual_distance_cm"])

    ba = bland_altman(system_distances, manual_distances)
    means = [(s + m) / 2 for s, m in zip(system_distances, manual_distances)]
    diffs = [s - m for s, m in zip(system_distances, manual_distances)]

    print(
        f"WBLT: n={len(means)} bias={ba['bias']:.4f}cm "
        f"LoA=[{ba['loa_lower']:.4f}, {ba['loa_upper']:.4f}]cm"
    )
    return _bland_altman_plot(
        means,
        diffs,
        ba["bias"],
        ba["loa_lower"],
        ba["loa_upper"],
        unit="cm",
        title="Bland-Altman -- WBLT reach distance\nSystem vs. simulated independent repeat tape reading",
        fig_name="bland_altman_wblt_distance",
    )


def main() -> None:
    sls_path = plot_sls()
    wblt_path = plot_wblt()
    print(f"wrote {sls_path}")
    print(f"wrote {wblt_path}")


if __name__ == "__main__":
    main()

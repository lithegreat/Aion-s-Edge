"""UI helpers for rendering Level 2 Pareto analysis."""

from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
from numpy.typing import NDArray


def draw_pareto_plot(
    solutions: NDArray,
    pareto_idx: List[int],
    dominated_idx: List[int],
    selected_idx: Optional[int],
) -> plt.Figure:
    """Draw the scatter plot with Pareto front highlighted."""
    fig, ax = plt.subplots(figsize=(8, 6))

    dominated = solutions[dominated_idx]
    ax.scatter(
        dominated[:, 0],
        dominated[:, 1],
        c="#3498db",
        s=50,
        alpha=0.6,
        label="Dominated",
        zorder=3,
    )

    pareto = solutions[pareto_idx]
    sort_order = pareto[:, 0].argsort()
    pareto_sorted = pareto[sort_order]
    ax.scatter(
        pareto[:, 0],
        pareto[:, 1],
        c="#e74c3c",
        s=80,
        edgecolors="black",
        linewidths=1,
        label="Pareto Front",
        zorder=4,
    )
    ax.plot(
        pareto_sorted[:, 0],
        pareto_sorted[:, 1],
        "-",
        color="#e74c3c",
        alpha=0.5,
        linewidth=1.5,
        zorder=3,
    )

    if selected_idx is not None:
        point = solutions[selected_idx]
        ax.scatter(
            [point[0]],
            [point[1]],
            c="gold",
            s=200,
            marker="*",
            edgecolors="black",
            linewidths=1.5,
            label="Your choice",
            zorder=5,
        )

    for index, (px, py) in enumerate(solutions):
        ax.annotate(
            str(index),
            (px, py),
            fontsize=6,
            alpha=0.5,
            textcoords="offset points",
            xytext=(4, 4),
        )

    ax.set_xlabel("Pollution (lower is better)", fontsize=12)
    ax.set_ylabel("Economic Output (higher is better)", fontsize=12)
    ax.set_title(
        "Aion's Edge · Level 2 — Pareto Front",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
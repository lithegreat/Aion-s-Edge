"""UI helpers for rendering Level 1 linear-programming content."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Polygon

from src.campaign import (
    DEFAULT_B_UB,
    TOTAL_TURNS,
    X_MAX,
    Y_MAX,
    GameEvent,
    get_b_ub,
    get_objective,
)
from .core import compute_feasible_polygon, is_feasible


def draw_lp_plot(
    x1_player: float,
    x2_player: float,
    x1_opt: float,
    x2_opt: float,
) -> plt.Figure:
    """Render the 2-D feasible-region plot."""
    b_ub = get_b_ub()
    objective = get_objective()

    fig, ax = plt.subplots(figsize=(8, 6))
    x_range = np.linspace(0, X_MAX, 400)

    ax.plot(
        x_range,
        b_ub[0] - 2 * x_range,
        label=rf"$C_1$: $2x_1 + x_2 \leq {b_ub[0]:.0f}$ (Energy)",
        color="#1f77b4",
        linewidth=2,
    )
    ax.plot(
        x_range,
        (b_ub[1] - x_range) / 2,
        label=rf"$C_2$: $x_1 + 2x_2 \leq {b_ub[1]:.0f}$ (Labour)",
        color="#ff7f0e",
        linewidth=2,
    )

    if not np.allclose(b_ub, DEFAULT_B_UB):
        ax.plot(
            x_range,
            DEFAULT_B_UB[0] - 2 * x_range,
            "--",
            color="#1f77b4",
            alpha=0.25,
            linewidth=1,
        )
        ax.plot(
            x_range,
            (DEFAULT_B_UB[1] - x_range) / 2,
            "--",
            color="#ff7f0e",
            alpha=0.25,
            linewidth=1,
        )

    ax.add_patch(Polygon(
        compute_feasible_polygon(),
        closed=True,
        facecolor="lightgray",
        edgecolor="gray",
        alpha=0.45,
        label="Feasible Region",
    ))

    player_color = "red" if not is_feasible(x1_player, x2_player) else "#e74c3c"
    ax.plot(
        x1_player,
        x2_player,
        "o",
        color=player_color,
        markersize=12,
        markeredgecolor="black",
        markeredgewidth=1.5,
        label=f"Player choice ({x1_player:.0f}, {x2_player:.0f})",
        zorder=5,
    )
    ax.plot(
        x1_opt,
        x2_opt,
        "*",
        color="#2ecc71",
        markersize=20,
        markeredgecolor="black",
        markeredgewidth=1,
        label=f"Optimal ({x1_opt:.1f}, {x2_opt:.1f})",
        zorder=5,
    )

    z_player = objective[0] * x1_player + objective[1] * x2_player
    if objective[1] != 0:
        ax.plot(
            x_range,
            (z_player - objective[0] * x_range) / objective[1],
            "--",
            color="#9b59b6",
            linewidth=1,
            alpha=0.6,
            label=f"Iso-profit line Z = {z_player:.0f}",
        )

    ax.set_xlim(0, X_MAX)
    ax.set_ylim(0, Y_MAX)
    ax.set_xlabel(r"$x_1$ — Oxygen production", fontsize=12)
    ax.set_ylabel(r"$x_2$ — Food production", fontsize=12)
    ax.set_title(
        f"Aion's Edge · Level 1 — Turn {st.session_state.turn}/{TOTAL_TURNS}",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def render_event_banner() -> None:
    """Display the current-turn event as a prominent banner."""
    event: Optional[GameEvent] = st.session_state.current_event
    if event is None:
        return

    if event.name in ("dust_storm", "flu"):
        st.warning(f"{event.title}\n\n{event.description}", icon=event.icon)
    elif event.name == "tech_breakthrough":
        st.success(f"{event.title}\n\n{event.description}", icon="🔬")
    else:
        st.info(f"{event.title}\n\n{event.description}", icon="☀️")
"""Level 1 UI and logic for linear-programming survival planning."""

from __future__ import annotations

from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Polygon
from numpy.typing import NDArray

from src.OptimizationEngine import LPSolver
from src.campaign import (
    A_UB,
    BOUNDS,
    DEFAULT_B_UB,
    TOTAL_TURNS,
    X_MAX,
    Y_MAX,
    GameEvent,
    advance_turn,
    apply_colony_delta,
    get_b_ub,
    get_objective,
    reset_session_state,
)


def compute_optimal_solution() -> Tuple[NDArray[np.float64], float]:
    """Use the LP solver to find the current optimum."""
    result = LPSolver.solve(
        c=get_objective(),
        A_ub=A_UB,
        b_ub=get_b_ub(),
        bounds=BOUNDS,
        maximize=True,
    )
    return result.solution, result.optimal_value


def resolve_level1_turn(
    x1_player: float,
    x2_player: float,
    opt_value: float,
    feasible: bool,
) -> None:
    """Translate a production choice into persistent colony effects."""
    objective = get_objective()
    z_player = float(objective[0] * x1_player + objective[1] * x2_player)

    if feasible:
        efficiency = z_player / max(opt_value, 1.0)
        oxygen_delta = 0.28 * (x1_player - 18.0)
        food_delta = 0.28 * (x2_player - 18.0)
        economy_delta = 8.0 * efficiency - 2.0
        morale_delta = 5.0 * efficiency - 1.0
        environment_delta = -max(0.0, x1_player + x2_player - 55.0) * 0.18

        st.session_state.total_score += z_player
        apply_colony_delta(
            oxygen=oxygen_delta,
            food=food_delta,
            economy=economy_delta,
            environment=environment_delta,
            morale=morale_delta,
            log_message=(
                f"Turn {st.session_state.turn}: production yielded"
                f" {z_player:.0f} output at {efficiency * 100:.0f}%"
                " efficiency."
            ),
        )
        return

    apply_colony_delta(
        oxygen=-8.0,
        food=-8.0,
        economy=-6.0,
        morale=-12.0,
        log_message=(
            f"Turn {st.session_state.turn}: infeasible production plan"
            " triggered rationing and unrest."
        ),
    )


def is_feasible(x1: float, x2: float) -> bool:
    """Check whether a point satisfies all current constraints."""
    point = np.array([x1, x2])
    within_ub = np.all(A_UB @ point <= get_b_ub() + 1e-9)
    return bool(within_ub and x1 >= 0 and x2 >= 0)


def compute_feasible_polygon() -> NDArray[np.float64]:
    """Compute the vertices of the feasible polygon."""
    b_ub = get_b_ub()
    lines = [(A_UB[i, 0], A_UB[i, 1], b_ub[i]) for i in range(A_UB.shape[0])]
    lines.extend([(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])

    vertices = []
    n_lines = len(lines)
    for i in range(n_lines):
        for j in range(i + 1, n_lines):
            a_matrix = np.array([
                [lines[i][0], lines[i][1]],
                [lines[j][0], lines[j][1]],
            ])
            b_vector = np.array([lines[i][2], lines[j][2]])
            if abs(np.linalg.det(a_matrix)) < 1e-12:
                continue
            point = np.linalg.solve(a_matrix, b_vector)
            if is_feasible(point[0], point[1]):
                vertices.append(point)

    vertices_array = np.array(vertices)
    centroid = vertices_array.mean(axis=0)
    angles = np.arctan2(
        vertices_array[:, 1] - centroid[1],
        vertices_array[:, 0] - centroid[0],
    )
    return vertices_array[np.argsort(angles)]


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


def render_level1() -> None:
    """Render Level 1 — Linear Programming survival mode."""
    render_event_banner()

    if st.session_state.game_over:
        if st.session_state.defeat_reason is None:
            st.balloons()
            st.success(
                f"🎉 Congratulations! You survived {TOTAL_TURNS} turns!\n\n"
                f"Cumulative total output: **{st.session_state.total_score:.0f}**"
            )
        else:
            st.error(
                f"☠️ Colony lost. {st.session_state.defeat_reason}\n\n"
                f"Final total output: **{st.session_state.total_score:.0f}**"
            )
        if st.button("🔄 Restart", key="l1_restart"):
            reset_session_state()
            st.rerun()
        return

    b_ub = get_b_ub()
    objective = get_objective()

    st.markdown(
        f"""
        You are the colony's central AI **AION**. Adjust production of **Oxygen** ($x_1$)
        and **Food** ($x_2$) to maximise total colony output under limited **Energy**
        and **Labour** constraints:

        $$Z = {objective[0]:.0f}\\,x_1 + {objective[1]:.0f}\\,x_2$$
        """
    )

    st.sidebar.header("⚙️ L1 Production Control")
    st.sidebar.markdown(f"**Turn {st.session_state.turn} / {TOTAL_TURNS}**")

    x1_player = st.sidebar.slider("x₁ — Oxygen production", 0, 60, 20, 1, key="l1_x1")
    x2_player = st.sidebar.slider("x₂ — Food production", 0, 80, 20, 1, key="l1_x2")

    opt_solution, opt_value = compute_optimal_solution()
    x1_opt, x2_opt = opt_solution[0], opt_solution[1]
    feasible = is_feasible(x1_player, x2_player)
    z_player = float(objective[0] * x1_player + objective[1] * x2_player)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Current Constraints")
    st.sidebar.latex(rf"C_1:\;2x_1+x_2\leq {b_ub[0]:.0f}")
    st.sidebar.latex(rf"C_2:\;x_1+2x_2\leq {b_ub[1]:.0f}")

    st.sidebar.markdown("---")
    if st.sidebar.button("⏭️ Submit and Next Turn", use_container_width=True, key="l1_next"):
        resolve_level1_turn(x1_player, x2_player, opt_value, feasible)
        if not st.session_state.game_over:
            advance_turn()
        st.rerun()

    st.sidebar.metric("📈 Cumulative Total Output", f"{st.session_state.total_score:.0f}")

    col_chart, col_info = st.columns([2, 1])
    with col_chart:
        st.pyplot(draw_lp_plot(x1_player, x2_player, x1_opt, x2_opt))

    with col_info:
        st.markdown("### 📊 Panel Status")
        if feasible:
            st.success("✅ Production plan is feasible!")
        else:
            st.error("🚨 Not enough resources — plan exceeds constraints!")

        st.metric(
            "Current Total Output Z",
            f"{z_player:.0f}",
            delta=(f"{z_player - opt_value:+.0f} vs Optimal" if feasible else "Infeasible"),
        )
        st.metric("Optimal Total Output Z*", f"{opt_value:.0f}")

        st.markdown("---")
        c1_used = 2 * x1_player + x2_player
        c2_used = x1_player + 2 * x2_player
        st.markdown(f"**Energy** (C₁): {c1_used:.0f}/{b_ub[0]:.0f}")
        st.progress(min(c1_used / b_ub[0], 1.0))
        st.markdown(f"**Labour** (C₂): {c2_used:.0f}/{b_ub[1]:.0f}")
        st.progress(min(c2_used / b_ub[1], 1.0))

        st.markdown("---")
        st.markdown(f"**Optimal solution**: $x_1^*={x1_opt:.1f}$, $x_2^*={x2_opt:.1f}$")
        if feasible and opt_value > 0:
            efficiency = z_player / opt_value * 100
            st.markdown(f"**Efficiency**: {efficiency:.1f}%")
            if efficiency >= 99.9:
                st.balloons()
                st.success("🎉 Perfect!")
            elif efficiency >= 90:
                st.info("👍 Very close!")
            elif efficiency >= 70:
                st.warning("💡 Room for improvement.")
            else:
                st.warning("⚠️ Low output.")

    if st.session_state.event_log:
        with st.expander("📜 Event Log"):
            for entry in reversed(st.session_state.event_log):
                st.markdown(f"- {entry}")
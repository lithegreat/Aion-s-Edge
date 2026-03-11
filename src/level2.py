"""Level 2 UI and logic for multi-objective policy design."""

from __future__ import annotations

from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from numpy.typing import NDArray

from src.OptimizationEngine import MOOSolver
from src.campaign import (
    apply_colony_delta,
    change_influence_tokens,
    record_turn_report,
    set_phase,
)


N_MOO_SOLUTIONS = 50


def generate_policy_allocations() -> NDArray[np.float64]:
    """Create AI policy budgets for Level 2."""
    rng = np.random.default_rng()
    return rng.dirichlet(
        np.array([2.5, 1.8, 1.5]),
        size=N_MOO_SOLUTIONS - 1,
    ) * 100.0


def policy_to_objectives(
    allocation: NDArray[np.float64],
) -> Tuple[float, float, float]:
    """Map a budget split to pollution, output, and morale lift."""
    industry, ecology, welfare = allocation

    pollution = (
        22.0
        + 0.78 * industry
        - 0.58 * ecology
        - 0.10 * welfare
        + max(0.0, 55.0 - st.session_state.environment) * 0.22
    )
    output = (
        35.0
        + 0.88 * industry
        + 0.24 * welfare
        - 0.16 * ecology
        + st.session_state.economy * 0.22
    )
    morale_lift = (
        0.18 * welfare
        + 0.10 * ecology
        - 0.12 * industry
        + (st.session_state.morale - 50.0) * 0.02
    )

    pollution = float(np.clip(pollution, 5.0, 140.0))
    output = float(np.clip(output, 10.0, 170.0))
    return pollution, output, morale_lift


def apply_policy_choice(
    allocation: NDArray[np.float64],
    pollution: float,
    output: float,
    morale_lift: float,
    pareto_optimal: bool,
) -> None:
    """Persist the chosen Level 2 policy into the campaign."""
    industry, ecology, welfare = allocation
    apply_colony_delta(
        oxygen=0.05 * ecology + 0.03 * welfare - 0.04 * industry,
        food=0.06 * welfare - 0.02 * industry,
        economy=(output - 80.0) / 8.0,
        environment=(55.0 - pollution) / 5.0,
        morale=morale_lift / 2.0,
        log_message=(
            "Policy enacted: "
            f"industry {industry:.0f}%, ecology {ecology:.0f}%, "
            f"welfare {welfare:.0f}% -> pollution {pollution:.0f}, "
            f"output {output:.0f}."
        ),
    )
    change_influence_tokens(1 if pareto_optimal else 0)
    pareto_text = "Pareto-optimal" if pareto_optimal else "dominated"
    record_turn_report(
        "Policy",
        (
            f"Adopted a {pareto_text} budget: industry {industry:.0f}%,"
            f" ecology {ecology:.0f}%, welfare {welfare:.0f}%"
            f" -> output {output:.0f}, pollution {pollution:.0f}."
        ),
    )


def draw_pareto_plot(
    solutions: NDArray[np.float64],
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
    sort_order = np.argsort(pareto[:, 0])
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


def find_dominator(
    idx: int,
    solutions: NDArray[np.float64],
    pareto_front: List[int],
) -> Optional[int]:
    """Find a Pareto-front member that dominates the chosen solution."""
    candidate = solutions[idx]
    for pareto_idx in pareto_front:
        other = solutions[pareto_idx]
        if (
            other[0] <= candidate[0]
            and other[1] >= candidate[1]
            and (other[0] < candidate[0] or other[1] > candidate[1])
        ):
            return pareto_idx
    return None


def render_level2() -> None:
    """Render Level 2 — Multi-Objective Optimisation."""
    st.markdown(
        """
        The colony now has a **policy budget**. Split it between **industry**,
        **ecology**, and **welfare**, then compare your proposal against the
        AI-generated alternatives. The goal is no longer just to spot a good
        point; it is to **design** one.
        """
    )

    st.sidebar.header("🔬 L2 Policy Design")
    st.sidebar.caption("Stage 2 of 4: commit a medium-term policy package.")
    if st.sidebar.button(
        "🎲 Generate New Policy Market",
        use_container_width=True,
        key="l2_gen",
    ):
        st.session_state.moo_ai_allocations = None
        st.rerun()

    if st.session_state.moo_ai_allocations is None:
        st.session_state.moo_ai_allocations = generate_policy_allocations()

    st.sidebar.markdown("### 🧮 Budget Split")
    industry_share = st.sidebar.slider("Industry %", 0, 100, 40, 1, key="l2_industry")
    ecology_max = 100 - industry_share
    ecology_share = st.sidebar.slider(
        "Ecology %",
        0,
        ecology_max,
        min(30, ecology_max),
        1,
        key="l2_ecology",
    )
    welfare_share = 100 - industry_share - ecology_share
    st.sidebar.metric("Welfare %", f"{welfare_share}")

    player_allocation = np.array([industry_share, ecology_share, welfare_share], dtype=np.float64)
    ai_allocations = np.asarray(st.session_state.moo_ai_allocations, dtype=np.float64)
    ai_solutions = np.array([policy_to_objectives(allocation)[:2] for allocation in ai_allocations])
    player_pollution, player_output, morale_lift = policy_to_objectives(player_allocation)
    solutions = np.vstack([ai_solutions, np.array([player_pollution, player_output])])
    player_idx = int(solutions.shape[0] - 1)

    pareto_result = MOOSolver.find_pareto_front(solutions, maximize=[False, True])

    col_chart, col_info = st.columns([2, 1])
    with col_chart:
        st.pyplot(
            draw_pareto_plot(
                solutions,
                pareto_result.pareto_front,
                pareto_result.dominated,
                player_idx,
            )
        )

    with col_info:
        st.markdown("### 📊 Your Policy")
        st.markdown(
            f"**Industry**: `{industry_share}%`  \n"
            f"**Ecology**: `{ecology_share}%`  \n"
            f"**Welfare**: `{welfare_share}%`"
        )
        st.markdown(
            f"Predicted pollution: `{player_pollution:.1f}`  \n"
            f"Predicted output: `{player_output:.1f}`  \n"
            f"Morale lift: `{morale_lift:+.1f}`"
        )

        is_pareto = player_idx in pareto_result.pareto_front
        if is_pareto:
            st.success(
                "⭐ Pareto optimal! Your policy survives comparison with every"
                " AI alternative."
            )
        else:
            st.error(
                "❌ Dominated policy! Another portfolio is at least as good on"
                " both objectives and strictly better on one of them."
            )
            dominator_idx = find_dominator(player_idx, solutions, pareto_result.pareto_front)
            if dominator_idx is not None:
                dominator = solutions[dominator_idx]
                st.markdown(
                    f"For example, **AI policy #{dominator_idx}** (pollution"
                    f" `{dominator[0]:.1f}`, output `{dominator[1]:.1f}`)"
                    " dominates your proposal."
                )

        if st.button(
            "✅ Enact policy and continue",
            use_container_width=True,
            key="l2_enact",
        ):
            apply_policy_choice(
                allocation=player_allocation,
                pollution=player_pollution,
                output=player_output,
                morale_lift=morale_lift,
                pareto_optimal=is_pareto,
            )
            if not st.session_state.game_over:
                set_phase("council")
            st.rerun()

        st.markdown("---")
        st.markdown("### 📈 Pareto Statistics")
        st.markdown(f"- Number of Pareto-optimal solutions: **{len(pareto_result.pareto_front)}**")
        st.markdown(f"- Number of dominated solutions: **{len(pareto_result.dominated)}**")

        nadir = MOOSolver.nadir_point(pareto_result.pareto_points, maximize=[False, True])
        st.markdown("---")
        st.markdown("### ⚠️ Nadir point (worst-case)")
        st.markdown(
            f"Highest pollution: `{nadir[0]:.1f}`  \n"
            f"Lowest output: `{nadir[1]:.1f}`"
        )
        st.caption(
            "The Nadir point shows the worst value of each objective on the"
            " Pareto front — avoid this disaster point."
        )
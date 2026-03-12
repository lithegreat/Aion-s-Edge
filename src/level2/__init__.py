"""Level 2 orchestration for multi-objective policy design."""

from __future__ import annotations

import numpy as np
import streamlit as st

from src.OptimizationEngine import MOOSolver
from src.campaign import set_phase
from .core import (
    apply_policy_choice,
    find_dominator,
    generate_policy_allocations,
    policy_to_objectives,
)
from .views import draw_pareto_plot


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
    industry_share = st.sidebar.slider(
        "Industry %", 0, 100, 40, 1, key="l2_industry"
    )
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

    player_allocation = np.array(
        [industry_share, ecology_share, welfare_share],
        dtype=np.float64,
    )
    ai_allocations = np.asarray(
        st.session_state.moo_ai_allocations,
        dtype=np.float64,
    )
    ai_solutions = np.array([
        policy_to_objectives(allocation)[:2]
        for allocation in ai_allocations
    ])
    player_pollution, player_output, morale_lift = policy_to_objectives(
        player_allocation
    )
    solutions = np.vstack([
        ai_solutions,
        np.array([player_pollution, player_output]),
    ])
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
            dominator_idx = find_dominator(
                player_idx,
                solutions,
                pareto_result.pareto_front,
            )
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
        st.markdown(
            "- Number of Pareto-optimal solutions:"
            f" **{len(pareto_result.pareto_front)}**"
        )
        st.markdown(
            f"- Number of dominated solutions:"
            f" **{len(pareto_result.dominated)}**"
        )

        nadir = MOOSolver.nadir_point(
            pareto_result.pareto_points,
            maximize=[False, True],
        )
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
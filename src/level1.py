"""Level 1 orchestration for linear-programming survival planning."""

from __future__ import annotations

import streamlit as st

from src.campaign import (
    TOTAL_TURNS,
    get_b_ub,
    get_objective,
    reset_session_state,
    set_phase,
)
from src.level1_core import (
    compute_optimal_solution,
    is_feasible,
    resolve_level1_turn,
)
from src.level1_views import draw_lp_plot, render_event_banner


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
    st.sidebar.caption("Stage 1 of 4: lock the colony's production plan.")

    x1_player = st.sidebar.slider(
        "x₁ — Oxygen production", 0, 60, 20, 1, key="l1_x1"
    )
    x2_player = st.sidebar.slider(
        "x₂ — Food production", 0, 80, 20, 1, key="l1_x2"
    )

    opt_solution, opt_value = compute_optimal_solution()
    x1_opt, x2_opt = opt_solution[0], opt_solution[1]
    feasible = is_feasible(x1_player, x2_player)
    z_player = float(objective[0] * x1_player + objective[1] * x2_player)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Current Constraints")
    st.sidebar.latex(rf"C_1:\;2x_1+x_2\leq {b_ub[0]:.0f}")
    st.sidebar.latex(rf"C_2:\;x_1+2x_2\leq {b_ub[1]:.0f}")

    st.sidebar.markdown("---")
    if st.sidebar.button(
        "✅ Lock production and continue",
        use_container_width=True,
        key="l1_next",
    ):
        resolve_level1_turn(x1_player, x2_player, opt_value, feasible)
        if not st.session_state.game_over:
            set_phase("policy")
        st.rerun()

    st.sidebar.metric(
        "📈 Cumulative Total Output",
        f"{st.session_state.total_score:.0f}",
    )

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
            delta=(
                f"{z_player - opt_value:+.0f} vs Optimal"
                if feasible else "Infeasible"
            ),
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
        st.markdown(
            f"**Optimal solution**: $x_1^*={x1_opt:.1f}$,"
            f" $x_2^*={x2_opt:.1f}$"
        )
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
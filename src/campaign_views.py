"""UI helpers for rendering campaign-wide status and resolution."""

from __future__ import annotations

import streamlit as st

from src.campaign_core import (
    PHASE_LABELS,
    TOTAL_TURNS,
    TURN_PHASES,
    advance_turn,
    get_phase_index,
)


def render_campaign_status() -> None:
    """Show the persistent colony state above the game tabs."""
    st.markdown("### Colony Status")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Oxygen Reserve", f"{st.session_state.oxygen_reserve:.0f}")
    col2.metric("Food Reserve", f"{st.session_state.food_reserve:.0f}")
    col3.metric("Economy", f"{st.session_state.economy:.0f}")
    col4.metric("Environment", f"{st.session_state.environment:.0f}")
    col5.metric("Morale", f"{st.session_state.morale:.0f}")
    col6.metric("Influence", f"{st.session_state.influence_tokens}/5")

    st.caption(
        "The three levels now feed into one campaign: optimise production,"
        " shape long-term policy, and then survive the political fallout."
    )

    with st.expander("Recent campaign log"):
        for entry in reversed(st.session_state.campaign_log[-6:]):
            st.markdown(f"- {entry}")

    phase_columns = st.columns(len(TURN_PHASES))
    active_index = get_phase_index()
    for index, phase in enumerate(TURN_PHASES):
        label = PHASE_LABELS[phase]
        if index < active_index:
            phase_columns[index].success(label)
        elif index == active_index:
            phase_columns[index].info(label)
        else:
            phase_columns[index].caption(label)


def render_turn_resolution() -> None:
    """Display the end-of-turn summary and advance button."""
    st.markdown(
        f"### Turn {st.session_state.turn} Resolution"
    )
    st.markdown(
        "This is the campaign heartbeat: review what happened across all"
        " three systems, then lock in the consequences and continue."
    )

    for label in ["Event", "Production", "Policy", "Council"]:
        if label in st.session_state.turn_report:
            st.markdown(
                f"- **{label}**: {st.session_state.turn_report[label]}"
            )

    if st.session_state.turn >= TOTAL_TURNS:
        button_label = "🏁 Finalize campaign"
    else:
        button_label = f"⏭️ Start turn {st.session_state.turn + 1}"

    if st.button(
        button_label,
        use_container_width=True,
        key="campaign_next_turn",
    ):
        advance_turn()
        st.rerun()
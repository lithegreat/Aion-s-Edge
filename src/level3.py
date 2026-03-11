"""Level 3 orchestration for parliamentary voting and MCDA."""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st

from src.campaign import (
    apply_colony_delta,
    change_influence_tokens,
    record_turn_report,
    set_phase,
)
from src.level3_core import (
    FACTIONS,
    PLANS,
    enact_council_plan,
    generate_live_ballots,
    resolve_voting_rule,
)
from src.level3_views import (
    detect_paradox,
    render_plan_catalog,
    render_preferences_table,
    render_voting_buttons,
    show_borda,
    show_condorcet,
    show_plurality,
)


def _render_live_controls() -> str:
    """Render live-council controls and return the active rule."""
    st.sidebar.markdown("### 🧭 Constitutional rule")
    council_rule = st.sidebar.radio(
        "Rule used to pass legislation",
        options=["Plurality", "Borda Count", "Condorcet"],
        key="l3_live_rule",
    )
    st.sidebar.markdown("### 🎯 Lobbying")
    st.sidebar.metric(
        "Influence tokens",
        str(st.session_state.influence_tokens),
    )
    lobby_faction = st.sidebar.selectbox(
        "Target faction",
        options=FACTIONS,
        key="l3_lobby_faction",
    )
    lobby_plan = st.sidebar.selectbox(
        "Plan to pitch",
        options=PLANS,
        key="l3_lobby_plan",
    )
    if st.sidebar.button(
        "🗣️ Spend 1 token to lobby",
        use_container_width=True,
        key="l3_lobby",
    ):
        if st.session_state.influence_tokens > 0:
            st.session_state.live_lobby = (lobby_faction, lobby_plan)
            change_influence_tokens(-1)
            st.session_state.campaign_log.append(
                f"Lobbying: pushed {lobby_plan} to {lobby_faction}."
            )
            st.rerun()
        else:
            st.sidebar.error("No influence tokens left.")
    return council_rule


def _resolve_live_council(rule: str) -> None:
    """Resolve the live council vote and apply the outcome."""
    ballots, _ = generate_live_ballots()
    winner, summary = resolve_voting_rule(ballots, rule)
    if winner is None:
        apply_colony_delta(
            economy=-3.0,
            morale=-6.0,
            log_message=(
                f"Council deadlock under {rule}. {summary}"
            ),
        )
        st.session_state.last_council_outcome = summary
        record_turn_report(
            "Council",
            f"Deadlock under {rule}. The council stalled and morale fell.",
        )
    else:
        enact_council_plan(winner, rule)
        record_turn_report(
            "Council",
            f"{rule} approved {winner} and converted it into law.",
        )
    st.session_state.live_lobby = None


def render_level3() -> None:
    """Render Level 3 — Voting Theory / MCDA."""
    st.markdown(
        """
        The colony parliament has three factions that must choose one development
        plan to implement. This is the political checkpoint of the turn: you
        now need to convert your policy direction into an actual law.
        """
    )

    st.sidebar.header("🏛️ L3 Parliamentary Voting")

    st.sidebar.caption("Stage 3 of 4: negotiate and resolve the council vote.")
    council_rule = _render_live_controls()
    if st.sidebar.button(
        "🏛️ Resolve council and continue",
        use_container_width=True,
        key="l3_enact_live",
    ):
        _resolve_live_council(council_rule)
        if not st.session_state.game_over:
            set_phase("resolution")
        st.rerun()

    ballots, factions_info = generate_live_ballots()

    st.markdown("**Scenario: Live Council Vote**")
    st.markdown(
        "*Faction weights and preferences react to the current colony. Use"
        " influence carefully before the chamber locks its decision.*"
    )

    render_plan_catalog()
    if st.session_state.last_council_outcome is not None:
        st.info(st.session_state.last_council_outcome)

    render_preferences_table(factions_info)

    run_plurality, run_borda, run_condorcet, run_all = (
        render_voting_buttons()
    )

    if run_plurality or run_all:
        show_plurality(ballots)
    if run_borda or run_all:
        show_borda(ballots)
    if run_condorcet or run_all:
        show_condorcet(ballots)
    if run_all:
        detect_paradox(ballots)

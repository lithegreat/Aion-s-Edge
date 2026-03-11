"""Level 3 orchestration for parliamentary voting and MCDA."""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st

from src.campaign import apply_colony_delta, change_influence_tokens
from src.level3_core import (
    FACTIONS,
    PLANS,
    VOTING_SCENARIOS,
    enact_council_plan,
    generate_live_ballots,
    generate_random_ballots,
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
    else:
        enact_council_plan(winner, rule)
    st.session_state.live_lobby = None


def _resolve_ballots(
    live_mode: bool,
) -> Tuple[List[Tuple[List[str], int]], List[Tuple[str, str]]]:
    """Return ballots and faction labels for the chosen scenario."""
    if live_mode:
        return generate_live_ballots()

    scenario = VOTING_SCENARIOS[st.session_state.l3_scenario]
    if scenario["ballots"] is not None:
        return scenario["ballots"], scenario["factions"]

    if st.session_state.voting_ballots is None:
        ballots, factions_info = generate_random_ballots()
        st.session_state.voting_ballots = ballots
        st.session_state.voting_factions = factions_info
    return (
        st.session_state.voting_ballots,
        st.session_state.voting_factions,
    )


def render_level3() -> None:
    """Render Level 3 — Voting Theory / MCDA."""
    st.markdown(
        """
        The colony parliament has three factions that must choose one development
        plan to implement. Different voting rules can produce **different
        winners** — this is the well-known **voting paradox**.

        Choose a scenario and try different voting methods to see how winners
        change.
        """
    )

    st.sidebar.header("🏛️ L3 Parliamentary Voting")

    scenario_names = [scenario["name"] for scenario in VOTING_SCENARIOS]
    chosen_idx = st.sidebar.radio(
        "Choose scenario",
        options=range(len(scenario_names)),
        format_func=lambda index: scenario_names[index],
        key="l3_scenario",
    )
    scenario = VOTING_SCENARIOS[chosen_idx]
    live_mode = scenario["ballots"] == "live"

    if live_mode:
        council_rule = _render_live_controls()
        if st.sidebar.button(
            "🏛️ Resolve council and enact winner",
            use_container_width=True,
            key="l3_enact_live",
        ):
            _resolve_live_council(council_rule)
            st.rerun()

    if st.sidebar.button(
        "🎲 Refresh random scenario",
        use_container_width=True,
        key="l3_refresh",
    ):
        st.session_state.voting_ballots = None
        st.session_state.voting_factions = None
        st.session_state.live_lobby = None
        st.rerun()

    ballots, factions_info = _resolve_ballots(live_mode)

    st.markdown(f"**Scenario: {scenario['name']}**")
    st.markdown(f"*{scenario['description']}*")

    if live_mode:
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

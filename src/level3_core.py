"""Core voting data and resolution logic for Level 3."""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st

from src.OptimizationEngine import VotingSystem
from src.campaign import (
    DEVELOPMENT_PLANS,
    DevelopmentPlan,
    apply_colony_delta,
)


FACTIONS = [
    "⛏️ Miners Guild",
    "🌿 Environmentalists",
    "👨‍👩‍👧 Residents",
]
PLANS = ["Plan A", "Plan B", "Plan C"]

VOTING_SCENARIOS: List[Dict[str, object]] = [
    {
        "name": "Live Council Vote",
        "description": (
            "Faction weights and preferences react to the current colony."
            " Spend influence to lobby, then let the constitutional rule"
            " decide which plan becomes law."
        ),
        "ballots": "live",
        "factions": "live",
    },
    {
        "name": "Classic Condorcet Paradox",
        "description": (
            "Miners prefer A>B>C, Environmentalists prefer B>C>A,"
            " Residents prefer C>A>B — this produces a cycle!"
        ),
        "ballots": [
            (["Plan A", "Plan B", "Plan C"], 4),
            (["Plan B", "Plan C", "Plan A"], 3),
            (["Plan C", "Plan A", "Plan B"], 2),
        ],
        "factions": [
            ("⛏️ Miners Guild (4 votes)", "A > B > C"),
            ("🌿 Environmentalists (3 votes)", "B > C > A"),
            ("👨‍👩‍👧 Residents (2 votes)", "C > A > B"),
        ],
    },
    {
        "name": "Plurality vs Borda Divergence",
        "description": (
            "Plurality and Borda can pick different winners!"
        ),
        "ballots": [
            (["Plan A", "Plan B", "Plan C"], 5),
            (["Plan B", "Plan C", "Plan A"], 4),
            (["Plan C", "Plan B", "Plan A"], 3),
        ],
        "factions": [
            ("⛏️ Miners Guild (5 votes)", "A > B > C"),
            ("🌿 Environmentalists (4 votes)", "B > C > A"),
            ("👨‍👩‍👧 Residents (3 votes)", "C > B > A"),
        ],
    },
    {
        "name": "Random Preferences",
        "description": "Randomly generated faction preferences.",
        "ballots": None,
        "factions": None,
    },
]


def generate_random_ballots() -> Tuple[
    List[Tuple[List[str], int]],
    List[Tuple[str, str]],
]:
    """Generate random preference ballots for three factions."""
    rng = random.Random()
    ballots: List[Tuple[List[str], int]] = []
    factions_info: List[Tuple[str, str]] = []
    for faction_name in FACTIONS:
        ranking = PLANS.copy()
        rng.shuffle(ranking)
        weight = rng.randint(2, 6)
        ballots.append((ranking, weight))
        factions_info.append(
            (f"{faction_name} ({weight} votes)", " > ".join(ranking))
        )
    return ballots, factions_info


def plan_utility(
    faction: str,
    plan: DevelopmentPlan,
) -> float:
    """Score how attractive a plan is to a faction."""
    oxygen_need = max(0.0, 65.0 - st.session_state.oxygen_reserve)
    food_need = max(0.0, 65.0 - st.session_state.food_reserve)
    economy_need = max(0.0, 60.0 - st.session_state.economy)
    environment_need = max(0.0, 60.0 - st.session_state.environment)
    morale_need = max(0.0, 60.0 - st.session_state.morale)

    if faction == FACTIONS[0]:
        return (
            plan.economy_delta * (1.25 + economy_need / 100.0)
            + 0.20 * plan.oxygen_delta
            + 0.10 * plan.food_delta
            + 0.10 * plan.morale_delta
            + 0.15 * max(0.0, -plan.environment_delta)
        )
    if faction == FACTIONS[1]:
        return (
            plan.environment_delta * (1.30 + environment_need / 100.0)
            + 0.20 * plan.morale_delta
            + 0.10 * plan.food_delta
            + 0.08 * plan.economy_delta
        )
    return (
        plan.morale_delta * (0.90 + morale_need / 100.0)
        + plan.oxygen_delta * (0.80 + oxygen_need / 100.0)
        + plan.food_delta * (0.80 + food_need / 100.0)
        + 0.20 * plan.economy_delta
        + 0.10 * plan.environment_delta
    )


def live_vote_weight(faction: str) -> int:
    """Compute dynamic vote weights from the colony state."""
    if faction == FACTIONS[0]:
        raw = 3.0 + (
            st.session_state.economy / 35.0
            + (100.0 - st.session_state.environment) / 45.0
        )
    elif faction == FACTIONS[1]:
        raw = 3.0 + (
            st.session_state.environment / 30.0
            + st.session_state.morale / 120.0
        )
    else:
        raw = 3.0 + (
            (
                st.session_state.oxygen_reserve
                + st.session_state.food_reserve
                + st.session_state.morale
            ) / 75.0
        )
    return int(np.clip(round(raw), 2, 7))


def generate_live_ballots() -> Tuple[
    List[Tuple[List[str], int]],
    List[Tuple[str, str]],
]:
    """Generate faction ballots from the persistent colony state."""
    ballots: List[Tuple[List[str], int]] = []
    factions_info: List[Tuple[str, str]] = []
    lobby = st.session_state.live_lobby

    for faction in FACTIONS:
        ranking = sorted(
            PLANS,
            key=lambda plan_name: plan_utility(
                faction, DEVELOPMENT_PLANS[plan_name]
            ),
            reverse=True,
        )
        if lobby is not None and faction == lobby[0]:
            ranking = [lobby[1]] + [
                plan_name for plan_name in ranking
                if plan_name != lobby[1]
            ]

        weight = live_vote_weight(faction)
        ballots.append((ranking, weight))

        label = f"{faction} ({weight} votes)"
        if lobby is not None and faction == lobby[0]:
            label += " · lobbied"
        factions_info.append((label, " > ".join(ranking)))

    return ballots, factions_info


def resolve_voting_rule(
    ballots: List[Tuple[List[str], int]],
    rule: str,
) -> Tuple[Optional[str], str]:
    """Resolve one voting rule into a winner and summary."""
    if rule == "Plurality":
        result = VotingSystem.plurality(ballots)
        return result.winner, f"Plurality winner: {result.winner}"
    if rule == "Borda Count":
        result = VotingSystem.borda_count(ballots)
        return result.winner, f"Borda winner: {result.winner}"

    result = VotingSystem.condorcet(ballots)
    if result.winner is None:
        cycle = result.cycle_description or "No winner"
        return None, f"Condorcet deadlock: {cycle}"
    return result.winner, f"Condorcet winner: {result.winner}"


def enact_council_plan(plan_name: str, rule: str) -> None:
    """Apply the winning council plan to the campaign state."""
    plan = DEVELOPMENT_PLANS[plan_name]
    apply_colony_delta(
        oxygen=plan.oxygen_delta,
        food=plan.food_delta,
        economy=plan.economy_delta,
        environment=plan.environment_delta,
        morale=plan.morale_delta,
        log_message=(
            f"{rule} enacted {plan.name}: {plan.description}"
        ),
    )
    st.session_state.last_council_outcome = (
        f"{rule} enacted {plan.name}."
    )
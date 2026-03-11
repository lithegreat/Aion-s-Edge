"""Shared campaign state and cross-level systems for Aion's Edge."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
from numpy.typing import NDArray


DEFAULT_OBJECTIVE = np.array([30.0, 20.0])

A_UB = np.array([
    [2.0, 1.0],
    [1.0, 2.0],
])

DEFAULT_B_UB = np.array([100.0, 80.0])
BOUNDS: List[Tuple[float, None]] = [(0, None), (0, None)]
TOTAL_TURNS = 12
X_MAX = 70
Y_MAX = 100

START_OXYGEN_RESERVE = 60.0
START_FOOD_RESERVE = 60.0
START_ECONOMY = 50.0
START_ENVIRONMENT = 55.0
START_MORALE = 60.0
START_INFLUENCE_TOKENS = 2
CRITICAL_THRESHOLD = 0.0


@dataclass(frozen=True)
class DevelopmentPlan:
    """Persistent policy option used by the live council."""

    name: str
    description: str
    economy_delta: float
    environment_delta: float
    morale_delta: float
    oxygen_delta: float
    food_delta: float


DEVELOPMENT_PLANS: Dict[str, DevelopmentPlan] = {
    "Plan A": DevelopmentPlan(
        name="Plan A",
        description=(
            "Heavy industrial expansion that boosts output but strains"
            " ecology and public trust."
        ),
        economy_delta=12.0,
        environment_delta=-12.0,
        morale_delta=-3.0,
        oxygen_delta=1.0,
        food_delta=-1.0,
    ),
    "Plan B": DevelopmentPlan(
        name="Plan B",
        description=(
            "Green modernisation that grows steadily while restoring"
            " planetary systems."
        ),
        economy_delta=7.0,
        environment_delta=10.0,
        morale_delta=4.0,
        oxygen_delta=2.0,
        food_delta=1.0,
    ),
    "Plan C": DevelopmentPlan(
        name="Plan C",
        description=(
            "Civic relief package that stabilises households and boosts"
            " reserves at the cost of slower growth."
        ),
        economy_delta=4.0,
        environment_delta=3.0,
        morale_delta=10.0,
        oxygen_delta=4.0,
        food_delta=4.0,
    ),
}


@dataclass
class GameEvent:
    """Describes a random event that modifies the LP."""

    name: str
    title: str
    description: str
    icon: str
    b_ub_override: Optional[NDArray[np.float64]] = None
    coeff_multiplier: Optional[float] = None


EVENT_CATALOGUE: Dict[str, GameEvent] = {
    "dust_storm": GameEvent(
        name="dust_storm",
        title="🌪️ Dust Storm",
        description=(
            "A fierce dust storm shrouds the solar arrays! "
            "Energy capacity drops from 100 to 60."
        ),
        icon="🌪️",
        b_ub_override=np.array([60.0, 80.0]),
    ),
    "flu": GameEvent(
        name="flu",
        title="🤒 Flu Outbreak",
        description=(
            "A widespread flu outbreak hits the colonists! "
            "Available labour falls from 80 to 50."
        ),
        icon="🤒",
        b_ub_override=np.array([100.0, 50.0]),
    ),
    "tech_breakthrough": GameEvent(
        name="tech_breakthrough",
        title="🔬 Tech Breakthrough",
        description=(
            "Research teams achieve a major breakthrough! "
            "All production coefficients are doubled this turn."
        ),
        icon="🔬",
        coeff_multiplier=2.0,
    ),
    "clear": GameEvent(
        name="clear",
        title="☀️ All Clear",
        description="Nothing unusual this turn; systems nominal.",
        icon="☀️",
    ),
}

EVENT_WEIGHTS: List[Tuple[str, float]] = [
    ("dust_storm", 0.25),
    ("flu", 0.20),
    ("tech_breakthrough", 0.10),
    ("clear", 0.45),
]


def roll_event() -> GameEvent:
    """Randomly select an event based on weighted probabilities."""
    names, weights = zip(*EVENT_WEIGHTS)
    chosen = random.choices(names, weights=weights, k=1)[0]
    return EVENT_CATALOGUE[chosen]


def init_session_state() -> None:
    """Initialise all session-state keys on first run."""
    defaults: Dict[str, object] = {
        "turn": 1,
        "b_ub": DEFAULT_B_UB.copy(),
        "objective": DEFAULT_OBJECTIVE.copy(),
        "current_event": None,
        "event_log": [],
        "total_score": 0.0,
        "game_over": False,
        "defeat_reason": None,
        "moo_ai_allocations": None,
        "voting_ballots": None,
        "voting_factions": None,
        "live_lobby": None,
        "last_council_outcome": None,
        "oxygen_reserve": START_OXYGEN_RESERVE,
        "food_reserve": START_FOOD_RESERVE,
        "economy": START_ECONOMY,
        "environment": START_ENVIRONMENT,
        "morale": START_MORALE,
        "influence_tokens": START_INFLUENCE_TOKENS,
        "campaign_log": [
            "Charter signed: AION now governs the new colony."
        ],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session_state() -> None:
    """Clear the entire campaign state and restart cleanly."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def get_b_ub() -> NDArray[np.float64]:
    """Return the current LP right-hand-side vector."""
    return np.asarray(st.session_state.b_ub, dtype=np.float64)


def get_objective() -> NDArray[np.float64]:
    """Return the current LP objective coefficients."""
    return np.asarray(st.session_state.objective, dtype=np.float64)


def _clip_stat(value: float) -> float:
    """Clamp a colony stat to the range [0, 100]."""
    return float(np.clip(value, 0.0, 100.0))


def change_influence_tokens(delta: int) -> None:
    """Adjust the finite pool of political influence tokens."""
    st.session_state.influence_tokens = int(np.clip(
        st.session_state.influence_tokens + delta, 0, 5
    ))


def _check_campaign_failure() -> None:
    """End the run if a critical colony stat collapses."""
    if st.session_state.game_over:
        return

    failure_conditions = [
        ("oxygen_reserve", "Oxygen reserves were exhausted."),
        ("food_reserve", "Food reserves were exhausted."),
        ("morale", "Colony morale collapsed into unrest."),
    ]
    for key, message in failure_conditions:
        if float(st.session_state[key]) <= CRITICAL_THRESHOLD:
            st.session_state.game_over = True
            st.session_state.defeat_reason = message
            st.session_state.campaign_log.append(
                f"Campaign failed: {message}"
            )
            return


def apply_colony_delta(
    *,
    oxygen: float = 0.0,
    food: float = 0.0,
    economy: float = 0.0,
    environment: float = 0.0,
    morale: float = 0.0,
    log_message: Optional[str] = None,
) -> None:
    """Apply persistent colony-state changes across levels."""
    st.session_state.oxygen_reserve = _clip_stat(
        st.session_state.oxygen_reserve + oxygen
    )
    st.session_state.food_reserve = _clip_stat(
        st.session_state.food_reserve + food
    )
    st.session_state.economy = _clip_stat(
        st.session_state.economy + economy
    )
    st.session_state.environment = _clip_stat(
        st.session_state.environment + environment
    )
    st.session_state.morale = _clip_stat(
        st.session_state.morale + morale
    )

    if log_message:
        st.session_state.campaign_log.append(log_message)
    _check_campaign_failure()


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


def advance_turn() -> None:
    """Advance the game by one turn and roll the next event."""
    if st.session_state.turn >= TOTAL_TURNS:
        st.session_state.game_over = True
        return

    st.session_state.b_ub = DEFAULT_B_UB.copy()
    st.session_state.objective = DEFAULT_OBJECTIVE.copy()

    event = roll_event()
    st.session_state.current_event = event

    if event.b_ub_override is not None:
        st.session_state.b_ub = event.b_ub_override.copy()
    if event.coeff_multiplier is not None:
        st.session_state.objective = (
            DEFAULT_OBJECTIVE * event.coeff_multiplier
        )

    st.session_state.event_log.append(
        f"Turn {st.session_state.turn + 1}: {event.title}"
    )
    st.session_state.turn += 1
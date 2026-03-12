"""Core computations for Level 2 policy design."""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import streamlit as st
from numpy.typing import NDArray

from src.campaign import (
    apply_colony_delta,
    change_influence_tokens,
    record_turn_report,
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
"""Core computations for Level 1 linear-programming gameplay."""

from __future__ import annotations

from typing import Tuple

import numpy as np
import streamlit as st
from numpy.typing import NDArray

from src.OptimizationEngine import LPSolver
from src.campaign import (
    A_UB,
    BOUNDS,
    apply_colony_delta,
    get_b_ub,
    get_objective,
    record_turn_report,
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
        record_turn_report(
            "Production",
            (
                f"Feasible plan produced {z_player:.0f} output at"
                f" {efficiency * 100:.0f}% efficiency."
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
    record_turn_report(
        "Production",
        "Infeasible production caused rationing, unrest, and reserve losses.",
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
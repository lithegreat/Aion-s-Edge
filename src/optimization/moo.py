"""Multi-objective optimisation helpers for Aion's Edge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from numpy.typing import NDArray


@dataclass
class ParetoResult:
    """Container for Pareto-front analysis.

    Attributes:
        pareto_front: Indices of non-dominated solutions.
        dominated: Indices of dominated solutions.
        pareto_points: The actual objective-space points on the front.
    """

    pareto_front: List[int]
    dominated: List[int]
    pareto_points: NDArray[np.float64]


class MOOSolver:
    """Identify Pareto-optimal solutions in objective space.

    Mathematical background
    -----------------------
    In multi-objective optimisation (MOO) we rarely have a
    single best solution. Instead, we seek the Pareto front,
    the set of non-dominated solutions.
    """

    @staticmethod
    def find_pareto_front(
        solutions: NDArray[np.float64],
        maximize: Optional[List[bool]] = None,
    ) -> ParetoResult:
        """Partition candidate solutions into Pareto and dominated sets."""
        solutions = np.asarray(solutions, dtype=np.float64)
        if solutions.ndim != 2:
            raise ValueError(
                "solutions must be a 2-D array "
                "(n_solutions × n_objectives)."
            )

        n_solutions, n_objectives = solutions.shape
        directions = MOOSolver._normalise_directions(maximize, n_objectives)
        adjusted = MOOSolver._adjust_for_directions(solutions, directions)

        pareto_mask = np.ones(n_solutions, dtype=bool)
        for i in range(n_solutions):
            if not pareto_mask[i]:
                continue
            for j in range(n_solutions):
                if i == j:
                    continue
                if MOOSolver._dominates(adjusted[j], adjusted[i]):
                    pareto_mask[i] = False
                    break

        pareto_indices = [int(i) for i in range(n_solutions) if pareto_mask[i]]
        dominated_indices = [
            int(i) for i in range(n_solutions) if not pareto_mask[i]
        ]
        return ParetoResult(
            pareto_front=pareto_indices,
            dominated=dominated_indices,
            pareto_points=solutions[pareto_mask],
        )

    @staticmethod
    def is_dominated(
        candidate: NDArray[np.float64],
        reference_set: NDArray[np.float64],
        maximize: Optional[List[bool]] = None,
    ) -> bool:
        """Check whether a candidate is dominated by any reference point."""
        candidate = np.asarray(candidate, dtype=np.float64)
        reference_set = np.asarray(reference_set, dtype=np.float64)
        directions = MOOSolver._normalise_directions(
            maximize,
            candidate.shape[0],
        )

        adjusted_candidate = MOOSolver._adjust_for_directions(
            candidate[np.newaxis, :],
            directions,
        )[0]
        adjusted_reference = MOOSolver._adjust_for_directions(
            reference_set,
            directions,
        )

        for reference in adjusted_reference:
            if MOOSolver._dominates(reference, adjusted_candidate):
                return True
        return False

    @staticmethod
    def nadir_point(
        pareto_points: NDArray[np.float64],
        maximize: Optional[List[bool]] = None,
    ) -> NDArray[np.float64]:
        """Compute the Nadir point for the Pareto front."""
        pareto_points = np.asarray(pareto_points, dtype=np.float64)
        directions = MOOSolver._normalise_directions(
            maximize,
            pareto_points.shape[1],
        )

        nadir = np.empty(pareto_points.shape[1])
        for idx, is_max in enumerate(directions):
            if is_max:
                nadir[idx] = pareto_points[:, idx].min()
            else:
                nadir[idx] = pareto_points[:, idx].max()
        return nadir

    @staticmethod
    def _normalise_directions(
        maximize: Optional[List[bool]],
        n_objectives: int,
    ) -> List[bool]:
        """Return one optimisation direction flag per objective."""
        if maximize is None:
            return [True] * n_objectives
        if len(maximize) != n_objectives:
            raise ValueError(
                f"maximize list length ({len(maximize)}) must match "
                f"n_objectives ({n_objectives})."
            )
        return list(maximize)

    @staticmethod
    def _adjust_for_directions(
        points: NDArray[np.float64],
        maximize: List[bool],
    ) -> NDArray[np.float64]:
        """Flip minimisation objectives so every dimension becomes max-only."""
        adjusted = np.array(points, copy=True)
        for idx, is_max in enumerate(maximize):
            if not is_max:
                adjusted[:, idx] *= -1
        return adjusted

    @staticmethod
    def _dominates(
        candidate_a: NDArray[np.float64],
        candidate_b: NDArray[np.float64],
    ) -> bool:
        """Check whether one adjusted objective vector dominates another."""
        return bool(
            np.all(candidate_a >= candidate_b)
            and np.any(candidate_a > candidate_b)
        )
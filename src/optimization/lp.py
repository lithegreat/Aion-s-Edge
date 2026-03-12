"""Linear-programming solver utilities for Aion's Edge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import OptimizeResult, linprog


@dataclass
class LPResult:
    """Container for a linear-programming solution.

    Attributes:
        optimal_value: The optimised objective function value.
        solution: The decision-variable vector at the optimum.
        success: Whether the solver converged.
        message: Human-readable solver status string.
    """

    optimal_value: float
    solution: NDArray[np.float64]
    success: bool
    message: str


class LPSolver:
    """Solve linear programmes with inequality and equality constraints.

    Mathematical background
    -----------------------
    A linear programme (LP) seeks the best outcome in a
    mathematical model whose requirements are represented by
    linear relationships. The feasible region is a convex
    polytope, and the Fundamental Theorem of LP guarantees
    that the optimum (if it exists) is at a vertex of this
    polytope.
    """

    @staticmethod
    def solve(
        c: NDArray[np.float64],
        A_ub: NDArray[np.float64],
        b_ub: NDArray[np.float64],
        A_eq: Optional[NDArray[np.float64]] = None,
        b_eq: Optional[NDArray[np.float64]] = None,
        bounds: Optional[List[Tuple[Optional[float], Optional[float]]]] = None,
        maximize: bool = True,
    ) -> LPResult:
        """Solve an LP and return structured results.

        Args:
            c: Coefficient vector of the objective function.
            A_ub: Inequality constraint matrix.
            b_ub: Right-hand side of inequality constraints.
            A_eq: Equality constraint matrix.
            b_eq: Right-hand side of equality constraints.
            bounds: Per-variable ``(min, max)`` bounds.
            maximize: Whether to maximise instead of minimise.

        Returns:
            An ``LPResult`` with the optimal value, solution,
            success flag, and solver message.

        Raises:
            ValueError: If the input dimensions are inconsistent.
        """
        c = np.asarray(c, dtype=np.float64)
        A_ub = np.asarray(A_ub, dtype=np.float64)
        b_ub = np.asarray(b_ub, dtype=np.float64)

        if A_ub.ndim != 2:
            raise ValueError("A_ub must be a 2-D matrix.")
        if c.shape[0] != A_ub.shape[1]:
            raise ValueError(
                f"Dimension mismatch: c has {c.shape[0]} "
                f"variables but A_ub has {A_ub.shape[1]} columns."
            )
        if A_ub.shape[0] != b_ub.shape[0]:
            raise ValueError(
                f"Dimension mismatch: A_ub has {A_ub.shape[0]} "
                f"rows but b_ub has {b_ub.shape[0]} entries."
            )

        c_internal = -c if maximize else c
        result: OptimizeResult = linprog(
            c_internal,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )

        optimal_value = -result.fun if maximize and result.success else result.fun
        return LPResult(
            optimal_value=float(optimal_value),
            solution=np.array(result.x) if result.x is not None else np.array([]),
            success=bool(result.success),
            message=str(result.message),
        )
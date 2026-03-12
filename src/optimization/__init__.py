"""Optimization solvers for Aion's Edge.

This package groups the mathematical engines by responsibility:

- ``lp`` for linear programming
- ``moo`` for Pareto and multi-objective analysis
- ``voting`` for voting-rule evaluation
"""

from .lp import LPResult, LPSolver
from .moo import MOOSolver, ParetoResult
from .voting import (
    BordaResult,
    CondorcetResult,
    PluralityResult,
    VotingSystem,
)

__all__ = [
    "BordaResult",
    "CondorcetResult",
    "LPResult",
    "LPSolver",
    "MOOSolver",
    "ParetoResult",
    "PluralityResult",
    "VotingSystem",
]
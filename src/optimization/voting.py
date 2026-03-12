"""Voting-rule utilities for Aion's Edge council decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


@dataclass
class PluralityResult:
    """Result of a plurality vote."""

    scores: Dict[str, int]
    winner: str


@dataclass
class BordaResult:
    """Result of a Borda Count vote."""

    scores: Dict[str, float]
    winner: str


@dataclass
class CondorcetResult:
    """Result of a Condorcet pairwise comparison."""

    pairwise_wins: Dict[Tuple[str, str], int]
    winner: Optional[str]
    has_cycle: bool
    cycle_description: str


class VotingSystem:
    """Implement classical voting methods for rank-order ballots.

    Mathematical background
    -----------------------
    Voting theory studies how individual preferences aggregate
    into a collective decision. Arrow's Impossibility Theorem
    shows that no rank-order voting system can satisfy all
    fairness criteria simultaneously.
    """

    @staticmethod
    def plurality(
        ballots: List[Tuple[List[str], int]],
    ) -> PluralityResult:
        """Count first-place votes for each candidate."""
        scores: Dict[str, int] = {}
        for ranking, weight in ballots:
            top = ranking[0]
            scores[top] = scores.get(top, 0) + weight

        all_candidates = {candidate for ranking, _ in ballots for candidate in ranking}
        for candidate in all_candidates:
            scores.setdefault(candidate, 0)

        winner = max(sorted(scores.keys()), key=lambda candidate: scores[candidate])
        return PluralityResult(scores=scores, winner=winner)

    @staticmethod
    def borda_count(
        ballots: List[Tuple[List[str], int]],
    ) -> BordaResult:
        """Compute Borda scores from weighted rankings."""
        all_candidates = {candidate for ranking, _ in ballots for candidate in ranking}
        candidate_count = len(all_candidates)
        scores: Dict[str, float] = {
            candidate: 0.0 for candidate in all_candidates
        }

        for ranking, weight in ballots:
            for position, candidate in enumerate(ranking):
                scores[candidate] += (candidate_count - 1 - position) * weight

        winner = max(sorted(scores.keys()), key=lambda candidate: scores[candidate])
        return BordaResult(scores=scores, winner=winner)

    @staticmethod
    def condorcet(
        ballots: List[Tuple[List[str], int]],
    ) -> CondorcetResult:
        """Run pairwise Condorcet comparisons across all candidates."""
        all_candidates = sorted(
            {candidate for ranking, _ in ballots for candidate in ranking}
        )
        size = len(all_candidates)
        index = {candidate: idx for idx, candidate in enumerate(all_candidates)}
        pairwise = np.zeros((size, size), dtype=np.int64)

        for ranking, weight in ballots:
            for higher_idx, higher in enumerate(ranking):
                for lower in ranking[higher_idx + 1 :]:
                    pairwise[index[higher]][index[lower]] += weight

        pairwise_wins: Dict[Tuple[str, str], int] = {}
        for candidate_a in all_candidates:
            for candidate_b in all_candidates:
                if candidate_a == candidate_b:
                    continue
                pairwise_wins[(candidate_a, candidate_b)] = int(
                    pairwise[index[candidate_a]][index[candidate_b]]
                )

        winner = VotingSystem._find_condorcet_winner(
            all_candidates,
            pairwise,
            index,
        )
        has_cycle = winner is None and size >= 2
        cycle_description = ""
        if has_cycle:
            cycle_description = " > ".join(
                VotingSystem._trace_cycle(all_candidates, pairwise, index)
            )

        return CondorcetResult(
            pairwise_wins=pairwise_wins,
            winner=winner,
            has_cycle=has_cycle,
            cycle_description=cycle_description,
        )

    @staticmethod
    def _find_condorcet_winner(
        candidates: List[str],
        pairwise: NDArray[np.int64],
        index: Dict[str, int],
    ) -> Optional[str]:
        """Return the candidate that beats every other candidate pairwise."""
        for candidate_a in candidates:
            if all(
                pairwise[index[candidate_a]][index[candidate_b]]
                > pairwise[index[candidate_b]][index[candidate_a]]
                for candidate_b in candidates
                if candidate_b != candidate_a
            ):
                return candidate_a
        return None

    @staticmethod
    def _trace_cycle(
        candidates: List[str],
        pairwise: NDArray[np.int64],
        index: Dict[str, int],
    ) -> List[str]:
        """Trace one cycle in the pairwise majority graph."""
        beats: Dict[str, List[str]] = {candidate: [] for candidate in candidates}
        for candidate_a in candidates:
            for candidate_b in candidates:
                if candidate_a == candidate_b:
                    continue
                if (
                    pairwise[index[candidate_a]][index[candidate_b]]
                    > pairwise[index[candidate_b]][index[candidate_a]]
                ):
                    beats[candidate_a].append(candidate_b)

        visited: List[str] = []
        visited_set: set[str] = set()
        current = candidates[0]

        while current not in visited_set:
            visited.append(current)
            visited_set.add(current)
            if not beats[current]:
                break
            current = beats[current][0]

        if current in visited_set:
            cycle_start = visited.index(current)
            return visited[cycle_start:] + [current]
        return visited + [visited[0]]
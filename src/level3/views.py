"""UI helpers for rendering Level 3 voting content."""

from __future__ import annotations

from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import streamlit as st

from src.optimization import VotingSystem
from src.campaign import DEVELOPMENT_PLANS


def render_plan_catalog() -> None:
    """Show the candidate plans and their long-term effects."""
    st.markdown("#### 🧾 Candidate plans")
    st.table({
        "Plan": [plan.name for plan in DEVELOPMENT_PLANS.values()],
        "Description": [
            plan.description for plan in DEVELOPMENT_PLANS.values()
        ],
        "Economy": [
            f"{plan.economy_delta:+.0f}"
            for plan in DEVELOPMENT_PLANS.values()
        ],
        "Environment": [
            f"{plan.environment_delta:+.0f}"
            for plan in DEVELOPMENT_PLANS.values()
        ],
        "Morale": [
            f"{plan.morale_delta:+.0f}"
            for plan in DEVELOPMENT_PLANS.values()
        ],
    })


def render_preferences_table(
    factions_info: List[Tuple[str, str]],
) -> None:
    """Display faction names and preference rankings."""
    st.markdown("#### 🗳️ Faction preferences")
    st.table({
        "Faction": [info[0] for info in factions_info],
        "Preferences": [info[1] for info in factions_info],
    })


def render_voting_buttons() -> Tuple[bool, bool, bool, bool]:
    """Render buttons for the three voting methods and combined run."""
    st.markdown("#### 🗳️ Choose a voting method")
    btn1, btn2, btn3 = st.columns(3)

    with btn1:
        run_plurality = st.button(
            "📊 Plurality",
            use_container_width=True,
            key="l3_plurality",
        )
    with btn2:
        run_borda = st.button(
            "📊 Borda Count",
            use_container_width=True,
            key="l3_borda",
        )
    with btn3:
        run_condorcet = st.button(
            "📊 Condorcet",
            use_container_width=True,
            key="l3_condorcet",
        )

    run_all = st.button(
        "⚡ Run all methods — show voting paradox",
        use_container_width=True,
        key="l3_all",
    )
    return run_plurality, run_borda, run_condorcet, run_all


def bar_chart(
    scores: Dict[str, int],
    title: str,
    color: str,
) -> plt.Figure:
    """Create a horizontal bar chart for vote scores."""
    fig, ax = plt.subplots(figsize=(4, 2.5))
    candidates = sorted(scores.keys())
    values = [scores[candidate] for candidate in candidates]

    bars = ax.barh(candidates, values, color=color, alpha=0.8)
    ax.bar_label(bars, padding=3)
    ax.set_xlabel("Score")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    return fig


def show_plurality(ballots: List[Tuple[List[str], int]]) -> None:
    """Display plurality voting results."""
    result = VotingSystem.plurality(ballots)
    st.markdown("---")
    st.markdown("### 📊 Plurality results")
    st.markdown(
        "Each faction's **first choice** receives all of its votes."
    )

    col_s, col_c = st.columns([1, 1])
    with col_s:
        for candidate in sorted(result.scores.keys()):
            bar = "█" * result.scores[candidate]
            st.markdown(
                f"**{candidate}**: {result.scores[candidate]} votes `{bar}`"
            )
    with col_c:
        st.pyplot(bar_chart(result.scores, "Plurality scores", "#3498db"))
    st.success(f"🏆 Plurality winner: **{result.winner}**")


def show_borda(ballots: List[Tuple[List[str], int]]) -> None:
    """Display Borda Count voting results."""
    result = VotingSystem.borda_count(ballots)
    st.markdown("---")
    st.markdown("### 📊 Borda Count results")
    st.markdown(
        "1st gets 2 points, 2nd gets 1 point, 3rd gets 0 points"
        " (times faction votes)."
    )

    col_s, col_c = st.columns([1, 1])
    with col_s:
        for candidate in sorted(result.scores.keys()):
            st.markdown(f"**{candidate}**: {result.scores[candidate]:.0f} 分")
    with col_c:
        st.pyplot(
            bar_chart(
                {key: int(value) for key, value in result.scores.items()},
                "Borda scores",
                "#2ecc71",
            )
        )
    st.success(f"🏆 Borda winner: **{result.winner}**")


def show_condorcet(ballots: List[Tuple[List[str], int]]) -> None:
    """Display Condorcet pairwise comparison results."""
    result = VotingSystem.condorcet(ballots)
    st.markdown("---")
    st.markdown("### 📊 Condorcet results")
    st.markdown(
        "Compare each pair of plans head-to-head to see which plan beats"
        " all others."
    )

    candidates = sorted({candidate for ranking, _ in ballots for candidate in ranking})
    st.markdown("**Pairwise comparison matrix** (row beats column votes):")

    header = [""] + candidates
    rows = []
    for candidate_a in candidates:
        row = [f"**{candidate_a}**"]
        for candidate_b in candidates:
            if candidate_a == candidate_b:
                row.append("—")
            else:
                wins = result.pairwise_wins.get((candidate_a, candidate_b), 0)
                losses = result.pairwise_wins.get((candidate_b, candidate_a), 0)
                marker = "✅" if wins > losses else "❌"
                row.append(f"{wins} {marker}")
        rows.append(row)

    markdown = "| " + " | ".join(header) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        markdown += "| " + " | ".join(row) + " |\n"
    st.markdown(markdown)

    if result.winner:
        st.success(
            f"🏆 Condorcet winner: **{result.winner}** (beats all opponents)"
        )
    else:
        st.error(
            "🔄 Condorcet paradox! No plan beats all opponents — a voting"
            " cycle exists."
        )
        if result.cycle_description:
            st.warning(f"Cycle: {result.cycle_description}")


def detect_paradox(ballots: List[Tuple[List[str], int]]) -> None:
    """Compare winners across methods and highlight paradoxes."""
    plurality = VotingSystem.plurality(ballots)
    borda = VotingSystem.borda_count(ballots)
    condorcet = VotingSystem.condorcet(ballots)

    winners = {
        "Plurality": plurality.winner,
        "Borda": borda.winner,
        "Condorcet": (
            condorcet.winner if condorcet.winner else "None (cycle)"
        ),
    }

    st.markdown("---")
    st.markdown("### 🔍 Voting paradox analysis")

    unique = set(winners.values())
    if len(unique) == 1 and "None (cycle)" not in unique:
        st.info(
            f"All methods produced the **same winner**:"
            f" **{list(unique)[0]}** — no paradox."
        )
        return

    st.warning(
        "⚠️ Voting paradox detected! Different rules produced different winners:"
    )
    for method, winner in winners.items():
        st.markdown(f"- **{method}** → {winner}")
    st.markdown(
        "\n> This illustrates Arrow's impossibility theorem: no ranked"
        " voting system can satisfy all fairness criteria simultaneously."
    )
"""Aion's Edge — Streamlit entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.campaign import (  # noqa: E402
    PHASE_LABELS,
    TOTAL_TURNS,
    init_session_state,
    render_campaign_status,
    render_turn_resolution,
    reset_session_state,
)
from src.level1 import render_level1  # noqa: E402
from src.level2 import render_level2  # noqa: E402
from src.level3 import render_level3  # noqa: E402


def _render_game_over() -> None:
    """Render the end-of-campaign screen."""
    if st.session_state.defeat_reason is None:
        st.balloons()
        st.success(
            f"Campaign complete. You survived {TOTAL_TURNS} turns with"
            f" total output **{st.session_state.total_score:.0f}**."
        )
    else:
        st.error(
            f"Campaign failed: {st.session_state.defeat_reason}"
        )

    if st.button("🔄 Restart campaign", key="campaign_restart"):
        reset_session_state()
        st.rerun()


def main() -> None:
    """Run the Aion's Edge Streamlit application."""
    st.set_page_config(
        page_title="Aion's Edge",
        page_icon="🚀",
        layout="wide",
    )

    init_session_state()

    st.title("🚀 Aion's Edge: The Optimization Frontier")
    render_campaign_status()

    if st.session_state.game_over:
        _render_game_over()
        return

    st.markdown(
        f"### Active Phase: {PHASE_LABELS[st.session_state.phase]}"
    )

    if st.session_state.phase == "production":
        render_level1()
    elif st.session_state.phase == "policy":
        render_level2()
    elif st.session_state.phase == "council":
        render_level3()
    else:
        render_turn_resolution()


if __name__ == "__main__":
    main()

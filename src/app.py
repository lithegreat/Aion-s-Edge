"""Aion's Edge — Streamlit entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.campaign import init_session_state, render_campaign_status  # noqa: E402
from src.level1 import render_level1  # noqa: E402
from src.level2 import render_level2  # noqa: E402
from src.level3 import render_level3  # noqa: E402


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

    tab1, tab2, tab3 = st.tabs([
        "🔋 Level 1 — Linear Programming",
        "🔬 Level 2 — Multi-Objective Optimisation",
        "🏛️ Level 3 — Parliamentary Voting",
    ])

    with tab1:
        render_level1()

    with tab2:
        render_level2()

    with tab3:
        render_level3()


if __name__ == "__main__":
    main()

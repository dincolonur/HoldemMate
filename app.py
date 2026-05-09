"""HoldemMate — Streamlit entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from holdemmate.card_picker import card_picker
from holdemmate.cards import pretty_html
from holdemmate.config import get_settings
from holdemmate.game_state import GameState
from holdemmate.graph import recommend

st.set_page_config(
    page_title="HoldemMate",
    page_icon="🃏",
    # `centered` produces a sensible max-width on desktop and lets the page
    # collapse cleanly on mobile. The card grid stays compact instead of
    # ballooning across a 27" monitor.
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------- Password gate -------------------------------------------------------
#
# When APP_PASSWORD is set (Streamlit secret on Cloud, or env var locally), the
# whole UI is gated behind a single shared password. When unset, the app is
# fully open — useful for local development and demos.

def _require_password() -> None:
    cfg = get_settings()
    expected = cfg.app_password
    if not expected:
        return  # No password configured = open access.

    if st.session_state.get("hm_auth_ok"):
        return

    st.title("🃏 HoldemMate")
    st.caption("Multi-agent Texas Hold'em assistant")
    st.write("This app is password-protected.")
    pw = st.text_input(
        "Password",
        type="password",
        key="hm_auth_input",
    )
    if pw:
        if pw == expected:
            st.session_state["hm_auth_ok"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()


_require_password()

# ---------- Card-grid CSS --------------------------------------------------------
#
# We scope all "card button" styling to the Streamlit container created with
# `st.container(key="hm_card_grid")`. Streamlit renders that container as a
# div carrying the class `.st-key-hm_card_grid`, which gives us a stable,
# predictable hook to target with CSS — no `:has()` tricks, no marker divs,
# robust against Streamlit's internal DOM rearrangements between versions.

CARD_GRID_CSS = """
<style>
/*
 * The card grid is rendered by a custom Streamlit component (see
 * holdemmate/card_picker/), which lives in an iframe with its own CSS.
 * Streamlit's stylesheet cannot reach inside the iframe, so the picker is
 * immune to mobile column-stacking and other DOM rearrangements.
 *
 * The CSS in this block now only handles app-level chrome: the
 * recommendation banner, action-row stacking, and small mobile tweaks.
 */

/* === Recommendation banner: wrap on small screens ============================ */

.hm-rec-banner {
    background: var(--rec-color, #64748b);
    color: white;
    padding: 18px 22px;
    border-radius: 14px;
    font-size: 22px;
    font-weight: 700;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: space-between;
    align-items: center;
}

.hm-rec-confidence {
    font-size: 14px;
    opacity: 0.9;
    font-weight: 500;
}

@media (max-width: 480px) {
    .hm-rec-banner {
        font-size: 18px;
        padding: 14px 16px;
    }
}

/* === Action row stacks on phones ============================================= */

@media (max-width: 480px) {
    /* The horizontal block immediately following our marker becomes a column. */
    [data-testid="stMarkdownContainer"]:has(> .hm-action-row-marker)
        + [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 8px !important;
    }
    [data-testid="stMarkdownContainer"]:has(> .hm-action-row-marker)
        + [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 100% !important;
    }
}

/* === General mobile tweaks =================================================== */

@media (max-width: 480px) {
    /* Make Streamlit metric labels and values comfortably readable on phones. */
    [data-testid="stMetricLabel"] { font-size: 12px !important; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }

    /* Tighten heading + caption spacing on phones */
    h1 { font-size: 28px !important; }
    h2 { font-size: 22px !important; }
    h3 { font-size: 18px !important; }
}
</style>
"""

st.markdown(CARD_GRID_CSS, unsafe_allow_html=True)


# ---------- Helpers --------------------------------------------------------------

POSITIONS = ["BTN", "SB", "BB", "UTG", "MP", "CO"]

DEFAULTS: dict[str, object] = {
    "street": "preflop",
    "hole_cards": [],
    "flop_cards": [],
    "turn_card": [],   # list[str] of length 0 or 1 (for grid uniformity)
    "river_card": [],  # list[str] of length 0 or 1
    "num_opponents": 1,
    "pot": 3.0,
    "to_call": 1.0,
    "hero_stack": 100.0,
    "position": "BTN",
    "history": [],
    "last_result": None,
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def board_now() -> list[str]:
    """Combine the per-street card lists into the full board."""
    return list(
        st.session_state["flop_cards"]
        + st.session_state["turn_card"]
        + st.session_state["river_card"]
    )


def cards_html(cards) -> str:
    if not cards:
        return "<em>(none)</em>"
    return " &nbsp; ".join(pretty_html(c) for c in cards)


def reset_hand() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = list(value) if isinstance(value, list) else value
    # Drop any leftover button keys from previous renders.
    for k in list(st.session_state.keys()):
        if k.startswith("grid_"):
            del st.session_state[k]


# ---------- Card grid component --------------------------------------------------

def card_grid(state_key: str, max_count: int, disabled_cards: set[str]) -> None:
    """Render the 52-card picker via the custom HTML component.

    The component lives in an iframe with its own CSS, so Streamlit's mobile
    column-stacking can't reach it. Click events come back as the new selection
    list; we mirror that into session state and rerun on change.

    Args:
        state_key: session-state key holding a list[str] of selected cards.
        max_count: how many cards the user is allowed to pick at this step.
        disabled_cards: cards that can't be clicked (already used elsewhere).
    """
    current: list[str] = list(st.session_state.get(state_key, []))

    new_selection = card_picker(
        selected=current,
        max_count=max_count,
        disabled=disabled_cards,
        key=f"picker_{state_key}",
    )

    if new_selection != current:
        st.session_state[state_key] = new_selection
        st.rerun()


# ---------- Recommendation rendering --------------------------------------------

def render_recommendation(result: dict) -> None:
    strat = result["strategy"]
    math = result["math"]
    coach = result["coach"]
    opp = result["opponent"]

    action = strat["action"]
    color = {
        "RAISE": "#16a34a",
        "CALL": "#2563eb",
        "CHECK": "#0891b2",
        "FOLD": "#dc2626",
    }.get(action, "#64748b")

    st.markdown(
        f"""
        <div class="hm-rec-banner" style="--rec-color:{color};">
            <span>Recommended action: {action}</span>
            <span class="hm-rec-confidence">
                confidence {strat.get("confidence", 0):.0%}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if strat.get("size_hint"):
        st.caption(f"Suggested size: **{strat['size_hint']}**")

    cols = st.columns(3)
    cols[0].metric("Equity", f"{math['equity_value']:.1f}%")
    cols[1].metric(
        "Pot odds",
        f"{math['pot_odds_pct']:.1f}%" if math["pot_odds_pct"] is not None else "—",
    )
    cols[2].metric("Made hand", math["made_hand"])

    with st.expander("Coach's note", expanded=True):
        st.write(coach)
    with st.expander("Opponent read"):
        st.json(opp)
    with st.expander("Strategy rationale"):
        st.write(strat.get("rationale", ""))
    with st.expander("Raw math"):
        st.json(math)


# ---------- Sidebar -------------------------------------------------------------

with st.sidebar:
    st.title("🃏 HoldemMate")
    st.caption("Multi-agent Texas Hold'em assistant")

    settings = get_settings()
    if not settings.anthropic_api_key:
        st.error(
            "ANTHROPIC_API_KEY not set. Copy `.env.example` to `.env` "
            "and add your key, then restart."
        )

    st.subheader("Table parameters")
    st.session_state["num_opponents"] = st.number_input(
        "Number of opponents", min_value=1, max_value=8,
        value=int(st.session_state["num_opponents"]),
    )
    st.session_state["position"] = st.selectbox(
        "Your position", POSITIONS,
        index=POSITIONS.index(st.session_state["position"]),
    )
    st.session_state["pot"] = st.number_input(
        "Current pot size", min_value=0.0, value=float(st.session_state["pot"]),
        step=0.5,
    )
    st.session_state["to_call"] = st.number_input(
        "Amount to call", min_value=0.0, value=float(st.session_state["to_call"]),
        step=0.5,
    )
    st.session_state["hero_stack"] = st.number_input(
        "Your remaining stack", min_value=0.0,
        value=float(st.session_state["hero_stack"]), step=1.0,
    )

    st.divider()
    if st.button("🔄 Start a new hand"):
        reset_hand()
        st.rerun()


# ---------- Main UI -------------------------------------------------------------

st.title("HoldemMate")
st.write(
    "Click cards on the grid to enter what you can see, then ask the agent crew "
    "for a recommendation."
)

street = st.session_state["street"]
st.subheader(f"Step: {street.capitalize()}")

if street == "preflop":
    st.markdown("**Pick your 2 hole cards** _(click to toggle)_")
    card_grid(
        state_key="hole_cards",
        max_count=2,
        disabled_cards=set(),
    )
    selected = st.session_state["hole_cards"]
    st.markdown(
        f"<div style='margin-top:12px;font-size:18px;'>Selected: {cards_html(selected)} "
        f"<span style='color:#64748b;font-size:14px;'>({len(selected)}/2)</span></div>",
        unsafe_allow_html=True,
    )
    ready = len(selected) == 2

elif street == "flop":
    st.markdown(
        f"**Your hand:** &nbsp; {cards_html(st.session_state['hole_cards'])}",
        unsafe_allow_html=True,
    )
    st.markdown("**Pick the 3 flop cards** _(click to toggle)_")
    card_grid(
        state_key="flop_cards",
        max_count=3,
        disabled_cards=set(st.session_state["hole_cards"]),
    )
    selected = st.session_state["flop_cards"]
    st.markdown(
        f"<div style='margin-top:12px;font-size:18px;'>Flop: {cards_html(selected)} "
        f"<span style='color:#64748b;font-size:14px;'>({len(selected)}/3)</span></div>",
        unsafe_allow_html=True,
    )
    ready = len(selected) == 3

elif street == "turn":
    st.markdown(
        f"**Your hand:** &nbsp; {cards_html(st.session_state['hole_cards'])}",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Flop:** &nbsp; {cards_html(st.session_state['flop_cards'])}",
        unsafe_allow_html=True,
    )
    st.markdown("**Pick the turn card** _(the 4th community card)_")
    card_grid(
        state_key="turn_card",
        max_count=1,
        disabled_cards=set(st.session_state["hole_cards"])
        | set(st.session_state["flop_cards"]),
    )
    selected = st.session_state["turn_card"]
    st.markdown(
        f"<div style='margin-top:12px;font-size:18px;'>Turn: {cards_html(selected)}</div>",
        unsafe_allow_html=True,
    )
    ready = len(selected) == 1

elif street == "river":
    st.markdown(
        f"**Your hand:** &nbsp; {cards_html(st.session_state['hole_cards'])}",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Flop:** &nbsp; {cards_html(st.session_state['flop_cards'])}",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Turn:** &nbsp; {cards_html(st.session_state['turn_card'])}",
        unsafe_allow_html=True,
    )
    st.markdown("**Pick the river card** _(the 5th community card)_")
    card_grid(
        state_key="river_card",
        max_count=1,
        disabled_cards=set(st.session_state["hole_cards"])
        | set(st.session_state["flop_cards"])
        | set(st.session_state["turn_card"]),
    )
    selected = st.session_state["river_card"]
    st.markdown(
        f"<div style='margin-top:12px;font-size:18px;'>River: {cards_html(selected)}</div>",
        unsafe_allow_html=True,
    )
    ready = len(selected) == 1

else:
    ready = False


# ---------- Action buttons ------------------------------------------------------

st.divider()
# A marker so our CSS can target this row and stack it vertically on phones.
st.markdown('<div class="hm-action-row-marker"></div>', unsafe_allow_html=True)
left, right = st.columns([1, 2])

with left:
    run = st.button(
        "🤖 Get recommendation",
        type="primary",
        disabled=not ready,
        use_container_width=True,
    )

with right:
    if street != "preflop":
        if st.button("◀ Back to previous street", use_container_width=True):
            order = ["preflop", "flop", "turn", "river"]
            idx = order.index(street)
            st.session_state["street"] = order[idx - 1]
            st.rerun()

if run:
    with st.spinner("Math, Opponent, Strategy, and Coach agents thinking…"):
        game = GameState(
            hole_cards=list(st.session_state["hole_cards"]),
            board=board_now(),
            num_opponents=int(st.session_state["num_opponents"]),
            pot=float(st.session_state["pot"]),
            to_call=float(st.session_state["to_call"]),
            hero_stack=float(st.session_state["hero_stack"]),
            position=st.session_state["position"],
            action_history=[h["action"] for h in st.session_state["history"]],
        )
        try:
            result = recommend(game)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Pipeline error: {exc}")
            result = None

    if result is not None:
        st.session_state["last_result"] = result
        st.session_state["history"].append(
            {
                "street": street,
                "action": result["strategy"]["action"],
                "equity": result["math"]["equity_value"],
            }
        )

# ---------- Result + navigation -------------------------------------------------

if st.session_state["last_result"]:
    st.divider()
    st.subheader("Recommendation")
    render_recommendation(st.session_state["last_result"])

    st.divider()
    if street != "river":
        next_street = {"preflop": "flop", "flop": "turn", "turn": "river"}[street]
        if st.button(f"➡ Continue to {next_street}", type="secondary"):
            st.session_state["street"] = next_street
            st.session_state["last_result"] = None
            st.rerun()
    else:
        st.info("River decided. Click *Start a new hand* in the sidebar to play again.")

# ---------- Hand log -----------------------------------------------------------

if st.session_state["history"]:
    st.divider()
    st.subheader("Hand log")
    for i, entry in enumerate(st.session_state["history"], start=1):
        st.write(
            f"{i}. **{entry['street'].capitalize()}** — {entry['action']} "
            f"(equity {entry['equity']:.1f}%)"
        )

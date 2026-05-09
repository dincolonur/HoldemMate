"""Custom Streamlit component for the 52-card picker.

The Python side declares the component pointing at `frontend/index.html`,
which renders the full grid in a sandboxed iframe with its own CSS — Streamlit
cannot reach into the iframe to override layout, so the responsive 4×13 grid
on desktop and 4×13 column-major flow on mobile work reliably.

Click events in the iframe call `Streamlit.setComponentValue()`, which becomes
the return value of the Python wrapper.
"""

from __future__ import annotations

import os
from typing import Iterable

import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

_card_picker_component = components.declare_component(
    "hm_card_picker",
    path=_FRONTEND_DIR,
)


def card_picker(
    selected: Iterable[str],
    max_count: int,
    disabled: Iterable[str],
    key: str | None = None,
) -> list[str]:
    """Render the card picker and return the updated selection list.

    Args:
        selected: cards currently selected (e.g. ['Ad', 'Ks']).
        max_count: how many cards the user is allowed to pick at this step.
            Picking beyond this count drops the oldest selection.
        disabled: cards that should be greyed out and unclickable
            (typically those used by an earlier street).
        key: Streamlit widget key. Use a different key per street so the
            component's iframe state doesn't bleed between preflop / flop /
            turn / river.

    Returns:
        The card list after the user's interaction. If the iframe hasn't
        sent an update yet (first render), returns the input `selected` list.
    """
    selected_list = list(selected)
    disabled_list = list(disabled)

    raw = _card_picker_component(
        selected=selected_list,
        max_count=int(max_count),
        disabled=disabled_list,
        default=selected_list,
        key=key,
    )
    if raw is None:
        return selected_list
    # The component returns whatever JS sent; coerce defensively.
    if isinstance(raw, list):
        return [str(c) for c in raw]
    return selected_list

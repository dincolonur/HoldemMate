"""Card representation helpers.

We use the `treys` two-character format internally:
    rank: 2 3 4 5 6 7 8 9 T J Q K A
    suit: s (spades), h (hearts), d (diamonds), c (clubs)

Example: 'Ah' = Ace of hearts, 'Td' = Ten of diamonds.
"""

from __future__ import annotations

RANKS: tuple[str, ...] = ("2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A")
SUITS: tuple[str, ...] = ("s", "h", "d", "c")

RANK_LABELS: dict[str, str] = {
    "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "T": "10", "J": "Jack", "Q": "Queen",
    "K": "King", "A": "Ace",
}

SUIT_LABELS: dict[str, str] = {
    "s": "Spades",
    "h": "Hearts",
    "d": "Diamonds",
    "c": "Clubs",
}

SUIT_SYMBOLS: dict[str, str] = {
    "s": "♠",  # ♠
    "h": "♥",  # ♥
    "d": "♦",  # ♦
    "c": "♣",  # ♣
}

# Same glyphs followed by U+FE0F (Variation Selector-16). This forces emoji
# rendering on systems that support it, which means hearts and diamonds render
# in red while spades and clubs stay black — even inside Streamlit selectboxes,
# where HTML/CSS in option labels isn't supported.
SUIT_SYMBOLS_EMOJI: dict[str, str] = {
    "s": "♠️",  # ♠️
    "h": "♥️",  # ♥️
    "d": "♦️",  # ♦️
    "c": "♣️",  # ♣️
}

# Standard poker convention: hearts and diamonds in red, spades and clubs in black.
SUIT_COLORS: dict[str, str] = {
    "s": "#111827",  # near-black
    "h": "#dc2626",  # red-600
    "d": "#dc2626",
    "c": "#111827",
}


def card_code(rank: str, suit: str) -> str:
    """Build a treys-style card code from a rank + suit token."""
    if rank not in RANKS:
        raise ValueError(f"Unknown rank: {rank}")
    if suit not in SUITS:
        raise ValueError(f"Unknown suit: {suit}")
    return f"{rank}{suit}"


def pretty(card: str) -> str:
    """Human-friendly plain-text representation, e.g. 'A♦'."""
    if len(card) != 2:
        raise ValueError(f"Bad card code: {card!r}")
    rank, suit = card[0], card[1]
    return f"{rank}{SUIT_SYMBOLS[suit]}"


def pretty_html(card: str) -> str:
    """HTML representation with red hearts/diamonds, e.g. 'A<span style=...>♦</span>'."""
    if len(card) != 2:
        raise ValueError(f"Bad card code: {card!r}")
    rank, suit = card[0], card[1]
    color = SUIT_COLORS[suit]
    symbol = SUIT_SYMBOLS[suit]
    return (
        f'<span style="font-weight:700;color:{color};">{rank}{symbol}</span>'
    )


def long_name(card: str) -> str:
    """Spoken name, e.g. 'Ace of Diamonds'."""
    rank, suit = card[0], card[1]
    return f"{RANK_LABELS[rank]} of {SUIT_LABELS[suit]}"


def all_cards() -> list[str]:
    """Return every card in a standard 52-card deck."""
    return [f"{r}{s}" for r in RANKS for s in SUITS]


def validate_unique(*cards: str) -> None:
    """Raise if any card appears twice."""
    seen: set[str] = set()
    for c in cards:
        if not c:
            continue
        if c in seen:
            raise ValueError(f"Duplicate card: {pretty(c)}")
        seen.add(c)

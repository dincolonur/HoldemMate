# HoldemMate

A multi-agent AI assistant for Texas Hold'em. You enter your hole cards, then the
flop / turn / river as the hand develops, and a small crew of specialised agents
(Math, Opponent, Strategy, Coach) collaborates to recommend **RAISE**, **CALL/CHECK**,
or **FOLD** with a plain-language explanation.

## Architecture

```
   ┌─────────────────────┐
   │  Streamlit UI       │   user enters cards / pot / opponents
   └──────────┬──────────┘
              │  GameState
              ▼
   ┌─────────────────────┐
   │  LangGraph workflow │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 1. Math Agent       │  ← treys + Monte Carlo equity, pot odds
   ├─────────────────────┤
   │ 2. Opponent Agent   │  ← LLM: range read & threats
   ├─────────────────────┤
   │ 3. Strategy Agent   │  ← LLM: RAISE / CALL / FOLD + confidence
   ├─────────────────────┤
   │ 4. Coach Agent      │  ← LLM: plain-English explanation
   └─────────────────────┘
```

- **Stack:** Python + Streamlit
- **Agents:** LangGraph orchestration
- **LLM:** Anthropic Claude (configurable model)
- **Math engine:** [`treys`](https://github.com/ihendley/treys) hand evaluator + Monte Carlo equity simulation

## Setup

```bash
cd HoldemMate
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY
```

## Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## How a hand flows

1. **Preflop** — pick your two hole cards (e.g. `A♦ K♠`), set number of opponents,
   pot size, amount to call. Click *Get recommendation*.
2. **Flop** — enter the 3 community cards. The agents re-evaluate.
3. **Turn** — enter the 4th community card. Re-evaluate.
4. **River** — enter the 5th. Final decision.

At each street the Math Agent re-runs Monte Carlo against random opponent ranges,
the Opponent Agent reasons about what the villain might hold given betting action,
the Strategy Agent picks an action, and the Coach Agent writes the explanation.

## Project layout

```
HoldemMate/
├── app.py                         # Streamlit UI (entry point)
├── requirements.txt
├── .env.example
├── holdemmate/
│   ├── config.py                  # env loading, model settings
│   ├── cards.py                   # card constants & parsing helpers
│   ├── poker_math.py              # treys + Monte Carlo equity
│   ├── game_state.py              # GameState dataclass
│   ├── graph.py                   # LangGraph workflow
│   └── agents/
│       ├── base.py                # Anthropic client wrapper
│       ├── math_agent.py
│       ├── opponent_agent.py
│       ├── strategy_agent.py
│       └── coach_agent.py
└── tests/
    └── test_poker_math.py
```

## Disclaimer

HoldemMate is an educational / training tool. It does not guarantee winning play,
and the equity numbers are simulation estimates. Don't use it where the rules of
the game prohibit assistance.

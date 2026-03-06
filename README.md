# Blackjack AI Engine

A probability-based Blackjack strategy engine that computes optimal player actions using expected value (EV) analysis and dynamic programming (memoization).

## Current Features (v1)
- Infinite-deck probability model
- Dealer outcome distribution (S17)
- Optimal action recommendation among: Stand / Hit / Double
- Unit tests for key components

## Roadmap
- H17 support
- Surrender
- Splits (DAS, resplits)
- Finite-shoe (composition-dependent) probabilities
- CLI UX improvements + web UI

## Quickstart

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pytest -q
python examples/demo.py
```

## Generate strategy tables

CSV + HTML (recommended):

```bash
python -m blackjack_ai table --csv --html --out outputs/strategy
```
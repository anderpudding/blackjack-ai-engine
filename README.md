# Blackjack AI Engine

A probability-based Blackjack strategy engine that computes optimal player actions using expected value analysis and dynamic programming.

## Features

- Expected value calculation for Blackjack actions
- Recursive probability modeling
- Memoized decision engine
- Configurable casino rules
- Strategy recommendation system

## Project Structure

```
blackjack-ai-engine
│
├── README.md
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements.txt
│
├── src
│   └── blackjack_ai
│       ├── __init__.py
│       ├── cards.py
│       ├── hand.py
│       ├── dealer.py
│       ├── ev_engine.py
│       ├── strategy.py
│       └── simulator.py
│
├── tests
│   ├── test_hand.py
│   ├── test_dealer.py
│   └── test_engine.py
│
└── examples
    └── demo.py
```
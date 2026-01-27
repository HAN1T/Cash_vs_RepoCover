# src/config.py
from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # repo root
DATA_DIR = PROJECT_ROOT / "data"

CASH_CSV = DATA_DIR / "cash_trades.csv"
REPO_CSV = DATA_DIR / "repo_trades.csv"

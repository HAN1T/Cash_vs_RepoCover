# src/generate_data.py
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pandas as pd

from config import CASH_CSV, REPO_CSV, DATA_DIR

# Keep bonds list here (do NOT import from config)
BONDS = ["BOND_A", "BOND_B", "BOND_C", "BOND_D", "BOND_E"]


def _now_str_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def init_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CASH_CSV.exists():
        pd.DataFrame(columns=["trade_id", "book_time", "settle_date", "bond", "side", "qty"]).to_csv(CASH_CSV, index=False)

    if not REPO_CSV.exists():
        pd.DataFrame(columns=["repo_id", "book_time", "settle_date", "bond", "cover_qty", "status"]).to_csv(REPO_CSV, index=False)


def append_random_cash_trades(n: int = 3, settle_days_ahead: int = 1) -> list[dict]:
    df = pd.read_csv(CASH_CSV)
    settle = (datetime.now(timezone.utc).date() + timedelta(days=settle_days_ahead)).isoformat()

    rows: list[dict] = []
    for _ in range(n):
        rows.append({
            "trade_id": f"T{len(df) + len(rows) + 1:06d}",
            "book_time": _now_str_utc(),
            "settle_date": settle,
            "bond": random.choice(BONDS),
            "side": random.choice(["BUY", "SELL"]),
            "qty": random.choice([1_000_000, 2_000_000, 5_000_000, 10_000_000]),
        })

    out = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    out.to_csv(CASH_CSV, index=False)
    return rows


def append_random_repo_covers(n: int = 1, settle_days_ahead: int = 1) -> list[dict]:
    df = pd.read_csv(REPO_CSV)
    settle = (datetime.now(timezone.utc).date() + timedelta(days=settle_days_ahead)).isoformat()

    rows: list[dict] = []
    for _ in range(n):
        rows.append({
            "repo_id": f"R{len(df) + len(rows) + 1:06d}",
            "book_time": _now_str_utc(),
            "settle_date": settle,
            "bond": random.choice(BONDS),
            "cover_qty": random.choice([1_000_000, 2_000_000, 5_000_000, 10_000_000]),
            "status": "OPEN",
        })

    out = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    out.to_csv(REPO_CSV, index=False)
    return rows


if __name__ == "__main__":
    init_files()
    append_random_cash_trades()
    append_random_repo_covers()
    print("Initialized CSVs + added sample rows.")

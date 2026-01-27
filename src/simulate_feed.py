# src/simulate_feed.py
from __future__ import annotations

import time

from generate_data import (
    init_files,
    append_random_cash_trades,
    append_random_repo_covers,
)


def main(loop_seconds: int = 5, iterations: int = 30) -> None:
    init_files()
    print("Writing into CSVs. If dashboard Watch is ON, it should update live.")

    for i in range(iterations):
        append_random_cash_trades(n=3, settle_days_ahead=1)
        if i % 2 == 0:
            append_random_repo_covers(n=1, settle_days_ahead=1)

        print(f"Iteration {i + 1}/{iterations}: wrote rows.")
        time.sleep(loop_seconds)


if __name__ == "__main__":
    main()

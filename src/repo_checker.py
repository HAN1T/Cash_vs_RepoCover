import pandas as pd
from config import CASH_CSV, REPO_CSV


def load_cash() -> pd.DataFrame:
    df = pd.read_csv(CASH_CSV)
    if df.empty:
        return df
    df["qty"] = df["qty"].astype(int)
    df["signed_qty"] = df.apply(lambda r: r["qty"] if r["side"] == "BUY" else -r["qty"], axis=1)
    return df


def load_repo() -> pd.DataFrame:
    df = pd.read_csv(REPO_CSV)
    if df.empty:
        return df
    df["cover_qty"] = df["cover_qty"].astype(int)
    return df


def compute_actions(cash_df: pd.DataFrame, repo_df: pd.DataFrame) -> pd.DataFrame:
    # Aggregate cash net by bond + settle_date
    if cash_df.empty:
        cash_agg = pd.DataFrame(columns=["bond", "settle_date", "net_cash_qty"])
    else:
        cash_agg = (
            cash_df.groupby(["bond", "settle_date"], as_index=False)["signed_qty"]
            .sum()
            .rename(columns={"signed_qty": "net_cash_qty"})
        )

    # Aggregate OPEN repo covers by bond + settle_date
    if repo_df.empty:
        repo_agg = pd.DataFrame(columns=["bond", "settle_date", "open_cover_qty"])
    else:
        repo_open = repo_df[repo_df["status"] == "OPEN"].copy()
        repo_agg = (
            repo_open.groupby(["bond", "settle_date"], as_index=False)["cover_qty"]
            .sum()
            .rename(columns={"cover_qty": "open_cover_qty"})
        )

    merged = cash_agg.merge(repo_agg, on=["bond", "settle_date"], how="outer")
    merged["net_cash_qty"] = merged["net_cash_qty"].fillna(0).astype(int)
    merged["open_cover_qty"] = merged["open_cover_qty"].fillna(0).astype(int)

    # Compute short requirement
    merged["short_needed"] = merged["net_cash_qty"].apply(lambda x: abs(x) if x < 0 else 0)

    actions = []
    for _, r in merged.iterrows():
        bond = r["bond"]
        settle_date = r["settle_date"]
        short_needed = int(r["short_needed"])
        open_cover_qty = int(r["open_cover_qty"])

        if short_needed > open_cover_qty:
            actions.append({
                "action": "NEW_COVER_NEEDED",
                "bond": bond,
                "settle_date": settle_date,
                "notional_qty": short_needed - open_cover_qty,
                "reason": f"Short {short_needed} vs open cover {open_cover_qty}"
            })
        elif open_cover_qty > short_needed:
            actions.append({
                "action": "CLOSE_COVER",
                "bond": bond,
                "settle_date": settle_date,
                "notional_qty": open_cover_qty - short_needed,
                "reason": f"Excess cover {open_cover_qty} vs short {short_needed}"
            })
        else:
            actions.append({
                "action": "NO_ACTION",
                "bond": bond,
                "settle_date": settle_date,
                "notional_qty": 0,
                "reason": "Cover matches short (or both zero)"
            })

    return pd.DataFrame(actions).sort_values(["settle_date", "bond", "action"])


def run_checker() -> pd.DataFrame:
    cash_df = load_cash()
    repo_df = load_repo()
    actions_df = compute_actions(cash_df, repo_df)
    return actions_df


if __name__ == "__main__":
    out = run_checker()
    print(out.to_string(index=False))

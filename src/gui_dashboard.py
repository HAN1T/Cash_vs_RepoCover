# src/gui_dashboard.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timezone
from pathlib import Path
import pandas as pd

from config import CASH_CSV, REPO_CSV

HORIZONS = [0, 1, 2]  # T0/T1/T2


# ----------------------------
# Formatting helpers
# ----------------------------
def fmt_mm(x: int) -> str:
    """
    Display values in "mm" (millions):
      10_400_000 -> "10.4mm"
      2_000_000  -> "2mm"
      4_000      -> "0.004mm"
      0          -> "0"
    Keeps sign for negatives: -2_400_000 -> "-2.4mm"
    """
    try:
        v = int(x)
    except Exception:
        return str(x)

    if v == 0:
        return "0"

    mm = v / 1_000_000
    s = f"{mm:.3f}".rstrip("0").rstrip(".")
    return f"{s}mm"


def parse_yyyy_mm_dd(s: str) -> date:
    return datetime.strptime(str(s), "%Y-%m-%d").date()


def parse_settle_date(s: str) -> date:
    # Expect YYYY-MM-DD in CSV
    return parse_yyyy_mm_dd(s)


def horizon_bucket(settle: date, as_of: date) -> int | None:
    d = (settle - as_of).days
    return d if d in HORIZONS else None


# ----------------------------
# Data loading + dashboard build
# ----------------------------
def load_cash() -> pd.DataFrame:
    df = pd.read_csv(CASH_CSV)
    if df.empty:
        return df
    df["settle_date"] = df["settle_date"].map(parse_settle_date)
    df["qty"] = df["qty"].astype(int)
    df["signed_qty"] = df.apply(lambda r: r["qty"] if r["side"] == "BUY" else -r["qty"], axis=1)
    return df


def load_repo() -> pd.DataFrame:
    df = pd.read_csv(REPO_CSV)
    if df.empty:
        return df
    df["settle_date"] = df["settle_date"].map(parse_settle_date)
    df["cover_qty"] = df["cover_qty"].astype(int)
    return df


def build_dashboard(as_of: date) -> pd.DataFrame:
    cash_df = load_cash()
    repo_df = load_repo()

    # Cash aggregate by (bond, horizon)
    if cash_df.empty:
        cash_agg = pd.DataFrame(columns=["bond", "h", "cash_pos"])
    else:
        c = cash_df.copy()
        c["h"] = c["settle_date"].apply(lambda x: horizon_bucket(x, as_of))
        c = c.dropna(subset=["h"])
        c["h"] = c["h"].astype(int)
        cash_agg = (
            c.groupby(["bond", "h"], as_index=False)["signed_qty"]
            .sum()
            .rename(columns={"signed_qty": "cash_pos"})
        )

    # Repo aggregate (OPEN) by (bond, horizon)
    if repo_df.empty:
        repo_agg = pd.DataFrame(columns=["bond", "h", "cover_pos"])
    else:
        r = repo_df.copy()
        r = r[r["status"] == "OPEN"]
        r["h"] = r["settle_date"].apply(lambda x: horizon_bucket(x, as_of))
        r = r.dropna(subset=["h"])
        r["h"] = r["h"].astype(int)
        repo_agg = (
            r.groupby(["bond", "h"], as_index=False)["cover_qty"]
            .sum()
            .rename(columns={"cover_qty": "cover_pos"})
        )

    # Inventory universe: bonds present in horizon window in either dataset
    bonds = sorted(set(cash_agg["bond"].unique()).union(set(repo_agg["bond"].unique())))
    out = pd.DataFrame({"Bond": bonds})

    cash_map = {(row.bond, int(row.h)): int(row.cash_pos) for row in cash_agg.itertuples(index=False)}
    repo_map = {(row.bond, int(row.h)): int(row.cover_pos) for row in repo_agg.itertuples(index=False)}

    for h in HORIZONS:
        out[f"Cash_T{h}"] = out["Bond"].apply(lambda b: cash_map.get((b, h), 0))
    for h in HORIZONS:
        out[f"Cover_T{h}"] = out["Bond"].apply(lambda b: repo_map.get((b, h), 0))

    # NetBreak = max(-cash,0) - cover
    for h in HORIZONS:
        out[f"NetBreak_T{h}"] = out.apply(
            lambda r: max(-int(r[f"Cash_T{h}"]), 0) - int(r[f"Cover_T{h}"]),
            axis=1
        )

    # Commentary: earliest horizon with issue
    def comment_row(r) -> str:
        for h in HORIZONS:
            nb = int(r[f"NetBreak_T{h}"])
            cash = int(r[f"Cash_T{h}"])
            cov = int(r[f"Cover_T{h}"])

            if nb == 0:
                continue

            if nb > 0:
                return f"Need cover T{h}: missing {nb:,} (short {max(-cash,0):,} vs cover {cov:,})"

            excess = abs(nb)
            if max(-cash, 0) == 0 and cov > 0:
                return f"Close cover T{h}: excess {excess:,} (no short, cover {cov:,})"

            return f"Reduce/Close cover T{h}: excess {excess:,} (short {max(-cash,0):,} vs cover {cov:,})"

        return "OK"

    out["Commentary"] = out.apply(comment_row, axis=1)
    return out


# ----------------------------
# GUI
# ----------------------------
class RepoDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Repo Checker Dashboard (Popup)")
        self.geometry("1500x560")

        # ---- Styling: make it readable on macOS ----
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            foreground="black",
            rowheight=26,
        )
        style.configure(
            "Treeview.Heading",
            background="#efefef",
            foreground="black",
        )

        # ---- Top controls ----
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="As-of date (UTC):").pack(side="left")

        self.asof_var = tk.StringVar(value=datetime.now(timezone.utc).date().isoformat())
        self.asof_entry = ttk.Entry(top, textvariable=self.asof_var, width=12)
        self.asof_entry.pack(side="left", padx=6)

        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=6)
        ttk.Button(top, text="Auto-refresh (5s)", command=self.toggle_auto).pack(side="left", padx=6)
        ttk.Button(top, text="Watch (force refresh 1s)", command=self.toggle_watch).pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        # ---- Table ----
        cols = (
            ["Bond"]
            + [f"Cash T{h}" for h in HORIZONS]
            + [f"Cover T{h}" for h in HORIZONS]
            + [f"NetBreak T{h}" for h in HORIZONS]
            + ["Commentary"]
        )

        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)

        for c in cols:
            self.tree.heading(c, text=c)
            if c == "Bond":
                self.tree.column(c, width=120, anchor="w")
            elif c == "Commentary":
                self.tree.column(c, width=720, anchor="w")
            else:
                self.tree.column(c, width=110, anchor="e")

        # Stronger colors + black text for readability
        self.tree.tag_configure("ok", background="#C8E6C9", foreground="black")      # green
        self.tree.tag_configure("break", background="#FFCDD2", foreground="black")  # red

        # ---- Auto-refresh timer (5s) ----
        self._auto = False
        self._after_id = None

        # ---- Force-refresh watcher (1s) ----
        self.cash_path = Path(CASH_CSV)
        self.repo_path = Path(REPO_CSV)
        self._watch = False
        self._watch_after_id = None

        # Initial load
        self.refresh()

    # ----------------------------
    # Timers
    # ----------------------------
    def toggle_auto(self):
        self._auto = not self._auto
        if self._auto:
            self.status_var.set("Auto-refresh ON (every 5s)")
            self._schedule_auto()
        else:
            self.status_var.set("Auto-refresh OFF")
            if self._after_id is not None:
                self.after_cancel(self._after_id)
                self._after_id = None

    def _schedule_auto(self):
        self.refresh()
        if self._auto:
            self._after_id = self.after(5000, self._schedule_auto)

    def toggle_watch(self):
        self._watch = not self._watch
        if self._watch:
            self.status_var.set("Watch ON: forced refresh every 1s")
            self._watch_tick()
        else:
            self.status_var.set("Watch OFF")
            if self._watch_after_id is not None:
                self.after_cancel(self._watch_after_id)
                self._watch_after_id = None

    def _watch_tick(self):
        # Bulletproof: always refresh (no mtime reliance)
        self.refresh()
        if self._watch:
            self._watch_after_id = self.after(1000, self._watch_tick)

    # ----------------------------
    # Refresh render
    # ----------------------------
    def refresh(self):
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Parse as-of
        try:
            as_of = parse_yyyy_mm_dd(self.asof_var.get())
        except Exception:
            self.status_var.set("Invalid as-of date. Use YYYY-MM-DD.")
            return

        try:
            df = build_dashboard(as_of)
        except Exception as e:
            self.status_var.set(f"Error building dashboard: {e}")
            return

        # Populate
        for _, r in df.iterrows():
            raw_nb = [int(r[f"NetBreak_T{h}"]) for h in HORIZONS]
            has_break = any(nb != 0 for nb in raw_nb)
            tag = "break" if has_break else "ok"

            values = [
                r["Bond"],
                fmt_mm(r["Cash_T0"]), fmt_mm(r["Cash_T1"]), fmt_mm(r["Cash_T2"]),
                fmt_mm(r["Cover_T0"]), fmt_mm(r["Cover_T1"]), fmt_mm(r["Cover_T2"]),
                fmt_mm(r["NetBreak_T0"]), fmt_mm(r["NetBreak_T1"]), fmt_mm(r["NetBreak_T2"]),
                r["Commentary"],
            ]

            self.tree.insert("", "end", values=values, tags=(tag,))

        self.status_var.set(
            f"Last refresh: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC | Rows: {len(df)} | "
            f"CASH: {self.cash_path} | REPO: {self.repo_path}"
        )


if __name__ == "__main__":
    app = RepoDashboard()
    app.mainloop()

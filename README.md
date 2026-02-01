# Cash_vs_RepoCover

A **non-confidential portfolio project** that simulates a common middle-office workflow:  
**identify short cash positions** and **compare them against available repo/financing cover**, then surface potential breaks in a simple local dashboard across **T+0 / T+1 / T+2 buckets**. 

> **Representation only:** all data in this repository is synthetic / simulated. No client, position, or firm-confidential data is used.
---

## Bigger Picture (production context)

In a live trading environment, a frequent operational problem is:
- cash positions show a short (or potential fail)
- financing/repo cover is missing, insufficient, late, or in the wrong settlement bucket
- teams need a fast view of “what’s broken” and “when” (T+0/T+1/T+2) to triage actions

This repo demonstrates a simplified version of that process.

---

## What the project does

1) **Generates synthetic datasets** representing:
- cash trades/positions (front office source in real life e.g., TOMS)
- repo/financing cover (financing system source in real life)

2) **Computes breaks** by comparing:
- required cover (cash short) vs available repo cover
- settlement timing buckets (T+0 / T+1 / T+2)

3) **Displays results in a local dashboard**
- breaks grouped by bucket (T+0/T+1/T+2)

4) **Simulates an incoming feed**
- a lightweight “stream” to mimic intraday updates (run in a second terminal)

---

<img width="1271" height="157" alt="Screenshot 2026-01-28 at 21 35 13" src="https://github.com/user-attachments/assets/ee7a859d-db63-45e8-b526-7cba20e0e81e" />

https://github.com/user-attachments/assets/dbce358f-b10c-4ab0-b5b7-74ed0a7d14c6

---

## Repository structure

├─ data/ # synthetic data outputs
├─ src/ # scripts (data generation, dashboard, feed simulation)
├─ requirements.txt
├─ README.md
└─ git1.mp4 # quick demo video



## Run
```bash
pip install -r requirements.txt
python src/generate_data.py
python src/gui_dashboard.py
# in another terminal:
python src/simulate_feed.py

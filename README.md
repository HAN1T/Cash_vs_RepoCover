# Cash_vs_RepoCover

This project is created for representation purpose only for identification of cash trades and comparison against existing repo cover. 

Result are then populated on a local dashboard which identifies T+0/T+1/T+2 breaks.

Real world cash trades would have been populated from TOMS or respective front office system, similarly financing trades would have been populated from financing system data



https://github.com/user-attachments/assets/dbce358f-b10c-4ab0-b5b7-74ed0a7d14c6



## Run
```bash
pip install -r requirements.txt
python src/generate_data.py
python src/gui_dashboard.py
# in another terminal:
python src/simulate_feed.py

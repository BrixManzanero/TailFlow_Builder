# TailFlow Consolidated Report

A Streamlit app that turns raw TailFlow platform exports into a clean,
Excel-style consolidated report — **Revenue (GMV & NMV)**, **Product
Performance**, and ready-to-fill **Conversion** and **ROAS** sheets.

Pure-Python backend (data extraction), HTML/CSS frontend (presentation),
cleanly separated.

## Project layout
```
tailflow_report_app/
├── app.py                  # Streamlit entry point (uploads + orchestration)
├── requirements.txt
├── backend/                # data extraction — no UI imports
│   ├── revenue.py          #   GMV / NMV orders  -> monthly revenue sheet
│   ├── products.py         #   yearly product CSVs -> product performance
│   └── utils.py            #   cursor-safe CSV reading, formatting
└── frontend/               # presentation only
    ├── render.py           #   injects data into the template
    ├── report.html         #   markup + interactivity (tabs, sort)
    └── report.css          #   styling (navy GMV / green NMV banding)
```

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Inputs
| Sheet               | Upload                                      |
|---------------------|---------------------------------------------|
| Revenue (GMV & NMV) | `*_GMV_orders.csv` + `*_NMV_orders.csv`     |
| Product Performance | `TailflowProduct_2024.csv` (+ 2025, 2026)   |
| Conversion / ROAS   | (their exports — appear once added)         |

The year for product files is read from the filename (e.g. `..._2025.csv`).

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo.
2. On share.streamlit.io, point a new app at `app.py`.
3. Future updates: commit to GitHub → auto-redeploys in ~1 min.

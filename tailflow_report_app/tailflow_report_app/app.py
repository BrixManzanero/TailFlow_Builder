"""TailFlow Consolidated Report — Streamlit app.

Frontend orchestration only: file uploads, calls into the backend extractors,
hands the structured data to the frontend renderer, and shows the result.
All data processing lives in backend/; all presentation lives in frontend/.

Run locally:   streamlit run app.py
Deploy:        push to GitHub -> Streamlit Community Cloud (auto-redeploy)
"""
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from backend import extract_revenue, extract_products, extract_products_monthly, build_excel
from frontend import build_report

st.set_page_config(page_title="TailFlow Consolidated Report", page_icon="📊", layout="wide")

# Trim Streamlit's default chrome so the report fills the page.
st.markdown(
    """
    <style>
      .block-container{padding-top:1.4rem;padding-bottom:0;max-width:1320px}
      header[data-testid="stHeader"]{height:0}
      [data-testid="stSidebar"]{min-width:320px}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("## TailFlow Report Builder")
    st.caption("Upload your TailFlow exports. The report builds itself.")

    st.markdown("### 1 · Revenue (GMV & NMV)")
    gmv_file = st.file_uploader("GMV orders CSV", type="csv", key="gmv")
    nmv_file = st.file_uploader("NMV orders CSV", type="csv", key="nmv")

    st.markdown("### 2 · Product Performance")
    product_files = st.file_uploader(
        "Yearly product CSVs (2024 / 2025 / 2026)",
        type="csv",
        accept_multiple_files=True,
        key="products",
        help="The year is detected from each file name, e.g. TailflowProduct_2025.csv",
    )
    monthly_product_files = st.file_uploader(
        "Monthly product exports (optional → enables MoM)",
        type="csv",
        accept_multiple_files=True,
        key="products_monthly",
        help="One file per month, e.g. January2024.csv, February2024.csv. The "
             "month is read from each file name. When provided, the Product tab "
             "switches from Year-over-Year to true Month-over-Month.",
    )

    st.divider()
    st.caption("Conversion & ROAS sheets appear automatically once those exports are added.")

# ----------------------------------------------------------------------------- extract
data = {
    "meta": {
        "source": "TailFlow exports",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "extracted": datetime.now().strftime("%Y-%m-%d %H:%M"),
    },
    "revenue": [],
    "summary": None,
    "products_yearly": {},
    "products_monthly": {},
}

if gmv_file and nmv_file:
    try:
        data["revenue"], data["summary"] = extract_revenue(gmv_file, nmv_file)
    except Exception as exc:  # surface the real reason, don't fail silently
        st.error(f"Revenue extraction failed — check the GMV/NMV exports. ({exc})")
elif gmv_file or nmv_file:
    st.warning("Revenue needs **both** the GMV and NMV exports to build that sheet.")

if product_files:
    try:
        data["products_yearly"] = extract_products(product_files)
    except Exception as exc:
        st.error(f"Yearly product extraction failed — check the exports. ({exc})")

if monthly_product_files:
    try:
        data["products_monthly"] = extract_products_monthly(monthly_product_files)
    except Exception as exc:
        st.error(f"Monthly product extraction failed — check the exports. ({exc})")

# ----------------------------------------------------------------------------- render
def _scoped(data, choice):
    """Return (subset_data, filename_tag) for the chosen download scope.
    'Everything' -> full workbook; a single period -> only that product sheet.
    """
    if choice.startswith("Everything"):
        return data, "Full"
    kind, period = choice.split(" · ", 1)
    sub = {"meta": data["meta"], "revenue": [], "summary": None,
           "products_yearly": {}, "products_monthly": {}}
    if kind == "Month":
        sub["products_monthly"] = {period: data["products_monthly"][period]}
    else:  # YoY
        sub["products_yearly"] = {period: data["products_yearly"][period]}
    return sub, f"{kind}_{period}"


nothing_uploaded = not (gmv_file and nmv_file) and not product_files and not monthly_product_files

if nothing_uploaded:
    st.info(
        "👋 Upload the **GMV** and **NMV** order exports (and your **product** CSVs) "
        "in the sidebar. The consolidated report renders here — Revenue, Product YoY, "
        "Product MoM, plus ready-to-fill Conversion and ROAS sheets."
    )
else:
    components.html(build_report(data), height=860, scrolling=True)

    scopes = ["Everything (all sheets)"]
    scopes += [f"Month · {m}" for m in data["products_monthly"]]
    scopes += [f"YoY · {y}" for y in data["products_yearly"]]

    col1, col2 = st.columns([1, 1])
    with col1:
        scope = st.selectbox(
            "Download scope",
            scopes,
            help="Pick a single month or year to export just that sheet, "
                 "or 'Everything' for the full workbook.",
        )
    with col2:
        sub, tag = _scoped(data, scope)
        st.download_button(
            "⬇️ Download Excel (.xlsx)",
            build_excel(sub),
            file_name=f"TailFlow_{tag}_{datetime.now():%Y%m%d_%H%M}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        yoy = ", ".join(data["products_yearly"]) or "—"
        mom = ", ".join(data["products_monthly"]) or "—"
        st.caption(f"YoY: {yoy}  ·  MoM: {mom}")

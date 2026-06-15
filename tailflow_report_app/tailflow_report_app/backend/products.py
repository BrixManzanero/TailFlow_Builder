"""Product performance extractor: turns the yearly TailFlow product exports
into the 'Product Performance' sheet data.

Each product CSV has a one-line header banner ('Total Entries, NN') above the
real table, so we skip the first row. The declared entry count is padded with
blank lines, so we keep only rows that actually carry an SKU.
"""
from .utils import safe_csv, detect_year, to_int, to_float

REQUIRED = ["Name", "SKU", "GMV", "Quantity Sold", "Stock", "Sell Through Rate"]


def _extract_one(uploaded):
    df = safe_csv(uploaded, skiprows=1)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Product file missing columns: {missing}")
    df = df.dropna(subset=["SKU"])

    rows = []
    for _, r in df.iterrows():
        sku = str(r["SKU"]).strip()
        if not sku or sku.lower() == "nan":
            continue
        rows.append({
            "name": str(r["Name"]).strip(),
            "sku": sku,
            "gmv": to_float(r["GMV"]),
            "qty": to_int(r["Quantity Sold"]),
            "stock": to_int(r["Stock"]),
            "st": round(to_float(r["Sell Through Rate"]), 3),
        })
    rows.sort(key=lambda x: -x["gmv"])

    totals = {
        "gmv": sum(x["gmv"] for x in rows),
        "qty": sum(x["qty"] for x in rows),
        "stock": sum(x["stock"] for x in rows),
        "count": len(rows),
    }
    return {"rows": rows, "totals": totals}


def extract_products(files):
    """files: list of UploadedFile. Year is read from each file name.
    Returns {year: {rows, totals}} sorted by year.
    """
    out = {}
    for f in files:
        year = detect_year(getattr(f, "name", f))
        out[year] = _extract_one(f)
    return {y: out[y] for y in sorted(out)}

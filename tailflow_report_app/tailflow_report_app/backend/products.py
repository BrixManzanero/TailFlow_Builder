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


def _yoy(curr, prior):
    """Percent change of curr vs prior; None when there's no comparable base."""
    if prior in (None, 0):
        return None
    return round((curr - prior) / prior * 100, 1)


def _add_period_change(by_year):
    """Attach a period-over-period change to every SKU and to each year's
    totals. With yearly files this is Year-over-Year (same SKU vs the prior
    year). If a monthly product export is supplied instead, the same field is
    populated month-over-month upstream — the frontend renders it either way.
    """
    years = sorted(by_year, key=lambda y: int(y) if str(y).isdigit() else 0)
    for y in years:
        prior_key = str(int(y) - 1) if str(y).isdigit() else None
        prior_rows = {r["sku"]: r for r in by_year[prior_key]["rows"]} if prior_key in by_year else {}
        for r in by_year[y]["rows"]:
            base = prior_rows.get(r["sku"])
            r["chg"] = _yoy(r["gmv"], base["gmv"] if base else None)
        t = by_year[y]["totals"]
        pt = by_year[prior_key]["totals"] if prior_key in by_year else None
        t["chg"] = _yoy(t["gmv"], pt["gmv"] if pt else None)
    # the most recent year is treated as year-to-date (partial)
    if years:
        by_year[years[-1]]["ytd"] = True
    return by_year


def extract_products(files):
    """files: list of UploadedFile. Year is read from each file name.
    Returns {year: {rows, totals, ...}} sorted by year, with a YoY change
    ('chg') on every row and on the totals.
    """
    out = {}
    for f in files:
        year = detect_year(getattr(f, "name", f))
        out[year] = _extract_one(f)
    out = {y: out[y] for y in sorted(out)}
    return _add_period_change(out)

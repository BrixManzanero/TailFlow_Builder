"""Monthly product performance extractor.

The real TailFlow monthly export is one file per month, laid out exactly like
the yearly product file (a 'Total Entries' banner row, then a header row of
Name / SKU / GMV / Quantity Sold / Stock / Sell Through Rate). The month is
taken from the file name, e.g. '..._January2024.csv' -> 'Jan-2024'.

Month-over-month is computed per SKU across the uploaded months, in
chronological order.
"""
import re
from datetime import datetime

from .utils import safe_csv, to_int, to_float, clean_name

REQUIRED = ["Name", "SKU", "GMV", "Quantity Sold", "Stock", "Sell Through Rate"]
_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
         "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def detect_month(name):
    """'..._January2024.csv' -> ('Jan-2024', datetime(2024, 1, 1))."""
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]?\s*(20\d{2})",
                  str(name), re.I)
    if not m:
        raise ValueError(f"Could not read a month and year from file name '{name}'")
    dt = datetime(int(m.group(2)), _ABBR[m.group(1).lower()[:3]], 1)
    return dt.strftime("%b-%Y"), dt


def _rows(uploaded):
    df = safe_csv(uploaded, skiprows=1)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Monthly product file missing columns: {missing}")
    df = df.dropna(subset=["SKU"])
    out = []
    for _, r in df.iterrows():
        sku = str(r["SKU"]).strip()
        if not sku or sku.lower() == "nan":
            continue
        out.append({
            "name": clean_name(r["Name"]),
            "sku": sku,
            "gmv": to_float(r["GMV"]),
            "qty": to_int(r["Quantity Sold"]),
            "stock": to_int(r["Stock"]),
            "st": round(to_float(r["Sell Through Rate"]), 3),
        })
    out.sort(key=lambda x: -x["gmv"])
    return out


def extract_products_monthly(files):
    """files: list of UploadedFile, one per month. Returns {month: {rows, totals}}
    in chronological order, with month-over-month change ('chg') per SKU and on
    the totals.
    """
    parsed = []
    for f in files:
        label, dt = detect_month(getattr(f, "name", f))
        parsed.append((dt, label, _rows(f)))
    parsed.sort(key=lambda x: x[0])

    by_period = {}
    for _, label, rows in parsed:
        by_period[label] = {
            "rows": rows,
            "totals": {
                "gmv": sum(x["gmv"] for x in rows),
                "qty": sum(x["qty"] for x in rows),
                "stock": sum(x["stock"] for x in rows),
                "count": len(rows),
            },
        }

    keys = list(by_period.keys())
    for i, key in enumerate(keys):
        prior = {r["sku"]: r for r in by_period[keys[i - 1]]["rows"]} if i > 0 else {}
        for r in by_period[key]["rows"]:
            base = prior.get(r["sku"])
            r["chg"] = None if (base is None or base["gmv"] == 0) else round(
                (r["gmv"] - base["gmv"]) / base["gmv"] * 100, 1)
        t = by_period[key]["totals"]
        pt = by_period[keys[i - 1]]["totals"] if i > 0 else None
        t["chg"] = None if (pt is None or pt["gmv"] == 0) else round(
            (t["gmv"] - pt["gmv"]) / pt["gmv"] * 100, 1)

    # All months are kept and individually downloadable. The earliest month is
    # the baseline (no prior month), so its MoM column is blank — that's expected.
    return by_period

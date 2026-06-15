"""Revenue extractor: turns the TailFlow GMV / NMV order exports into the
monthly 'Revenue (GMV & NMV)' sheet data.

The TailFlow export holds two side-by-side blocks; block '0' (column prefix
'0 ...') carries the live monthly series. Block '1' is a legacy range that is
mostly empty, so we ignore it.
"""
from .utils import safe_csv, month_label, to_float

PLATFORMS = ["Shopee", "Shopify", "Lazada", "TikTok"]


def _block(df, metric):
    """Slice block 0 (date + 4 platforms + sum) and drop empty rows."""
    cols = ["date_series"] + [f"0 {p}" for p in PLATFORMS] + [f"0_sum_{metric}"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Export is missing expected columns: {missing}")
    block = df[cols].dropna(subset=["date_series"])
    block = block[block["0 Shopee"].notna()].reset_index(drop=True)
    return block


def extract_revenue(gmv_file, nmv_file):
    """Return (months, summary).

    months: one dict per month with gmv{}, nmv{}, and month-over-month % on GMV.
    summary: grand totals used by the KPI strip.
    """
    g = _block(safe_csv(gmv_file), "gmv")
    n = _block(safe_csv(nmv_file), "nmv")

    # index NMV by month label so the two files stay aligned even if row
    # counts differ slightly.
    nmap = {month_label(row["date_series"]): row for _, row in n.iterrows()}

    months = []
    prev_total = None
    for _, row in g.iterrows():
        label = month_label(row["date_series"])
        total = to_float(row["0_sum_gmv"])
        mom = None if prev_total in (None, 0) else round((total - prev_total) / prev_total * 100, 2)
        prev_total = total

        nrow = nmap.get(label)
        nmv = {p: (to_float(nrow[f"0 {p}"]) if nrow is not None else 0.0) for p in PLATFORMS}
        nmv["Total"] = to_float(nrow["0_sum_nmv"]) if nrow is not None else 0.0

        months.append({
            "month": label,
            "gmv": {**{p: to_float(row[f"0 {p}"]) for p in PLATFORMS}, "Total": total},
            "mom": mom,
            "nmv": nmv,
        })

    gmv_by_platform = {p: sum(m["gmv"][p] for m in months) for p in PLATFORMS}
    gmv_by_platform["Total"] = sum(m["gmv"]["Total"] for m in months)

    summary = {
        "gmv_by_platform": gmv_by_platform,
        "nmv_total": sum(m["nmv"]["Total"] for m in months),
        "months": len(months),
        "span": f"{months[0]['month']} – {months[-1]['month']}" if months else "",
    }
    return months, summary

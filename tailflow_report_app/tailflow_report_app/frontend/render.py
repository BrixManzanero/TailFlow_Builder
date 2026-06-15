"""Frontend renderer: load the HTML/CSS templates and inject the report data.

Keeps presentation (report.html + report.css) fully separate from the Python
backend. Returns a single self-contained HTML string ready for
streamlit.components.v1.html().
"""
import json
import os

_DIR = os.path.dirname(__file__)


def _read(name):
    with open(os.path.join(_DIR, name), encoding="utf-8") as f:
        return f.read()


def build_report(data):
    html = _read("report.html")
    css = _read("report.css")
    html = html.replace("/*CSS*/", css)
    # json.dumps is HTML-safe here because the payload is pure numbers/strings
    # with no '</script>' sequences; we guard anyway.
    payload = json.dumps(data).replace("</", "<\\/")
    html = html.replace("/*DATA*/", payload)
    return html

"""TailFlow report backend — data extraction only, no UI dependencies."""
from .revenue import extract_revenue
from .products import extract_products
from .products_monthly import extract_products_monthly
from .excel_export import build_excel

__all__ = ["extract_revenue", "extract_products", "extract_products_monthly", "build_excel"]

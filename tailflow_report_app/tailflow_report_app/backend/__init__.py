"""TailFlow report backend — data extraction only, no UI dependencies."""
from .revenue import extract_revenue
from .products import extract_products

__all__ = ["extract_revenue", "extract_products"]

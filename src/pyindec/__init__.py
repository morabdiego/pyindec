"""pyindec — Cliente amigable en Python para el Catálogo API-INDEC."""

from .catalog import ENDPOINTS, describe_endpoint, list_endpoints, resolve_endpoint
from .client import DEFAULT_BASE_URL, IndecClient
from .exceptions import (
    IndecAPIError,
    IndecAuthError,
    IndecError,
    IndecFilterError,
    IndecNotFoundError,
    IndecPermissionError,
    IndecRateLimitError,
)
from .models import SIGNOS_CONVENCIONALES, ColumnInfo, EndpointInfo, IndecResponse, explain_sign, parse_content_range
from .query import F, Filter, FilterOp, MultiFilterOp, QueryBuilder

__version__ = "0.1.0"
__all__ = [
    "DEFAULT_BASE_URL", "ENDPOINTS", "SIGNOS_CONVENCIONALES", "ColumnInfo", "EndpointInfo",
    "F", "Filter", "FilterOp", "IndecAPIError", "IndecAuthError", "IndecClient", "IndecError",
    "IndecFilterError", "IndecNotFoundError", "IndecPermissionError", "IndecRateLimitError",
    "IndecResponse", "MultiFilterOp", "QueryBuilder", "__version__", "describe_endpoint",
    "explain_sign", "list_endpoints", "parse_content_range", "resolve_endpoint",
]

"""Constructor de consultas PostgREST (QueryBuilder) y operadores de filtro (F)."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

from .catalog import resolve_endpoint
from .exceptions import IndecFilterError
from .models import EndpointInfo, IndecResponse

if TYPE_CHECKING:
    from .client import IndecClient

VALID_OPERATORS = frozenset({"eq", "neq", "gt", "gte", "lt", "lte", "like", "ilike", "in", "is"})
MAX_LIMIT = 1000


def _to_str(val: Any) -> str:
    if val is None:
        return "null"
    return ("true" if val else "false") if isinstance(val, bool) else str(val)


@dataclass(frozen=True)
class FilterOp:
    operator: str
    value: Any

    def __post_init__(self) -> None:
        op = self.operator.lower().strip()
        if op not in VALID_OPERATORS:
            raise IndecFilterError(f"Operador PostgREST inválido: {self.operator!r}")
        object.__setattr__(self, "operator", op)

    def to_postgrest(self) -> str:
        op, val = self.operator, self.value
        if op == "in":
            if isinstance(val, str):
                s = val.strip()
                return f"in.{s}" if s.startswith("(") and s.endswith(")") else f"in.({s})"
            if not isinstance(val, Iterable) or not (items := [_to_str(x) for x in val]):
                raise IndecFilterError("El operador 'in' requiere una colección no vacía.")
            return f"in.({','.join(items)})"
        if op == "is":
            s = _to_str(val).strip().lower()
            if s not in ("null", "true", "false"):
                raise IndecFilterError(f"El operador 'is' solo admite None, True o False ({val!r}).")
            return f"is.{s}"
        if op in ("like", "ilike"):
            return f"{op}.{str(val).replace('%', '*')}"
        return f"{op}.{_to_str(val)}"


@dataclass(frozen=True)
class MultiFilterOp:
    filters: tuple[FilterOp, ...]

    def to_postgrest_list(self) -> list[str]:
        return [f.to_postgrest() for f in self.filters]


class F:
    """Helpers para filtros PostgREST (``F.eq``, ``F.gte``, ``F.between``, ``F.ilike``, ``F.in_``, ``F.is_``)."""

    eq = staticmethod(lambda v: FilterOp("eq", v))
    neq = staticmethod(lambda v: FilterOp("neq", v))
    gt = staticmethod(lambda v: FilterOp("gt", v))
    gte = staticmethod(lambda v: FilterOp("gte", v))
    lt = staticmethod(lambda v: FilterOp("lt", v))
    lte = staticmethod(lambda v: FilterOp("lte", v))
    like = staticmethod(lambda p: FilterOp("like", p))
    ilike = staticmethod(lambda p: FilterOp("ilike", p))
    in_ = staticmethod(lambda vals: FilterOp("in", list(vals)))
    is_ = staticmethod(lambda v: FilterOp("is", v))
    is_null = staticmethod(lambda: FilterOp("is", None))
    between = staticmethod(lambda low, high: MultiFilterOp((FilterOp("gte", low), FilterOp("lte", high))))
    contains = staticmethod(lambda s, *, case_sensitive=False: FilterOp("like" if case_sensitive else "ilike", f"*{s.strip('*')}*"))
    startswith = staticmethod(lambda s, *, case_sensitive=False: FilterOp("like" if case_sensitive else "ilike", f"{s.rstrip('*')}*"))
    endswith = staticmethod(lambda s, *, case_sensitive=False: FilterOp("like" if case_sensitive else "ilike", f"*{s.lstrip('*')}"))


Filter = F
FilterValue = Any | FilterOp | MultiFilterOp | Sequence[Any]


def encode_filter_values(val: Any) -> list[str]:
    if isinstance(val, FilterOp):
        return [val.to_postgrest()]
    if isinstance(val, MultiFilterOp):
        return val.to_postgrest_list()
    if isinstance(val, (list, tuple, set, frozenset)):
        items = list(val)
        return [x.to_postgrest() for x in items] if all(isinstance(x, FilterOp) for x in items) else [F.in_(items).to_postgrest()]
    if isinstance(val, str) and "." in val and val.split(".", 1)[0] in VALID_OPERATORS:
        return [val]
    return [f"eq.{_to_str(val)}"]


class QueryBuilder:
    """Constructor fluido de consultas PostgREST para cualquier endpoint del INDEC."""

    def __init__(self, client: IndecClient, endpoint: str) -> None:
        self._client = client
        self.endpoint_info: EndpointInfo | None = resolve_endpoint(endpoint)
        self._path = self.endpoint_info.path if self.endpoint_info else f"/{endpoint.strip().lstrip('/')}"
        self._col_map = {c.name.lower(): c.name for c in self.endpoint_info.columns} if self.endpoint_info else {}
        self._select: list[str] = []
        self._order: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._exact_count: bool = False
        self._filters: list[tuple[str, str]] = []

    def _col(self, name: str) -> str:
        c = name.strip()
        return self._col_map.get(c.lower(), c)

    def select(self, *columns: str | Iterable[str]) -> QueryBuilder:
        for item in columns:
            for p in (item.split(",") if isinstance(item, str) else item):
                if s := str(p).strip():
                    norm = "*" if s == "*" else self._col(s)
                    if norm not in self._select:
                        self._select.append(norm)
        return self

    def order(self, *columns: str | Iterable[str], desc: bool = False) -> QueryBuilder:
        for item in columns:
            for p in (item.split(",") if isinstance(item, str) else item):
                if s := str(p).strip():
                    c, *rest = s.split(".", 1)
                    spec = f"{self._col(c)}.{rest[0]}" if rest else (f"{self._col(c)}.desc" if desc else self._col(c))
                    if spec not in self._order:
                        self._order.append(spec)
        return self

    def limit(self, count: int) -> QueryBuilder:
        if not (1 <= count <= MAX_LIMIT):
            raise IndecFilterError(f"'limit' debe estar entre 1 y {MAX_LIMIT} ({count}).")
        self._limit = count
        return self

    def offset(self, start: int) -> QueryBuilder:
        if start < 0:
            raise IndecFilterError(f"'offset' no puede ser negativo ({start}).")
        self._offset = start
        return self

    def count(self, exact: bool = True) -> QueryBuilder:
        self._exact_count = exact
        return self

    def filter(self, column: str, operator: str, value: Any) -> QueryBuilder:
        self._filters.append((self._col(column), FilterOp(operator, value).to_postgrest()))
        return self

    def where(self, **filters: Any) -> QueryBuilder:
        for col, val in filters.items():
            if val is not None:
                c = self._col(col)
                self._filters.extend((c, enc) for enc in encode_filter_values(val))
        return self

    def eq(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "eq", value)
    def neq(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "neq", value)
    def gt(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "gt", value)
    def gte(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "gte", value)
    def lt(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "lt", value)
    def lte(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "lte", value)
    def like(self, column: str, pattern: str) -> QueryBuilder: return self.filter(column, "like", pattern)
    def ilike(self, column: str, pattern: str) -> QueryBuilder: return self.filter(column, "ilike", pattern)
    def in_(self, column: str, values: Iterable[Any]) -> QueryBuilder: return self.filter(column, "in", list(values))
    def is_(self, column: str, value: Any) -> QueryBuilder: return self.filter(column, "is", value)
    def between(self, column: str, low: Any, high: Any) -> QueryBuilder: return self.gte(column, low).lte(column, high)

    def contains(self, column: str, sub: str, *, case_sensitive: bool = False) -> QueryBuilder:
        self._filters.append((self._col(column), F.contains(sub, case_sensitive=case_sensitive).to_postgrest()))
        return self

    def build_params(
        self,
        *,
        limit_override: int | None = None,
        offset_override: int | None = None,
        ensure_pagination_key: bool = False,
    ) -> list[tuple[str, str]]:
        params: list[tuple[str, str]] = []
        if self._select:
            params.append(("select", ",".join(self._select)))
        specs = list(self._order)
        if ensure_pagination_key and self.endpoint_info and self.endpoint_info.pagination_key:
            seen = {s.split(".", 1)[0].lower() for s in specs}
            specs.extend(k for k in self.endpoint_info.pagination_key if k.lower() not in seen)
        if specs:
            params.append(("order", ",".join(specs)))
        if (lim := limit_override if limit_override is not None else self._limit) is not None:
            params.append(("limit", str(lim)))
        if (off := offset_override if offset_override is not None else self._offset) is not None:
            params.append(("offset", str(off)))
        params.extend(self._filters)
        return params

    def _fetch_pages(self, page_size: int = MAX_LIMIT, use_count: bool = False) -> Iterator[IndecResponse]:
        if not (1 <= page_size <= MAX_LIMIT):
            raise IndecFilterError(f"page_size debe estar entre 1 y {MAX_LIMIT}.")
        offset, total, first = self._offset or 0, None, True
        while True:
            params = self.build_params(limit_override=page_size, offset_override=offset, ensure_pagination_key=True)
            resp = self._client._request_page(self._path, params=params, exact_count=(first or use_count))
            first = False
            if resp.total_count is not None:
                total = resp.total_count
            yield resp
            if len(resp.data) < page_size or (total is not None and offset + len(resp.data) >= total):
                break
            offset += len(resp.data)

    def execute(self, *, fetch_all: bool = False, page_size: int = MAX_LIMIT, include_count: bool | None = None) -> IndecResponse:
        use_count = self._exact_count if include_count is None else include_count
        if not fetch_all:
            return self._client._request_page(self._path, params=self.build_params(), exact_count=use_count)
        pages = list(self._fetch_pages(page_size, use_count))
        rows = [r for p in pages for r in p.data]
        last = pages[-1] if pages else None
        total = next((p.total_count for p in pages if p.total_count is not None), len(rows))
        return IndecResponse(
            data=rows,
            endpoint=self._path,
            status_code=last.status_code if last else 200,
            content_range=last.content_range if last else None,
            range_start=(self._offset or 0) if rows else None,
            range_end=(self._offset or 0) + len(rows) - 1 if rows else None,
            total_count=total,
            pages_fetched=len(pages),
        )

    def iter_pages(self, *, page_size: int = MAX_LIMIT, as_dataframe: bool = True) -> Iterator[pd.DataFrame | list[dict[str, Any]]]:
        for p in self._fetch_pages(page_size, self._exact_count):
            if p.data:
                yield p.df if as_dataframe else p.data

    def df(self, *, fetch_all: bool = False) -> pd.DataFrame: return self.execute(fetch_all=fetch_all).df
    to_df = df
    def raw(self, *, fetch_all: bool = False) -> list[dict[str, Any]]: return self.execute(fetch_all=fetch_all).data

    def all(self, *, as_dataframe: bool = True, page_size: int = MAX_LIMIT) -> pd.DataFrame | list[dict[str, Any]]:
        resp = self.execute(fetch_all=True, page_size=page_size)
        return resp.df if as_dataframe else resp.data

    def count_rows(self) -> int:
        resp = self._client._request_page(self._path, params=self.build_params(limit_override=1, offset_override=0), exact_count=True)
        return resp.total_count if resp.total_count is not None else len(resp.data)

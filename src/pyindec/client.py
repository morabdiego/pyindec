"""Cliente principal para el Catálogo API-INDEC."""

from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .catalog import describe_endpoint, list_endpoints
from .exceptions import (
    IndecAPIError,
    IndecAuthError,
    IndecFilterError,
    IndecNotFoundError,
    IndecPermissionError,
    IndecRateLimitError,
)
from .models import EndpointInfo, IndecResponse, parse_content_range
from .query import FilterValue, QueryBuilder

DEFAULT_BASE_URL = "https://api.indec.gob.ar/v1"
_TOKEN_ENV_VARS = ("INDEC_API_TOKEN", "INDEC_TOKEN", "INDEC_API_KEY", "API_KEY")
_ERROR_MAP: dict[int, type[IndecAPIError]] = {
    400: IndecFilterError,
    401: IndecAuthError,
    403: IndecPermissionError,
    404: IndecNotFoundError,
    429: IndecRateLimitError,
}


def _load_dotenv_token(path: Path | None = None) -> str | None:
    p = path or (Path.cwd() / ".env")
    if not p.is_file():
        return None
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip().removeprefix("export ").strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                if k.strip() in _TOKEN_ENV_VARS and (val := v.strip().strip("'\"")):
                    return val
    except OSError:
        pass
    return None


class IndecClient:
    """Cliente amigable para los 19 servicios de datos del Catálogo API-INDEC."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
        load_dotenv: bool = True,
    ) -> None:
        raw = token or next((os.environ[k] for k in _TOKEN_ENV_VARS if os.environ.get(k)), None)
        if not raw and load_dotenv:
            raw = _load_dotenv_token()
        if raw and raw.lower().startswith("bearer "):
            raw = raw[7:].strip()

        self.token: str | None = raw
        self.base_url: str = (base_url or os.environ.get("INDEC_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout: float = timeout
        self._owns_session = session is None
        self._session = session or requests.Session()

        if self._owns_session and max_retries > 0:
            retry = Retry(
                total=max_retries,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> IndecClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _request_page(
        self,
        path: str,
        *,
        params: list[tuple[str, str]] | None = None,
        exact_count: bool = False,
    ) -> IndecResponse:
        if not self.token:
            raise IndecAuthError(
                "No se configuró un token JWT. Páselo como IndecClient(token='...') o defina INDEC_API_TOKEN / API_KEY.",
                status_code=401,
            )
        clean_path = f"/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "pyindec/0.1.0",
        }
        if exact_count:
            headers["Prefer"] = "count=exact"

        resp = self._session.get(f"{self.base_url}{clean_path}", params=params or [], headers=headers, timeout=self.timeout)
        if not (200 <= resp.status_code < 300):
            self._raise_error(resp)

        data = resp.json() if resp.content else []
        if not isinstance(data, list):
            data = [data]
        cr = resp.headers.get("Content-Range") or resp.headers.get("content-range")
        r_start, r_end, total = parse_content_range(cr)
        return IndecResponse(data, clean_path, resp.status_code, cr, r_start, r_end, total, 1)

    @staticmethod
    def _raise_error(resp: requests.Response) -> None:
        msg = f"Error HTTP {resp.status_code} al consultar {resp.url}"
        code = details = hint = payload = None
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                code = payload.get("code")
                msg = payload.get("message") or payload.get("error") or msg
                details, hint = payload.get("details"), payload.get("hint")
        except ValueError:
            if text := (resp.text or "").strip():
                msg = text[:500]
        exc_cls = _ERROR_MAP.get(resp.status_code, IndecAPIError)
        raise exc_cls(msg, status_code=resp.status_code, code=code, details=details, hint=hint, payload=payload)

    def endpoints(self, *, as_dataframe: bool = True) -> pd.DataFrame | list[EndpointInfo]:
        return list_endpoints(as_dataframe=as_dataframe)

    def describe(self, endpoint: str, *, as_dataframe: bool = True) -> pd.DataFrame | EndpointInfo:
        return describe_endpoint(endpoint, as_dataframe=as_dataframe)

    def query(self, endpoint: str) -> QueryBuilder:
        return QueryBuilder(self, endpoint)

    table = from_ = query

    def get(
        self,
        endpoint: str,
        *,
        select: str | Iterable[str] | None = None,
        order: str | Iterable[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        fetch_all: bool = False,
        as_dataframe: bool = True,
        include_count: bool = False,
        return_response: bool = False,
        **filters: FilterValue,
    ) -> pd.DataFrame | list[dict[str, Any]] | IndecResponse:
        qb = self.query(endpoint)
        if select is not None:
            qb.select(select)
        if order is not None:
            qb.order(order)
        if limit is not None:
            qb.limit(limit)
        if offset is not None:
            qb.offset(offset)
        if include_count:
            qb.count(True)
        if filters:
            qb.where(**filters)
        resp = qb.execute(fetch_all=fetch_all, include_count=True if include_count else None)
        return resp if return_response else (resp.df if as_dataframe else resp.data)

    # Métodos dedicados para los 19 endpoints oficiales y sus alias cortos
    def ipi_manufacturero(self, **kw: Any) -> Any: return self.get("ipi_manufacturero", **kw)
    def ipi_minero(self, **kw: Any) -> Any: return self.get("ipi_minero", **kw)
    def estimaciones_poblacion_departamento_2022_2035(self, **kw: Any) -> Any: return self.get("estimaciones_poblacion_departamento_2022_2035", **kw)
    def proyecciones_poblacion_jurisdiccion_2022_2040(self, **kw: Any) -> Any: return self.get("proyecciones_poblacion_jurisdiccion_2022_2040", **kw)
    def proyecciones_poblacion_nacional_2022_2040(self, **kw: Any) -> Any: return self.get("proyecciones_poblacion_nacional_2022_2040", **kw)
    def ipc_nacional(self, **kw: Any) -> Any: return self.get("ipc_nacional", **kw)
    def valorizacion_canastas_cba_cbt(self, **kw: Any) -> Any: return self.get("valorizacion_canastas_cba_cbt", **kw)
    def indice_salarios(self, **kw: Any) -> Any: return self.get("indice_salarios", **kw)
    def icc_precios_construccion(self, **kw: Any) -> Any: return self.get("icc_precios_construccion", **kw)
    def redeterminacion_precios_contratos_obras_publicas(self, **kw: Any) -> Any: return self.get("redeterminacion_precios_contratos_obras_publicas", **kw)
    def sipm_precios_mayoristas(self, **kw: Any) -> Any: return self.get("sipm_precios_mayoristas", **kw)
    def estimador_mensual_de_actividad_economica_nivel_general(self, **kw: Any) -> Any: return self.get("estimador-mensual-de-actividad-economica-nivel-general", **kw)
    def estimador_mensual_de_actividad_economica_sectores(self, **kw: Any) -> Any: return self.get("estimador-mensual-de-actividad-economica-sectores", **kw)
    def pobreza_eph(self, **kw: Any) -> Any: return self.get("pobreza_eph", **kw)
    def mercado_trabajo_eph(self, **kw: Any) -> Any: return self.get("mercado_trabajo_eph", **kw)
    def canasta_crianza(self, **kw: Any) -> Any: return self.get("canasta-crianza", **kw)
    def comercio_exterior_nomenclaturas(self, **kw: Any) -> Any: return self.get("comercio_exterior_nomenclaturas", **kw)
    def comercio_exterior_exportacion_bienes(self, **kw: Any) -> Any: return self.get("comercio_exterior_exportacion_bienes", **kw)
    def comercio_exterior_importacion_bienes(self, **kw: Any) -> Any: return self.get("comercio_exterior_importacion_bienes", **kw)

    # Alias cortos
    poblacion_departamento = estimaciones_poblacion_departamento_2022_2035
    poblacion_jurisdiccion = proyecciones_poblacion_jurisdiccion_2022_2040
    poblacion_nacional = proyecciones_poblacion_nacional_2022_2040
    ipc = ipc_nacional
    canastas_cba_cbt = valorizacion_canastas_cba_cbt
    salarios = indice_salarios
    icc = icc_precios_construccion
    obras_publicas = redeterminacion_precios_contratos_obras_publicas
    sipm = precios_mayoristas = sipm_precios_mayoristas
    emae = emae_nivel_general = estimador_mensual_de_actividad_economica_nivel_general
    emae_sectores = estimador_mensual_de_actividad_economica_sectores
    pobreza = pobreza_eph
    mercado_trabajo = mercado_trabajo_eph
    comex_nomenclaturas = comercio_exterior_nomenclaturas
    exportaciones = comex_exportaciones = comercio_exterior_exportacion_bienes
    importaciones = comex_importaciones = comercio_exterior_importacion_bienes

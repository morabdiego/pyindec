"""Excepciones personalizadas para pyindec."""

from __future__ import annotations

from typing import Any


class IndecError(Exception):
    """Excepción base de pyindec."""


class IndecAPIError(IndecError):
    """Error devuelto por la API del INDEC (PostgREST / HTTP)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: str | None = None,
        hint: str | None = None,
        payload: Any = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.hint = hint
        self.payload = payload
        parts = [
            message,
            f"[code={code}]" if code else "",
            f"(HTTP {status_code})" if status_code else "",
            f"Detalles: {details}" if details else "",
            f"Sugerencia: {hint}" if hint else "",
        ]
        super().__init__(" ".join(p for p in parts if p))


class IndecFilterError(IndecAPIError):
    """Error 400: Filtro mal formado, operador inválido o columna inexistente."""


class IndecAuthError(IndecAPIError):
    """Error 401: Token JWT faltante o inválido."""


class IndecPermissionError(IndecAPIError):
    """Error 403: Sin permisos sobre el recurso."""


class IndecNotFoundError(IndecAPIError):
    """Error 404: Endpoint o recurso no encontrado."""


class IndecRateLimitError(IndecAPIError):
    """Error 429: Límite de peticiones excedido."""

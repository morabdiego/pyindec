"""Modelos de datos, respuestas y signos convencionales del INDEC."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

import pandas as pd

SIGNOS_CONVENCIONALES: dict[str, str] = {
    "*": "Dato provisorio",
    "**": "Dato preliminar",
    "e": "Dato estimado por extrapolación, proyección",
    "i": "Dato estimado por imputación",
    "u": "Dato de calidad inferior al estándar",
    "-": "Cero absoluto",
    ".": "Dato no registrado",
    "...": "Dato no disponible a la fecha de presentación de los resultados",
    "///": "Dato que no corresponde presentar",
    "s": "Dato confidencial por aplicación de las reglas del secreto estadístico",
}

_RANGE_RE = re.compile(r"^(?:(?:items|rows)\s+)?(?:(\d+)-(\d+)|\*)/(\d+|\*)$")


def explain_sign(sign: str) -> str | None:
    """Devuelve el significado oficial de un signo convencional del INDEC."""
    return SIGNOS_CONVENCIONALES.get(sign.strip())


def parse_content_range(value: str | None) -> tuple[int | None, int | None, int | None]:
    """Parsea el header ``Content-Range`` (ej. ``0-999/103545`` o ``*/0``)."""
    if not value or not (m := _RANGE_RE.match(value.strip())):
        return None, None, None
    s, e, t = m.groups()
    return (int(s) if s else None, int(e) if e else None, int(t) if t and t != "*" else None)


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str = "string"
    nullable: bool = True
    description: str = ""
    is_key: bool = False


@dataclass(frozen=True)
class EndpointInfo:
    path: str
    name: str
    aliases: tuple[str, ...]
    summary: str
    direction: str
    pagination_key: tuple[str, ...]
    columns: tuple[ColumnInfo, ...]
    description: str = ""
    methodology_url: str | None = None

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "columna": c.name,
                    "tipo": c.type,
                    "nullable": c.nullable,
                    "es_clave_paginacion": c.is_key,
                    "descripcion": c.description,
                }
                for c in self.columns
            ]
        )


@dataclass
class IndecResponse:
    data: list[dict[str, Any]] = field(default_factory=list)
    endpoint: str = ""
    status_code: int = 200
    content_range: str | None = None
    range_start: int | None = None
    range_end: int | None = None
    total_count: int | None = None
    pages_fetched: int = 1

    @property
    def df(self) -> pd.DataFrame:
        return pd.DataFrame(self.data)

    to_df = df.fget  # type: ignore[assignment]

    def __len__(self) -> int:
        return len(self.data)

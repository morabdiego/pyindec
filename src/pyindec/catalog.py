"""Catálogo compacto de los 19 endpoints oficiales de la API del INDEC."""

from __future__ import annotations

import pandas as pd

from .exceptions import IndecNotFoundError
from .models import ColumnInfo, EndpointInfo

# Formato de columnas: nombre:s (string), nombre:n (number), sufijo "?" indica nullable
_RAW_CATALOG: tuple[tuple[str, str, str, tuple[str, ...], tuple[str, ...], str | None, str], ...] = (
    ("ipi_manufacturero", "Índice de producción industrial manufacturero", "Dirección de Estadísticas Mineras, Manufactureras, Energéticas y de la Construcción", ("manufacturero",), ("periodo", "indicador", "cuadro_web", "codigo_CLaNAE_2004", "descripcion", "serie", "tipo_de_indicador"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_manufacturero_2019.pdf", "periodo:s anio:n mes:n indicador:s cuadro_web:s codigo_CLaNAE_2004:s descripcion:s serie:s tipo_de_indicador:s unidad_de_medida:s valor:n?"),
    ("ipi_minero", "Índice de producción industrial minero", "Dirección de Estadísticas Mineras, Manufactureras, Energéticas y de la Construcción", ("minero",), ("periodo", "anio", "mes", "indicador", "cuadro_web", "codigo_ClaNAE_2010", "codigo_CPC_2_1", "serie", "descripcion", "tipo_de_indicador", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_minero.pdf", "periodo:s anio:n mes:n indicador:s cuadro_web:s codigo_ClaNAE_2010:s codigo_CPC_2_1:s serie:s descripcion:s tipo_de_indicador:s unidad_de_medida:s valor:n?"),
    ("estimaciones_poblacion_departamento_2022_2035", "Estimaciones de población por departamento y sexo", "Dirección de Estadísticas Poblacionales", ("poblacion_departamento", "estimaciones_poblacion_departamento"), ("departamento_cod", "sexo_cod", "fecha"), "https://www.indec.gob.ar/ftp/cuadros/publicaciones/estimaciones_departamentos_2022_2035.pdf", "jurisdiccion_cod:s jurisdiccion_nom:s departamento_cod:s departamento_nom:s rmba:s sexo_cod:s sexo_nom:s poblacion:n? fecha:s"),
    ("proyecciones_poblacion_jurisdiccion_2022_2040", "Proyecciones de población por jurisdicción, sexo y edad", "Dirección de Estadísticas Poblacionales", ("poblacion_jurisdiccion", "proyecciones_poblacion_jurisdiccion"), ("jurisdiccion_cod", "sexo_cod", "edad_cod", "fecha"), "https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_jurisdicciones_2022_2040.pdf", "jurisdiccion_cod:s jurisdiccion_nom:s sexo_cod:s sexo_nom:s edad_cod:s edad_nom:s poblacion:n? fecha:s"),
    ("proyecciones_poblacion_nacional_2022_2040", "Proyecciones nacionales de población por sexo y edad", "Dirección de Estadísticas Poblacionales", ("poblacion_nacional", "proyecciones_poblacion_nacional"), ("edad", "sexo_cod", "fecha"), "https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_nacionales_2022_2040.pdf", "edad:n sexo_cod:s sexo_nom:s poblacion:n? fecha:n"),
    ("ipc_nacional", "Índice de Precios al Consumidor (IPC)", "Dirección de Índices de Precios de Consumo", ("ipc", "inflacion"), ("clasificador", "nivel", "codigo", "descripcion", "periodo", "anio", "mes", "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", "region", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipc_nacional_2019.pdf", "clasificador:s nivel:s codigo:s descripcion:s periodo:s anio:n mes:n indicador:s tipo_de_indicador:s tipo_de_indicador_descripcion:s region:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("valorizacion_canastas_cba_cbt", "Valorización de las canastas básicas (CBA y CBT)", "Dirección de Índices de Precios de Consumo", ("canastas_cba_cbt", "cba_cbt"), ("clasificador", "nivel", "codigo", "descripcion", "periodo", "anio", "mes", "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", "region", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/sociedad/EPH_metodologia_22_pobreza.pdf", "clasificador:s nivel:s codigo:s descripcion:s periodo:s anio:n mes:n indicador:s tipo_de_indicador:s tipo_de_indicador_descripcion:s region:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("indice_salarios", "Índice de salarios", "Dirección de Índices de Precios de la Producción", ("salarios",), ("clasificador", "nivel", "codigo", "descripcion", "periodo", "anio", "mes", "indicador", "tipo_de_indicador", "tipo_de_indicador_descripcion", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/sociedad/cvs_metodologia.pdf", "clasificador:s nivel:s codigo:s descripcion:s periodo:s anio:n mes:n indicador:s tipo_de_indicador:s tipo_de_indicador_descripcion:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("icc_precios_construccion", "Índice del costo de la construcción", "Dirección de Índices de Precios de la Producción", ("icc", "costo_construccion"), ("indicador", "codigo_apertura", "codigo_CPC_1", "clasificador", "nivel", "descripcion", "periodo", "anio", "mes", "tipo_de_indicador", "tipo_de_indicador_descripcion", "region", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_icc.pdf", "indicador:s codigo_apertura:s codigo_CPC_1:s clasificador:s nivel:s descripcion:s periodo:s anio:n mes:n tipo_de_indicador:s tipo_de_indicador_descripcion:s region:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("redeterminacion_precios_contratos_obras_publicas", "Redeterminación de precios de obras públicas", "Dirección de Índices de Precios de la Producción", ("obras_publicas", "redeterminacion_obras_publicas"), ("indicador", "operativo", "inciso", "descripcion_inciso", "codigo_apertura", "clasificador", "nivel", "descripcion", "origen", "periodo", "anio", "mes", "tipo_de_indicador", "tipo_de_indicador_descripcion", "region", "unidad_de_medida"), "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-112", "indicador:s operativo:s inciso:s descripcion_inciso:s codigo_apertura:s codigo_CPC_1:s? codigo_CIUU_3:s? clasificador:s nivel:s descripcion:s origen:s periodo:s anio:n mes:n tipo_de_indicador:s tipo_de_indicador_descripcion:s region:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("sipm_precios_mayoristas", "Sistema de índices de precios mayoristas", "Dirección de Índices de Precios de la Producción", ("sipm", "precios_mayoristas"), ("operativo", "indicador", "clasificador", "nivel", "codigo_apertura", "descripcion", "periodo", "anio", "mes", "tipo_de_indicador", "tipo_de_indicador_descripcion", "region", "unidad_de_medida"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia1_8_sipm.pdf", "operativo:s indicador:s clasificador:s nivel:s codigo_apertura:s descripcion:s periodo:s anio:n mes:n tipo_de_indicador:s tipo_de_indicador_descripcion:s region:s unidad_de_medida:s valor:n? observaciones:s?"),
    ("estimador-mensual-de-actividad-economica-nivel-general", "Estimador mensual de actividad económica. Nivel general", "Dirección Nacional de Cuentas Nacionales", ("emae_nivel_general", "emae"), ("tipo_de_indicador_descripcion", "anio", "mes", "periodo", "tipo_de_indicador"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf", "tipo_de_indicador_descripcion:s anio:n mes:n periodo:s tipo_de_indicador:s valor:n? observaciones:s?"),
    ("estimador-mensual-de-actividad-economica-sectores", "Estimador mensual de actividad económica. Sectores", "Dirección Nacional de Cuentas Nacionales", ("emae_sectores",), ("anio", "mes", "codigo", "descripcion", "periodo", "tipo_de_indicador"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf", "anio:n mes:n codigo:s descripcion:s periodo:s tipo_de_indicador:s valor:n? observaciones:s?"),
    ("pobreza_eph", "Incidencia de la pobreza y la indigencia (EPH)", "Dirección Nacional de Estadísticas de Condiciones de Vida", ("pobreza", "indigencia"), ("area_geografica_nom", "periodo"), "https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf", "area_geografica_nom:s area_geografica_cod:n? periodo:s anio:n semestre:n tasa_pobreza_hogares:n? tasa_pobreza_personas:n? tasa_indigencia_hogares:n? tasa_indigencia_personas:n? observaciones:s?"),
    ("mercado_trabajo_eph", "Principales tasas del mercado de trabajo (EPH)", "Dirección Nacional de Estadísticas de Condiciones de Vida", ("mercado_trabajo", "desocupacion", "empleo_eph"), ("area_geografica_nom", "periodo"), "https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf", "area_geografica_nom:s area_geografica_cod:n? periodo:s anio:n trimestre:n tasa_de_actividad:n? tasa_de_empleo:n? tasa_de_empleo_formal:n? tasa_de_empleo_informal:n? tasa_de_desocupacion:n? tasa_de_ocupacion_demandante:n? tasa_de_subocupacion:n? tasa_de_subocupacion_demandante:n? tasa_de_subocupacion_no_demandante:n? observaciones:s?"),
    ("canasta-crianza", "Valorización de la canasta de crianza", "Dirección Nacional de Estadísticas de Condiciones de Vida", ("crianza",), ("Periodo",), "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-43-173", "anio:n Mes:n Periodo:s bys_men1:n? cuid_men1:n? tot_men1:n? bys_1a3:n? cuid_1a3:n? tot_1a3:n? bys_4a5:n? cuid_4a5:n? tot_4a5:n? bys_6a12:n? cuid_6a12:n? tot_6a12:n?"),
    ("comercio_exterior_nomenclaturas", "Códigos y denominaciones de comercio exterior", "Dirección Nacional de Estadísticas del Sector Externo y Cuentas Internacionales", ("comex_nomenclaturas", "nomenclaturas_comex"), ("nombre_columna", "codigo"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf", "nombre_columna:s codigo:s codigo_descripcion:s"),
    ("comercio_exterior_exportacion_bienes", "Exportaciones de bienes por rubros y países de destino", "Dirección Nacional de Estadísticas del Sector Externo y Cuentas Internacionales", ("exportaciones", "comex_exportaciones"), ("Anio", "Mes", "Periodo", "rubro_cod", "subrubro_cod", "pais_cod"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf", "Anio:n Mes:n Periodo:s rubro_cod:s subrubro_cod:s pais_cod:s valor_FOB:n? Peso_Neto:n?"),
    ("comercio_exterior_importacion_bienes", "Importaciones de bienes por uso económico y país de origen", "Dirección Nacional de Estadísticas del Sector Externo y Cuentas Internacionales", ("importaciones", "comex_importaciones"), ("Anio", "Mes", "Periodo", "uso_economico_cod", "gce_cod", "pais_cod"), "https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf", "Anio:n Mes:n Periodo:s uso_economico_cod:s gce_cod:s pais_cod:s valor_CIF:n? peso_neto:n?"),
)

_TYPE_MAP = {"s": "string", "n": "number"}


def _parse_col(token: str, keys: set[str]) -> ColumnInfo:
    name, spec = token.split(":")
    return ColumnInfo(
        name=name,
        type=_TYPE_MAP[spec[0]],
        nullable=spec.endswith("?"),
        is_key=name in keys,
    )


ENDPOINTS: dict[str, EndpointInfo] = {}
_ALIAS_MAP: dict[str, str] = {}

for _raw, _summary, _dir, _aliases, _keys, _url, _cols_str in _RAW_CATALOG:
    _py_name = _raw.replace("-", "_")
    _all_aliases = tuple(dict.fromkeys([_raw, _py_name, *_aliases]))
    _key_set = set(_keys)
    ENDPOINTS[_raw] = EndpointInfo(
        path=f"/{_raw}",
        name=_py_name,
        aliases=_all_aliases,
        summary=_summary,
        direction=_dir,
        pagination_key=_keys,
        columns=tuple(_parse_col(c, _key_set) for c in _cols_str.split()),
        methodology_url=_url,
    )
    for _a in (_raw, f"/{_raw}", _py_name, *_all_aliases):
        _ALIAS_MAP[_a.lower()] = _raw


def resolve_endpoint(endpoint: str) -> EndpointInfo | None:
    """Resuelve un nombre, ruta o alias al ``EndpointInfo`` oficial."""
    clean = endpoint.strip().lstrip("/").lower().removeprefix("v1/")
    key = _ALIAS_MAP.get(clean) or _ALIAS_MAP.get(clean.replace("_", "-"))
    return ENDPOINTS.get(key) if key else None


def list_endpoints(*, as_dataframe: bool = True) -> pd.DataFrame | list[EndpointInfo]:
    """Lista los 19 endpoints disponibles en el Catálogo API-INDEC."""
    items = list(ENDPOINTS.values())
    if not as_dataframe:
        return items
    return pd.DataFrame(
        [
            {
                "endpoint": ep.path.lstrip("/"),
                "metodo_cliente": ep.name,
                "alias": ", ".join(a for a in ep.aliases if a not in (ep.name, ep.path.lstrip("/"))),
                "resumen": ep.summary,
                "direccion": ep.direction,
                "columnas": len(ep.columns),
                "clave_paginacion": ",".join(ep.pagination_key),
                "metodologia_url": ep.methodology_url,
            }
            for ep in items
        ]
    )


def describe_endpoint(endpoint: str, *, as_dataframe: bool = True) -> pd.DataFrame | EndpointInfo:
    """Devuelve el detalle de columnas y tipos de un endpoint por nombre o alias."""
    if not (info := resolve_endpoint(endpoint)):
        raise IndecNotFoundError(f"Endpoint desconocido: {endpoint!r}", status_code=404)
    return info.to_dataframe() if as_dataframe else info

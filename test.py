"""Script de prueba en vivo contra la API del INDEC usando la API_KEY de .env."""

from __future__ import annotations

import pandas as pd

from pyindec import (
    F,
    IndecAPIError,
    IndecClient,
    IndecFilterError,
    describe_endpoint,
    explain_sign,
    list_endpoints,
)


def separator(title: str) -> None:
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")


def main() -> None:
    pd.set_option("display.max_columns", 10)
    pd.set_option("display.width", 120)

    # 1. Inicializar cliente (toma automáticamente API_KEY / INDEC_API_TOKEN desde .env)
    client = IndecClient()
    print(f"✅ Cliente inicializado contra: {client.base_url}")
    print(f"🔑 Token detectado desde .env: {'Sí (' + client.token[:10] + '...)' if client.token else 'No'}")

    # 2. Catálogo offline: listar los 19 endpoints disponibles
    separator("1. Catálogo de los 19 Endpoints Oficiales (list_endpoints)")
    df_endpoints = list_endpoints()
    print(df_endpoints[["endpoint", "metodo_cliente", "alias", "columnas"]].to_string(index=False))

    # 3. Describir columnas de un endpoint específico
    separator("2. Esquema y columnas del endpoint 'ipc_nacional' (describe_endpoint)")
    df_schema_ipc = describe_endpoint("ipc")
    print(df_schema_ipc[["columna", "tipo", "nullable", "es_clave_paginacion"]].to_string(index=False))

    # 4. Consulta directa con método dedicado + filtros F (IPC Nacional)
    separator("3. Consulta directa: client.ipc_nacional(anio=F.gte(2024), limit=5)")
    df_ipc = client.ipc_nacional(
        anio=F.gte(2024),
        order="periodo.desc",
        limit=5,
    )
    print(f"Filas recibidas: {len(df_ipc)}")
    print(df_ipc[["periodo", "region", "descripcion", "tipo_de_indicador", "valor", "observaciones"]])

    # 5. Consulta con QueryBuilder encadenable + conteo exacto de filas (Content-Range)
    separator("4. QueryBuilder fluido + conteo exacto (Prefer: count=exact) en EMAE")
    resp_emae = (
        client.query("emae")
        .select("periodo", "anio", "mes", "tipo_de_indicador", "valor")
        .gte("anio", 2023)
        .order("periodo", desc=True)
        .limit(5)
        .execute(include_count=True)
    )
    print(f"HTTP Status: {resp_emae.status_code} | Content-Range: {resp_emae.content_range}")
    print(f"Total de filas en el servidor para anio >= 2023: {resp_emae.total_count}")
    print(resp_emae.df)

    # 6. Consulta de Pobreza e Indigencia (EPH) y Mercado de Trabajo
    separator("5. Condiciones de Vida: Pobreza (EPH) y Canasta de Crianza")
    df_pobreza = client.pobreza(anio=F.gte(2023), order="periodo.desc", limit=5)
    print("-> Pobreza EPH:")
    print(
        df_pobreza[
            [
                "periodo",
                "area_geografica_nom",
                "tasa_pobreza_hogares",
                "tasa_pobreza_personas",
                "tasa_indigencia_personas",
            ]
        ]
    )

    df_crianza = client.canasta_crianza(order="Periodo.desc", limit=3)
    print("\n-> Canasta de Crianza (últimos 3 períodos):")
    print(df_crianza[["Periodo", "tot_men1", "tot_1a3", "tot_4a5", "tot_6a12"]])

    # 7. Comercio Exterior (probando normalización automática de mayúsculas/minúsculas)
    separator("6. Comercio Exterior: Nomenclaturas y Exportaciones")
    total_exportaciones_2024 = client.query("exportaciones").eq("anio", 2024).count_rows()
    print(f"Total de registros de exportaciones en 2024 (count_rows): {total_exportaciones_2024}")

    df_expo = (
        client.query("exportaciones")
        .select("periodo", "pais_cod", "rubro_cod", "valor_FOB", "peso_neto")
        .eq("anio", 2024)
        .gt("valor_FOB", 10_000_000)
        .order("valor_FOB", desc=True)
        .limit(5)
        .df()
    )
    print(df_expo)

    # 8. Prueba de manejo de errores de la API (filtro a una columna inexistente -> HTTP 400)
    separator("7. Prueba de captura de errores PostgREST (IndecFilterError HTTP 400)")
    try:
        client.query("ipc_nacional").eq("columna_que_no_existe", 123).df()
    except IndecFilterError as err:
        print("✅ Error HTTP 400 capturado correctamente como IndecFilterError:")
        print(f"   - status_code: {err.status_code}")
        print(f"   - code:        {err.code}")
        print(f"   - message:     {err.message}")
        print(f"   - details:     {err.details}")
        print(f"   - hint:        {err.hint}")
    except IndecAPIError as err:
        print(f"Error general de API: {err}")

    # 9. Signos convencionales del INDEC
    separator("8. Signos convencionales del INDEC")
    for signo in ("*", "e", "s", "..."):
        print(f"  Signo {signo!r:5} -> {explain_sign(signo)}")


if __name__ == "__main__":
    main()

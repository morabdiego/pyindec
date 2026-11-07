# PyINDEC

Desarrollado por [@morabdiego](https://github.com/morabdiego) · Contacto: [morabdiego@gmail.com](mailto:morabdiego@gmail.com)

Cliente en Python para consultar la [API de datos del INDEC](https://api.indec.gob.ar/docs).

La API del INDEC está montada sobre PostgREST: exige pasar operadores en la URL (`?anio=gte.2024`), devuelve un máximo de 1.000 filas por consulta y requiere ordenar por la clave compuesta de cada tabla para paginar sin perder ni duplicar registros. `pyindec` resuelve esos detalles por detrás y devuelve los resultados directamente en un `DataFrame` de pandas (o en listas de diccionarios).

## Instalación

```bash
pip install pyindec
```

## Configuración del token

La API requiere un token JWT gratuito que se genera desde el perfil de usuario en [api.indec.gob.ar](https://api.indec.gob.ar).

Podés pasarlo al instanciar el cliente o definir la variable `INDEC_API_TOKEN` (también reconoce `API_KEY`) en el entorno o en un archivo `.env` local:

```python
from pyindec import IndecClient

client = IndecClient()  # lee INDEC_API_TOKEN / API_KEY del entorno o .env
# o explícitamente:
# client = IndecClient(token="eyJhbG...")
```

## Uso básico

Podés consultar cada endpoint mediante su método directo o armar la consulta encadenando filtros:

```python
from pyindec import IndecClient, F

client = IndecClient()

# IPC nacional desde 2024 para GBA y Total Nacional
df_ipc = client.ipc(
    anio=F.gte(2024),
    region=["GBA", "Nacional"],
    order="periodo.desc",
    limit=100,
)

# Serie completa del EMAE paginando automáticamente de a 1.000 filas
df_emae = client.emae(fetch_all=True)

# Si preferís list[dict] en lugar de DataFrame:
datos_pobreza = client.pobreza(anio=2024, as_dataframe=False)
```

### Consultas encadenadas (QueryBuilder)

Para consultas con múltiples condiciones, selección de columnas o rangos:

```python
df = (
    client.query("ipc")
    .select("periodo", "region", "descripcion", "valor")
    .eq("region", "GBA")
    .between("anio", 2023, 2024)
    .ilike("descripcion", "*alimentos*")
    .order("periodo", desc=True)
    .df()
)

# Descargar todas las páginas que cumplan el filtro
df_expo = client.query("exportaciones").eq("anio", 2024).all()

# Consultar solo la cantidad total de registros (header Prefer: count=exact)
total = client.query("exportaciones").eq("anio", 2024).count_rows()

# Iterar página por página sin cargar todo en memoria
for pagina_df in client.query("sipm").eq("anio", 2024).iter_pages():
    procesar(pagina_df)
```

> Nota: algunos endpoints de la API usan nombres de columna con mayúscula inicial (`Anio`, `Mes`, `Periodo`, `Peso_Neto` en comercio exterior o canasta de crianza) y otros en minúscula (`anio`, `mes`, `periodo`). `pyindec` normaliza los nombres según la tabla consultada, por lo que podés escribir `anio` o `periodo` en minúscula en todos los casos.

## Filtros disponibles

En los métodos del cliente podés pasar valores directos, listas, objetos `F` o strings con sintaxis PostgREST (`"gte.2024"`):

| Expresión | Equivalente PostgREST | Uso |
|---|---|---|
| `valor` / `F.eq(valor)` | `eq.valor` | Igual a |
| `F.neq(valor)` | `neq.valor` | Distinto de |
| `F.gt(valor)` / `F.gte(valor)` | `gt.valor` / `gte.valor` | Mayor / Mayor o igual |
| `F.lt(valor)` / `F.lte(valor)` | `lt.valor` / `lte.valor` | Menor / Menor o igual |
| `F.between(a, b)` | `gte.a` y `lte.b` | Rango inclusivo sobre la misma columna |
| `[a, b]` / `F.in_([a, b])` | `in.(a,b)` | Valor dentro de una lista |
| `F.like("*txt*")` / `F.ilike("*txt*")` | `like.*txt*` / `ilike.*txt*` | Coincidencia de texto (con o sin mayúsculas) |
| `F.contains("txt")` | `ilike.*txt*` | Contiene subcadena |
| `F.is_(None)` / `F.is_null()` | `is.null` | Nulos o booleanos (`True` / `False`) |

## Endpoints soportados

Para inspeccionar desde código los endpoints y las columnas de cada tabla sin hacer llamadas a la red:

```python
from pyindec import list_endpoints, describe_endpoint, explain_sign

list_endpoints()              # DataFrame con los 19 endpoints y sus claves de paginación
describe_endpoint("emae")     # DataFrame con las columnas y tipos del endpoint
explain_sign("*")             # 'Dato provisorio'
```

| Método / Alias en `IndecClient` | Endpoint en `/v1` | Descripción |
|---|---|---|
| `client.ipc()` / `client.ipc_nacional()` | `/ipc_nacional` | Índice de Precios al Consumidor (IPC) |
| `client.canastas_cba_cbt()` | `/valorizacion_canastas_cba_cbt` | Canasta Básica Alimentaria y Total (CBA y CBT) |
| `client.emae()` / `client.emae_nivel_general()` | `/estimador-mensual-de-actividad-economica-nivel-general` | EMAE - Nivel general |
| `client.emae_sectores()` | `/estimador-mensual-de-actividad-economica-sectores` | EMAE - Apertura por sectores |
| `client.pobreza()` / `client.pobreza_eph()` | `/pobreza_eph` | Incidencia de la pobreza y la indigencia (EPH) |
| `client.mercado_trabajo()` | `/mercado_trabajo_eph` | Tasas del mercado de trabajo (EPH) |
| `client.canasta_crianza()` | `/canasta-crianza` | Valorización de la canasta de crianza |
| `client.salarios()` / `client.indice_salarios()` | `/indice_salarios` | Índice de salarios |
| `client.icc()` / `client.icc_precios_construccion()` | `/icc_precios_construccion` | Índice del costo de la construcción (ICC) |
| `client.sipm()` / `client.precios_mayoristas()` | `/sipm_precios_mayoristas` | Sistema de índices de precios mayoristas (SIPM) |
| `client.obras_publicas()` | `/redeterminacion_precios_contratos_obras_publicas` | Redeterminación de precios de obras públicas |
| `client.ipi_manufacturero()` | `/ipi_manufacturero` | Índice de producción industrial manufacturero |
| `client.ipi_minero()` | `/ipi_minero` | Índice de producción industrial minero |
| `client.exportaciones()` | `/comercio_exterior_exportacion_bienes` | Exportaciones de bienes por rubro y país |
| `client.importaciones()` | `/comercio_exterior_importacion_bienes` | Importaciones de bienes por uso económico y país |
| `client.comex_nomenclaturas()` | `/comercio_exterior_nomenclaturas` | Nomenclaturas y códigos de comercio exterior |
| `client.poblacion_nacional()` | `/proyecciones_poblacion_nacional_2022_2040` | Proyecciones nacionales de población (2022-2040) |
| `client.poblacion_jurisdiccion()` | `/proyecciones_poblacion_jurisdiccion_2022_2040` | Proyecciones de población por jurisdicción (2022-2040) |
| `client.poblacion_departamento()` | `/estimaciones_poblacion_departamento_2022_2035` | Estimaciones de población por departamento (2022-2035) |

## Manejo de errores

Los errores de la API lanzan subclases de `IndecAPIError` con el detalle devuelto por PostgREST (`status_code`, `code`, `message`, `details`, `hint`):

- `IndecFilterError` (HTTP 400): columna inexistente o filtro mal armado.
- `IndecAuthError` (HTTP 401): token faltante o inválido.
- `IndecPermissionError` (HTTP 403): sin permisos sobre el recurso.
- `IndecNotFoundError` (HTTP 404): endpoint inexistente.
- `IndecRateLimitError` (HTTP 429): límite de consultas superado.

## Autor y contacto

Creado y mantenido por **Diego Mora** ([@morabdiego](https://github.com/morabdiego)).
Consultas, sugerencias o contacto: [morabdiego@gmail.com](mailto:morabdiego@gmail.com).

## Licencia

MIT

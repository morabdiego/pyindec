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

## Endpoints soportados, códigos y metodologías del INDEC

Podés consultar la guía detallada de cada método, sus columnas, clasificadores y todos los códigos internos del INDEC en **[docs/METODOS_Y_CODIGOS.md](https://github.com/morabdiego/pyindec/blob/main/docs/METODOS_Y_CODIGOS.md)**.

También podés inspeccionar desde código los endpoints, las columnas de cada tabla y los links metodológicos sin hacer llamadas a la red:

```python
from pyindec import list_endpoints, describe_endpoint, explain_sign

list_endpoints()              # DataFrame con los 19 endpoints, claves de paginación y URL de metodología
describe_endpoint("emae")     # DataFrame con las columnas y tipos del endpoint
explain_sign("*")             # 'Dato provisorio'
```

| Método / Alias en `IndecClient` | Endpoint en `/v1` | Códigos principales del INDEC | Metodología / Fuente oficial |
|---|---|---|---|
| `client.ipc()` / `client.ipc_nacional()` | `/ipc_nacional` | `region`: `"Nacional"`, `"GBA"`, `"Pampeana"`, `"Cuyo"`, `"Noreste"`, `"Noroeste"`, `"Patagonia"`<br>`codigo`: `"0"` (Nivel general), `"N"` (Núcleo), `"E"` (Estacional), `"R"` (Regulados), `"B"` (Bienes), `"S"` (Servicios), `"01"` a `"12"` (Divisiones COICOP)<br>`tipo_de_indicador`: `"v_m"`, `"v_ia"`, `"v_acum"`, `"Indice"` | [Metodología N° 32 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipc_nacional_2019.pdf) |
| `client.canastas_cba_cbt()` | `/valorizacion_canastas_cba_cbt` | `codigo`: `"CBA"`, `"CBT"`, `"ICE"`, `"CBA H1..H3"`, `"CBT H1..H3"`<br>`tipo_de_indicador`: `"CBA"`, `"CBT"`, `"Hogar 1..3"`, `"v_m"`, `"v_ia"` | [Metodología N° 22 (PDF)](https://www.indec.gob.ar/ftp/cuadros/sociedad/EPH_metodologia_22_pobreza.pdf) |
| `client.emae()` / `client.emae_nivel_general()` | `/estimador-mensual-de-actividad-economica-nivel-general` | `tipo_de_indicador`: `"Índice base 2004=100"`, `"Variación porcentual"`<br>`tipo_de_indicador_descripcion`: `"Índice serie original"`, `"Índice serie desestacionalizada"`, `"Var % interanual serie original"`, etc. | [Metodología N° 20 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf) |
| `client.emae_sectores()` | `/estimador-mensual-de-actividad-economica-sectores` | `codigo` (ClaNAE 2004): `"A"` Agro, `"B"` Pesca, `"C"` Minas, `"D"` Industria, `"E"` EGA, `"F"` Construcción, `"G"` Comercio, `"H"` Hoteles/Rest., `"I"` Transporte, `"J"` Finanzas, `"K"` Inmob., `"L"` Adm. Pública, `"M"` Enseñanza, `"N"` Salud, `"O"` Otros, `"T_S"` Impuestos netos | [Metodología N° 20 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf) |
| `client.pobreza()` / `client.pobreza_eph()` | `/pobreza_eph` | `area_geografica_nom`: `"T_31_A"` (Total 31 aglomerados)<br>`periodo`: `"AAAANS"` (ej. `"20251S"`, `"20252S"`), `semestre`: `1`, `2` | [Metodología EPH (PDF)](https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf) · [Bases EPH](https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos) |
| `client.mercado_trabajo()` | `/mercado_trabajo_eph` | `area_geografica_nom`: `"T_31_A"`<br>`periodo`: `"AAAANT"` (ej. `"20251T"`..`"20254T"`), `trimestre`: `1`..`4` | [Metodología EPH (PDF)](https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf) · [Informes EPH](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58) |
| `client.canasta_crianza()` | `/canasta-crianza` | Columnas por tramo: `<1 año` (`bys_men1`, `cuid_men1`, `tot_men1`), `1 a 3` (`*_1a3`), `4 a 5` (`*_4a5`), `6 a 12` (`*_6a12`) | [Canasta de crianza INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-43-173) |
| `client.salarios()` / `client.indice_salarios()` | `/indice_salarios` | `codigo`: `"0"` (Nivel general), `"100"` (Total registrado), `"110"` (Privado registrado), `"120"` (Público), `"121"` (Público nac.), `"122"` (Público prov.), `"200"` (Privado no registrado) | [Metodología N° 16 (PDF)](https://www.indec.gob.ar/ftp/cuadros/sociedad/cvs_metodologia.pdf) |
| `client.icc()` / `client.icc_precios_construccion()` | `/icc_precios_construccion` | `codigo_apertura`: `"0"` (Nivel general), `"01"` (Materiales), `"02"` (Mano de obra), `"03"` (Gastos generales), `"IT-01"`..`"IT-11"` (Ítems de obra), más aperturas `codigo_CPC_1` | [Metodología N° 9 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_icc.pdf) |
| `client.sipm()` / `client.precios_mayoristas()` | `/sipm_precios_mayoristas` | `indicador`: `"IPIM"`, `"IPIB"`, `"IPP"`<br>`clasificador`: `"SIPM 93"` y `"CIIU3"` (`codigo_apertura`: `"A"`..`"E"` y CIIU 4 dígitos) | [Metodología N° 8 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia1_8_sipm.pdf) |
| `client.obras_publicas()` | `/redeterminacion_precios_contratos_obras_publicas` | `operativo`: `"ICC"`, `"IPIB"`<br>`inciso` (Art. 15 Dec. 1295/2002): `"a"` a `"x"` | [Redeterminación Obra Pública](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-112) |
| `client.ipi_manufacturero()` | `/ipi_manufacturero` | `serie`: `"Serie original"`, `"Serie desestacionalizada"`, `"Serie tendencia-ciclo"`<br>`codigo_CLaNAE_2004`: divisiones `"15"` a `"36"` y subclases a 5 dígitos | [Metodología N° 31 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_manufacturero_2019.pdf) |
| `client.ipi_minero()` | `/ipi_minero` | `codigo_ClaNAE_2010`: `"B"` (Nivel General), `"06.100"` (Petróleo crudo), `"06.200"` (Gas natural), `"07.10 y 07.29"` (Metalíferos), etc. | [Metodología N° 41 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_minero.pdf) |
| `client.exportaciones()` | `/comercio_exterior_exportacion_bienes` | `rubro_cod`: `"1"` (Primarios), `"2"` (MOA), `"3"` (MOI), `"4"` (Combustibles y energía)<br>`subrubro_cod` y `pais_cod`: ver `client.comex_nomenclaturas()` | [Metodología N° 26 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf) |
| `client.importaciones()` | `/comercio_exterior_importacion_bienes` | `uso_economico_cod`: `"1"` (Bienes de capital), `"2"` (Intermedios), `"3"` (Combustibles), `"4"` (Piezas y acc.), `"5"` (Consumo), `"6"` (Vehículos pasajeros)<br>`gce_cod` y `pais_cod`: ver `client.comex_nomenclaturas()` | [Metodología N° 26 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf) |
| `client.comex_nomenclaturas()` | `/comercio_exterior_nomenclaturas` | `nombre_columna`: `"rubro_cod"`, `"subrubro_cod"`, `"uso_economico_cod"`, `"gce_cod"`, `"pais_cod"` | [Metodología N° 26 (PDF)](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf) |
| `client.poblacion_nacional()` | `/proyecciones_poblacion_nacional_2022_2040` | `sexo_cod`: `"1"` (Mujer), `"2"` (Varón)<br>`edad`: `0` a `100` · `fecha`: `2022` a `2040` | [Proyecciones Nacionales (PDF)](https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_nacionales_2022_2040.pdf) |
| `client.poblacion_jurisdiccion()` | `/proyecciones_poblacion_jurisdiccion_2022_2040` | `jurisdiccion_cod`: `"02"` (CABA), `"06"` (PBA), `"14"` (Córdoba), ..., `"94"` (TDF)<br>`edad_cod`: grupos quinquenales (`"0"`, `"5"`, ..., `"100"`) | [Proyecciones Jurisdicciones (PDF)](https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_jurisdicciones_2022_2040.pdf) · [Códigos Geo](https://www.indec.gob.ar/indec/web/Institucional-Indec-CodigosGeograficos) |
| `client.poblacion_departamento()` | `/estimaciones_poblacion_departamento_2022_2035` | `departamento_cod`: 5 dígitos (2 prov. + 3 depto.)<br>`rmba`: `"1"` (RMBA), `"0"` (Resto) | [Estimaciones Departamentos (PDF)](https://www.indec.gob.ar/ftp/cuadros/publicaciones/estimaciones_departamentos_2022_2035.pdf) · [Códigos Geo](https://www.indec.gob.ar/indec/web/Institucional-Indec-CodigosGeograficos) |

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

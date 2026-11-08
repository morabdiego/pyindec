# Documentación de métodos y códigos del INDEC (`pyindec`)

Desarrollado por [@morabdiego](https://github.com/morabdiego) · Contacto: [morabdiego@gmail.com](mailto:morabdiego@gmail.com)

Esta guía documenta cada uno de los **19 métodos** de `IndecClient`, las columnas por las que se puede filtrar, los **códigos y clasificadores internos que utiliza el INDEC** en cada base de datos y los enlaces oficiales a las metodologías y cuadros técnicos.

---

## Cómo inspeccionar columnas y códigos desde Python

Antes de consultar cualquier tabla, podés ver sus columnas, clave de paginación y enlace metodológico sin consumir red:

```python
from pyindec import list_endpoints, describe_endpoint

# Ver los 19 endpoints, sus alias y links de metodología
df_catalogo = list_endpoints()

# Ver las columnas y tipos de un endpoint específico
df_cols = describe_endpoint("ipc")
```

Y para explorar qué valores únicos de códigos o clasificadores trae un endpoint desde la API:

```python
from pyindec import IndecClient

client = IndecClient()
df = client.ipc(anio=2025, mes=1, select=["clasificador", "nivel", "codigo", "descripcion"], fetch_all=True)
print(df.drop_duplicates())
```

---

## 1. Precios de Consumo (IPC y Canastas CBA/CBT)

### 1.1 `client.ipc(...)` / `client.ipc_nacional(...)`
- **Endpoint:** `/v1/ipc_nacional` (desde diciembre 2016)
- **Metodología INDEC N° 32:** [metodologia_ipc_nacional_2019.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipc_nacional_2019.pdf)
- **Columnas:** `clasificador`, `nivel`, `codigo`, `descripcion`, `periodo` (`AAAAMM`), `anio`, `mes`, `indicador`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `region`, `unidad_de_medida`, `valor`, `observaciones`.

#### Códigos provistos por el INDEC en `ipc_nacional`

- **`region`**:
  - `"Nacional"` (Total Nacional)
  - `"GBA"` (Gran Buenos Aires)
  - `"Pampeana"`, `"Noreste"`, `"Noroeste"`, `"Cuyo"`, `"Patagonia"`
- **`tipo_de_indicador`**:
  - `"v_m"`: Variación porcentual mensual
  - `"v_ia"`: Variación porcentual interanual
  - `"v_acum"`: Variación porcentual acumulada en el año
  - `"Indice"`: Índice base diciembre 2016 = 100
  - `"Incidencia_m"`, `"Incidencia_ia"`, `"Incidencia_acum"`: Incidencias en puntos porcentuales
- **`clasificador`, `nivel` y `codigo`**:

| `clasificador` | `nivel` | `codigo` | `descripcion` |
|---|---|---|---|
| `"IPC"` | `"Nivel General"` | `"0"` | Nivel general |
| `"Estacional, Núcleo y Regulados"` | `"Categoría"` | `"N"` | IPC Núcleo |
| `"Estacional, Núcleo y Regulados"` | `"Categoría"` | `"E"` | Estacional |
| `"Estacional, Núcleo y Regulados"` | `"Categoría"` | `"R"` | Regulados |
| `"Bienes y servicios"` | `"Categoría"` | `"B"` | Bienes |
| `"Bienes y servicios"` | `"Categoría"` | `"S"` | Servicios |
| `"COICOP Argentina 2019"` | `"División"` | `"01"` | Alimentos y bebidas no alcohólicas |
| `"COICOP Argentina 2019"` | `"División"` | `"02"` | Bebidas alcohólicas y tabaco |
| `"COICOP Argentina 2019"` | `"División"` | `"03"` | Prendas de vestir y calzado |
| `"COICOP Argentina 2019"` | `"División"` | `"04"` | Vivienda, agua, electricidad, gas y otros combustibles |
| `"COICOP Argentina 2019"` | `"División"` | `"05"` | Equipamiento y mantenimiento del hogar |
| `"COICOP Argentina 2019"` | `"División"` | `"06"` | Salud |
| `"COICOP Argentina 2019"` | `"División"` | `"07"` | Transporte |
| `"COICOP Argentina 2019"` | `"División"` | `"08"` | Comunicación |
| `"COICOP Argentina 2019"` | `"División"` | `"09"` | Recreación y cultura |
| `"COICOP Argentina 2019"` | `"División"` | `"10"` | Educación |
| `"COICOP Argentina 2019"` | `"División"` | `"11"` | Restaurantes y hoteles |
| `"COICOP Argentina 2019"` | `"División"` | `"12"` | Bienes y servicios varios |

*(Además, bajo `"COICOP Argentina 2019"` existen aperturas con `nivel="Grupo"` como `"01.1"`, `nivel="Clase"`, y `nivel="Producto"` para precios promedio de alimentos y artículos específicos).*

```python
# Ejemplo: inflación mensual Nivel General Nacional desde 2024
df = client.ipc(
    region="Nacional",
    codigo="0",
    tipo_de_indicador="v_m",
    anio=F.gte(2024),
    order="periodo.asc",
)
```

---

### 1.2 `client.canastas_cba_cbt(...)` / `client.valorizacion_canastas_cba_cbt(...)`
- **Endpoint:** `/v1/valorizacion_canastas_cba_cbt` (Gran Buenos Aires, desde abril 2016)
- **Metodología INDEC N° 22:** [EPH_metodologia_22_pobreza.pdf](https://www.indec.gob.ar/ftp/cuadros/sociedad/EPH_metodologia_22_pobreza.pdf)
- **Columnas:** `clasificador`, `nivel`, `codigo`, `descripcion`, `periodo`, `anio`, `mes`, `indicador`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `region`, `unidad_de_medida`, `valor`, `observaciones`.

#### Códigos provistos por el INDEC en `valorizacion_canastas_cba_cbt`

- **`nivel`**: `"Adulto equivalente"` o `"Hogar"`
- **`codigo`**:
  - `"CBA"`: Canasta Básica Alimentaria (línea de indigencia por adulto equivalente)
  - `"CBT"`: Canasta Básica Total (línea de pobreza por adulto equivalente)
  - `"ICE"`: Inversa del Coeficiente de Engel
  - `"CBA H1"`, `"CBT H1"`: Hogar 1 (de 3 integrantes)
  - `"CBA H2"`, `"CBT H2"`: Hogar 2 (tipo de 4 integrantes: 3,09 adultos equivalentes)
  - `"CBA H3"`, `"CBT H3"`: Hogar 3 (de 5 integrantes)
- **`tipo_de_indicador`**: `"CBA"`, `"CBT"`, `"ICE"`, `"Hogar 1"`, `"Hogar 2"`, `"Hogar 3"` (valores en pesos), o `"v_m"` y `"v_ia"` (variaciones porcentuales).

```python
# Ejemplo: valor en pesos de la CBT para un hogar tipo de 4 integrantes (CBT H2)
df = client.canastas_cba_cbt(codigo="CBT H2", tipo_de_indicador="Hogar 2", anio=2025)
```

---

## 2. Nivel de Actividad (EMAE) e Industria (IPI)

### 2.1 `client.emae(...)` / `client.emae_nivel_general(...)`
- **Endpoint:** `/v1/estimador-mensual-de-actividad-economica-nivel-general` (desde enero 2004, base 2004=100)
- **Metodología INDEC N° 20:** [metodologia_emae_ago_16.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf)
- **Columnas:** `periodo`, `anio`, `mes`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `valor`, `observaciones`.
- **Valores de `tipo_de_indicador_descripcion`**:
  - `"Índice serie original"`, `"Índice serie desestacionalizada"`, `"Índice serie tendencia-ciclo"` (con `tipo_de_indicador="Índice base 2004=100"`)
  - `"Var % interanual serie original"`, `"Var % mensual serie desestacionalizada"`, `"Var % mensual serie tendencia-ciclo"` (con `tipo_de_indicador="Variación porcentual"`)

---

### 2.2 `client.emae_sectores(...)`
- **Endpoint:** `/v1/estimador-mensual-de-actividad-economica-sectores` (desde enero 2004)
- **Metodología INDEC N° 20:** [metodologia_emae_ago_16.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf)
- **Columnas:** `periodo`, `anio`, `mes`, `codigo`, `descripcion`, `tipo_de_indicador` (`"Índice base 2004=100"` o `"Variación porcentual interanual"`), `valor`, `observaciones`.

#### Códigos de letra ClaNAE 2004 (`codigo`) en `emae_sectores`

| `codigo` | `descripcion` |
|---|---|
| `"A"` | Agricultura, ganadería, caza y silvicultura |
| `"B"` | Pesca |
| `"C"` | Explotación de minas y canteras |
| `"D"` | Industria manufacturera |
| `"E"` | Electricidad, gas y agua |
| `"F"` | Construcción |
| `"G"` | Comercio mayorista, minorista y reparaciones |
| `"H"` | Hoteles y restaurantes |
| `"I"` | Transporte y comunicaciones |
| `"J"` | Intermediación financiera |
| `"K"` | Actividades inmobiliarias, empresariales y de alquiler |
| `"L"` | Administración pública y defensa; planes de seguridad social de afiliación obligatoria |
| `"M"` | Enseñanza |
| `"N"` | Servicios sociales y de salud |
| `"O"` | Otras actividades de servicios comunitarios, sociales y personales |
| `"T_S"` | Impuestos netos de subsidios |

---

### 2.3 `client.ipi_manufacturero(...)`
- **Endpoint:** `/v1/ipi_manufacturero` (desde enero 2016, base 2004=100)
- **Metodología INDEC N° 31:** [metodologia_ipi_manufacturero_2019.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_manufacturero_2019.pdf)
- **Columnas:** `periodo`, `anio`, `mes`, `indicador`, `cuadro_web`, `codigo_CLaNAE_2004`, `descripcion`, `serie`, `tipo_de_indicador`, `unidad_de_medida`, `valor`.
- **Códigos clave:**
  - `serie`: `"Serie original"`, `"Serie desestacionalizada"`, `"Serie tendencia-ciclo"`
  - `tipo_de_indicador`: `"Índice"`, `"Variación interanual"`, `"Variación acumulada interanual"`, `"Variación intermensual"`, `"Incidencia"`
  - `codigo_CLaNAE_2004`: divisiones de 2 dígitos (`"15"` Alimentos y bebidas, `"16"` Tabaco, `"17"` Textiles, `"18-19"` Prendas de vestir/cuero/calzado, `"20"` Madera, `"21"` Papel, `"22"` Edición e impresión, `"23"` Refinación de petróleo, `"24"` Sustancias y productos químicos, `"25"` Caucho y plástico, `"26"` Minerales no metálicos, `"27"` Industrias metálicas básicas, `"28"` Productos de metal, `"29"` Maquinaria y equipo, `"34"` Vehículos automotores, etc.) y aperturas a 5 dígitos (ej. `"15111"` Carne vacuna).

---

### 2.4 `client.ipi_minero(...)`
- **Endpoint:** `/v1/ipi_minero` (desde enero 2017, base 2016=100)
- **Metodología INDEC N° 41:** [metodologia_ipi_minero.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_ipi_minero.pdf)
- **Columnas:** `periodo`, `anio`, `mes`, `indicador`, `cuadro_web`, `codigo_ClaNAE_2010`, `codigo_CPC_2_1`, `serie`, `descripcion`, `tipo_de_indicador`, `unidad_de_medida`, `valor`.
- **Códigos clave:**
  - `codigo_ClaNAE_2010`: `"B"` (Nivel General - IPI Minero), `"06 y 09.1"` (Petróleo crudo, gas natural y servicios de apoyo), `"06.100"` (Petróleo crudo), `"06.200"` (Gas natural), `"07.10 y 07.29"` (Minerales metalíferos), `"05.100 y 08"` (Minerales no metalíferos y rocas de aplicación), `"08.912"` (Carbonato de litio y otros minerales para químicos), etc.
  - `serie`: `"Serie Original"`, `"Serie Desestacionalizada"`, `"Serie Tendencia-Ciclo"`
  - `tipo_de_indicador`: `"Índice"`, `"Variación intermensual"`, `"Variación interanual"`, `"Variación acumulada interanual"`, `"Unidades físicas"`

---

## 3. Precios de la Producción, Construcción, Obra Pública y Salarios

### 3.1 `client.salarios(...)` / `client.indice_salarios(...)`
- **Endpoint:** `/v1/indice_salarios` (desde noviembre 2015, base octubre 2016=100)
- **Metodología INDEC N° 16:** [cvs_metodologia.pdf](https://www.indec.gob.ar/ftp/cuadros/sociedad/cvs_metodologia.pdf)
- **Columnas:** `clasificador`, `nivel`, `codigo`, `descripcion`, `periodo`, `anio`, `mes`, `indicador`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `unidad_de_medida`, `valor`, `observaciones`.

#### Códigos provistos por el INDEC en `indice_salarios` (`clasificador="IS 2001"`)

| `codigo` | `nivel` | `descripcion` |
|---|---|---|
| `"0"` | `"0"` | Nivel general |
| `"100"` | `"1"` | Total registrado |
| `"110"` | `"2"` | Sector privado registrado |
| `"120"` | `"2"` | Sector público |
| `"121"` | `"3"` | Subsector público nacional |
| `"122"` | `"3"` | Subsector público provincial |
| `"200"` | `"1"` | Total no registrado (sector privado no registrado) |

- **`tipo_de_indicador`**: `"Indice"`, `"v_m"` (mensual), `"v_ia"` (interanual), `"v_acum"` (acumulada).

---

### 3.2 `client.icc(...)` / `client.icc_precios_construccion(...)`
- **Endpoint:** `/v1/icc_precios_construccion` (GBA, base 1993=100, desde noviembre 2015)
- **Metodología INDEC N° 9:** [metodologia_icc.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_icc.pdf)
- **Columnas:** `indicador`, `codigo_apertura`, `codigo_CPC_1`, `clasificador`, `nivel`, `descripcion`, `periodo`, `anio`, `mes`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `region`, `unidad_de_medida`, `valor`, `observaciones`.
- **Códigos principales (`codigo_apertura`)**:
  - `"0"`: Nivel general (`nivel="Nivel general"`)
  - `"01"`: Materiales (`nivel="Capitulo"`)
  - `"02"`: Mano de obra (`"02-01"` Mano de obra asalariada, `"02-02"` Subcontratos de mano de obra)
  - `"03"`: Gastos generales
  - `"IT-01"` a `"IT-11"`: Ítems de obra (`"IT-01"` Movimiento de tierra, `"IT-02"` Estructura, `"IT-03"` Albañilería, `"IT-04"` Yesería, `"IT-05"` Instalación sanitaria y contraincendios, `"IT-06"` Instalación de gas, `"IT-07"` Instalación eléctrica, `"IT-08"` Carpintería metálica y herrería, `"IT-09"` Carpintería de madera, `"IT-10"` Ascensores, `"IT-11"` Pintura).
  - Aperturas por insumo según clasificador provisorio de productos de la ONU (`codigo_CPC_1`).
- **`tipo_de_indicador`**: `"Indice"`, `"v_m"`, `"v_ia"`, `"v_acum"`, `"incidencia"`.

---

### 3.3 `client.sipm(...)` / `client.precios_mayoristas(...)` / `client.sipm_precios_mayoristas(...)`
- **Endpoint:** `/v1/sipm_precios_mayoristas` (desde diciembre 2015, base 1993=100 / dic 2015=100)
- **Metodología INDEC N° 8:** [metodologia1_8_sipm.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia1_8_sipm.pdf)
- **Columnas:** `operativo`, `indicador`, `clasificador`, `nivel`, `codigo_apertura`, `descripcion`, `periodo`, `anio`, `mes`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `region`, `unidad_de_medida`, `valor`, `observaciones`.
- **Códigos clave:**
  - `indicador`:
    - `"IPIM"`: Índice de Precios Internos al por Mayor
    - `"IPIB"`: Índice de Precios Internos Básicos al por Mayor
    - `"IPP"`: Índice de Precios Básicos del Productor
  - `clasificador`: `"SIPM 93"` (aperturas por origen Nacional/Importado y grandes rubros) y `"CIIU3"` (aperturas por letra `"A"` Productos agropecuarios, `"B"` Pesqueros, `"C"` Minerales, `"D"` Manufacturados, `"E"` Energía eléctrica, y códigos CIIU Rev. 3 de 2 a 4 dígitos como `"0111"` Cereales y oleaginosas).
  - `tipo_de_indicador`: `"Indice"`, `"v_m"`, `"v_ia"`, `"v_acum"`, `"incidencia"`.

---

### 3.4 `client.obras_publicas(...)` / `client.redeterminacion_precios_contratos_obras_publicas(...)`
- **Endpoint:** `/v1/redeterminacion_precios_contratos_obras_publicas` (desde diciembre 2015)
- **Documentación oficial y cuadros:** [Portal INDEC - Redeterminación de precios (Decreto 1295/2002 y Decreto 634/2003)](https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-112)
- **Columnas:** `indicador`, `operativo` (`"ICC"` o `"IPIB"`), `inciso`, `descripcion_inciso`, `codigo_apertura`, `codigo_CPC_1`, `codigo_CIUU_3`, `clasificador`, `nivel`, `descripcion`, `origen`, `periodo`, `anio`, `mes`, `tipo_de_indicador`, `tipo_de_indicador_descripcion`, `region`, `unidad_de_medida`, `valor`, `observaciones`.
- **Códigos de `inciso` (Art. 15 del Decreto 1295/2002)**: letras `"a"` (Mano de obra), `"b"` (Albañilería), `"c"` (Pisos y revestimientos), `"d"` (Carpinterías), `"e"` (Productos químicos), `"f"` (Andamios), `"g"` (Artefactos de iluminación y cableado), `"h"` (Caños de PVC), `"i"` (Motores eléctricos y equipos de aire), `"j"` (Equipo-Amortización de equipo), `"k"` (Asfaltos, combustibles y lubricantes), `"l"` (Transportes), `"m"` (Aceros - Hierro aletado), `"n"` (Cemento), `"o"` (Cal), `"p"` (Gastos generales), `"q"` (Arena), `"r"` (Artefactos para baño y grifería), `"s"` (Hormigón), `"t"` (Medidores de caudal), `"u"` (Válvulas de bronce), `"v"` (Electrobombas), `"w"` (Membrana impermeabilizante), `"x"` (Caños de hierro dúctil / acero).

---

## 4. Condiciones de Vida, Pobreza y Mercado de Trabajo (EPH)

### 4.1 `client.pobreza(...)` / `client.pobreza_eph(...)`
- **Endpoint:** `/v1/pobreza_eph` (frecuencia semestral desde 2° semestre 2016)
- **Metodología e informes técnicos:** [metodologia_eph_continua.pdf](https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf) · [Informes y cuadros EPH](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58) · [Diseño de registro y bases de microdatos EPH](https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos)
- **Columnas y formato:**
  - `periodo`: formato `"AAAANS"`, por ejemplo `"20251S"` (1° semestre 2025) o `"20252S"` (2° semestre 2025)
  - `anio` (`int`), `semestre` (`1` o `2`)
  - `area_geografica_nom`: `"T_31_A"` (Total 31 aglomerados urbanos)
  - `tasa_pobreza_hogares`, `tasa_pobreza_personas`, `tasa_indigencia_hogares`, `tasa_indigencia_personas`, `observaciones`.

---

### 4.2 `client.mercado_trabajo(...)` / `client.mercado_trabajo_eph(...)`
- **Endpoint:** `/v1/mercado_trabajo_eph` (frecuencia trimestral desde 2° trimestre 2016)
- **Metodología e informes técnicos:** [metodologia_eph_continua.pdf](https://www.indec.gob.ar/ftp/cuadros/sociedad/metodologia_eph_continua.pdf) · [Informes EPH](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58)
- **Columnas y formato:**
  - `periodo`: formato `"AAAANT"`, por ejemplo `"20251T"`, `"20252T"`, `"20253T"`, `"20254T"`
  - `anio` (`int`), `trimestre` (`1`, `2`, `3`, `4`)
  - `area_geografica_nom`: `"T_31_A"` (Total 31 aglomerados urbanos)
  - Tasas porcentuales: `tasa_de_actividad`, `tasa_de_empleo`, `tasa_de_empleo_formal`, `tasa_de_empleo_informal`, `tasa_de_desocupacion`, `tasa_de_ocupacion_demandante`, `tasa_de_subocupacion`, `tasa_de_subocupacion_demandante`, `tasa_de_subocupacion_no_demandante`, `observaciones`.

---

### 4.3 `client.canasta_crianza(...)`
- **Endpoint:** `/v1/canasta-crianza` (GBA, frecuencia mensual desde enero 2020)
- **Documentación oficial:** [Portal INDEC - Canasta de crianza](https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-43-173)
- **Columnas (valores expresados en pesos argentinos):**
  - `anio`, `Mes`, `Periodo` (`AAAAMM`)
  - Menores de 1 año: `bys_men1` (bienes y servicios), `cuid_men1` (tiempo de cuidado), `tot_men1` (total)
  - 1 a 3 años: `bys_1a3`, `cuid_1a3`, `tot_1a3`
  - 4 a 5 años: `bys_4a5`, `cuid_4a5`, `tot_4a5`
  - 6 a 12 años: `bys_6a12`, `cuid_6a12`, `tot_6a12`

---

## 5. Sector Externo (Comercio Exterior) y Diccionario de Códigos

La API del INDEC provee un endpoint dedicado de nomenclaturas (`comercio_exterior_nomenclaturas`) con todos los códigos utilizados tanto en exportaciones como en importaciones.

### 5.1 `client.comex_nomenclaturas(...)` / `client.comercio_exterior_nomenclaturas(...)`
- **Endpoint:** `/v1/comercio_exterior_nomenclaturas`
- **Metodología INDEC N° 26:** [metodologia_comex.pdf](https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf)
- **Columnas:** `nombre_columna`, `codigo`, `codigo_descripcion`.
- **Valores de `nombre_columna`** para consultar cada diccionario de códigos:
  1. `"rubro_cod"` (7 códigos de grandes rubros de exportación):
     - `"1"`: PRODUCTOS PRIMARIOS
     - `"2"`: MANUFACTURAS DE ORIGEN AGROPECUARIO (MOA)
     - `"3"`: MANUFACTURAS DE ORIGEN INDUSTRIAL (MOI)
     - `"4"`: COMBUSTIBLE Y ENERGIA
     - `"9"`: CONFIDENCIAL · `"X"`: DESCONOCIDO · `"Z"`: NO SE PUEDE ASIGNAR
  2. `"subrubro_cod"` (50 códigos de 3 dígitos de subrubros de exportación, ej. `"106"` Cereales, `"107"` Semillas y frutos oleaginosos, `"201"` Carnes y sus preparados, `"310"` Material de transporte terrestre).
  3. `"uso_economico_cod"` (8 códigos de uso económico de importación):
     - `"1"`: Bienes de Capital
     - `"2"`: Bienes Intermedios
     - `"3"`: Combustibles y Lubricantes
     - `"4"`: Piezas y Accesorios para Bienes de Capital
     - `"5"`: Bienes de Consumo
     - `"6"`: Vehículos Automotores de Pasajeros
     - `"9"`: Resto · `"X"`: DESCONOCIDO
  4. `"gce_cod"` (20 códigos de 3 dígitos de Grandes Categorías Económicas de importación, ej. `"111"` a `"700"`).
  5. `"pais_cod"` (240 códigos ISO de 2 letras de países de origen/destino, ej. `"BR"` Brasil, `"CN"` China, `"US"` Estados Unidos, `"CL"` Chile, `"DE"` Alemania).

```python
# Consultar desde Python el diccionario completo de subrubros o países:
df_subrubros = client.comex_nomenclaturas(nombre_columna="subrubro_cod", fetch_all=True)
df_paises = client.comex_nomenclaturas(nombre_columna="pais_cod", fetch_all=True)
```

---

### 5.2 `client.exportaciones(...)` / `client.comercio_exterior_exportacion_bienes(...)`
- **Endpoint:** `/v1/comercio_exterior_exportacion_bienes` (mensual desde enero 1986)
- **Columnas:** `Anio`, `Mes`, `Periodo` (`AAAAMM`), `rubro_cod`, `subrubro_cod`, `pais_cod`, `valor_FOB` (USD), `Peso_Neto` (kg).

```python
# Ejemplo: exportaciones de Manufacturas de Origen Agropecuario (rubro_cod="2") a Brasil ("BR") en 2025
df = client.exportaciones(Anio=2025, rubro_cod="2", pais_cod="BR", fetch_all=True)
```

---

### 5.3 `client.importaciones(...)` / `client.comercio_exterior_importacion_bienes(...)`
- **Endpoint:** `/v1/comercio_exterior_importacion_bienes` (mensual desde enero 1986)
- **Columnas:** `Anio`, `Mes`, `Periodo` (`AAAAMM`), `uso_economico_cod`, `gce_cod`, `pais_cod`, `valor_CIF` (USD), `peso_neto` (kg).

```python
# Ejemplo: importaciones de Bienes de Capital (uso_economico_cod="1") desde China ("CN") en 2025
df = client.importaciones(Anio=2025, uso_economico_cod="1", pais_cod="CN", fetch_all=True)
```

---

## 6. Población y Demografía (Censo 2022 - Proyecciones y Estimaciones)

En los tres endpoints demográficos se utilizan los códigos geográficos oficiales del INDEC ([Unidades Geoestadísticas y Códigos Geográficos del INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-CodigosGeograficos)):

#### Códigos de Sexo (`sexo_cod`)
- `"1"`: Mujer (`sexo_nom="Mujer"`)
- `"2"`: Varón (`sexo_nom="Varon"`)

#### Códigos de Jurisdicción / Provincia (`jurisdiccion_cod` - 2 dígitos)
| Código | Jurisdicción | Código | Jurisdicción |
|---|---|---|---|
| `"02"` | Ciudad Autónoma de Buenos Aires (CABA) | `"50"` | Mendoza |
| `"06"` | Buenos Aires | `"54"` | Misiones |
| `"10"` | Catamarca | `"58"` | Neuquén |
| `"14"` | Córdoba | `"62"` | Río Negro |
| `"18"` | Corrientes | `"66"` | Salta |
| `"22"` | Chaco | `"70"` | San Juan |
| `"26"` | Chubut | `"74"` | San Luis |
| `"30"` | Entre Ríos | `"78"` | Santa Cruz |
| `"34"` | Formosa | `"82"` | Santa Fe |
| `"38"` | Jujuy | `"86"` | Santiago del Estero |
| `"42"` | La Pampa | `"90"` | Tucumán |
| `"46"` | La Rioja | `"94"` | Tierra del Fuego, Antártida e Islas del Atlántico Sur |

---

### 6.1 `client.poblacion_nacional(...)` / `client.proyecciones_poblacion_nacional_2022_2040(...)`
- **Endpoint:** `/v1/proyecciones_poblacion_nacional_2022_2040`
- **Metodología:** [proyecciones_nacionales_2022_2040.pdf](https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_nacionales_2022_2040.pdf)
- **Columnas:** `edad` (años simples de `0` a `100`), `sexo_cod` (`"1"`, `"2"`), `sexo_nom`, `poblacion`, `fecha` (año numérico de `2022` a `2040`).

---

### 6.2 `client.poblacion_jurisdiccion(...)` / `client.proyecciones_poblacion_jurisdiccion_2022_2040(...)`
- **Endpoint:** `/v1/proyecciones_poblacion_jurisdiccion_2022_2040`
- **Metodología:** [proyecciones_jurisdicciones_2022_2040.pdf](https://www.indec.gob.ar/ftp/cuadros/publicaciones/proyecciones_jurisdicciones_2022_2040.pdf)
- **Columnas:** `jurisdiccion_cod`, `jurisdiccion_nom`, `sexo_cod`, `sexo_nom`, `edad_cod` (grupos quinquenales: `"0"`, `"5"`, `"10"`, `"15"`, ..., `"95"`, `"100"`), `edad_nom` (`"0 a 4 años"`, ..., `"100 y más años"`), `poblacion`, `fecha` (string `"2022"` a `"2040"`).

---

### 6.3 `client.poblacion_departamento(...)` / `client.estimaciones_poblacion_departamento_2022_2035(...)`
- **Endpoint:** `/v1/estimaciones_poblacion_departamento_2022_2035`
- **Metodología:** [estimaciones_departamentos_2022_2035.pdf](https://www.indec.gob.ar/ftp/cuadros/publicaciones/estimaciones_departamentos_2022_2035.pdf)
- **Columnas:** `jurisdiccion_cod` (2 dígitos), `jurisdiccion_nom`, `departamento_cod` (5 dígitos: 2 de provincia + 3 de departamento/partido/comuna), `departamento_nom`, `rmba` (`"1"` si pertenece a la Región Metropolitana de Buenos Aires, `"0"` en caso contrario), `sexo_cod`, `sexo_nom`, `poblacion`, `fecha` (string `"2022"` a `"2035"`).

---

## 7. Signos convencionales del INDEC (`observaciones`)

Cuando un dato numérico es `None` o tiene notas metodológicas, la columna `observaciones` utiliza los signos convencionales del INDEC (consultables con `pyindec.SIGNOS_CONVENCIONALES` o `pyindec.explain_sign(signo)`):

| Signo | Significado oficial |
|---|---|
| `*` | Dato provisorio |
| `**` | Dato preliminar |
| `e` | Dato estimado por extrapolación, proyección |
| `i` | Dato estimado por imputación |
| `u` | Dato de calidad inferior al estándar |
| `-` | Cero absoluto |
| `.` | Dato no registrado |
| `...` | Dato no disponible a la fecha de presentación de los resultados |
| `///` | Dato que no corresponde presentar |
| `s` | Dato confidencial por aplicación de las reglas del secreto estadístico |

---

## Autor y contacto

Creado y mantenido por **Diego Morabito** ([@morabdiego](https://github.com/morabdiego)).  
Contacto: [morabdiego@gmail.com](mailto:morabdiego@gmail.com).

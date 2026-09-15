# AGENTS.md — Guía para agentes de IA en `catalog-scrap`

Repositorio de extracción, parseo y normalización de catálogos y hojas técnicas de válvulas/tuberías para su integración con **AutoCAD Plant 3D 2027** (`plant3d`). Este archivo resume la arquitectura, contratos de datos y reglas críticas.

---

## 📌 Arquitectura y Contratos de Datos

1. **Datasheet Engine (`specific`)**:
   - Salida canónica: `output/specifications/<MODEL>.json`.
   - Contiene metadatos completos, lista BOM de partes y materiales, normas de fabricación y lista `plant3d_records` con $L, D_{flange}, H, L_1, E, OD$, peso y torque.
   - Modelo de referencia: `INTEC K200` (template `INTEC_K200_BALL_VALVE`, resuelto por modelo en `transformers/plant3d.py`, no por heurística).

2. **Catalog Engine (`generic`)**:
   - Salida canónica: `output/catalogs/<CATALOG_NAME>/manifest.json` (con `extraction_type: generic`, `pages` por modelo) y archivos individuales `<MODEL>.json`.
   - Schema v2 de records: `L_mm` (face-to-face), `D_flange_mm` (columna D1/OD de brida), `D_bore_mm` (columna D/paso), `Weight_kg`, `Source_PDF`, `Page_Number`, `Row_Index`. Sin `D_mm` ambiguo.
   - Reporte de calidad: `output/catalogs/<CATALOG>_quality.json` (filas leídas, records, descartes con motivo por tabla).

3. **Capa de tablas (`parsers/table.py`)**:
   - Todo parser tabular la usa: `strip_product_code` (códigos de 5-15 dígitos o `-`), `repair_fractures` (tallas partidas en 2 celdas), `classify_columns` (alias ES/EN/DE), `parse_length_cell` (L estricta + banda de plausibilidad L/DN en fracturas), `parse_bare_dn` (dialecto DN-mm sin comilla).
   - Semántica por parser, mecánica aquí: `D1` = brida y `D` = bore lo decide cada layout (en tablas roscadas simples `d1` es el bore).

---

## 🧠 Reglas Críticas de Extracción y Parseo

### 1. Normalización de Fracciones NPS y Celdas Compuestas/Fracturadas
- Usar siempre `parse_nps_cell` en `catalog_scrap.parsers.utils`, más `repair_fractures` en `catalog_scrap.parsers.table` cuando pdfplumber parta la talla en 2 celdas (`'...051 1'` + `'/2” 90 60.3'`).
- Normalizar fracciones con puntos (ej. `1.1/2"`) a fracciones con espacio (`1 1/2"` = $1.5"$, DN 40). NUNCA eliminar el punto si separa entero de fracción.
- En columnas compuestas tipo `DN D` (ej. `1/2" 14`, `1" 25`, `1 1/2" 38`), el primer token es la talla y el resto es el bore (`size_remainder`); nunca sumar los enteros subsiguientes.
- Entero desnudo de 1-3 dígitos presente en la tabla DN = dialecto DN-mm (`parse_bare_dn`: `65` -> DN65). JAMÁS leerlo como pulgadas.

### 2. Filtro de Sanidad de Ingeniería
- **Longitud $L > 0$ OBLIGATORIA**: Cualquier fila de tabla donde $L \le 0$ debe ser descartada. Plant 3D no puede rutear válvulas sin longitud cara a cara. La columna $L$ se parsea estricta (`parse_length_cell`): número único o primer token de cabecera agrupada (`L P H`/`L H`); en fracturas de 2 tokens se elige por banda de plausibilidad $1.0 \le L/DN \le 12.0$.
- **Rango de Diámetros Válidos**: $0.125" \le ND \le 48"$. Cualquier valor fuera de este rango es ruido de OCR o código de artículo mal parseado y debe ser descartado.
- **Válvulas Bridadas**: Requieren $D_{flange} > 0$. Si ambas son $\le 0$ en una válvula con bridas (`RF`/`FL`), la fila debe descartarse. Invariante físico: $D_{flange} > 1.2 \times D_{bore}$ (filtra D1 fracturados).
- **Todo descarte lleva motivo** (`TableQuality`: `invalid_nps`, `missing_L`, `flanged_without_D`, `flange_le_bore`, `note_row`) y sale al reporte `*_quality.json`. Prohibido descartar en silencio.

### 3. Comandos de Verificación
```bash
uv run python -m unittest discover -s tests -v
uv run python -m catalog_scrap.cli --output-dir output run-all
```
Nota: `--output-dir` es flag GLOBAL (antes del subcomando); `run-all` no lo acepta como propio.

---

## 📐 Convenciones Git

- **PROHIBIDO HACER COMMITS SIN AUTORIZACIÓN**: NUNCA ejecutar `git commit` por iniciativa propia ni como paso automático. Solo realizar commits si el usuario da una instrucción o permiso explícito e inmediato ("haz commit", "commitea esto").
- **Estilo de Commits**: En caso de estar autorizado por el usuario, usar commits atómicos tipo Conventional Commits (`<type>(<scope>): <subject>`) **con cero cuerpo/descripción**.


# AGENTS.md — Guía para agentes de IA en `catalog-scrap`

Repositorio de extracción, parseo y normalización de catálogos y hojas técnicas de válvulas/tuberías para su integración con **AutoCAD Plant 3D 2027** (`plant3d`). Este archivo resume la arquitectura, contratos de datos y reglas críticas.

---

## 📌 Arquitectura y Contratos de Datos

1. **Datasheet Engine (`specific`)**:
   - Salida canónica: `output/specifications/<MODEL>.json`.
   - Contiene metadatos completos, lista BOM de partes y materiales, normas de fabricación y lista `plant3d_records` con $L, D, H, L_1, E, OD$, peso y torque.
   - Modelo de referencia: `INTEC K200`.

2. **Catalog Engine (`generic`)**:
   - Salida canónica: `output/catalogs/<CATALOG_NAME>/manifest.json` y archivos individuales `<MODEL>.json`.
   - Contiene la lista de familias y sus ítems con cotas esenciales: `NPS_inch`, `DN_mm`, `L_mm`, `D_mm`, `Class_lbs`, `Body_Material`, `Geometry_Template`.

---

## 🧠 Reglas Críticas de Extracción y Parseo

### 1. Normalización de Fracciones NPS y Celdas Compuestas
- Usar siempre `parse_nps_cell` en `catalog_scrap.parsers.utils`.
- Normalizar fracciones con puntos (ej. `1.1/2"`) a fracciones con espacio (`1 1/2"` = $1.5"$, DN 40). NUNCA eliminar el punto si separa entero de fracción.
- En columnas compuestas tipo `DN D` (ej. `1/2" 14`, `1" 25`, `1 1/2" 38`), tomar únicamente el primer token NPS válido; nunca sumar los enteros subsiguientes.

### 2. Filtro de Sanidad de Ingeniería
- **Longitud $L > 0$ OBLIGATORIA**: Cualquier fila de tabla donde $L \le 0$ debe ser descartada. Plant 3D no puede rutear válvulas sin longitud cara a cara.
- **Rango de Diámetros Válidos**: $0.125" \le ND \le 48"$. Cualquier valor fuera de este rango es ruido de OCR o código de artículo mal parseado y debe ser descartado.
- **Válvulas Bridadas**: Requieren $D > 0$. Si $D \le 0$ en una válvula con bridas (`RF`/`FL`), la fila debe descartarse.

### 3. Comandos de Verificación
```powershell
uv run python -m unittest discover -s tests -v
uv run python -m catalog_scrap.cli run-all
```

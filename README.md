# Catalog-Scrap — Motor de Extracción y Transformación de Catálogos para Plant 3D

Pipeline automatizado en Python para la ingesta, parseo estructurado, normalización dimensional y exportación de hojas técnicas de ingeniería y catálogos comerciales de válvulas/accesorios en PDF hacia especificaciones y manifiestos listos para **AutoCAD Plant 3D 2027**.

---

## 📌 Arquitectura Dual-Engine

El proyecto opera con una arquitectura desacoplada de doble motor:

1. **Datasheet Engine (`specific`)**:
   - Para fichas técnicas de alta fidelidad de fabricantes (ej. Klinger Schöneberg INTEC K200).
   - Extrae el 100% de los parámetros geométricos de ingeniería ($L, D, H, L_1, E, OD$), torques, pesos, lista de materiales (BOM) y normas.
   - Genera un archivo canónico único: `output/specifications/<MODEL>.json`.

2. **Catalog Engine (`generic`)**:
   - Para catálogos comerciales generales de múltiples páginas y familias (ej. Saidi RK 2016).
   - Extrae longitudes cara a cara ($L$) y diámetros ($D$) gobernados por normas estándar ANSI B16.10 / ANSI B16.5.
   - Normaliza automáticamente fracciones de pulgada, descarta ruido de OCR y filas corruptas ($L \le 0$).
   - Genera un manifiesto estructurado: `output/catalogs/<CATALOG>/manifest.json` junto con archivos JSON por modelo.

---

## 📂 Estructura del Repositorio

```text
catalog-scrap/
├── docs/
│   ├── specifications/         # PDFs de fichas técnicas de alta fidelidad
│   └── catalogs/               # PDFs de catálogos comerciales generales
├── src/catalog_scrap/
│   ├── core/                   # Modelos de datos y Factory de parsers
│   ├── loaders/                # Cargador de documentos PDF (pdfplumber)
│   ├── parsers/                # Adaptadores específicos por fabricante/catálogo
│   │   ├── klinger_k200.py     # Parser de alta precisión para Klinger INTEC K200
│   │   ├── saidi_rk2016.py     # Parser multimodelo para Saidi RK 2016
│   │   └── utils.py            # Normalizador de fracciones NPS y DN
│   ├── transformers/           # Mapeo hacia estructuras y templates de Plant 3D
│   │   └── plant3d.py
│   ├── exporters/              # Exportadores JSON y CSV
│   └── cli.py                  # Interfaz de línea de comandos
├── output/
│   ├── specifications/         # JSONs de especificación detallada
│   └── catalogs/               # Manifiestos y JSONs de catálogo comercial
└── tests/                      # Suite de pruebas unitarias
```

---

## 🚀 Uso del CLI

### 1. Extracción de Ficha Técnica Detallada (Modo Específico)
```powershell
uv run python -m catalog_scrap.cli spec docs/specifications/INTEC-K200-NPS1-24inch-eng.pdf --output-dir output/specifications
```

### 2. Extracción de Catálogo Comercial Multimodelo (Modo Genérico)
```powershell
uv run python -m catalog_scrap.cli catalog docs/catalogs/CATALOGO_VAL_BOLA_2016-44.pdf --output-dir output/catalogs
```

### 3. Procesar Todo el Repositorio (`run-all`)
```powershell
uv run python -m catalog_scrap.cli run-all --output-dir output
```

---

## 🧪 Pruebas Unitarias
```powershell
uv run python -m unittest discover -s tests -v
```

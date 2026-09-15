import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from catalog_scrap.core.base_parser import BaseParser
from catalog_scrap.core.models import CatalogItem, DimensionEntry
from catalog_scrap.parsers.utils import parse_nps_cell
from catalog_scrap.parsers.table import (
    TableQuality,
    bare_remainder,
    classify_columns,
    clean_row,
    extract_size_candidate,
    first_bare_dn,
    first_float,
    first_token,
    iso_token,
    last_float,
    parse_bare_dn,
    parse_length_cell,
    repair_fractures,
    size_remainder,
    strip_product_code,
)

# La columna 'D' del PDF es bore/paso y 'D1' es diametro de brida en las
# tablas de valvulas bridadas multiculumna (pags. 2, 4, 25, 30, 34, 35).
# En tablas roscadas simples 'd1' es el bore ('2006SC', pag. 11).
# El prefijo opcional \d{4,} absorbe restos de codigo ('0039 10” 405' -> 405).
_SIZE_PREFIX_RE = re.compile(
    r'^\s*(?:\d{4,}\s+)?\d+(?:\s+\d+/\d+|\.\d+/\d+|/\d+)?\s*["\u201c\u201d]\s*'
)


def _fused_weight(weight_cell: str, next_cell: str) -> float:
    """Peso desde celda fusionada Peso+ISO+Par ('F25 510 248' -> 248.0).

    El peso es el ultimo token, salvo huerfano de un digito de la columna
    siguiente ('F25 510 248 2' + '2.5 ...' -> 248.0): si el ultimo token es
    un solo digito que continua en la celda vecina, se toma el anterior.
    """
    toks = (weight_cell or '').split()
    if not toks:
        return 0.0
    if len(toks) >= 2 and len(toks[-1]) == 1 and toks[-1].isdigit():
        nxt = (next_cell or '').split()
        if nxt and nxt[0] != toks[-1] and nxt[0].startswith(toks[-1]):
            toks = toks[:-1]
            if not toks:
                return 0.0
    try:
        return float(toks[-1].replace(',', '.'))
    except ValueError:
        return 0.0


class SaidiRK2016Parser(BaseParser):
    @classmethod
    def can_handle(cls, pdf_path: Path, text_sample: str = "") -> bool:
        filename = pdf_path.name.upper()
        if any(k in filename for k in ["SAIDI", "CATALOGO_VAL_BOLA", "2016"]):
            return True
        if "SAIDI" in text_sample.upper() or "RK VALVULAS" in text_sample.upper() or "RK VÁLVULAS" in text_sample.upper():
            return True
        return False

    def parse(self, pdf_handle) -> List[CatalogItem]:
        """Parse all pages from Saidi RK 2016 Ball Valves PDF Catalog into a list of CatalogItem entities."""
        items: List[CatalogItem] = []
        self.last_quality: List[TableQuality] = []

        for page_idx, page in enumerate(pdf_handle.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            lines = [l.strip() for l in text.split("\n") if l.strip()]

            # Extract clean figure model name (e.g. "C15F2RB", "C30F2RB", "C800NPT", "C15F2")
            fig_model = self._extract_figure_model(lines)
            if not fig_model:
                continue

            pressure_class = self._extract_class(lines)
            material_heading = self._extract_material_heading(lines)
            valve_type = self._extract_valve_type(lines)

            tables = page.extract_tables()
            materials = self._extract_materials(tables)
            dimensions = self._extract_dimensions(
                tables, fig_model=fig_model, valve_type=valve_type,
                page_number=page_idx + 1,
            )

            if dimensions:
                catalog_item = CatalogItem(
                    manufacturer="Saidi Spain / RK Válvulas",
                    model=fig_model,
                    valve_type=valve_type,
                    extraction_type="generic",
                    dimensions=dimensions,
                    materials=materials,
                    metadata={
                        "parser": "SaidiRK2016Parser",
                        "extraction_mode": "generic_catalog",
                        "page_number": page_idx + 1,
                        "pressure_class": pressure_class,
                        "material_heading": material_heading,
                        "standards": {
                            "face_to_face": "ANSI B16.10 / DIN 3202",
                            "flanges": "ANSI B16.5 / DIN 2543"
                        }
                    }
                )
                items.append(catalog_item)

        print(f"[SaidiRK2016Parser] Successfully extracted {len(items)} models across {len(pdf_handle.pages)} pages.")
        return items

    def _extract_figure_model(self, lines: List[str]) -> str:
        for line in lines:
            match = re.search(r'(?:RK\s*[\u00ae\u00ae]?\s*)?(?:Fig\.|FIG\.)\s*([A-Za-z0-9\s/_-]+)', line)
            if match:
                raw_fig = match.group(1).strip()
                raw_fig = raw_fig.split('Tipo:')[0].split('tipo:')[0].strip()
                raw_fig = re.sub(r'\s+(?:Tipo|tipo|1|2|3|piezas|pieza).*$', '', raw_fig, flags=re.IGNORECASE).strip()
                if raw_fig:
                    clean_fig = raw_fig.replace(' ', '-')
                    return re.sub(r'-{2,}', '-', clean_fig).strip('-')

            if any(k in line for k in ["C15F2", "C30F2", "C60F2", "C800", "S800", "2006SC", "I16F2", "C16F2", "S16F2", "C40F2", "S40F2"]):
                words = line.split()
                for w in words:
                    if re.match(r'^[CS]\d+[A-Z0-9]+', w):
                        clean_w = re.sub(r'-{2,}', '-', w).strip('-')
                        return clean_w
        return ""

    def _extract_class(self, lines: List[str]) -> str:
        # Orden estricto: LBS/# primero, luego WOG, luego PN aislado.
        # Sin esto, 'DIN 2543 PN16' se capturaba como '2543 PN16'.
        for line in lines:
            match = re.search(r'(150|300|600|800|1500|2500)\s*(LBS|lbs|#)', line)
            if match:
                return f"{match.group(1)}LBS"
            match = re.search(r'(\d+)\s*WOG', line, re.IGNORECASE)
            if match:
                return f"{match.group(1)}WOG"
        for line in lines:
            match = re.search(r'\bPN\s*(\d+)', line, re.IGNORECASE)
            if match:
                return f"PN{match.group(1)}"
        return "150LBS"

    def _extract_material_heading(self, lines: List[str]) -> str:
        first_line = lines[0] if lines else ""
        if "ACERO CARBONO" in first_line:
            return "Acero Carbono"
        elif "ACERO INOX" in first_line or "ACERO INOXIDABLE" in first_line:
            return "Acero Inoxidable"
        elif "HIERRO FUNDIDO" in first_line:
            return "Hierro Fundido"
        return "Acero Carbono"

    def _extract_valve_type(self, lines: List[str]) -> str:
        for line in lines:
            if "VÁLVULA" in line.upper() or "VALVULA" in line.upper():
                clean_type = " ".join(line.replace('\n', ' ').split()).strip()
                # Format to neat title case
                words = clean_type.split()
                cleaned_words = []
                for w in words:
                    if w.upper() in ["PN16", "PN40", "PN63", "150LBS", "300LBS", "600LBS", "800LBS", "1000WOG", "RF"]:
                        cleaned_words.append(w.upper())
                    else:
                        cleaned_words.append(w.capitalize())
                return " ".join(cleaned_words)
        return "Válvula de Bola"

    def _extract_materials(self, tables: List[List[List[str]]]) -> Dict[str, str]:
        materials = {}
        for table in tables:
            for row in table:
                clean_row = [" ".join(c.replace('\n', ' ').split()).strip() for c in row if c is not None and c.strip()]
                if len(clean_row) >= 2:
                    pos = clean_row[0]
                    if any(k in pos.lower() for k in ["cuerpo", "tapa", "terminal", "esfera", "eje", "husillo", "asiento"]):
                        materials[pos] = clean_row[1]
                    elif len(clean_row) >= 3 and pos.isdigit():
                        materials[clean_row[1]] = clean_row[2]
        return materials

    def _strip_size_prefix(self, cell: str) -> str:
        """Quita el fragmento de talla fusionado ('1” 110 79.4' -> '110 79.4').

        pdfplumber fusiona DN+D1+D2 en una celda cuando la talla no se
        fractura; sin esto first_float devolveria la talla (1.0) como D1.
        """
        return _SIZE_PREFIX_RE.sub('', cell or '').strip()

    def _extract_dimensions(self, tables: List[List[List[str]]], fig_model: str = "", valve_type: str = "", page_number: int = 0) -> List[DimensionEntry]:
        dimensions = []
        if not hasattr(self, "last_quality"):
            self.last_quality: List[TableQuality] = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Identify header row
            header = clean_row(table[0])
            header_str = " ".join(header).upper()

            if not any(k in header_str for k in ["DN", "NPS", "NPT", "D1", "CÓDIGO", "CODIGO"]):
                continue

            cmap = classify_columns(header)
            quality = TableQuality(page_number=page_number, model=fig_model)
            self.last_quality.append(quality)

            # Sin columna de longitud no puede haber cotas L-mandatorias:
            # tabla no dimensional (pares, BOM) -> skip limpio con traza.
            if "length" not in cmap and "length_grouped" not in cmap:
                quality.status = "skipped_no_length"
                quality.rows_in = len(table) - 1
                continue

            size_idx = cmap.get("size")
            code_idx = cmap.get("code")
            flange_idx = cmap.get("d1")
            bore_idx = cmap.get("d")
            length_idx = cmap.get("length")
            grouped_idx = cmap.get("length_grouped")
            height_idx = cmap.get("height")
            weight_idx = cmap.get("weight")
            iso_idx = cmap.get("iso")
            # Legacy: columna 'P' (palanca) como aproximacion de L1
            lever_idx = next(
                (i for i, h in enumerate(header)
                 if h.strip().upper() in ("P",) or "PALANCA" in h.upper() or "L1" in h.upper()),
                None,
            )

            for row_nr, raw in enumerate(table[1:], start=2):
                cells = repair_fractures(clean_row(raw))
                quality.rows_in += 1
                if not any(cells):
                    quality.discard(row_nr, "empty_row")
                    continue

                full_text = " ".join(cells)
                if any(note in full_text.lower() for note in ["certificado", "correspondientes", "marca", "prueba", "norma"]):
                    quality.discard(row_nr, "note_row", full_text)
                    continue

                no_codes = [strip_product_code(c) for c in cells]

                # 1. Size extraction: primer candidato que parsea valido.
                # Orden: columna size -> celdas 0..2 (zona codigo/talla) ->
                # fallback sobre la fila. Una celda de codigo puro no es
                # talla: se salta al siguiente candidato.
                ordered_cells = []
                if size_idx is not None and size_idx < len(no_codes):
                    ordered_cells.append((size_idx, no_codes[size_idx]))
                for ci in (code_idx, 0, 1, 2):
                    if ci is not None and ci < len(no_codes) and no_codes[ci] not in [t for _, t in ordered_cells]:
                        ordered_cells.append((ci, no_codes[ci]))
                ordered_cells.append((None, extract_size_candidate(no_codes)))

                raw_nps, nps_info = "", {"nps": "", "dn": 0, "dec_in": 0.0}
                size_cell_idx, size_cell_used, bare_dn_used = None, "", False
                for ci, cand in ordered_cells:
                    if not cand or any(k in cand for k in ["97/23", "0035", "0039", "CE", "PED"]):
                        continue
                    # Entero desnudo = dialecto DN-mm ('65' -> DN65, jamas
                    # pulgadas: parse_nps_cell lo leeria como 65").
                    if re.fullmatch(r'\s*\d{1,3}\s*', cand):
                        info = parse_bare_dn(cand) or {"nps": "", "dn": 0, "dec_in": 0.0}
                        bare = True
                    else:
                        info = parse_nps_cell(cand)
                        bare = False
                        if not (info["nps"] and info["dn"] > 0 and 0.0 < info["dec_in"] <= 24.0):
                            info = first_bare_dn(cand) or {"nps": "", "dn": 0, "dec_in": 0.0}
                            bare = info["nps"] != ""
                    if info["nps"] and info["dn"] > 0 and 0.0 < info["dec_in"] <= 24.0:
                        raw_nps, nps_info = cand, info
                        size_cell_idx, size_cell_used, bare_dn_used = ci, cand, bare
                        break
                if not raw_nps:
                    quality.discard(row_nr, "invalid_nps", full_text)
                    continue
                dn_mm = nps_info["dn"]

                l_val = 0.0
                if grouped_idx is not None and grouped_idx < len(cells):
                    l_val = parse_length_cell(cells[grouped_idx], grouped=True)
                elif length_idx is not None and length_idx < len(cells):
                    l_val = parse_length_cell(cells[length_idx], dn_mm=dn_mm)
                d_flange = first_float(self._strip_size_prefix(cells[flange_idx])) if flange_idx is not None and flange_idx < len(cells) else 0.0
                d_bore = first_float(cells[bore_idx]) if bore_idx is not None and bore_idx < len(cells) else 0.0
                # Tablas roscadas simples: 'd1' ES el bore (no hay brida)
                if d_bore <= 0.0 and flange_idx is not None and "BRIDADA" not in valve_type.upper() and "F2" not in fig_model:
                    d_bore = d_flange
                    d_flange = 0.0
                # Sin columna D ('DN D' fusionados, pag. 35): el bore es el
                # resto numerico de la celda de talla ('1/2” 14' -> 14).
                if d_bore <= 0.0 and size_idx is not None and size_idx < len(no_codes):
                    d_bore = first_float(size_remainder(no_codes[size_idx]))

                # D1 fracturado en dos celdas ('65 18' + '5 145' -> 185,
                # pag. 19): solo en dialecto DN desnudo sin columna size,
                # tomando el D1 de la celda SIGUIENTE a la de la talla, con
                # fragmentos cortos y resultado fisicamente coherente.
                next_idx = size_cell_idx + 1 if size_cell_idx is not None else None
                if (bare_dn_used and size_idx is None and next_idx is not None
                        and next_idx < len(cells) and d_bore > 0.0):
                    frag_r = bare_remainder(size_cell_used)
                    frag_f = first_token(cells[next_idx])
                    if (re.fullmatch(r'\d{1,2}', frag_r or '')
                            and re.fullmatch(r'\d{1,2}', frag_f or '')):
                        try:
                            joined = float(f"{frag_r}{frag_f}")
                        except ValueError:
                            joined = 0.0
                        if joined > d_bore * 1.2:
                            d_flange = joined
                h_val = first_float(cells[height_idx]) if height_idx is not None and height_idx < len(cells) else 0.0
                if h_val <= 0.0 and grouped_idx is not None and grouped_idx < len(cells):
                    # 'L P H' agrupado: el segundo token es H (paridad legacy)
                    parts = cells[grouped_idx].split()
                    if len(parts) >= 2:
                        try:
                            h_val = float(parts[1].replace(',', '.'))
                        except ValueError:
                            pass
                l1_val = first_float(cells[lever_idx]) if lever_idx is not None and lever_idx < len(cells) else 0.0
                weight_val = first_float(cells[weight_idx]) if weight_idx is not None and weight_idx < len(cells) else 0.0
                iso_flange = (cells[iso_idx] or "").upper() if iso_idx is not None and iso_idx < len(cells) else ""
                if weight_idx is not None and weight_idx < len(cells):
                    # Cabecera fusionada Peso+ISO+Par ('F25 510 248'):
                    # el peso es el ULTIMO token y el ISO el codigo Fxx.
                    weight_header = header[weight_idx].upper() if weight_idx < len(header) else ""
                    if "ISO" in weight_header and "PAR" in weight_header:
                        weight_cell = cells[weight_idx]
                        next_cell = cells[weight_idx + 1] if weight_idx + 1 < len(cells) else ""
                        weight_val = _fused_weight(weight_cell, next_cell)
                        if not iso_flange:
                            iso_flange = iso_token(weight_cell)

                # Strict validation: Face-to-face length L is mandatory for all valves
                if l_val <= 0.0:
                    quality.discard(row_nr, "missing_L", full_text)
                    continue

                # Flanged valves require a valid flange OD (D1 > 0 or D > 0)
                is_flanged = "F2" in fig_model or "BRIDADA" in valve_type.upper()
                if is_flanged and d_flange <= 0.0 and d_bore <= 0.0:
                    quality.discard(row_nr, "flanged_without_D", full_text)
                    continue

                # Invariante fisico: el OD de brida siempre supera al bore
                # con margen (corona + taladros). Filtra D1 fracturados.
                if is_flanged and d_bore > 0.0 and d_flange <= d_bore * 1.2:
                    quality.discard(row_nr, "flange_le_bore", full_text)
                    continue

                # D canonico: brida en bridadas, bore en roscadas
                d_val = d_flange if (is_flanged and d_flange > 0.0) else d_bore

                entry = DimensionEntry(
                    nps=nps_info['nps'],
                    dn=dn_mm,
                    dec_in=nps_info['dec_in'],
                    h=h_val,
                    l1=l1_val,
                    l_150=l_val,
                    l_300=l_val,
                    d_150=d_val,
                    d_300=d_val,
                    e=0.0,
                    iso_flange=iso_flange,
                    torque_150=0.0,
                    torque_300=0.0,
                    weight_150=weight_val,
                    weight_300=weight_val,
                    extra_dimensions={
                        "d_flange_mm": d_flange,
                        "d_bore_mm": d_bore,
                    },
                    page_number=page_number,
                    row_index=row_nr,
                    source="saidi_rk2016",
                )
                dimensions.append(entry)
                quality.records_out += 1

        return dimensions

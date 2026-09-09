import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from catalog_scrap.core.base_parser import BaseParser
from catalog_scrap.core.models import CatalogItem, DimensionEntry
from catalog_scrap.parsers.utils import parse_nps_cell


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
            dimensions = self._extract_dimensions(tables, fig_model=fig_model, valve_type=valve_type)

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
        for line in lines:
            match = re.search(r'(\d+)\s*(LBS|lbs|PN\s*\d+|WOG)', line)
            if match:
                return match.group(0).strip().upper()
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

    def _extract_dimensions(self, tables: List[List[List[str]]], fig_model: str = "", valve_type: str = "") -> List[DimensionEntry]:
        dimensions = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Identify header row
            header_row = [(" ".join(c.replace('\n', ' ').split()).upper() if c else "") for c in table[0]]
            header_str = " ".join(header_row)

            if not any(k in header_str for k in ["DN", "NPS", "NPT", "D1", "CÓDIGO", "CODIGO"]):
                continue

            # Map column names to indexes
            col_map = {}
            for idx, h in enumerate(header_row):
                if not h:
                    continue
                if h in ["DN", "NPS", "NPT"] or h.startswith("DN ") or h.startswith("NPS "):
                    col_map["size"] = idx
                elif "D1" in h or h == "D" or "DIÁMETRO" in h:
                    col_map["d"] = idx
                elif "L P H" in h or "L H" in h:
                    col_map["l_p_h"] = idx
                elif "L" == h:
                    col_map["l"] = idx
                elif "H" == h or "H1" in h:
                    col_map["h"] = idx
                elif h == "P" or "PALANCA" in h or "L1" in h:
                    col_map["l1"] = idx
                elif "PESO" in h or "WEIGHT" in h or "KG" in h:
                    col_map["weight"] = idx
                elif "ISO" in h:
                    col_map["iso"] = idx

            for row in table[1:]:
                clean_row = [(" ".join(c.replace('\n', ' ').split()).strip() if c else "") for c in row]
                if not any(clean_row):
                    continue

                full_text = " ".join(clean_row)
                if any(note in full_text.lower() for note in ["certificado", "correspondientes", "marca", "prueba", "norma"]):
                    continue

                # Remove product codes (10-15 digit numbers) from clean_row before size parsing
                clean_row_no_codes = [re.sub(r'^\d{8,15}\s*', '', cell) for cell in clean_row]

                # 1. Size extraction
                raw_nps = ""
                if "size" in col_map and col_map["size"] < len(clean_row_no_codes):
                    raw_nps = clean_row_no_codes[col_map["size"]]
                if not raw_nps:
                    match = re.search(r'(\d+\s*/\s*\d+\s*[\"\u201c\u201d\u00bd\u00be\u00bc]?|\d+(?:\.\d+)?\s*[\"\u201c\u201d\u00bd\u00be\u00bc]|\bDN\s*\d+|\b\d+\s*mm\b)', " ".join(clean_row_no_codes), re.IGNORECASE)
                    if match:
                        raw_nps = match.group(1)

                if not raw_nps or any(k in raw_nps for k in ["97/23", "0035", "0039", "CE", "PED"]):
                    continue

                nps_info = parse_nps_cell(raw_nps)
                dn_mm = nps_info['dn']
                if not nps_info['nps'] or dn_mm <= 0 or nps_info['dec_in'] <= 0.0 or nps_info['dec_in'] > 24.0:
                    continue

                l_val, d_val, h_val, l1_val, weight_val = 0.0, 0.0, 0.0, 0.0, 0.0
                iso_flange = ""

                # Handle grouped "L P H" column if present (e.g. "356 77 15" or "76 85")
                if "l_p_h" in col_map and col_map["l_p_h"] < len(clean_row_no_codes):
                    parts = clean_row_no_codes[col_map["l_p_h"]].split()
                    if len(parts) >= 1:
                        try:
                            l_val = float(parts[0])
                        except ValueError:
                            pass
                    if len(parts) >= 2:
                        try:
                            h_val = float(parts[1])
                        except ValueError:
                            pass

                if "l" in col_map and col_map["l"] < len(clean_row_no_codes) and l_val == 0.0:
                    try:
                        l_val = float(clean_row_no_codes[col_map["l"]])
                    except ValueError:
                        pass

                if "d" in col_map and col_map["d"] < len(clean_row_no_codes):
                    try:
                        d_val = float(clean_row_no_codes[col_map["d"]])
                    except ValueError:
                        pass

                if "h" in col_map and col_map["h"] < len(clean_row_no_codes) and h_val == 0.0:
                    try:
                        h_val = float(clean_row_no_codes[col_map["h"]])
                    except ValueError:
                        pass

                if "l1" in col_map and col_map["l1"] < len(clean_row_no_codes):
                    try:
                        l1_val = float(clean_row_no_codes[col_map["l1"]])
                    except ValueError:
                        pass

                if "weight" in col_map and col_map["weight"] < len(clean_row_no_codes):
                    try:
                        weight_val = float(clean_row_no_codes[col_map["weight"]])
                    except ValueError:
                        pass

                if "iso" in col_map and col_map["iso"] < len(clean_row_no_codes):
                    iso_flange = clean_row_no_codes[col_map["iso"]].upper()

                # Strict validation: Face-to-face length L is mandatory for all valves
                if l_val <= 0.0:
                    continue

                # Flanged valves require a valid flange OD (D > 0)
                is_flanged = "F2" in fig_model or "BRIDADA" in valve_type.upper()
                if is_flanged and d_val <= 0.0:
                    continue

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
                    weight_300=weight_val
                )
                dimensions.append(entry)

        return dimensions

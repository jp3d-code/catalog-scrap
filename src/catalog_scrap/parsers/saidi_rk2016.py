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
            dimensions = self._extract_dimensions(tables)

            if dimensions:
                catalog_item = CatalogItem(
                    manufacturer="Saidi Spain / RK Válvulas",
                    model=fig_model,
                    valve_type=valve_type,
                    dimensions=dimensions,
                    materials=materials,
                    metadata={
                        "parser": "SaidiRK2016Parser",
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
                # Clean up trailing words like 'Tipo:', 'piezas'
                raw_fig = raw_fig.split('Tipo:')[0].split('tipo:')[0].strip()
                raw_fig = re.sub(r'\s+(?:Tipo|tipo|1|2|3|piezas|pieza).*$', '', raw_fig, flags=re.IGNORECASE).strip()
                if raw_fig:
                    return raw_fig.replace(' ', '-')

            # Fallback check for model code in line (e.g. C15F2RB, S800NPT, C16F2)
            if any(k in line for k in ["C15F2", "C30F2", "C60F2", "C800", "S800", "2006SC", "I16F2", "C16F2", "S16F2", "C40F2", "S40F2"]):
                words = line.split()
                for w in words:
                    if re.match(r'^[CS]\d+[A-Z0-9]+', w):
                        return w
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
                return clean_type
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

    def _extract_dimensions(self, tables: List[List[List[str]]]) -> List[DimensionEntry]:
        dimensions = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            header_str = " ".join([" ".join(c.replace('\n', ' ').split()).upper() for c in table[0] if c])
            if not any(k in header_str for k in ["DN", "CÓDIGO", "CODIGO", "L", "H", "NPS", "NPT", "D1"]):
                continue

            for row in table[1:]:
                clean_cells = [" ".join(c.replace('\n', ' ').split()).strip() for c in row if c is not None and c.strip()]
                if not clean_cells:
                    continue

                full_text = " ".join(clean_cells)
                tokens = full_text.split()
                if not tokens:
                    continue

                # Skip header/footer notes (e.g. "97/23/CE", "Datos correspondientes...")
                if any(note in full_text.lower() for note in ["certificado", "correspondientes", "marca", "prueba", "norma"]):
                    continue

                # Token 0 product code check (10-15 digit number)
                code = ""
                if re.match(r'^\d{8,15}$', tokens[0]):
                    code = tokens.pop(0)

                rem_text = " ".join(tokens)

                # Match NPS / DN pattern
                nps_match = re.search(r'(\d+\s*/\s*\d+\s*[\"\u201c\u201d\u00bd\u00be\u00bc]?|\d+(?:\.\d+)?\s*[\"\u201c\u201d\u00bd\u00be\u00bc]|\bDN\s*\d+|\b\d+\s*mm\b)', rem_text, re.IGNORECASE)
                if not nps_match:
                    if tokens and tokens[0].isdigit() and int(tokens[0]) in [15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300]:
                        raw_nps = tokens.pop(0)
                    else:
                        continue
                else:
                    raw_nps = nps_match.group(1)

                # Ignore false match on standards like "97/23/CE"
                if "97/23" in raw_nps or "607" in raw_nps:
                    continue

                nps_info = parse_nps_cell(raw_nps)

                # Extract ISO Flange and numeric dimensions
                iso_flange = ""
                numbers = []
                for t in tokens:
                    t_clean = t.replace('"', '').strip()
                    if re.match(r'^F\d{2}$', t_clean, re.IGNORECASE):
                        iso_flange = t_clean.upper()
                        continue
                    try:
                        val = float(t_clean)
                        numbers.append(val)
                    except ValueError:
                        pass

                if len(numbers) >= 2:
                    # Select dimensions intelligently:
                    # In Saidi tables: D1 is flange OD, L is length, H is height, Weight is last number
                    l_val = 0.0
                    d_val = numbers[0]
                    h_val = 0.0
                    weight_val = numbers[-1] if len(numbers) >= 3 else 0.0

                    # Find length L (values typically between 75mm and 600mm)
                    for val in numbers[1:]:
                        if 70.0 <= val <= 1000.0 and l_val == 0.0:
                            l_val = val
                        elif val > 0 and h_val == 0.0 and val != l_val:
                            h_val = val

                    entry = DimensionEntry(
                        nps=nps_info['nps'],
                        dn=nps_info['dn'],
                        dec_in=nps_info['dec_in'],
                        h=h_val,
                        l1=0.0,
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

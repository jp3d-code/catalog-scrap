from typing import List
from catalog_scrap.core.base_parser import BaseParser
from catalog_scrap.core.models import CatalogItem, DimensionEntry
from catalog_scrap.parsers.utils import parse_nps_cell


class KlingerK200Parser(BaseParser):
    def parse(self, pdf_handle) -> List[CatalogItem]:
        """Parse tables from KLINGER INTEC K200 PDF page into a list containing 1 CatalogItem entity."""
        page = pdf_handle.pages[0]
        tables = page.extract_tables()

        materials = self._extract_materials(tables)
        dimensions = self._extract_dimensions(tables)

        item = CatalogItem(
            manufacturer="KLINGER Schöneberg",
            model="INTEC K200",
            valve_type="Flanged Ball Valve Full Bore",
            dimensions=dimensions,
            materials=materials,
            metadata={
                "parser": "KlingerK200Parser",
                "standards": {
                    "face_to_face": "ANSI B 16.10",
                    "flanges": "ANSI B 16.5"
                }
            }
        )
        return [item]

    def _extract_materials(self, tables) -> dict:
        materials = {}
        if len(tables) > 1:
            parts_table = tables[1]
            for row in parts_table:
                clean_cells = [c.strip() for c in row if c is not None and c.strip()]
                if len(clean_cells) >= 3:
                    part_no = clean_cells[0]
                    if part_no.isdigit():
                        part_name = clean_cells[1]
                        mat_str = " / ".join(clean_cells[2:])
                        materials[part_name] = mat_str
        return materials

    def _extract_dimensions(self, tables) -> list:
        dimensions = []
        if len(tables) > 3:
            dim_table = tables[3]
            data_rows = dim_table[3:]
            for row in data_rows:
                clean_cells = [c.strip() for c in row if c is not None and c.strip()]
                if len(clean_cells) >= 11:
                    nps_info = parse_nps_cell(clean_cells[0])

                    h_val = float(clean_cells[1])
                    l1_l150 = clean_cells[2].split()
                    l300_d150 = clean_cells[3].split()

                    l1_val = float(l1_l150[0])
                    l150_val = float(l1_l150[1])

                    l300_val = float(l300_d150[0])
                    d150_val = float(l300_d150[1])

                    d300_val = float(clean_cells[4])
                    e_val = float(clean_cells[5])
                    flange_iso = clean_cells[6]
                    torque_150 = float(clean_cells[7])
                    torque_300 = float(clean_cells[8])
                    weight_150 = float(clean_cells[9])
                    weight_300 = float(clean_cells[10])

                    entry = DimensionEntry(
                        nps=nps_info['nps'],
                        dn=nps_info['dn'],
                        dec_in=nps_info['dec_in'],
                        h=h_val,
                        l1=l1_val,
                        l_150=l150_val,
                        l_300=l300_val,
                        d_150=d150_val,
                        d_300=d300_val,
                        e=e_val,
                        iso_flange=flange_iso,
                        torque_150=torque_150,
                        torque_300=torque_300,
                        weight_150=weight_150,
                        weight_300=weight_300
                    )
                    dimensions.append(entry)
        return dimensions

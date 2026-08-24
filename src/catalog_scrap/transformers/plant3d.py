from typing import List, Dict, Any
from catalog_scrap.core.models import CatalogItem


class Plant3DTransformer:
    """Transform domain CatalogItem entity into flat records for Plant 3D catalog integration."""

    def transform(self, item: CatalogItem) -> List[Dict[str, Any]]:
        records = []
        materials = item.materials
        body_mat = materials.get('body', 'A216-WCB / ASTM A351-CF8M')
        ball_mat = materials.get('ball', '1.4408 (ASTM A351-CF8M)')
        stem_mat = materials.get('stem', '1.4462 (A479 UNS S31803)')
        seat_mat = materials.get('seat', 'KFGN/KFM')

        face_to_face_std = item.metadata.get('standards', {}).get('face_to_face', 'ANSI B 16.10')
        flange_std = item.metadata.get('standards', {}).get('flanges', 'ANSI B 16.5')

        for dim in item.dimensions:
            nps = dim.nps
            part_tag = nps.replace(' ', '').replace('"', 'IN')

            # Class 150 record
            rec_150 = {
                "Part_Number": f"{item.model.replace(' ', '-')}-{part_tag}-150LBS",
                "Manufacturer": item.manufacturer,
                "Model": item.model,
                "NPS_inch": nps,
                "DN_mm": dim.dn,
                "Class_lbs": 150,
                "H_mm": dim.h,
                "L1_mm": dim.l1,
                "L_mm": dim.l_150,
                "D_mm": dim.d_150,
                "E_mm": dim.e,
                "ISO_Flange": dim.iso_flange,
                "Torque_Nm": dim.torque_150,
                "Weight_kg": dim.weight_150,
                "Body_Material": body_mat,
                "Ball_Material": ball_mat,
                "Stem_Material": stem_mat,
                "Seat_Material": seat_mat,
                "Standard_Face_To_Face": face_to_face_std,
                "Standard_Flange": flange_std
            }
            records.append(rec_150)

            # Class 300 record
            rec_300 = {
                "Part_Number": f"{item.model.replace(' ', '-')}-{part_tag}-300LBS",
                "Manufacturer": item.manufacturer,
                "Model": item.model,
                "NPS_inch": nps,
                "DN_mm": dim.dn,
                "Class_lbs": 300,
                "H_mm": dim.h,
                "L1_mm": dim.l1,
                "L_mm": dim.l_300,
                "D_mm": dim.d_300,
                "E_mm": dim.e,
                "ISO_Flange": dim.iso_flange,
                "Torque_Nm": dim.torque_300,
                "Weight_kg": dim.weight_300,
                "Body_Material": body_mat,
                "Ball_Material": ball_mat,
                "Stem_Material": stem_mat,
                "Seat_Material": seat_mat,
                "Standard_Face_To_Face": face_to_face_std,
                "Standard_Flange": flange_std
            }
            records.append(rec_300)

        return records

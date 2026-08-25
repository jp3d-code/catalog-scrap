from typing import List, Dict, Any, Union
from catalog_scrap.core.models import CatalogItem


class Plant3DTransformer:
    """Transform domain CatalogItem entity (or list of entities) into flat records for Plant 3D integration."""

    def transform(self, items: Union[CatalogItem, List[CatalogItem]]) -> List[Dict[str, Any]]:
        if isinstance(items, CatalogItem):
            items_list = [items]
        else:
            items_list = items

        all_records = []
        for item in items_list:
            records = self._transform_single_item(item)
            all_records.extend(records)

        return all_records

    def _transform_single_item(self, item: CatalogItem) -> List[Dict[str, Any]]:
        records = []
        materials = item.materials
        body_mat = materials.get('cuerpo', materials.get('Cuerpo', materials.get('body', 'WCB / CF8M')))
        ball_mat = materials.get('esfera', materials.get('Esfera', materials.get('ball', 'F316 / 1.4408')))
        stem_mat = materials.get('eje', materials.get('Eje', materials.get('husillo', materials.get('stem', 'F316 / 1.4462'))))
        seat_mat = materials.get('asiento', materials.get('Asiento', materials.get('seat', 'PTFE / R-TFE')))

        face_to_face_std = item.metadata.get('standards', {}).get('face_to_face', 'ANSI B 16.10 / DIN')
        flange_std = item.metadata.get('standards', {}).get('flanges', 'ANSI B 16.5 / DIN')

        for dim in item.dimensions:
            nps = dim.nps
            part_tag = nps.replace(' ', '').replace('"', 'IN')
            model_slug = item.model.replace(' ', '-').replace('/', '-')
            default_class = item.metadata.get('pressure_class', '150LBS')

            # Handle dual-class entries (e.g. 150LBS and 300LBS in same row)
            if dim.l_150 > 0 and dim.l_300 > 0 and dim.l_150 != dim.l_300:
                rec_150 = {
                    "Part_Number": f"{model_slug}-{part_tag}-150LBS",
                    "Manufacturer": item.manufacturer,
                    "Model": item.model,
                    "Valve_Type": item.valve_type,
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

                rec_300 = {
                    "Part_Number": f"{model_slug}-{part_tag}-300LBS",
                    "Manufacturer": item.manufacturer,
                    "Model": item.model,
                    "Valve_Type": item.valve_type,
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
            else:
                rec = {
                    "Part_Number": f"{model_slug}-{part_tag}-{default_class}",
                    "Manufacturer": item.manufacturer,
                    "Model": item.model,
                    "Valve_Type": item.valve_type,
                    "NPS_inch": nps,
                    "DN_mm": dim.dn,
                    "Class_lbs": default_class,
                    "H_mm": dim.h,
                    "L1_mm": dim.l1,
                    "L_mm": dim.l_150 if dim.l_150 > 0 else dim.l_300,
                    "D_mm": dim.d_150 if dim.d_150 > 0 else dim.d_300,
                    "E_mm": dim.e,
                    "ISO_Flange": dim.iso_flange,
                    "Torque_Nm": dim.torque_150 if dim.torque_150 > 0 else dim.torque_300,
                    "Weight_kg": dim.weight_150 if dim.weight_150 > 0 else dim.weight_300,
                    "Body_Material": body_mat,
                    "Ball_Material": ball_mat,
                    "Stem_Material": stem_mat,
                    "Seat_Material": seat_mat,
                    "Standard_Face_To_Face": face_to_face_std,
                    "Standard_Flange": flange_std
                }
                records.append(rec)

        return records


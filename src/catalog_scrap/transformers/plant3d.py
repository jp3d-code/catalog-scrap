import re
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

    def _resolve_geometry_template(self, model: str, valve_type: str) -> str:
        m = model.upper()
        vt = valve_type.upper()
        if "HANDWHEEL" in vt or "VOLANTE" in vt:
            return "BALL_VALVE_HANDWHEEL"
        if "3 PIEZAS" in vt or "3PC" in vt or "2013S" in m or "2011S" in m:
            return "BALL_VALVE_3PC_THREADED"
        if "NPT" in m or "800LBS" in vt or "1 PIEZA" in vt:
            return "BALL_VALVE_1PC_COMPACT"
        return "BALL_VALVE_2PC_FLANGED"

    def _transform_single_item(self, item: CatalogItem) -> List[Dict[str, Any]]:
        records = []
        materials = item.materials
        body_mat = materials.get('cuerpo', materials.get('Cuerpo', materials.get('body', 'WCB / CF8M')))
        ball_mat = materials.get('esfera', materials.get('Esfera', materials.get('ball', 'F316 / 1.4408')))
        stem_mat = materials.get('eje', materials.get('Eje', materials.get('husillo', materials.get('stem', 'F316 / 1.4462'))))
        seat_mat = materials.get('asiento', materials.get('Asiento', materials.get('seat', 'PTFE / R-TFE')))

        face_to_face_std = item.metadata.get('standards', {}).get('face_to_face', 'ANSI B 16.10 / DIN')
        flange_std = item.metadata.get('standards', {}).get('flanges', 'ANSI B 16.5 / DIN')
        geom_template = self._resolve_geometry_template(item.model, item.valve_type)

        seen_part_numbers = set()
        is_generic = getattr(item, "extraction_type", "specific") == "generic"

        for dim in item.dimensions:
            nps = dim.nps
            part_tag = nps.replace(' ', '').replace('"', 'IN').replace('/', '-')
            model_slug = re.sub(r'-{2,}', '-', item.model.replace(' ', '-').replace('/', '-')).strip('-')
            default_class = item.metadata.get('pressure_class', '150LBS')

            # Handle dual-class entries (e.g. 150LBS and 300LBS in same row)
            if dim.l_150 > 0 and dim.l_300 > 0 and dim.l_150 != dim.l_300:
                pn_150 = f"{model_slug}-{part_tag}-150LBS"
                if pn_150 not in seen_part_numbers:
                    seen_part_numbers.add(pn_150)
                    if is_generic:
                        rec_150 = {
                            "Part_Number": pn_150,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "NPS_inch": nps,
                            "DN_mm": dim.dn,
                            "Class_lbs": 150,
                            "L_mm": dim.l_150,
                            "D_mm": dim.d_150,
                            "Body_Material": body_mat,
                            "Standard_Face_To_Face": face_to_face_std,
                            "Standard_Flange": flange_std
                        }
                    else:
                        rec_150 = {
                            "Part_Number": pn_150,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "Operator_Type": "LEVER",
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

                pn_300 = f"{model_slug}-{part_tag}-300LBS"
                if pn_300 not in seen_part_numbers:
                    seen_part_numbers.add(pn_300)
                    if is_generic:
                        rec_300 = {
                            "Part_Number": pn_300,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "NPS_inch": nps,
                            "DN_mm": dim.dn,
                            "Class_lbs": 300,
                            "L_mm": dim.l_300,
                            "D_mm": dim.d_300,
                            "Body_Material": body_mat,
                            "Standard_Face_To_Face": face_to_face_std,
                            "Standard_Flange": flange_std
                        }
                    else:
                        rec_300 = {
                            "Part_Number": pn_300,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "Operator_Type": "LEVER",
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
                pn = f"{model_slug}-{part_tag}-{default_class}"
                if pn not in seen_part_numbers:
                    seen_part_numbers.add(pn)
                    if is_generic:
                        rec = {
                            "Part_Number": pn,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "NPS_inch": nps,
                            "DN_mm": dim.dn,
                            "Class_lbs": default_class,
                            "L_mm": dim.l_150 if dim.l_150 > 0 else dim.l_300,
                            "D_mm": dim.d_150 if dim.d_150 > 0 else dim.d_300,
                            "Body_Material": body_mat,
                            "Standard_Face_To_Face": face_to_face_std,
                            "Standard_Flange": flange_std
                        }
                    else:
                        rec = {
                            "Part_Number": pn,
                            "Manufacturer": item.manufacturer,
                            "Model": item.model,
                            "Valve_Type": item.valve_type,
                            "Geometry_Template": geom_template,
                            "Operator_Type": "LEVER",
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



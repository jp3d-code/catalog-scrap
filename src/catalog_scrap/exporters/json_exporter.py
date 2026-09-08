import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from catalog_scrap.core.base_exporter import BaseExporter


class DatasheetJSONExporter:
    """
    Dedicated Exporter for Component Datasheets (Specific Piece Mode).
    GUARANTEES A SINGLE SELF-CONTAINED JSON FILE with 0 redundant subdirectories or manifests.
    """

    def export(self, item: Any, plant3d_records: List[Dict[str, Any]], destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)

        dimensions_data = [d.to_dict() for d in item.dimensions]
        parts_data = [
            (p.to_dict() if hasattr(p, "to_dict") else p)
            for p in getattr(item, "parts_bom", getattr(item, "parts_list", []))
        ]

        payload = {
            "model": item.model,
            "manufacturer": item.manufacturer,
            "valve_type": item.valve_type,
            "extraction_type": "specific",
            "metadata": item.metadata,
            "standards": getattr(item, "standards", item.metadata.get("standards", {})),
            "design_features": getattr(item, "design_features", item.metadata.get("design_features", [])),
            "materials": item.materials,
            "parts_bom": parts_data,
            "dimensions_count": len(dimensions_data),
            "dimensions_table": dimensions_data,
            "plant3d_records_count": len(plant3d_records),
            "plant3d_records": plant3d_records
        }

        with open(destination, mode="w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"[DatasheetJSONExporter] Successfully exported Single Component Specification: {destination}")
        return destination


class CatalogJSONExporter(BaseExporter):
    """
    Dedicated Exporter for Commercial Catalogs (Generic Catalog Mode).
    Generates structured manifest.json and lean per-model files (L & D only)
    for direct ingestion into AutoCAD Plant 3D SQLite .pcat catalogs.
    """

    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None, mode: str = "both") -> None:
        if not records:
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        meta = metadata or {}

        # 1. Group records by model
        grouped_by_model: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            model_name = str(rec.get("Model", "UNKNOWN")).replace(" ", "-").replace("/", "-")
            grouped_by_model.setdefault(model_name, []).append(rec)

        # 2. Master Consolidated JSON File
        if mode in ("consolidated", "both"):
            payload = {
                "metadata": meta,
                "items": records
            }
            with open(destination, mode="w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"[CatalogJSONExporter] Successfully exported Master Consolidated JSON: {destination}")

        # 3. Catalog Manifest & Clean Individual Model JSON Files
        if mode in ("split", "both"):
            catalog_dir = destination.parent / destination.stem.replace('_plant3d', '')
            catalog_dir.mkdir(parents=True, exist_ok=True)

            models_index = []

            for model_name, model_records in grouped_by_model.items():
                first_rec = model_records[0] if model_records else {}
                model_filename = f"{model_name}.json"
                model_json_path = catalog_dir / model_filename

                geom_template = first_rec.get("Geometry_Template", "BALL_VALVE_2PC_FLANGED")
                op_type = first_rec.get("Operator_Type", "LEVER")

                models_index.append({
                    "model": model_name,
                    "manufacturer": first_rec.get("Manufacturer", ""),
                    "valve_type": first_rec.get("Valve_Type", ""),
                    "geometry_template": geom_template,
                    "operator_type": op_type,
                    "records_count": len(model_records),
                    "file": model_filename
                })

                # Model JSON payload: ONLY clean model-specific data
                model_payload = {
                    "model": model_name,
                    "manufacturer": first_rec.get("Manufacturer", ""),
                    "valve_type": first_rec.get("Valve_Type", ""),
                    "geometry_template": geom_template,
                    "operator_type": op_type,
                    "records_count": len(model_records),
                    "standards": {
                        "face_to_face": first_rec.get("Standard_Face_To_Face", ""),
                        "flanges": first_rec.get("Standard_Flange", "")
                    },
                    "items": model_records
                }
                with open(model_json_path, mode="w", encoding="utf-8") as f:
                    json.dump(model_payload, f, indent=2, ensure_ascii=False)

            # Generate manifest.json for catalog index
            manifest_payload = {
                "source_catalog": meta.get("source_catalog", destination.name),
                "generated_at": datetime.now().isoformat(),
                "total_models": len(grouped_by_model),
                "total_records": len(records),
                "models": models_index
            }
            manifest_path = catalog_dir / "manifest.json"
            with open(manifest_path, mode="w", encoding="utf-8") as f:
                json.dump(manifest_payload, f, indent=2, ensure_ascii=False)
            print(f"[CatalogJSONExporter] Successfully exported Catalog Manifest ({manifest_path}) and {len(grouped_by_model)} clean model JSON files.")


class JSONExporter(BaseExporter):
    """
    Unified JSON Exporter Facade.
    Provides backward-compatible export() and export_specification() methods.
    """

    def __init__(self):
        self._datasheet_exporter = DatasheetJSONExporter()
        self._catalog_exporter = CatalogJSONExporter()

    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None, mode: str = "both") -> None:
        self._catalog_exporter.export(records, destination, metadata=metadata, mode=mode)

    def export_specification(self, catalog_item: Any, plant3d_records: List[Dict[str, Any]], destination: Path) -> Path:
        return self._datasheet_exporter.export(catalog_item, plant3d_records, destination)

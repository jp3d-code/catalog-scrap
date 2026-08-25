import json
from pathlib import Path
from typing import List, Dict, Any
from catalog_scrap.core.base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None) -> None:
        """
        Export records to JSON.
        Generates both:
        1. Master consolidated JSON file at `destination`.
        2. Individual model JSON files under `destination.parent / destination.stem / <Model>.json`.
        """
        if not records:
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": metadata or {},
            "items": records
        }

        # 1. Master JSON File
        with open(destination, mode="w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Successfully exported Master JSON: {destination}")

        # 2. Individual Model JSON Files
        models_dir = destination.parent / destination.stem.replace('_plant3d', '')
        models_dir.mkdir(parents=True, exist_ok=True)

        grouped_by_model: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            model_name = str(rec.get("Model", "UNKNOWN")).replace(" ", "-").replace("/", "-")
            grouped_by_model.setdefault(model_name, []).append(rec)

        for model_name, model_records in grouped_by_model.items():
            model_json_path = models_dir / f"{model_name}.json"
            model_payload = {
                "metadata": {
                    **(metadata or {}),
                    "model": model_name,
                    "records_count": len(model_records)
                },
                "items": model_records
            }
            with open(model_json_path, mode="w", encoding="utf-8") as f:
                json.dump(model_payload, f, indent=2, ensure_ascii=False)

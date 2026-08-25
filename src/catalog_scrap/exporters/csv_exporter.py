import csv
from pathlib import Path
from typing import List, Dict, Any
from catalog_scrap.core.base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None) -> None:
        """
        Export records to CSV.
        Generates both:
        1. Master consolidated CSV file at `destination`.
        2. Individual model CSV files under `destination.parent / destination.stem / <Model>.csv`.
        """
        if not records:
            print(f"[CSVExporter] No records to export to {destination}")
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(records[0].keys())

        # 1. Export Master Consolidated CSV File
        with open(destination, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"Successfully exported Master CSV: {destination} ({len(records)} total records)")

        # 2. Export Individual Model CSV Files
        models_dir = destination.parent / destination.stem.replace('_plant3d', '')
        models_dir.mkdir(parents=True, exist_ok=True)

        grouped_by_model: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            model_name = str(rec.get("Model", "UNKNOWN")).replace(" ", "-").replace("/", "-")
            grouped_by_model.setdefault(model_name, []).append(rec)

        for model_name, model_records in grouped_by_model.items():
            model_csv_path = models_dir / f"{model_name}.csv"
            with open(model_csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(model_records)

        print(f"Successfully exported {len(grouped_by_model)} individual model CSV files in: {models_dir}")

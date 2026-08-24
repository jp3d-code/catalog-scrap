import csv
from pathlib import Path
from typing import List, Dict, Any
from catalog_scrap.core.base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not records:
            return

        fieldnames = list(records[0].keys())
        with open(destination, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        print(f"Successfully exported CSV: {destination} ({len(records)} records)")

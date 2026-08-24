import json
from pathlib import Path
from typing import List, Dict, Any
from catalog_scrap.core.base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": metadata or {},
            "items": records
        }
        with open(destination, mode="w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Successfully exported JSON: {destination}")

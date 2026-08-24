from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BaseExporter(ABC):
    @abstractmethod
    def export(self, records: List[Dict[str, Any]], destination: Path, metadata: Dict[str, Any] = None) -> None:
        """Export formatted dictionary records to target file destination."""
        pass

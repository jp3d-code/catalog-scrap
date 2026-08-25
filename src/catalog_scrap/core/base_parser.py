from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List
from catalog_scrap.core.models import CatalogItem


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_content: Any) -> List[CatalogItem]:
        """Parse raw content from loader into a list of CatalogItem domain entities."""
        pass

    @classmethod
    def can_handle(cls, pdf_path: Path, text_sample: str = "") -> bool:
        """Return True if this parser can handle the given PDF file based on path or text snippet."""
        return False


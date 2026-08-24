from abc import ABC, abstractmethod
from typing import Any
from catalog_scrap.core.models import CatalogItem


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_content: Any) -> CatalogItem:
        """Parse raw content from loader into a CatalogItem domain entity."""
        pass

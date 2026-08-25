from abc import ABC, abstractmethod
from typing import Any, List
from catalog_scrap.core.models import CatalogItem


class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_content: Any) -> List[CatalogItem]:
        """Parse raw content from loader into a list of CatalogItem domain entities."""
        pass

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseLoader(ABC):
    @abstractmethod
    def load(self, source_path: Path) -> Any:
        """Load source file content and return raw handles/objects."""
        pass

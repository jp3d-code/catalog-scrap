from pathlib import Path
import pdfplumber
from catalog_scrap.core.base_loader import BaseLoader


class PdfLoader(BaseLoader):
    def load(self, source_path: Path):
        """Open PDF document using pdfplumber and return handle."""
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {source_path}")
        return pdfplumber.open(source_path)

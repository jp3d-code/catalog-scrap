from pathlib import Path
import pdfplumber
import pymupdf
from catalog_scrap.core.base_loader import BaseLoader


class PdfDocumentHandle:
    """Unified PDF document handle supporting both pdfplumber and pymupdf."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._plumber = None
        self._pymupdf = None

    @property
    def plumber(self):
        if self._plumber is None:
            self._plumber = pdfplumber.open(self.path)
        return self._plumber

    @property
    def pymupdf(self):
        if self._pymupdf is None:
            self._pymupdf = pymupdf.open(self.path)
        return self._pymupdf

    @property
    def pages(self):
        return self.plumber.pages

    def close(self):
        if self._plumber is not None:
            try:
                self._plumber.close()
            except Exception:
                pass
        if self._pymupdf is not None:
            try:
                self._pymupdf.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PdfLoader(BaseLoader):
    def load(self, source_path: Path) -> PdfDocumentHandle:
        """Open PDF document and return unified handle."""
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {source_path}")
        return PdfDocumentHandle(source_path)

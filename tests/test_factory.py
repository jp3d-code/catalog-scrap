import unittest
from pathlib import Path
from catalog_scrap.core.factory import CatalogParserFactory
from catalog_scrap.parsers.saidi_rk2016 import SaidiRK2016Parser
from catalog_scrap.parsers.klinger_k200 import KlingerK200Parser


class TestCatalogParserFactory(unittest.TestCase):
    def test_auto_detect_saidi(self):
        pdf_path = Path("docs/CATALOGO_VAL_BOLA_2016-44.pdf")
        parser = CatalogParserFactory.get_parser(pdf_path)
        self.assertIsInstance(parser, SaidiRK2016Parser)

    def test_auto_detect_klinger(self):
        pdf_path = Path("docs/INTEC-K200-NPS1-24inch-eng.pdf")
        parser = CatalogParserFactory.get_parser(pdf_path)
        self.assertIsInstance(parser, KlingerK200Parser)

    def test_explicit_adapter(self):
        pdf_path = Path("docs/some_file.pdf")
        parser = CatalogParserFactory.get_parser(pdf_path, adapter_name="saidi_rk2016")
        self.assertIsInstance(parser, SaidiRK2016Parser)


if __name__ == "__main__":
    unittest.main()

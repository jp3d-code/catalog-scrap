from pathlib import Path
from typing import Optional, Type, Dict
from catalog_scrap.core.base_parser import BaseParser
from catalog_scrap.parsers.klinger_k200 import KlingerK200Parser
from catalog_scrap.parsers.saidi_rk2016 import SaidiRK2016Parser


class CatalogParserFactory:
    _REGISTRY: Dict[str, Type[BaseParser]] = {
        "klinger_k200": KlingerK200Parser,
        "saidi_rk2016": SaidiRK2016Parser,
    }

    @classmethod
    def get_parser(cls, pdf_path: Path, adapter_name: Optional[str] = None) -> BaseParser:
        """Instantiate the appropriate BaseParser implementation for the given PDF file."""
        if adapter_name and adapter_name.lower() in cls._REGISTRY:
            parser_cls = cls._REGISTRY[adapter_name.lower()]
            print(f"[CatalogParserFactory] Using explicitly specified adapter: {adapter_name}")
            return parser_cls()

        # Auto-detect parser by querying registered parser classes via can_handle()
        for name, parser_cls in cls._REGISTRY.items():
            if parser_cls.can_handle(pdf_path):
                print(f"[CatalogParserFactory] Auto-detected adapter: '{name}' for {pdf_path.name}")
                return parser_cls()

        # Default fallback
        print(f"[CatalogParserFactory] Fallback to default adapter: 'klinger_k200'")
        return KlingerK200Parser()


    @classmethod
    def register_parser(cls, name: str, parser_cls: Type[BaseParser]) -> None:
        """Register a new catalog parser adapter dynamically."""
        cls._REGISTRY[name.lower()] = parser_cls
        print(f"[CatalogParserFactory] Registered new adapter: {name}")

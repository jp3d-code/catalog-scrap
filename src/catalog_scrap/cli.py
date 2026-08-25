import argparse
from pathlib import Path
from catalog_scrap.core import CatalogParserFactory
from catalog_scrap.loaders import PdfLoader
from catalog_scrap.transformers import Plant3DTransformer
from catalog_scrap.exporters import JSONExporter, CSVExporter


def run_pipeline(pdf_path: Path, output_dir: Path, adapter_name: str = None, export_csv: bool = False, mode: str = "both") -> None:
    print(f"==================================================")
    print(f"Catalog Scraping Pipeline (JSON Output)")
    print(f"Target PDF: {pdf_path}")
    print(f"Export Mode: {mode}")
    print(f"==================================================")

    if not pdf_path.exists():
        print(f"[Error] Specified PDF file does not exist: {pdf_path}")
        return

    # 1. Ingest PDF
    loader = PdfLoader()
    with loader.load(pdf_path) as pdf_handle:
        # 2. Get Parser from Factory and Parse PDF
        parser = CatalogParserFactory.get_parser(pdf_path, adapter_name)
        catalog_items = parser.parse(pdf_handle)

    print(f"[Pipeline] Successfully parsed {len(catalog_items)} catalog entities.")

    # 3. Transform Entities to Plant 3D Records
    transformer = Plant3DTransformer()
    plant3d_records = transformer.transform(catalog_items)
    print(f"[Pipeline] Generated {len(plant3d_records)} Plant 3D component records.")

    # 4. Export Records (JSON Primary)
    stem_name = pdf_path.stem.replace(' ', '_')
    json_path = output_dir / f"{stem_name}_plant3d.json"

    json_exporter = JSONExporter()
    json_exporter.export(plant3d_records, json_path, metadata={
        "source_catalog": pdf_path.name,
        "total_models": len(catalog_items),
        "total_records": len(plant3d_records),
        "models_summary": [item.model for item in catalog_items]
    }, mode=mode)

    if export_csv:
        csv_path = output_dir / f"{stem_name}_plant3d.csv"
        csv_exporter = CSVExporter()
        csv_exporter.export(plant3d_records, csv_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Catalog Scrap Pipeline for AutoCAD Plant 3D")
    parser.add_argument(
        "--pdf",
        type=str,
        default="docs/CATALOGO_VAL_BOLA_2016-44.pdf",
        help="Path to PDF catalog file (default: docs/CATALOGO_VAL_BOLA_2016-44.pdf)"
    )
    parser.add_argument(
        "--adapter",
        type=str,
        default=None,
        help="Adapter name: klinger_k200, saidi_rk2016, or leave blank for auto-detection"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory (default: output/)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["split", "consolidated", "both"],
        default="both",
        help="Export mode: 'split' (manifest + model files), 'consolidated' (single master JSON), or 'both' (default)"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also export legacy CSV files (disabled by default)"
    )

    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)

    run_pipeline(pdf_path, output_dir, args.adapter, export_csv=args.csv, mode=args.mode)



if __name__ == "__main__":
    main()

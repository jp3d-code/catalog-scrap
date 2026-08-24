from pathlib import Path
from catalog_scrap.loaders import PdfLoader
from catalog_scrap.parsers import KlingerK200Parser
from catalog_scrap.transformers import Plant3DTransformer
from catalog_scrap.exporters import CSVExporter, JSONExporter


def run_pipeline(pdf_path: Path, output_dir: Path) -> None:
    print(f"Starting catalog scraping pipeline for: {pdf_path}")

    # 1. Ingest PDF
    loader = PdfLoader()
    with loader.load(pdf_path) as pdf_handle:
        # 2. Parse PDF to Domain Entity
        parser = KlingerK200Parser()
        catalog_item = parser.parse(pdf_handle)

    print(f"Parsed catalog: {catalog_item.manufacturer} {catalog_item.model}")
    print(f"Extracted {len(catalog_item.dimensions)} dimension entries and {len(catalog_item.materials)} materials.")

    # 3. Transform Domain Entity to Plant 3D Records
    transformer = Plant3DTransformer()
    plant3d_records = transformer.transform(catalog_item)

    # 4. Export Records
    csv_exporter = CSVExporter()
    json_exporter = JSONExporter()

    csv_path = output_dir / "INTEC_K200_plant3d.csv"
    json_path = output_dir / "INTEC_K200_plant3d.json"

    csv_exporter.export(plant3d_records, csv_path)
    json_exporter.export(plant3d_records, json_path, metadata={
        "source_catalog": pdf_path.name,
        "manufacturer": catalog_item.manufacturer,
        "model": catalog_item.model,
        "total_variants": len(plant3d_records),
        "materials_scraped": catalog_item.materials
    })


def main() -> None:
    pdf_file = Path("docs/INTEC-K200-NPS1-24inch-eng.pdf")
    output_directory = Path("output")
    run_pipeline(pdf_file, output_directory)


if __name__ == "__main__":
    main()

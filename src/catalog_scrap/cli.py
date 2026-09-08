import argparse
from pathlib import Path
from catalog_scrap.core import CatalogParserFactory
from catalog_scrap.loaders import PdfLoader
from catalog_scrap.transformers import Plant3DTransformer
from catalog_scrap.exporters import JSONExporter, CSVExporter


def run_pipeline(
    pdf_path: Path,
    output_dir: Path,
    adapter_name: str = None,
    export_csv: bool = False,
    mode: str = "both",
    extraction_type: str = "auto"
) -> None:
    print(f"==================================================")
    print(f"Catalog Scraping Pipeline")
    print(f"Target PDF: {pdf_path}")
    print(f"Requested Extraction Type: {extraction_type}")
    print(f"Export Mode: {mode}")
    print(f"==================================================")

    # Resolve default path variations if needed
    if not pdf_path.exists():
        fallback_candidates = [
            Path("docs/catalogs") / pdf_path.name,
            Path("docs/specifications") / pdf_path.name,
            Path("docs") / pdf_path.name
        ]
        found = False
        for cand in fallback_candidates:
            if cand.exists():
                pdf_path = cand
                found = True
                print(f"[Pipeline] Found PDF at resolved path: {pdf_path}")
                break
        if not found:
            print(f"[Error] Specified PDF file does not exist: {pdf_path}")
            return

    # 1. Ingest PDF
    loader = PdfLoader()
    with loader.load(pdf_path) as pdf_handle:
        # 2. Get Parser from Factory and Parse PDF
        parser = CatalogParserFactory.get_parser(pdf_path, adapter_name)
        catalog_items = parser.parse(pdf_handle)

    if not catalog_items:
        print("[Pipeline] No catalog entities were extracted.")
        return

    # Resolve extraction type
    if extraction_type == "auto":
        parts = [p.lower() for p in pdf_path.parts]
        if "specifications" in parts or any(k in pdf_path.name.upper() for k in ["INTEC", "K200", "SPEC"]):
            effective_type = "specific"
        elif "catalogs" in parts or any(k in pdf_path.name.upper() for k in ["CATALOGO", "CATALOG"]):
            effective_type = "generic"
        else:
            effective_type = getattr(catalog_items[0], "extraction_type", "generic")
    else:
        effective_type = extraction_type

    for it in catalog_items:
        it.extraction_type = effective_type

    is_specific = (effective_type == "specific")
    print(f"[Pipeline] Successfully parsed {len(catalog_items)} catalog entities (Mode: {'SPECIFIC (Detailed)' if is_specific else 'GENERIC (L & D Only)'}).")

    # 3. Transform Entities to Plant 3D Records
    transformer = Plant3DTransformer()
    plant3d_records = transformer.transform(catalog_items)
    print(f"[Pipeline] Generated {len(plant3d_records)} Plant 3D component records.")

    # 4. Route Output Directory
    if output_dir == Path("output"):
        effective_output_dir = output_dir / ("specifications" if is_specific else "catalogs")
    else:
        effective_output_dir = output_dir
    effective_output_dir.mkdir(parents=True, exist_ok=True)

    json_exporter = JSONExporter()
    stem_name = pdf_path.stem.replace(' ', '_')

    # 5. Export Records
    if is_specific:
        # Detailed Component Mode: Export exhaustive JSON for each model
        for item in catalog_items:
            item_records = [r for r in plant3d_records if r.get("Model") == item.model]
            if not item_records:
                item_records = plant3d_records
            spec_json_path = effective_output_dir / f"{item.model.replace(' ', '_')}.json"
            json_exporter.export_specification(item, item_records, spec_json_path)

        # Also export catalog format if split or consolidated requested
        if mode in ("consolidated", "both", "split"):
            catalog_json_path = effective_output_dir / f"{stem_name}_plant3d.json"
            json_exporter.export(plant3d_records, catalog_json_path, metadata={
                "source_catalog": pdf_path.name,
                "extraction_type": "specific",
                "total_models": len(catalog_items),
                "total_records": len(plant3d_records),
                "models_summary": [it.model for it in catalog_items]
            }, mode=mode)
    else:
        # Generic Catalog Mode: Standardized L & D catalog export
        json_path = effective_output_dir / f"{stem_name}_plant3d.json"
        json_exporter.export(plant3d_records, json_path, metadata={
            "source_catalog": pdf_path.name,
            "extraction_type": "generic",
            "total_models": len(catalog_items),
            "total_records": len(plant3d_records),
            "models_summary": [it.model for it in catalog_items]
        }, mode=mode)

    if export_csv:
        csv_path = effective_output_dir / f"{stem_name}_plant3d.csv"
        csv_exporter = CSVExporter()
        csv_exporter.export(plant3d_records, csv_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Catalog Scrap Pipeline for AutoCAD Plant 3D")
    parser.add_argument(
        "--pdf",
        type=str,
        default="docs/catalogs/CATALOGO_VAL_BOLA_2016-44.pdf",
        help="Path to PDF catalog or specification file"
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
        "--type",
        dest="extraction_type",
        type=str,
        choices=["auto", "specific", "generic"],
        default="auto",
        help="Extraction type: 'specific' (full detailed part datasheet), 'generic' (standardized L & D catalog), or 'auto' (default)"
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

    run_pipeline(
        pdf_path=pdf_path,
        output_dir=output_dir,
        adapter_name=args.adapter,
        export_csv=args.csv,
        mode=args.mode,
        extraction_type=args.extraction_type
    )


if __name__ == "__main__":
    main()

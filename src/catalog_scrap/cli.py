import argparse
import sys
from pathlib import Path
from typing import Optional

from catalog_scrap.core import CatalogParserFactory
from catalog_scrap.loaders import PdfLoader
from catalog_scrap.transformers import DatasheetPlant3DTransformer, CatalogPlant3DTransformer
from catalog_scrap.exporters import DatasheetJSONExporter, CatalogJSONExporter, CSVExporter


def resolve_pdf_path(pdf_str: str) -> Optional[Path]:
    """Resolve PDF path supporting direct paths or fallbacks into docs folders."""
    p = Path(pdf_str)
    if p.exists():
        return p

    candidates = [
        Path("docs/specifications") / p.name,
        Path("docs/catalogs") / p.name,
        Path("docs") / p.name
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    return None


def run_spec_pipeline(pdf_path: Path, output_dir: Path, adapter_name: Optional[str] = None) -> None:
    """
    Datasheet Engine (Specific Piece Mode).
    Extracts 100% of engineering parameters, BOM and standards, producing
    EXACTLY ONE SELF-CONTAINED JSON FILE in output_dir.
    """
    resolved_pdf = resolve_pdf_path(str(pdf_path))
    if not resolved_pdf:
        print(f"[Error] Datasheet PDF file not found: {pdf_path}")
        return

    print(f"==================================================")
    print(f"Datasheet Engine (Specific Component Mode)")
    print(f"Target PDF: {resolved_pdf}")
    print(f"==================================================")

    # 1. Ingest PDF
    loader = PdfLoader()
    with loader.load(resolved_pdf) as pdf_handle:
        parser = CatalogParserFactory.get_parser(resolved_pdf, adapter_name)
        items = parser.parse(pdf_handle)

    if not items:
        print(f"[Datasheet Engine] No components parsed from: {resolved_pdf}")
        return

    item = items[0]
    clean_model_name = item.model.replace(' ', '_').replace('/', '_')

    # 2. Transform to Plant 3D detailed records
    transformer = DatasheetPlant3DTransformer()
    plant3d_records = transformer.transform(item)
    print(f"[Datasheet Engine] Generated {len(plant3d_records)} detailed Plant 3D component records.")

    # 3. Export SINGLE canonical specification JSON file
    out_dir = output_dir if output_dir != Path("output") else Path("output/specifications")
    out_dir.mkdir(parents=True, exist_ok=True)

    dest_file = out_dir / f"{clean_model_name}.json"
    exporter = DatasheetJSONExporter()
    exporter.export(item, plant3d_records, dest_file)

    print(f"[OK] Successfully generated single specification file: {dest_file}")


def run_catalog_pipeline(
    pdf_path: Path,
    output_dir: Path,
    adapter_name: Optional[str] = None,
    mode: str = "both",
    export_csv: bool = False
) -> None:
    """
    Catalog Engine (Generic Commercial Catalog Mode).
    Extracts multi-family catalog components strictly focusing on L & D,
    producing catalog manifest.json and clean per-model JSON files.
    """
    resolved_pdf = resolve_pdf_path(str(pdf_path))
    if not resolved_pdf:
        print(f"[Error] Catalog PDF file not found: {pdf_path}")
        return

    print(f"==================================================")
    print(f"Catalog Engine (Generic Commercial Catalog Mode)")
    print(f"Target PDF: {resolved_pdf}")
    print(f"Export Mode: {mode}")
    print(f"==================================================")

    # 1. Ingest PDF
    loader = PdfLoader()
    with loader.load(resolved_pdf) as pdf_handle:
        parser = CatalogParserFactory.get_parser(resolved_pdf, adapter_name)
        items = parser.parse(pdf_handle)

    if not items:
        print(f"[Catalog Engine] No catalog items parsed from: {resolved_pdf}")
        return

    # 2. Transform to lean Plant 3D records (L & D only)
    transformer = CatalogPlant3DTransformer()
    all_records = []
    for it in items:
        all_records.extend(transformer.transform(it))

    print(f"[Catalog Engine] Extracted {len(items)} models, generated {len(all_records)} lean catalog records.")

    # 3. Export catalog manifest & model files
    out_dir = output_dir if output_dir != Path("output") else Path("output/catalogs")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem_name = resolved_pdf.stem.replace(' ', '_')
    json_path = out_dir / f"{stem_name}_plant3d.json"

    exporter = CatalogJSONExporter()
    exporter.export(all_records, json_path, metadata={
        "source_catalog": resolved_pdf.name,
        "extraction_type": "generic",
        "total_models": len(items),
        "total_records": len(all_records),
        "models_summary": [it.model for it in items]
    }, mode=mode)

    if export_csv:
        csv_path = out_dir / f"{stem_name}_plant3d.csv"
        csv_exporter = CSVExporter()
        csv_exporter.export(all_records, csv_path)

    print(f"[OK] Successfully generated catalog structure under: {out_dir / stem_name}")


def run_all_pipelines(base_dir: Path = Path("docs"), output_dir: Path = Path("output")) -> None:
    """Batch runner: processes all PDFs in docs/specifications and docs/catalogs."""
    print("==================================================")
    print("Running All Extraction Pipelines (Batch Mode)")
    print("==================================================")

    specs_dir = base_dir / "specifications"
    if specs_dir.exists():
        for pdf in sorted(specs_dir.glob("*.pdf")):
            run_spec_pipeline(pdf, output_dir / "specifications")

    catalogs_dir = base_dir / "catalogs"
    if catalogs_dir.exists():
        for pdf in sorted(catalogs_dir.glob("*.pdf")):
            run_catalog_pipeline(pdf, output_dir / "catalogs")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Catalog Scrap Pipeline for AutoCAD Plant 3D (Dual-Engine)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Extraction subcommands")

    # Subcommand: spec
    spec_p = subparsers.add_parser("spec", help="Extract single component datasheet into a SINGLE JSON file")
    spec_p.add_argument("pdf", type=str, help="Path to datasheet PDF file")
    spec_p.add_argument("--adapter", type=str, default=None, help="Parser adapter name (optional)")
    spec_p.add_argument("--output-dir", type=str, default="output/specifications", help="Output directory")

    # Subcommand: catalog
    cat_p = subparsers.add_parser("catalog", help="Extract commercial multi-family catalog into manifest and model files")
    cat_p.add_argument("pdf", type=str, help="Path to catalog PDF file")
    cat_p.add_argument("--adapter", type=str, default=None, help="Parser adapter name (optional)")
    cat_p.add_argument("--output-dir", type=str, default="output/catalogs", help="Output directory")
    cat_p.add_argument("--mode", type=str, choices=["split", "consolidated", "both"], default="both", help="Export mode")
    cat_p.add_argument("--csv", action="store_true", help="Also export legacy CSV")

    # Subcommand: run-all
    subparsers.add_parser("run-all", help="Process all PDFs in docs/specifications and docs/catalogs")

    # Backward compatibility flags at root level
    parser.add_argument("--pdf", type=str, default=None, help="Legacy path to PDF file")
    parser.add_argument("--adapter", type=str, default=None, help="Legacy adapter name")
    parser.add_argument("--output-dir", type=str, default="output", help="Legacy output directory")
    parser.add_argument("--type", type=str, choices=["auto", "specific", "generic"], default="auto", help="Legacy extraction type")
    parser.add_argument("--mode", type=str, choices=["split", "consolidated", "both"], default="both", help="Legacy export mode")
    parser.add_argument("--csv", action="store_true", help="Legacy CSV export")

    args = parser.parse_args()

    # Route based on subcommand
    if args.subcommand == "spec":
        run_spec_pipeline(Path(args.pdf), Path(args.output_dir), args.adapter)
        return
    elif args.subcommand == "catalog":
        run_catalog_pipeline(Path(args.pdf), Path(args.output_dir), args.adapter, mode=args.mode, export_csv=args.csv)
        return
    elif args.subcommand == "run-all":
        run_all_pipelines(output_dir=Path(args.output_dir))
        return

    # Fallback to legacy flag handling
    pdf_target = args.pdf or "docs/specifications/INTEC-K200-NPS1-24inch-eng.pdf"
    resolved = resolve_pdf_path(pdf_target)
    if not resolved:
        resolved = resolve_pdf_path("docs/catalogs/CATALOGO_VAL_BOLA_2016-44.pdf")

    if not resolved:
        print(f"[Error] Could not resolve target PDF file: {pdf_target}")
        return

    parts = [p.lower() for p in resolved.parts]
    is_spec = (
        args.type == "specific" or
        (args.type == "auto" and ("specifications" in parts or any(k in resolved.name.upper() for k in ["INTEC", "K200", "SPEC"])))
    )

    if is_spec:
        out_d = Path(args.output_dir) if args.output_dir != "output" else Path("output/specifications")
        run_spec_pipeline(resolved, out_d, args.adapter)
    else:
        out_d = Path(args.output_dir) if args.output_dir != "output" else Path("output/catalogs")
        run_catalog_pipeline(resolved, out_d, args.adapter, mode=args.mode, export_csv=args.csv)


if __name__ == "__main__":
    main()

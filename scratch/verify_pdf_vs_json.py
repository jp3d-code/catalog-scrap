import json
import pdfplumber
from pathlib import Path

pdf_path = Path("docs/CATALOGO_VAL_BOLA_2016-44.pdf")
output_dir = Path("output/CATALOGO_VAL_BOLA_2016-44")

json_files = sorted(output_dir.rglob("*.json"))

for json_file in json_files:
    if json_file.name == "manifest.json" or "plant3d" in json_file.name:
        continue

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    model_name = data.get("model")
    items = data.get("items", [])

    print(f"\n==================================================")
    print(f"MODEL: {model_name} (File: {json_file.name})")
    print(f"Valve Type: {data.get('valve_type')}")
    print(f"Total Sizes Extracted: {len(items)}")
    print(f"==================================================")

    for idx, item in enumerate(items):
        part_no = item.get("Part_Number")
        nps = item.get("NPS_inch")
        dn = item.get("DN_mm")
        l_mm = item.get("L_mm")
        d_mm = item.get("D_mm")
        h_mm = item.get("H_mm")
        cls = item.get("Class_lbs")

        print(f"  [{idx+1:02d}] {part_no:<25} | Size: {nps:<6} (DN{dn:<3}) | L={l_mm:<6} D={d_mm:<6} H={h_mm:<6} | Class={cls}")


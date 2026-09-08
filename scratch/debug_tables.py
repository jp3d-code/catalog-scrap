import pdfplumber
from pathlib import Path

pdf_path = Path("docs/CATALOGO_VAL_BOLA_2016-44.pdf")

with pdfplumber.open(pdf_path) as pdf:
    for page_num in [4, 5, 8, 12, 16, 20]:  # Check sample pages
        if page_num <= len(pdf.pages):
            page = pdf.pages[page_num - 1]
            print(f"\n--- PAGE {page_num} ---")
            text_lines = [l.strip() for l in (page.extract_text() or "").split("\n") if l.strip()]
            print("TITLE LINES:", text_lines[:3])
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                print(f"\nTable {t_idx+1} ({len(table)} rows):")
                for row in table:
                    print("  ROW:", row)

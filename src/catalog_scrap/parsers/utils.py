def parse_nps_cell(raw_cell_str: str) -> dict:
    """Dynamically parse raw cell text from PDF (e.g. '½"', '1 ¼"', etc.) into NPS, decimal inches and DN (mm)."""
    normalized = (
        raw_cell_str
        .replace('\xbd', ' 1/2')  # ½
        .replace('\xbe', ' 3/4')  # ¾
        .replace('\xbc', ' 1/4')  # ¼
        .replace('\u201c', '"')   # “
        .replace('\u201d', '"')   # ”
    )
    normalized = " ".join(normalized.split())
    if not normalized.endswith('"'):
        normalized += '"'

    clean_num = normalized.replace('"', '').strip()
    decimal_in = 0.0
    for part in clean_num.split():
        if '/' in part:
            num, den = part.split('/')
            decimal_in += float(num) / float(den)
        else:
            decimal_in += float(part)

    dn_map = {
        0.5: 15,
        0.75: 20,
        1.0: 25,
        1.25: 32,
        1.5: 40,
        2.0: 50,
        2.5: 65,
        3.0: 80,
        4.0: 100
    }
    dn_mm = dn_map.get(decimal_in, int(round(decimal_in * 25.4)))

    return {
        "nps": normalized,
        "dn": dn_mm,
        "dec_in": decimal_in
    }

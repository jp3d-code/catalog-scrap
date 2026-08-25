import re


def parse_nps_cell(raw_cell_str: str) -> dict:
    """
    Dynamically parse raw size string from PDF (e.g. '½"', '1 ¼"', 'DN 50', '100mm', '15')
    into standard NPS string, decimal inches, and DN (mm).
    """
    normalized = (
        raw_cell_str
        .replace('\xbd', ' 1/2')  # ½
        .replace('\xbe', ' 3/4')  # ¾
        .replace('\xbc', ' 1/4')  # ¼
        .replace('\u201c', '"')   # “
        .replace('\u201d', '"')   # ”
    )
    normalized = " ".join(normalized.split())

    # Map of standard DN to NPS strings
    DN_TO_NPS = {
        15: '1/2"',
        20: '3/4"',
        25: '1"',
        32: '1 1/4"',
        40: '1 1/2"',
        50: '2"',
        65: '2 1/2"',
        80: '3"',
        100: '4"',
        125: '5"',
        150: '6"',
        200: '8"',
        250: '10"',
        300: '12"',
        350: '14"',
        400: '16"',
        450: '18"',
        500: '20"',
        600: '24"'
    }

    NPS_TO_DN = {v: k for k, v in DN_TO_NPS.items()}

    # Check for DN number pattern (e.g., DN 50, 50mm)
    dn_match = re.search(r'\b(?:DN)?\s*(\d+)\s*(?:mm)?\b', normalized, re.IGNORECASE)
    if 'DN' in normalized.upper() or 'MM' in normalized.upper() or (dn_match and not any(c in normalized for c in ['/', '"'])):
        if dn_match:
            dn_val = int(dn_match.group(1))
            nps_str = DN_TO_NPS.get(dn_val, f"{round(dn_val / 25.4, 1)}\"")
            return {
                "nps": nps_str,
                "dn": dn_val,
                "dec_in": round(dn_val / 25.4, 2)
            }

    # Clean fraction inch string
    if not normalized.endswith('"'):
        normalized += '"'

    clean_num = re.sub(r'[^\d\s/]', '', normalized).strip()
    decimal_in = 0.0
    for part in clean_num.split():
        if '/' in part:
            try:
                num, den = part.split('/')
                decimal_in += float(num) / float(den)
            except ValueError:
                pass
        else:
            try:
                decimal_in += float(part)
            except ValueError:
                pass

    dn_mm = int(round(decimal_in * 25.4))
    # Snap to nearest standard DN
    for standard_dn in sorted(DN_TO_NPS.keys()):
        if abs(dn_mm - standard_dn) <= 3:
            dn_mm = standard_dn
            break

    return {
        "nps": normalized,
        "dn": dn_mm,
        "dec_in": decimal_in
    }

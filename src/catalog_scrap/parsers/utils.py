import re


DN_TO_NPS = {
    6: '1/8"',
    8: '1/4"',
    10: '3/8"',
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
NPS_TO_DN.update({
    '1/8': 6,
    '1/4': 8,
    '3/8': 10,
    '1/2': 15,
    '3/4': 20,
    '1': 25,
    '1 1/4': 32,
    '1 1/2': 40,
    '1-1/2"': 40,
    '1.1/2"': 40,
    '2': 50,
    '2 1/2': 65,
    '2-1/2"': 65,
    '2.1/2"': 65,
    '3': 80,
    '4': 100,
    '5': 125,
    '6': 150,
    '8': 200,
    '10': 250,
    '12': 300,
    '14': 350,
    '16': 400,
    '18': 450,
    '20': 500,
    '24': 600
})


def parse_nps_cell(raw_cell_str: str) -> dict:
    """
    Dynamically parse raw size string from PDF (e.g. '½"', '1 ¼"', '1.1/2"', 'DN 50', '100mm', '1/2 14')
    into standard NPS string, decimal inches, and DN (mm).
    """
    if not raw_cell_str or not raw_cell_str.strip():
        return {"nps": "", "dn": 0, "dec_in": 0.0}

    normalized = (
        raw_cell_str
        .replace('\xbd', ' 1/2')  # ½
        .replace('\xbe', ' 3/4')  # ¾
        .replace('\xbc', ' 1/4')  # ¼
        .replace('\u201c', '"')   # “
        .replace('\u201d', '"')   # ”
        .replace('”', '"')
        .replace('“', '"')
        .strip()
    )

    # Check for explicit DN pattern (e.g. DN 50, 50mm, or DN50)
    dn_match = re.search(r'\bDN\s*(\d+)\b|\b(\d+)\s*mm\b', normalized, re.IGNORECASE)
    if dn_match:
        dn_val = int(dn_match.group(1) or dn_match.group(2))
        if dn_val in DN_TO_NPS:
            return {
                "nps": DN_TO_NPS[dn_val],
                "dn": dn_val,
                "dec_in": round(dn_val / 25.4, 3)
            }

    # Normalize dotted/dashed compound fractions: "1.1/2" -> "1 1/2", "2.1/2" -> "2 1/2"
    normalized = re.sub(r'(\d+)\s*[\.\-]\s*(\d+/\d+)', r'\1 \2', normalized)

    # Handle dot prefix clipped fraction: e.g. ".1/2 38" -> if 38 mm is bore, it's 1 1/2"
    if re.match(r'^\s*\.1/2\b', normalized):
        if '38' in normalized:
            normalized = re.sub(r'^\s*\.1/2\b', '1 1/2', normalized)
        else:
            normalized = re.sub(r'^\s*\.1/2\b', '1/2', normalized)

    # Match primary NPS token at start or before extra text (e.g. '1/2" 14', '1 1/2"', '2"')
    token_match = re.search(
        r'(?:^|\b)(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)\s*(?:\"|\'|\b)',
        normalized
    )
    if not token_match:
        token_match = re.search(r'(\d+/\d+|\d+)', normalized)

    if not token_match:
        return {"nps": "", "dn": 0, "dec_in": 0.0}

    nps_token = token_match.group(1).strip()

    # Calculate decimal inches
    decimal_in = 0.0
    if ' ' in nps_token:
        whole, frac = nps_token.split(None, 1)
        try:
            num, den = frac.split('/')
            decimal_in = float(whole) + (float(num) / float(den))
        except (ValueError, ZeroDivisionError):
            pass
    elif '/' in nps_token:
        try:
            num, den = nps_token.split('/')
            decimal_in = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            pass
    else:
        try:
            decimal_in = float(nps_token)
        except ValueError:
            pass

    # Safety bounds check: typical piping valves are between 1/8" (0.125) and 48"
    if decimal_in < 0.1 or decimal_in > 48.0:
        return {"nps": "", "dn": 0, "dec_in": 0.0}

    clean_nps = f"{nps_token}\""

    # Determine DN (mm)
    dn_mm = NPS_TO_DN.get(clean_nps) or NPS_TO_DN.get(nps_token)
    if dn_mm is None:
        approx_dn = int(round(decimal_in * 25.4))
        best_dn = approx_dn
        min_diff = 999
        for std_dn in sorted(DN_TO_NPS.keys()):
            diff = abs(approx_dn - std_dn)
            if diff < min_diff and diff <= 4:
                min_diff = diff
                best_dn = std_dn
        dn_mm = best_dn

    # Standardize clean NPS from standard DN if mapped
    if dn_mm in DN_TO_NPS:
        clean_nps = DN_TO_NPS[dn_mm]

    return {
        "nps": clean_nps,
        "dn": dn_mm,
        "dec_in": round(decimal_in, 3)
    }

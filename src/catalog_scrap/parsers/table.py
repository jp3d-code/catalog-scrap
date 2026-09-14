"""Capa reutilizable de normalizacion de tablas PDF (pdfplumber -> filas limpias).

Resuelve los dos modos de fractura observados en catalogos reales:
- Modo A: la celda de talla partida en 2 ('...051 1' + '/2” 90 60.3').
- Modo B: codigo de articulo (5-15 digitos) fusionado con la talla.

Los parsers por fabricante declaran la SEMANTICA (que columna es brida
vs bore); este modulo solo aporta MECANICA: limpieza, reparacion y
clasificacion de columnas por alias ES/EN/DE.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Codigo de articulo: pdfplumber a veces lo recorta (p. ej. 5 digitos en
# tablas roscadas) o lo fusiona con la talla. Tambien aparece '-' solo.
_CODE_RE = re.compile(r'^\s*(?:\d{5,15}|-)\s+')

# Continuacion de fraccion al inicio de la celda siguiente:
# '/2” ...' (denominador huerfano, modo A), '.1/2” 38' (punto recortado)
# o '2 ” ...' (talla completa tras codigo con '/').
_FRACT_CONT_RE = re.compile(r'^\s*(/\s*\d+\s*["\u201c\u201d]?|\.\d+/\d+\s*["\u201c\u201d]?[^\s]*|\d+\s*["\u201c\u201d])')

# Celda previa "incompleta": termina en numero parcial ('...051 1', '1.1',
# '2.1/') o en marcador '-'. Tras strip_product_code el codigo ya salio.
_PARTIAL_END_RE = re.compile(r'(\d+\.?\d*|[/.\-])\s*$')

# Token de talla al inicio de celda (fraccion o entero con comilla).
# Sirve para separar el resto numerico ('1/2” 14' -> resto '14').
_SIZE_TOKEN_RE = re.compile(
    r'^\s*(?:\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+\s*["\u201c\u201d])'
)


def size_remainder(cell: str) -> str:
    """Resto de la celda tras el token de talla inicial.

    '1/2” 14' -> '14' (bore fusionado). Sin token de talla devuelve la
    celda intacta ('38' -> '38', resto DN/bore huerfano tras reparacion).
    """
    m = _SIZE_TOKEN_RE.match(cell or '')
    if not m:
        return (cell or '').strip()
    return (cell[m.end():]).strip()


# Fallback de talla: la alternativa dotted-compound VA PRIMERO para no
# morder '1/4' dentro de '1.1/4”' (modo B).
_SIZE_FALLBACK_RES = [
    re.compile(r'(\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+)\s*(?:["\u201c\u201d\u00bd\u00be\u00bc]|\b)'),
    re.compile(r'(\d+\s*/\s*\d+\s*["\u201c\u201d\u00bd\u00be\u00bc]?|\d+(?:\.\d+)?\s*["\u201c\u201d\u00bd\u00be\u00bc]|\bDN\s*\d+|\b\d+\s*mm\b)', re.IGNORECASE),
]


def _clean_cell(cell: Optional[str]) -> str:
    """Colapsa espacios/saltos de linea de una celda cruda."""
    if not cell:
        return ""
    return " ".join(cell.replace('\n', ' ').split()).strip()


def strip_product_code(cell: str) -> str:
    """Elimina codigo de articulo (5-15 digitos) o '-' inicial de la celda."""
    return _CODE_RE.sub('', cell or '').strip()


def clean_row(row: List[Optional[str]]) -> List[str]:
    """Limpia todas las celdas de una fila cruda de pdfplumber."""
    return [_clean_cell(c) for c in row]


def repair_fractures(cells: List[str]) -> List[str]:
    """Repara tallas fracturadas entre celdas adyacentes (modo A).

    Si la celda i (sin codigo) termina en numero parcial y la celda i+1
    empieza con continuacion de fraccion, mueve ese fragmento a la celda i.
    Conserva el numero de columnas: el resto de la celda i+1 (D1, D2...)
    queda en su sitio.
    """
    cells = list(cells)
    for i in range(len(cells) - 1):
        prev = strip_product_code(cells[i])
        if not prev or not _PARTIAL_END_RE.search(prev):
            continue
        nxt = cells[i + 1] or ""
        m = _FRACT_CONT_RE.match(nxt)
        if not m:
            continue
        # No mover tallas completas: la celda previa debe ser parcial
        # (termina en '/', '.' o el match completa una fraccion con '/').
        frag = m.group(1)
        if '/' not in prev and '/' not in frag and not prev.endswith(('.', '/', '-')):
            continue
        cells[i] = (cells[i].rstrip() + frag).strip()
        cells[i + 1] = nxt[m.end():].strip()
    return cells


def extract_size_candidate(cells: List[str]) -> str:
    """Extrae el mejor candidato de talla de una fila ya reparada.

    Los codigos se eliminan ANTES de unir para que un codigo + fraccion
    ('90336 1/4”) no se lea como talla compuesta ('90336 1/4').
    Devuelve '' si no hay candidato.
    """
    cleaned = [strip_product_code(c) for c in cells]
    joined = " ".join(c for c in cleaned if c)
    for rx in _SIZE_FALLBACK_RES:
        m = rx.search(joined)
        if m:
            return m.group(1).strip()
    return ""


def _norm_header(cell: str) -> str:
    h = _clean_cell(cell).upper()
    h = (h.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
           .replace('Ó', 'O').replace('Ú', 'U').replace('Ø', 'O'))
    return h


def classify_columns(header: List[str]) -> Dict[str, int]:
    """Mapea cabecera cruda -> {rol_canonico: indice}.

    Roles: 'code', 'size', 'd1', 'd2', 'd3', 'd', 'length', 'height',
    'weight', 'torque', 'iso'. La SEMANTICA (d1 = brida vs bore) la decide
    cada parser segun su layout; aqui solo se normaliza la ortografia.
    Ante claves duplicadas gana la ULTIMA aparicion (columnas de datos
    reales suelen ir a la derecha de las fracturas de cabecera).
    """
    cmap: Dict[str, int] = {}
    for idx, raw in enumerate(header):
        h = _norm_header(raw)
        if not h:
            continue
        if 'CODIG' in h or h in ('CODE', 'ART', 'ARTICULO', 'FIG'):
            cmap['code'] = idx
        elif (h in ('DN', 'NPS', 'NPT') or h.startswith('DN ')
              or h.startswith('NPS ') or h == 'DN D') and 'D1' not in h:
            cmap['size'] = idx
        elif h == 'D1' or 'D1' in h:
            cmap['d1'] = idx
        elif h == 'D2':
            cmap['d2'] = idx
        elif h == 'D3':
            cmap['d3'] = idx
        elif h == 'D':
            cmap['d'] = idx
        elif h.replace(' ', '') in ('LPH', 'LH'):
            # Columna agrupada 'L P H' / 'L H': el primer token es L
            cmap['length_grouped'] = idx
        elif h == 'L' or 'FACE' in h or h in ('LENGTH', 'LONGITUD'):
            cmap['length'] = idx
        elif h in ('H', 'H1', 'ALTURA', 'HEIGHT'):
            cmap['height'] = idx
        elif 'PESO' in h or 'WEIGHT' in h or h == 'KG':
            cmap['weight'] = idx
        elif 'PAR' in h or 'TORQUE' in h:
            cmap['torque'] = idx
        elif 'ISO' in h:
            cmap['iso'] = idx
    return cmap


def first_float(cell: str) -> float:
    """Primer numero flotante de la celda (tolerante a '4-16', 'M12 x 1.5').

    Para columnas de cotas secundarias (D, H, peso). NO usar para L:
    la tolerancia convierte fracturas ('5 90') en valores falsos.
    """
    if not cell:
        return 0.0
    m = re.search(r'-?\d+(?:[.,]\d+)?', cell.replace(',', '.'))
    if not m:
        return 0.0
    try:
        return float(m.group(0))
    except ValueError:
        return 0.0


_SINGLE_NUMBER_RE = re.compile(r'^\s*-?\d+(?:[.,]\d+)?\s*$')

# Banda de plausibilidad L/DN para desambiguar fracturas ('5 90' -> 90,
# '190 1' -> 190, '115 3' -> 115). Face-to-face de bola siempre supera el
# DN y no excede ~12x (peor caso: 1/2" 600# = 165mm = 11xDN15).
_L_DN_RATIO_MIN = 1.0
_L_DN_RATIO_MAX = 12.0


def parse_bare_dn(token: str):
    """Talla expresada solo como DN en mm ('65' -> 2 1/2", DN65).

    Dialecto de tablas PN (pags. 17-22, 24): sin comilla ni 'DN'.
    Devuelve None si no es un DN estandar (nunca adivina).
    """
    from catalog_scrap.parsers.utils import DN_TO_NPS
    if not token or not re.fullmatch(r'\s*\d{1,3}\s*', token):
        return None
    dn_val = int(token.strip())
    nps = DN_TO_NPS.get(dn_val)
    if not nps:
        return None
    return {"nps": nps, "dn": dn_val, "dec_in": round(dn_val / 25.4, 3)}


def parse_length_cell(cell: str, grouped: bool = False, dn_mm: int = 0) -> float:
    """Parse de la longitud cara a cara (L).

    - Cabecera agrupada ('L P H', 'L H'): el PRIMER token es L.
    - Numero unico limpio: ese valor.
    - Dos tokens (fractura '5 90' / '190 1' / '115 3'): el token
      plausible segun banda L/DN; si no hay exactamente uno -> 0.0.
    """
    if not cell:
        return 0.0
    if grouped:
        return first_float(cell)
    if _SINGLE_NUMBER_RE.match(cell):
        try:
            return float(cell.strip().replace(',', '.'))
        except ValueError:
            return 0.0
    if dn_mm > 0:
        plausible = []
        for tok in cell.replace(',', '.').split():
            try:
                val = float(tok)
            except ValueError:
                continue
            ratio = val / dn_mm
            if _L_DN_RATIO_MIN <= ratio <= _L_DN_RATIO_MAX:
                plausible.append(val)
        if len(plausible) == 1:
            return plausible[0]
    return 0.0


@dataclass
class TableQuality:
    """Trazabilidad de calidad por tabla: que entro, que salio y por que no."""
    page_number: int = 0
    model: str = ""
    rows_in: int = 0
    records_out: int = 0
    discarded: List[Dict[str, str]] = field(default_factory=list)
    status: str = "parsed"  # parsed | skipped_no_length

    def discard(self, row_nr: int, reason: str, row_preview: str = "") -> None:
        self.discarded.append({
            "row": str(row_nr),
            "reason": reason,
            "preview": row_preview[:120],
        })

    def to_dict(self) -> Dict:
        return {
            "page_number": self.page_number,
            "model": self.model,
            "status": self.status,
            "rows_in": self.rows_in,
            "records_out": self.records_out,
            "discarded_count": len(self.discarded),
            "discarded": self.discarded,
        }


_BARE_LEAD_RE = re.compile(r'^\s*(\d{1,3})\b')


def first_bare_dn(cell: str):
    """Primer token entero desnudo como DN ('65 18' -> DN65, '1Bola' -> None)."""
    m = _BARE_LEAD_RE.match(cell or '')
    if not m:
        return None
    return parse_bare_dn(m.group(1))


def first_token(cell: str) -> str:
    """Primer token separado por espacios de la celda."""
    toks = (cell or '').split()
    return toks[0] if toks else ''


def last_float(cell: str) -> float:
    """ULTIMO numero de la celda (para celdas fusionadas 'F25 510 248').

    En cabeceras fusionadas Peso+ISO+Par el peso es el ultimo token;
    first_float devolveria el codigo ISO o el par.
    """
    if not cell:
        return 0.0
    nums = re.findall(r'-?\d+(?:[.,]\d+)?', cell.replace(',', '.'))
    if not nums:
        return 0.0
    try:
        return float(nums[-1])
    except ValueError:
        return 0.0


_ISO_TOKEN_RE = re.compile(r'\bF\d{1,2}\b')


def iso_token(cell: str) -> str:
    """Codigo de brida superior ISO 5211 ('F25 510 248' -> 'F25')."""
    m = _ISO_TOKEN_RE.search((cell or '').upper())
    return m.group(0) if m else ''


_BARE_LEAD_STRIP_RE = re.compile(r'^\s*\d{1,3}\b\s*')


def bare_remainder(cell: str) -> str:
    """Resto tras un DN desnudo inicial ('65 18' -> '18')."""
    return _BARE_LEAD_STRIP_RE.sub('', cell or '').strip()

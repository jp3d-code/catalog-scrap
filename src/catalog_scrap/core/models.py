from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class DimensionEntry:
    nps: str
    dn: int
    dec_in: float
    h: float
    l1: float
    l_150: float
    l_300: float
    d_150: float
    d_300: float
    e: float
    iso_flange: str
    torque_150: float
    torque_300: float
    weight_150: float
    weight_300: float


@dataclass
class CatalogItem:
    manufacturer: str
    model: str
    valve_type: str
    dimensions: List[DimensionEntry] = field(default_factory=list)
    materials: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

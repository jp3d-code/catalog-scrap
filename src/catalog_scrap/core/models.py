from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class DimensionEntry:
    nps: str
    dn: int
    dec_in: float
    h: float = 0.0
    l1: float = 0.0
    l_150: float = 0.0
    l_300: float = 0.0
    d_150: float = 0.0
    d_300: float = 0.0
    e: float = 0.0
    iso_flange: str = ""
    torque_150: float = 0.0
    torque_300: float = 0.0
    weight_150: float = 0.0
    weight_300: float = 0.0
    extra_dimensions: Dict[str, Any] = field(default_factory=dict)



@dataclass
class CatalogItem:
    manufacturer: str
    model: str
    valve_type: str
    dimensions: List[DimensionEntry] = field(default_factory=list)
    materials: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

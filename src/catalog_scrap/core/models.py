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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize dimension entry to clean dictionary."""
        data = {
            "nps": self.nps,
            "dn": self.dn,
            "dec_in": self.dec_in,
            "h": self.h,
            "l1": self.l1,
            "l_150": self.l_150,
            "l_300": self.l_300,
            "d_150": self.d_150,
            "d_300": self.d_300,
            "e": self.e,
            "top_flange_iso": self.iso_flange,
            "torque_150": self.torque_150,
            "torque_300": self.torque_300,
            "weight_150": self.weight_150,
            "weight_300": self.weight_300,
        }
        if self.extra_dimensions:
            data["extra_parameters"] = self.extra_dimensions
        return data


@dataclass
class CatalogItem:
    manufacturer: str
    model: str
    valve_type: str
    extraction_type: str = "specific"  # "specific" (detailed part) or "generic" (catalog L & D)
    dimensions: List[DimensionEntry] = field(default_factory=list)
    materials: Dict[str, str] = field(default_factory=dict)
    parts_list: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

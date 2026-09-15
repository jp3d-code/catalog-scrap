from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union


@dataclass
class BOMItem:
    """Bill of Materials entry for technical part datasheets."""
    item_no: str
    part: str
    material: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "item_no": self.item_no,
            "part": self.part,
            "material": self.material
        }


@dataclass
class DimensionEntry:
    """Detailed dimension row for engineering datasheets and models."""
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
    # Trazabilidad: de que pagina/fila del PDF salio esta cota
    page_number: int = 0
    row_index: int = 0
    source: str = ""

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
            "page_number": self.page_number,
            "row_index": self.row_index,
            "source": self.source,
        }
        if self.extra_dimensions:
            data["extra_parameters"] = self.extra_dimensions
        return data


# Alias for explicit datasheet domain semantics
DatasheetRow = DimensionEntry


@dataclass
class CatalogSizeRow:
    """Minimal dimension row for generic commercial catalogs (strictly L & D)."""
    nps: str
    dn: int
    class_lbs: Union[str, int]
    l_mm: float
    d_mm: float
    end_type: str = "FL"
    body_material: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nps": self.nps,
            "dn": self.dn,
            "class_lbs": self.class_lbs,
            "l_mm": self.l_mm,
            "d_mm": self.d_mm,
            "end_type": self.end_type,
            "body_material": self.body_material
        }


@dataclass
class CatalogItem:
    """Generic catalog entity or single component container."""
    manufacturer: str
    model: str
    valve_type: str
    extraction_type: str = "specific"  # "specific" (detailed part) or "generic" (catalog L & D)
    dimensions: List[DimensionEntry] = field(default_factory=list)
    materials: Dict[str, str] = field(default_factory=dict)
    parts_list: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentDatasheet(CatalogItem):
    """
    Component Datasheet Domain Entity (Specific Piece Mode).
    Represents an exhaustive engineering datasheet for a single valve or fitting model.
    """
    extraction_type: str = "specific"
    standards: Dict[str, str] = field(default_factory=dict)
    design_features: List[str] = field(default_factory=list)
    parts_bom: List[BOMItem] = field(default_factory=list)

    def __post_init__(self):
        self.extraction_type = "specific"
        if not self.standards and "standards" in self.metadata:
            self.standards = self.metadata["standards"]
        if not self.design_features and "design_features" in self.metadata:
            self.design_features = self.metadata["design_features"]
        if not self.parts_bom and self.parts_list:
            self.parts_bom = [
                BOMItem(item_no=str(p.get("item_no", "")), part=p.get("part", ""), material=p.get("material", ""))
                for p in self.parts_list
            ]


@dataclass
class CommercialCatalog:
    """
    Commercial Catalog Domain Entity (Generic Catalog Mode).
    Represents a multi-family catalog containing multiple models.
    """
    source_catalog: str
    extraction_type: str = "generic"
    families: List[CatalogItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

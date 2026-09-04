from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class MoleculeBase(BaseModel):
    compound_id: str
    canonical_smiles: str
    target_value: Optional[float] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None
    h_bond_donors: Optional[int] = None
    h_bond_acceptors: Optional[int] = None
    rotatable_bonds: Optional[int] = None


class MoleculeResponse(MoleculeBase):
    id: str
    dataset_id: str
    original_smiles: str

    model_config = ConfigDict(from_attributes=True)


class MoleculeDetailResponse(MoleculeResponse):
    svg_2d: Optional[str] = None
    fingerprint_bits: Optional[str] = None


class MoleculeListResponse(BaseModel):
    total: int
    items: List[MoleculeResponse]

"""
Molecule endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.repository import MoleculeRepository
from backend.app.schemas.molecule import MoleculeResponse, MoleculeDetailResponse
from backend.app.utils.rdkit_utils import smiles_to_svg

router = APIRouter(prefix="/molecules", tags=["Molecules"])


@router.get("", response_model=List[MoleculeResponse])
def list_molecules(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = MoleculeRepository(db)
    return repo.list_molecules(skip=skip, limit=limit)


@router.get("/{molecule_id}", response_model=MoleculeDetailResponse)
def get_molecule(molecule_id: str, db: Session = Depends(get_db)):
    repo = MoleculeRepository(db)
    mol = repo.get_molecule_by_id(molecule_id)
    if not mol:
        raise HTTPException(status_code=404, detail="Molecule not found")

    svg = smiles_to_svg(mol.canonical_smiles)
    data = MoleculeDetailResponse.model_validate(mol)
    data.svg_2d = svg
    return data

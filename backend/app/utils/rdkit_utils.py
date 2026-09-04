"""
RDKit Utility Module
Provides robust molecular parsing, canonicalization, descriptor calculation,
fingerprint generation, and 2D SVG generation for BioForge.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, AllChem
from backend.app.core.logging import logger


def parse_smiles(smiles: str) -> Optional[Chem.Mol]:
    """Parse SMILES string into an RDKit Mol object with sanitization."""
    if not smiles or not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        return mol
    except Exception as e:
        logger.debug(f"Failed to parse SMILES '{smiles}': {e}")
        return None


def canonicalize_smiles(smiles: str) -> Optional[str]:
    """Return standard canonical SMILES or None if invalid."""
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    try:
        return Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
    except Exception as e:
        logger.debug(f"Failed to canonicalize SMILES '{smiles}': {e}")
        return None


def compute_molecular_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate primary molecular physicochemical descriptors:
    - Molecular Weight (MW)
    - Partition Coefficient (MolLogP)
    - Topological Polar Surface Area (TPSA)
    - Hydrogen Bond Donors (NumHDonors)
    - Hydrogen Bond Acceptors (NumHAcceptors)
    - Rotatable Bonds (NumRotatableBonds)
    - Heavy Atom Count (HeavyAtomCount)
    - Ring Count (RingCount)
    """
    if mol is None:
        raise ValueError("Cannot calculate descriptors for None molecule")

    return {
        "molecular_weight": float(Descriptors.MolWt(mol)),
        "logp": float(Descriptors.MolLogP(mol)),
        "tpsa": float(Descriptors.TPSA(mol)),
        "h_bond_donors": int(rdMolDescriptors.CalcNumHBD(mol)),
        "h_bond_acceptors": int(rdMolDescriptors.CalcNumHBA(mol)),
        "rotatable_bonds": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        "heavy_atom_count": int(mol.GetNumHeavyAtoms()),
        "ring_count": int(rdMolDescriptors.CalcNumRings(mol)),
    }


def compute_morgan_fingerprint(
    mol: Chem.Mol, radius: int = 2, n_bits: int = 1024
) -> np.ndarray:
    """Generate Morgan fingerprint (ECFP4 equivalent) as numpy bit array."""
    if mol is None:
        raise ValueError("Cannot generate fingerprint for None molecule")

    try:
        from rdkit.Chem import rdFingerprintGenerator
        mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
        fp = mfpgen.GetFingerprint(mol)
    except Exception:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=radius, nBits=n_bits)

    arr = np.zeros((n_bits,), dtype=np.int8)
    for bit in fp.GetOnBits():
        arr[bit] = 1
    return arr


def smiles_to_svg(smiles: str, width: int = 300, height: int = 200) -> Optional[str]:
    """Generate clean 2D vector SVG representation for molecular visualization."""
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    try:
        from rdkit.Chem.Draw import rdMolDraw2D
        mol = Chem.Mol(mol)
        AllChem.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        drawer.drawOptions().clearBackground = True
        drawer.drawOptions().bondLineWidth = 2
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception as e:
        logger.debug(f"Failed to generate SVG for SMILES '{smiles}': {e}")
        return None

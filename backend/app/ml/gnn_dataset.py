"""
Molecular Graph Construction and Dataset Module
Converts SMILES into PyTorch molecular graph representations with rich atom and bond features.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
import torch
from torch.utils.data import Dataset
from rdkit import Chem
from backend.app.utils.rdkit_utils import parse_smiles

# Common atomic numbers in drug-like molecules
ALLOWED_ATOMS = [1, 6, 7, 8, 9, 15, 16, 17, 35, 53]  # H, C, N, O, F, P, S, Cl, Br, I
HYBRIDIZATIONS = [
    Chem.rdchem.HybridizationType.SP,
    Chem.rdchem.HybridizationType.SP2,
    Chem.rdchem.HybridizationType.SP3,
    Chem.rdchem.HybridizationType.SP3D,
    Chem.rdchem.HybridizationType.SP3D2,
]
BOND_TYPES = [
    Chem.rdchem.BondType.SINGLE,
    Chem.rdchem.BondType.DOUBLE,
    Chem.rdchem.BondType.TRIPLE,
    Chem.rdchem.BondType.AROMATIC,
]

NODE_DIM = 21
EDGE_DIM = 7


def get_atom_features(atom: Chem.Atom) -> List[float]:
    """
    Extract atom node features:
    - Atomic number one-hot (plus other)
    - Degree (0 to 4+)
    - Formal charge
    - Hybridization one-hot
    - Aromaticity flag (0 or 1)
    - Total hydrogen count
    """
    features = []

    # Atomic number one-hot
    atomic_num = atom.GetAtomicNum()
    atom_one_hot = [1.0 if atomic_num == a else 0.0 for a in ALLOWED_ATOMS]
    atom_one_hot.append(1.0 if atomic_num not in ALLOWED_ATOMS else 0.0)
    features.extend(atom_one_hot)

    # Degree
    degree = atom.GetTotalDegree()
    features.append(float(min(degree, 6)) / 6.0)

    # Formal charge
    features.append(float(atom.GetFormalCharge()))

    # Hybridization
    hyb = atom.GetHybridization()
    hyb_one_hot = [1.0 if hyb == h else 0.0 for h in HYBRIDIZATIONS]
    hyb_one_hot.append(1.0 if hyb not in HYBRIDIZATIONS else 0.0)
    features.extend(hyb_one_hot)

    # Aromaticity
    features.append(1.0 if atom.GetIsAromatic() else 0.0)

    # Number of Hydrogens
    features.append(float(atom.GetTotalNumHs()) / 4.0)

    return features


def get_bond_features(bond: Chem.Bond) -> List[float]:
    """
    Extract edge/bond features:
    - Bond type one-hot (single, double, triple, aromatic)
    - Conjugation flag
    - Ring membership flag
    """
    features = []
    bond_type = bond.GetBondType()
    b_one_hot = [1.0 if bond_type == b else 0.0 for b in BOND_TYPES]
    b_one_hot.append(1.0 if bond_type not in BOND_TYPES else 0.0)
    features.extend(b_one_hot)

    features.append(1.0 if bond.GetIsConjugated() else 0.0)
    features.append(1.0 if bond.IsInRing() else 0.0)
    return features


@dataclass
class MolecularGraph:
    x: torch.Tensor          # [N, NODE_DIM]
    edge_index: torch.Tensor # [2, E]
    edge_attr: torch.Tensor  # [E, EDGE_DIM]
    y: Optional[torch.Tensor] = None # [1]
    smiles: str = ""
    num_nodes: int = 0


def mol_to_graph(smiles: str, target: Optional[float] = None) -> Optional[MolecularGraph]:
    """Convert SMILES string into a MolecularGraph data structure."""
    mol = parse_smiles(smiles)
    if mol is None:
        return None

    # Node features
    node_features = []
    for atom in mol.GetAtoms():
        node_features.append(get_atom_features(atom))

    x = torch.tensor(node_features, dtype=torch.float32)
    num_nodes = mol.GetNumAtoms()

    # Edge features (bidirectional)
    edge_indices = []
    edge_features = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        feat = get_bond_features(bond)

        # Forward edge
        edge_indices.append([i, j])
        edge_features.append(feat)

        # Backward edge
        edge_indices.append([j, i])
        edge_features.append(feat)

    if len(edge_indices) > 0:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_features, dtype=torch.float32)
    else:
        # Isolated single atom edge handling
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, EDGE_DIM), dtype=torch.float32)

    y_tensor = torch.tensor([target], dtype=torch.float32) if target is not None else None

    return MolecularGraph(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y_tensor,
        smiles=smiles,
        num_nodes=num_nodes,
    )


class BatchMolecularGraph:
    """Collated batch of disjoint molecular graphs for batched GNN processing."""

    def __init__(self, graphs: List[MolecularGraph]):
        self.num_graphs = len(graphs)
        total_nodes = sum(g.num_nodes for g in graphs)

        x_list = []
        edge_index_list = []
        edge_attr_list = []
        batch_list = []
        y_list = []

        node_offset = 0
        for graph_idx, g in enumerate(graphs):
            x_list.append(g.x)
            if g.edge_index.size(1) > 0:
                edge_index_list.append(g.edge_index + node_offset)
                edge_attr_list.append(g.edge_attr)
            batch_list.append(torch.full((g.num_nodes,), graph_idx, dtype=torch.long))
            if g.y is not None:
                y_list.append(g.y)
            node_offset += g.num_nodes

        self.x = torch.cat(x_list, dim=0)
        self.edge_index = torch.cat(edge_index_list, dim=1) if edge_index_list else torch.empty((2, 0), dtype=torch.long)
        self.edge_attr = torch.cat(edge_attr_list, dim=0) if edge_attr_list else torch.empty((0, EDGE_DIM), dtype=torch.float32)
        self.batch = torch.cat(batch_list, dim=0)
        self.y = torch.cat(y_list, dim=0) if y_list else None


def collate_molecular_graphs(graphs: List[Optional[MolecularGraph]]) -> BatchMolecularGraph:
    valid_graphs = [g for g in graphs if g is not None]
    if not valid_graphs:
        raise ValueError("Cannot collate empty or invalid graph batch")
    return BatchMolecularGraph(valid_graphs)


class MolecularDataset(Dataset):
    """PyTorch Dataset yielding MolecularGraphs."""

    def __init__(self, smiles_list: List[str], targets: Optional[List[float]] = None):
        self.smiles_list = smiles_list
        self.targets = targets

    def __len__(self):
        return len(self.smiles_list)

    def __getitem__(self, idx: int) -> MolecularGraph:
        smiles = self.smiles_list[idx]
        target = self.targets[idx] if self.targets is not None else None
        graph = mol_to_graph(smiles, target)
        if graph is None:
            raise ValueError(f"Failed to featurize SMILES: {smiles}")
        return graph

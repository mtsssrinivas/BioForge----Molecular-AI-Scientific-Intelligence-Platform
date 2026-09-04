"""
PyTorch Graph Neural Network Architecture for Molecular Property Prediction
Modular message-passing architecture operating on chemical molecular graphs.
"""

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from backend.app.ml.gnn_dataset import NODE_DIM, EDGE_DIM


class MessagePassingLayer(nn.Module):
    """
    Message passing layer:
    m_{ij} = MLP([h_i, h_j, e_{ij}])
    m_i = sum_{j in N(i)} m_{ij}
    h_i' = LayerNorm(h_i + MLP([h_i, m_i]))
    """

    def __init__(self, hidden_dim: int, edge_dim: int, dropout: float = 0.1):
        super().__init__()
        self.message_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.update_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.norm = nn.LayerNorm(hidden_dim)

    def forward(
        self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor
    ) -> torch.Tensor:
        num_nodes = x.size(0)

        if edge_index.size(1) == 0:
            # Molecule with no bonds (isolated atom)
            return self.norm(x)

        src, dst = edge_index[0], edge_index[1]
        msg_input = torch.cat([x[src], x[dst], edge_attr], dim=-1)
        messages = self.message_mlp(msg_input)

        # Aggregate messages into target nodes
        aggregated = torch.zeros(num_nodes, x.size(1), device=x.device, dtype=x.dtype)
        aggregated.index_add_(0, dst, messages)

        # Update node states with residual connection
        update_input = torch.cat([x, aggregated], dim=-1)
        updated = self.update_mlp(update_input)
        return self.norm(x + updated)


class MolecularGNN(nn.Module):
    """
    BioForge Modular Graph Neural Network:
    - Atom Node Encoder
    - Bond Edge Encoder
    - N Message Passing Layers with Residuals
    - Global Graph Pooling (Mean + Max)
    - Property Prediction Head
    """

    def __init__(
        self,
        node_in_dim: int = NODE_DIM,
        edge_in_dim: int = EDGE_DIM,
        hidden_dim: int = 64,
        num_layers: int = 3,
        dropout: float = 0.1,
        out_dim: int = 1,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim

        # Initial Encoders
        self.node_encoder = nn.Sequential(
            nn.Linear(node_in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(edge_in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        # Message Passing Layers
        self.layers = nn.ModuleList(
            [MessagePassingLayer(hidden_dim, hidden_dim, dropout=dropout) for _ in range(num_layers)]
        )

        # Output Prediction Head
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, out_dim),
        )

    def global_pooling(
        self, x: torch.Tensor, batch: torch.Tensor, num_graphs: int
    ) -> torch.Tensor:
        """Combine mean pooling and max pooling over graph nodes."""
        # Mean pooling
        mean_pool = torch.zeros(num_graphs, self.hidden_dim, device=x.device, dtype=x.dtype)
        counts = torch.zeros(num_graphs, 1, device=x.device, dtype=x.dtype)
        mean_pool.index_add_(0, batch, x)
        counts.index_add_(0, batch, torch.ones(x.size(0), 1, device=x.device))
        mean_pool = mean_pool / torch.clamp(counts, min=1.0)

        # Max pooling
        max_pool = torch.full((num_graphs, self.hidden_dim), -1e9, device=x.device, dtype=x.dtype)
        for i in range(num_graphs):
            mask = batch == i
            if mask.any():
                max_pool[i] = x[mask].max(dim=0)[0]
            else:
                max_pool[i] = 0.0

        return torch.cat([mean_pool, max_pool], dim=-1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
        batch: torch.Tensor,
        num_graphs: int,
    ) -> torch.Tensor:
        h = self.node_encoder(x)
        e = self.edge_encoder(edge_attr) if edge_attr.size(0) > 0 else edge_attr

        for layer in self.layers:
            h = layer(h, edge_index, e)

        # Graph-level representation
        graph_repr = self.global_pooling(h, batch, num_graphs)

        # Scalar property prediction
        out = self.head(graph_repr).squeeze(-1)
        return out

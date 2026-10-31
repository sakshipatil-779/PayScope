"""Pydantic schemas for Neo4j Graph Intelligence & Cytoscape.js Explorer."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class GraphNodeData(BaseModel):
    id: str
    label: str
    name: str
    node_type: str  # User, Account, Transaction, Merchant, DescriptorAlias, Commitment, CommitmentInsight, CancellationEvent
    category: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    cadence: Optional[str] = None
    confidence_band: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    data: GraphNodeData


class GraphEdgeData(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str  # OWNS_ACCOUNT, HAS_TRANSACTION, PAID_TO, HAS_DESCRIPTOR, ALIAS_OF, HAS_COMMITMENT, SUPPORTED_BY, HAS_INSIGHT, HAS_CANCELLATION_EVENT, EVIDENCED_BY
    label: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    data: GraphEdgeData


class GraphElements(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphHealthResponse(BaseModel):
    status: str
    enabled: bool
    connected: bool
    uri: str
    database: str
    node_count: int = 0
    edge_count: int = 0
    message: str


class GraphSyncResponse(BaseModel):
    status: str
    nodes_synced: int
    relationships_synced: int
    execution_time_ms: float
    last_sync_at: datetime
    error: Optional[str] = None


class GraphSummaryResponse(BaseModel):
    total_nodes: int
    total_relationships: int
    counts_by_label: Dict[str, int]
    counts_by_relationship: Dict[str, int]
    last_sync_timestamp: Optional[datetime] = None

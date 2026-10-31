"""API endpoints for Phase 10 Neo4j Graph Relationship Intelligence."""
from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.graph.config import neo4j_settings
from app.graph.driver import check_neo4j_connection, get_neo4j_driver
from app.graph.exceptions import Neo4jDisabledError, Neo4jSyncError
from app.graph.query_service import GraphQueryService
from app.graph.schemas import (
    GraphElements,
    GraphHealthResponse,
    GraphSummaryResponse,
    GraphSyncResponse,
)
from app.graph.sync_service import GraphSyncService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/graph", tags=["Graph Intelligence"])


def _resolve_user_id(db: Session, user_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    if user_id:
        return user_id
    user = UserRepository.get_or_create_demo_user(db)
    return user.id


@router.get("/health", response_model=GraphHealthResponse)
def get_graph_health(db: Session = Depends(get_db)) -> GraphHealthResponse:
    """Check connectivity and operational readiness of Neo4j graph engine."""
    enabled = neo4j_settings.ENABLED
    connected = False
    message = "Neo4j is disabled in configuration. Graph explorer operates in relational projection mode."
    node_count = 0
    edge_count = 0

    if enabled:
        try:
            connected = check_neo4j_connection()
            if connected:
                driver = get_neo4j_driver()
                if driver:
                    with driver.session(database=neo4j_settings.DATABASE) as session:
                        n_rec = session.run("MATCH (n) RETURN count(n) AS cnt").single()
                        e_rec = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()
                        node_count = n_rec["cnt"] if n_rec else 0
                        edge_count = e_rec["cnt"] if e_rec else 0
                message = f"Neo4j active and connected to {neo4j_settings.DATABASE} ({node_count} nodes, {edge_count} relationships)."
            else:
                message = f"Neo4j is enabled but unreachable at {neo4j_settings.URI}."
        except Exception as e:
            message = f"Neo4j connection error: {e}"

    return GraphHealthResponse(
        status="healthy" if (not enabled or connected) else "degraded",
        enabled=enabled,
        connected=connected,
        uri=neo4j_settings.URI,
        database=neo4j_settings.DATABASE,
        node_count=node_count,
        edge_count=edge_count,
        message=message,
    )


@router.get("/summary", response_model=GraphSummaryResponse)
def get_graph_summary(db: Session = Depends(get_db)) -> GraphSummaryResponse:
    """Returns entity and relationship count breakdown across the graph projection."""
    svc = GraphQueryService(db)
    return svc.get_summary()


@router.post("/sync", response_model=GraphSyncResponse)
def sync_graph_projection(
    user_id: Optional[uuid.UUID] = Query(None, description="Workspace user UUID"),
    db: Session = Depends(get_db),
) -> GraphSyncResponse:
    """Idempotently synchronizes the PostgreSQL source-of-truth records into Neo4j."""
    target_user_id = _resolve_user_id(db, user_id)
    if not neo4j_settings.ENABLED:
        # Return graceful demo projection response
        return GraphSyncResponse(
            status="simulated",
            nodes_synced=0,
            relationships_synced=0,
            execution_time_ms=0.0,
            last_sync_at=datetime.now(timezone.utc),
            error="Neo4j is currently disabled in environment; PostgreSQL relational projection active.",
        )

    try:
        sync_svc = GraphSyncService(db)
        return sync_svc.sync_user_graph(target_user_id)
    except (Neo4jDisabledError, Neo4jSyncError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sync failed: {e}")


@router.get("/explorer", response_model=GraphElements)
def get_graph_explorer_network(
    user_id: Optional[uuid.UUID] = Query(None, description="Workspace user UUID"),
    db: Session = Depends(get_db),
) -> GraphElements:
    """Retrieve the multi-hop relationship graph elements for Cytoscape.js rendering."""
    target_user_id = _resolve_user_id(db, user_id)
    svc = GraphQueryService(db)
    return svc.get_payment_overview(target_user_id)


@router.get("/merchants/{id}", response_model=GraphElements)
def get_merchant_graph(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> GraphElements:
    """Retrieve merchant descriptor aliases and transaction links for graph exploration."""
    svc = GraphQueryService(db)
    try:
        return svc.get_merchant_descriptors(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/commitments/{id}", response_model=GraphElements)
def get_commitment_graph(
    id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Workspace user UUID"),
    db: Session = Depends(get_db),
) -> GraphElements:
    """Retrieve commitment evidence trail and anomaly insights in Cytoscape graph format."""
    target_user_id = _resolve_user_id(db, user_id)
    svc = GraphQueryService(db)
    try:
        return svc.get_commitment_evidence(target_user_id, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

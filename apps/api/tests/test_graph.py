"""Unit and integration tests for Phase 10 Neo4j Graph Intelligence."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid
import pytest
from fastapi.testclient import TestClient

from app.graph.config import neo4j_settings
from app.graph.driver import check_neo4j_connection, get_neo4j_driver
from app.graph.queries import (
    QUERY_COMMITMENT_EVIDENCE,
    QUERY_MERCHANT_DESCRIPTORS,
    QUERY_PAYMENT_OVERVIEW,
)
from app.graph.query_service import GraphQueryService
from app.graph.schema import SCHEMA_CONSTRAINTS, SCHEMA_INDEXES
from app.graph.schemas import GraphElements
from app.graph.sync_service import GraphSyncService
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.commitment_transaction import CommitmentTransaction
from app.models.demo_user import DemoUser
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant
from app.models.transaction import Transaction


@pytest.fixture
def graph_test_data(db_session):
    user = DemoUser(workspace_key=f"ws_graph_{uuid.uuid4().hex[:6]}")
    db_session.add(user)
    db_session.commit()

    merchant = Merchant(canonical_name="Spotify India", category="Entertainment")
    db_session.add(merchant)
    db_session.commit()

    alias = DescriptorAlias(
        merchant_id=merchant.id,
        alias_text="SPOTIFY*PREMIUM",
        normalised_alias="spotify premium",
        matcher_type="exact",
        pattern="SPOTIFY*PREMIUM",
    )
    db_session.add(alias)
    db_session.commit()

    now = datetime.now(timezone.utc)
    comm = Commitment(
        user_id=user.id,
        merchant_id=merchant.id,
        display_name="Spotify Premium Plan",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("119.00"),
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(comm)
    db_session.commit()

    tx = Transaction(
        user_id=user.id,
        merchant_id=merchant.id,
        transaction_date=now,
        raw_descriptor="UPI/SPOTIFY*PREMIUM/99001",
        amount=Decimal("119.00"),
        direction="debit",
        payment_channel="UPI",
    )
    db_session.add(tx)
    db_session.commit()

    ct = CommitmentTransaction(
        commitment_id=comm.id,
        transaction_id=tx.id,
        relationship_role="evidence",
    )
    db_session.add(ct)
    db_session.commit()

    insight = CommitmentInsight(
        user_id=user.id,
        commitment_id=comm.id,
        insight_type="price_increase",
        severity="low",
        status="open",
        title="Price Check",
        summary="Standard rate verified.",
        explanation="Verified regular debit cycle.",
        unique_fingerprint=f"fp_gr_{uuid.uuid4().hex}",
        confidence_band="high",
        detected_at=now,
    )
    db_session.add(insight)
    db_session.commit()

    return {"user": user, "merchant": merchant, "comm": comm, "tx": tx, "insight": insight}


def test_schema_constraints_defined():
    """Verify essential graph uniqueness constraints and indexes are specified."""
    assert len(SCHEMA_CONSTRAINTS) >= 7
    assert any("User" in c for c in SCHEMA_CONSTRAINTS)
    assert any("Commitment" in c for c in SCHEMA_CONSTRAINTS)
    assert any("Merchant" in c for c in SCHEMA_CONSTRAINTS)
    assert any("Transaction" in c for c in SCHEMA_CONSTRAINTS)
    assert len(SCHEMA_INDEXES) >= 4


def test_cypher_query_syntax_and_parameters():
    """Verify Cypher query templates contain required parameterized tokens."""
    assert "$merchant_id" in QUERY_MERCHANT_DESCRIPTORS
    assert "$commitment_id" in QUERY_COMMITMENT_EVIDENCE
    assert "$user_id" in QUERY_PAYMENT_OVERVIEW


def test_query_service_cytoscape_formatting(db_session, graph_test_data):
    """Verify query service correctly maps records into Cytoscape nodes and edges."""
    svc = GraphQueryService(db_session)
    user = graph_test_data["user"]
    comm = graph_test_data["comm"]
    merchant = graph_test_data["merchant"]

    # 1. Payment overview
    elements = svc.get_payment_overview(user.id)
    assert isinstance(elements, GraphElements)
    assert len(elements.nodes) >= 3  # User, Commitment, Merchant
    assert len(elements.edges) >= 2

    node_types = {n.data.node_type for n in elements.nodes}
    assert "User" in node_types
    assert "Commitment" in node_types
    assert "Merchant" in node_types

    # 2. Commitment evidence
    comm_elements = svc.get_commitment_evidence(user.id, comm.id)
    assert any(n.data.id == str(comm.id) for n in comm_elements.nodes)
    assert any(n.data.id == str(merchant.id) for n in comm_elements.nodes)

    # 3. Merchant descriptors
    m_elements = svc.get_merchant_descriptors(merchant.id)
    assert any(n.data.node_type == "Merchant" for n in m_elements.nodes)


def test_mocked_sync_service_execution(db_session, graph_test_data):
    """Verify idempotent sync service runs without errors when mocked driver is active."""
    user = graph_test_data["user"]
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    with patch("app.graph.sync_service.get_neo4j_driver", return_value=mock_driver), \
         patch("app.graph.config.neo4j_settings.ENABLED", True):
        svc = GraphSyncService(db_session)
        sync_res = svc.sync_user_graph(user.id)

        assert sync_res.status == "success"
        assert sync_res.nodes_synced > 0
        assert sync_res.relationships_synced > 0
        assert mock_session.run.called


def test_api_graph_health(client: TestClient):
    """Test GET /api/v1/graph/health."""
    res = client.get("/api/v1/graph/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "enabled" in data
    assert "connected" in data


def test_api_graph_summary(client: TestClient, db_session, graph_test_data):
    """Test GET /api/v1/graph/summary."""
    res = client.get("/api/v1/graph/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_nodes" in data
    assert data["total_nodes"] >= 3


def test_api_graph_explorer(client: TestClient, db_session, graph_test_data):
    """Test GET /api/v1/graph/explorer."""
    user = graph_test_data["user"]
    res = client.get(f"/api/v1/graph/explorer?user_id={user.id}")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 3

"""Query Service executing parameterized Cypher queries and serializing into Cytoscape elements."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graph.config import neo4j_settings
from app.graph.driver import get_neo4j_driver
from app.graph.exceptions import Neo4jConnectionError, Neo4jDisabledError
from app.graph.queries import (
    QUERY_CATEGORY_RELATIONSHIPS,
    QUERY_COMMITMENT_EVIDENCE,
    QUERY_INSIGHT_RELATIONSHIP,
    QUERY_MERCHANT_COMMITMENTS,
    QUERY_MERCHANT_DESCRIPTORS,
    QUERY_PAYMENT_OVERVIEW,
)
from app.graph.schemas import (
    GraphEdge,
    GraphEdgeData,
    GraphElements,
    GraphNode,
    GraphNodeData,
    GraphSummaryResponse,
)
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.merchant import Merchant
from app.models.transaction import Transaction


class GraphQueryService:
    """Executes parameterized graph queries, converting Neo4j result records into Cytoscape.js elements."""

    def __init__(self, db: Session):
        self.db = db

    def _convert_node(self, node_id: str, label: str, name: str, node_type: str, **kwargs: Any) -> GraphNode:
        return GraphNode(
            data=GraphNodeData(
                id=str(node_id),
                label=label,
                name=name,
                node_type=node_type,
                **kwargs,
            )
        )

    def _convert_edge(self, source: str, target: str, rel_type: str, label: str) -> GraphEdge:
        edge_id = f"e_{source}_{target}_{rel_type}"
        return GraphEdge(
            data=GraphEdgeData(
                id=edge_id,
                source=str(source),
                target=str(target),
                relationship_type=rel_type,
                label=label,
            )
        )

    def get_payment_overview(self, user_id: uuid.UUID) -> GraphElements:
        """Executes Query 6: Payment Relationship Overview."""
        if not neo4j_settings.ENABLED:
            return self._fallback_pg_overview(user_id)

        driver = get_neo4j_driver()
        if not driver:
            return self._fallback_pg_overview(user_id)

        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        try:
            with driver.session(database=neo4j_settings.DATABASE) as session:
                result = session.run(QUERY_PAYMENT_OVERVIEW, user_id=str(user_id))
                record = result.single()
                if not record:
                    return self._fallback_pg_overview(user_id)

                user_node = record["u"]
                if user_node:
                    u_id = user_node["id"]
                    nodes[u_id] = self._convert_node(
                        node_id=u_id,
                        label=user_node.get("display_name", "User"),
                        name=user_node.get("display_name", "User"),
                        node_type="User",
                    )

                for comm in record.get("commitments", []):
                    c_id = comm["id"]
                    nodes[c_id] = self._convert_node(
                        node_id=c_id,
                        label=comm.get("display_name", "Commitment"),
                        name=comm.get("display_name", "Commitment"),
                        node_type="Commitment",
                        status=comm.get("status"),
                        cadence=comm.get("cadence"),
                        amount=float(comm.get("representative_amount") or 0.0),
                    )
                    edges[f"{u_id}_{c_id}"] = self._convert_edge(u_id, c_id, "HAS_COMMITMENT", "has commitment")

                for m in record.get("merchants", []):
                    m_id = m["id"]
                    nodes[m_id] = self._convert_node(
                        node_id=m_id,
                        label=m.get("canonical_name", "Merchant"),
                        name=m.get("canonical_name", "Merchant"),
                        node_type="Merchant",
                        category=m.get("category"),
                    )

                for ins in record.get("insights", []):
                    i_id = ins["id"]
                    nodes[i_id] = self._convert_node(
                        node_id=i_id,
                        label=ins.get("title", "Insight"),
                        name=ins.get("title", "Insight"),
                        node_type="CommitmentInsight",
                        category=ins.get("insight_type"),
                        status=ins.get("severity"),
                    )

                for tx in record.get("transactions", []):
                    tx_id = tx["id"]
                    nodes[tx_id] = self._convert_node(
                        node_id=tx_id,
                        label=f"Debit ₹{tx.get('amount')}",
                        name=tx.get("raw_descriptor", "Transaction"),
                        node_type="Transaction",
                        amount=float(tx.get("amount") or 0.0),
                    )

        except Exception:
            return self._fallback_pg_overview(user_id)

        return GraphElements(nodes=list(nodes.values()), edges=list(edges.values()))

    def get_merchant_descriptors(self, merchant_id: uuid.UUID) -> GraphElements:
        """Executes Query 1: Merchant Descriptor Discovery."""
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        if neo4j_settings.ENABLED:
            driver = get_neo4j_driver()
            if driver:
                try:
                    with driver.session(database=neo4j_settings.DATABASE) as session:
                        result = session.run(QUERY_MERCHANT_DESCRIPTORS, merchant_id=str(merchant_id))
                        record = result.single()
                        if record and record["m"]:
                            m = record["m"]
                            m_id = m["id"]
                            nodes[m_id] = self._convert_node(
                                node_id=m_id,
                                label=m.get("canonical_name", "Merchant"),
                                name=m.get("canonical_name", "Merchant"),
                                node_type="Merchant",
                                category=m.get("category"),
                            )

                            for d in record.get("aliases", []):
                                d_id = d["id"]
                                nodes[d_id] = self._convert_node(
                                    node_id=d_id,
                                    label=d.get("raw_pattern", "Alias"),
                                    name=d.get("raw_pattern", "Alias"),
                                    node_type="DescriptorAlias",
                                )
                                edges[f"{d_id}_{m_id}"] = self._convert_edge(d_id, m_id, "ALIAS_OF", "alias of")

                            for t in record.get("transactions", []):
                                t_id = t["id"]
                                nodes[t_id] = self._convert_node(
                                    node_id=t_id,
                                    label=f"Tx ₹{t.get('amount')}",
                                    name=t.get("raw_descriptor", "Transaction"),
                                    node_type="Transaction",
                                    amount=float(t.get("amount") or 0.0),
                                )
                                edges[f"{t_id}_{m_id}"] = self._convert_edge(t_id, m_id, "PAID_TO", "paid to")

                            return GraphElements(nodes=list(nodes.values()), edges=list(edges.values()))
                except Exception:
                    pass

        # PostgreSQL fallback for merchant descriptors
        merchant = self.db.execute(select(Merchant).where(Merchant.id == merchant_id)).scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found.")

        m_id = str(merchant.id)
        nodes[m_id] = self._convert_node(
            node_id=m_id,
            label=merchant.canonical_name,
            name=merchant.canonical_name,
            node_type="Merchant",
            category=merchant.category,
        )

        for a in merchant.aliases:
            a_id = str(a.id)
            pattern_text = a.pattern or a.alias_text
            nodes[a_id] = self._convert_node(
                node_id=a_id,
                label=pattern_text,
                name=pattern_text,
                node_type="DescriptorAlias",
            )
            edges[f"{a_id}_{m_id}"] = self._convert_edge(a_id, m_id, "ALIAS_OF", "alias of")

        return GraphElements(nodes=list(nodes.values()), edges=list(edges.values()))

    def get_commitment_evidence(self, user_id: uuid.UUID, commitment_id: uuid.UUID) -> GraphElements:
        """Executes Query 3: Commitment Evidence Trace."""
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        comm = self.db.execute(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not comm:
            raise ValueError(f"Commitment {commitment_id} not found.")

        c_id = str(comm.id)
        nodes[c_id] = self._convert_node(
            node_id=c_id,
            label=comm.display_name,
            name=comm.display_name,
            node_type="Commitment",
            status=comm.status,
            amount=float(comm.representative_amount or 0.0),
        )

        if comm.merchant:
            m_id = str(comm.merchant.id)
            nodes[m_id] = self._convert_node(
                node_id=m_id,
                label=comm.merchant.canonical_name,
                name=comm.merchant.canonical_name,
                node_type="Merchant",
                category=comm.merchant.category,
            )
            edges[f"{c_id}_{m_id}"] = self._convert_edge(c_id, m_id, "ASSOCIATED_WITH", "associated with")

        # Supporting transactions
        for tx in comm.transactions:
            t_id = str(tx.id)
            nodes[t_id] = self._convert_node(
                node_id=t_id,
                label=f"Debit ₹{tx.amount}",
                name=tx.raw_descriptor,
                node_type="Transaction",
                amount=float(tx.amount),
            )
            edges[f"{c_id}_{t_id}"] = self._convert_edge(c_id, t_id, "SUPPORTED_BY", "supported by")

        # Insights
        for ins in comm.insights:
            i_id = str(ins.id)
            nodes[i_id] = self._convert_node(
                node_id=i_id,
                label=ins.title,
                name=ins.title,
                node_type="CommitmentInsight",
                category=ins.insight_type,
                status=ins.severity,
            )
            edges[f"{c_id}_{i_id}"] = self._convert_edge(c_id, i_id, "HAS_INSIGHT", "has insight")

        return GraphElements(nodes=list(nodes.values()), edges=list(edges.values()))

    def _fallback_pg_overview(self, user_id: uuid.UUID) -> GraphElements:
        """PostgreSQL relational projection fallback for graph explorer."""
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        u_id = str(user_id)
        nodes[u_id] = self._convert_node(node_id=u_id, label="Demo Workspace", name="Workspace Owner", node_type="User")

        commitments = list(self.db.execute(select(Commitment).where(Commitment.user_id == user_id)).scalars().all())

        for c in commitments:
            c_id = str(c.id)
            nodes[c_id] = self._convert_node(
                node_id=c_id,
                label=c.display_name,
                name=c.display_name,
                node_type="Commitment",
                status=c.status,
                cadence=c.cadence,
                amount=float(c.representative_amount or 0.0),
            )
            edges[f"{u_id}_{c_id}"] = self._convert_edge(u_id, c_id, "HAS_COMMITMENT", "has commitment")

            if c.merchant:
                m_id = str(c.merchant.id)
                if m_id not in nodes:
                    nodes[m_id] = self._convert_node(
                        node_id=m_id,
                        label=c.merchant.canonical_name,
                        name=c.merchant.canonical_name,
                        node_type="Merchant",
                        category=c.merchant.category,
                    )
                edges[f"{c_id}_{m_id}"] = self._convert_edge(c_id, m_id, "ASSOCIATED_WITH", "associated with")

            for ins in c.insights:
                i_id = str(ins.id)
                nodes[i_id] = self._convert_node(
                    node_id=i_id,
                    label=ins.title,
                    name=ins.title,
                    node_type="CommitmentInsight",
                    category=ins.insight_type,
                    status=ins.severity,
                )
                edges[f"{c_id}_{i_id}"] = self._convert_edge(c_id, i_id, "HAS_INSIGHT", "has insight")

            for tx in c.transactions[:5]:
                t_id = str(tx.id)
                if t_id not in nodes:
                    nodes[t_id] = self._convert_node(
                        node_id=t_id,
                        label=f"Debit ₹{tx.amount}",
                        name=tx.raw_descriptor,
                        node_type="Transaction",
                        amount=float(tx.amount),
                    )
                edges[f"{c_id}_{t_id}"] = self._convert_edge(c_id, t_id, "SUPPORTED_BY", "supported by")

        return GraphElements(nodes=list(nodes.values()), edges=list(edges.values()))

    def get_summary(self) -> GraphSummaryResponse:
        """Returns node and relationship counts from Neo4j or PostgreSQL fallback."""
        if neo4j_settings.ENABLED:
            driver = get_neo4j_driver()
            if driver:
                try:
                    with driver.session(database=neo4j_settings.DATABASE) as session:
                        node_res = session.run("MATCH (n) RETURN count(n) AS node_count").single()
                        edge_res = session.run("MATCH ()-[r]->() RETURN count(r) AS edge_count").single()
                        return GraphSummaryResponse(
                            total_nodes=node_res["node_count"] if node_res else 0,
                            total_relationships=edge_res["edge_count"] if edge_res else 0,
                            counts_by_label={},
                            counts_by_relationship={},
                            last_sync_timestamp=datetime.now(timezone.utc),
                        )
                except Exception:
                    pass

        # Relational fallback
        merchants_count = self.db.query(Merchant).count()
        commitments_count = self.db.query(Commitment).count()
        transactions_count = self.db.query(Transaction).count()
        insights_count = self.db.query(CommitmentInsight).count()

        total_nodes = merchants_count + commitments_count + min(transactions_count, 100) + insights_count + 1
        return GraphSummaryResponse(
            total_nodes=total_nodes,
            total_relationships=commitments_count * 2 + insights_count,
            counts_by_label={
                "Merchant": merchants_count,
                "Commitment": commitments_count,
                "Transaction": min(transactions_count, 100),
                "CommitmentInsight": insights_count,
            },
            counts_by_relationship={},
            last_sync_timestamp=None,
        )

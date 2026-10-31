"""Graph Synchronization Service projecting PostgreSQL source-of-truth records into Neo4j."""
from datetime import datetime, timezone
import time
from typing import Dict, List, Optional
import uuid
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graph.config import neo4j_settings
from app.graph.driver import get_neo4j_driver
from app.graph.exceptions import Neo4jConnectionError, Neo4jDisabledError, Neo4jSyncError
from app.graph.schema import initialize_graph_schema
from app.graph.schemas import GraphSyncResponse
from app.models.account import Account
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.commitment_transaction import CommitmentTransaction
from app.models.demo_user import DemoUser
from app.models.descriptor_alias import DescriptorAlias
from app.models.insight_evidence import InsightEvidence
from app.models.merchant import Merchant
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class GraphSyncService:
    """Manages idempotent synchronization of entities and relationships from PostgreSQL to Neo4j."""

    def __init__(self, db: Session):
        self.db = db

    def sync_user_graph(self, user_id: uuid.UUID) -> GraphSyncResponse:
        """Synchronizes all entities and relationships associated with a user workspace."""
        if not neo4j_settings.ENABLED:
            raise Neo4jDisabledError("Neo4j graph integration is disabled.")

        driver = get_neo4j_driver()
        if not driver:
            raise Neo4jConnectionError("Neo4j driver is unavailable.")

        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)

        # Ensure schema constraints are active
        try:
            initialize_graph_schema(driver, database=neo4j_settings.DATABASE)
        except Exception as e:
            logger.warning(f"Schema initialization warning: {e}")

        # Fetch records from PostgreSQL
        user = self.db.execute(select(DemoUser).where(DemoUser.id == user_id)).scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found.")

        accounts = list(self.db.execute(select(Account).where(Account.user_id == user_id)).scalars().all())
        transactions = list(self.db.execute(select(Transaction).where(Transaction.user_id == user_id)).scalars().all())
        commitments = list(self.db.execute(select(Commitment).where(Commitment.user_id == user_id)).scalars().all())
        insights = list(self.db.execute(select(CommitmentInsight).where(CommitmentInsight.user_id == user_id)).scalars().all())
        cancellations = list(self.db.execute(select(CancellationEvent).where(CancellationEvent.user_id == user_id)).scalars().all())
        merchants = list(self.db.execute(select(Merchant)).scalars().all())
        aliases = list(self.db.execute(select(DescriptorAlias)).scalars().all())
        comm_txs = list(
            self.db.execute(
                select(CommitmentTransaction)
                .join(Commitment, CommitmentTransaction.commitment_id == Commitment.id)
                .where(Commitment.user_id == user_id)
            ).scalars().all()
        )
        insight_evidences = list(
            self.db.execute(
                select(InsightEvidence)
                .join(CommitmentInsight, InsightEvidence.insight_id == CommitmentInsight.id)
                .where(CommitmentInsight.user_id == user_id)
            ).scalars().all()
        )

        nodes_count = 0
        relationships_count = 0

        # Execute idempotent MERGE operations inside a Neo4j session
        try:
            with driver.session(database=neo4j_settings.DATABASE) as session:
                # 1. User Node
                session.run(
                    """
                    MERGE (u:User {id: $id})
                    SET u.workspace_key = $workspace_key,
                        u.display_name = $display_name,
                        u.updated_at = $updated_at
                    """,
                    id=str(user.id),
                    workspace_key=user.workspace_key,
                    display_name=user.display_name or "Demo User",
                    updated_at=now.isoformat(),
                )
                nodes_count += 1

                # 2. Merchants & Aliases
                for m in merchants:
                    session.run(
                        """
                        MERGE (m:Merchant {id: $id})
                        SET m.canonical_name = $canonical_name,
                            m.category = $category
                        """,
                        id=str(m.id),
                        canonical_name=m.canonical_name,
                        category=m.category or "General",
                    )
                    nodes_count += 1

                for a in aliases:
                    session.run(
                        """
                        MERGE (d:DescriptorAlias {id: $id})
                        SET d.raw_pattern = $raw_pattern,
                            d.alias_type = $alias_type
                        WITH d
                        MATCH (m:Merchant {id: $merchant_id})
                        MERGE (d)-[:ALIAS_OF]->(m)
                        """,
                        id=str(a.id),
                        raw_pattern=a.pattern or a.alias_text,
                        alias_type=a.matcher_type or "exact",
                        merchant_id=str(a.merchant_id),
                    )
                    nodes_count += 1
                    relationships_count += 1

                # 3. Accounts
                for acc in accounts:
                    session.run(
                        """
                        MERGE (a:Account {id: $id})
                        SET a.account_type = $account_type,
                            a.account_number_masked = $account_number_masked,
                            a.currency = $currency
                        WITH a
                        MATCH (u:User {id: $user_id})
                        MERGE (u)-[:OWNS_ACCOUNT]->(a)
                        """,
                        id=str(acc.id),
                        account_type=acc.account_type,
                        account_number_masked=acc.account_number_masked,
                        currency=acc.currency,
                        user_id=str(user_id),
                    )
                    nodes_count += 1
                    relationships_count += 1

                # 4. Transactions
                for tx in transactions:
                    session.run(
                        """
                        MERGE (t:Transaction {id: $id})
                        SET t.raw_descriptor = $raw_descriptor,
                            t.amount = $amount,
                            t.direction = $direction,
                            t.transaction_date = $transaction_date,
                            t.payment_channel = $payment_channel,
                            t.user_id = $user_id
                        WITH t
                        WHERE $account_id IS NOT NULL
                        MATCH (a:Account {id: $account_id})
                        MERGE (a)-[:HAS_TRANSACTION]->(t)
                        """,
                        id=str(tx.id),
                        raw_descriptor=tx.raw_descriptor,
                        amount=float(tx.amount),
                        direction=tx.direction,
                        transaction_date=tx.transaction_date.isoformat(),
                        payment_channel=tx.payment_channel or "unknown",
                        user_id=str(user_id),
                        account_id=str(tx.account_id) if tx.account_id else None,
                    )
                    nodes_count += 1
                    if tx.account_id:
                        relationships_count += 1

                    # Link Transaction -> Merchant if merchant_id is present
                    if tx.merchant_id:
                        session.run(
                            """
                            MATCH (t:Transaction {id: $tx_id})
                            MATCH (m:Merchant {id: $merchant_id})
                            MERGE (t)-[:PAID_TO]->(m)
                            """,
                            tx_id=str(tx.id),
                            merchant_id=str(tx.merchant_id),
                        )
                        relationships_count += 1

                # 5. Commitments
                for c in commitments:
                    session.run(
                        """
                        MERGE (comm:Commitment {id: $id})
                        SET comm.display_name = $display_name,
                            comm.commitment_type = $commitment_type,
                            comm.cadence = $cadence,
                            comm.representative_amount = $amount,
                            comm.status = $status,
                            comm.confidence_band = $confidence_band,
                            comm.user_id = $user_id
                        WITH comm
                        MATCH (u:User {id: $user_id})
                        MERGE (u)-[:HAS_COMMITMENT]->(comm)
                        """,
                        id=str(c.id),
                        display_name=c.display_name,
                        commitment_type=c.commitment_type,
                        cadence=c.cadence,
                        amount=float(c.representative_amount) if c.representative_amount else 0.0,
                        status=c.status,
                        confidence_band=c.confidence_band,
                        user_id=str(user_id),
                    )
                    nodes_count += 1
                    relationships_count += 1

                    if c.merchant_id:
                        session.run(
                            """
                            MATCH (comm:Commitment {id: $c_id})
                            MATCH (m:Merchant {id: $m_id})
                            MERGE (comm)-[:ASSOCIATED_WITH]->(m)
                            """,
                            c_id=str(c.id),
                            m_id=str(c.merchant_id),
                        )
                        relationships_count += 1

                # 6. Commitment -> Transaction (SUPPORTED_BY)
                for ct in comm_txs:
                    session.run(
                        """
                        MATCH (comm:Commitment {id: $comm_id})
                        MATCH (t:Transaction {id: $tx_id})
                        MERGE (comm)-[:SUPPORTED_BY]->(t)
                        """,
                        comm_id=str(ct.commitment_id),
                        tx_id=str(ct.transaction_id),
                    )
                    relationships_count += 1

                # 7. Insights
                for ins in insights:
                    session.run(
                        """
                        MERGE (i:CommitmentInsight {id: $id})
                        SET i.insight_type = $insight_type,
                            i.severity = $severity,
                            i.status = $status,
                            i.title = $title,
                            i.summary = $summary,
                            i.detected_at = $detected_at,
                            i.user_id = $user_id
                        WITH i
                        MATCH (comm:Commitment {id: $comm_id})
                        MERGE (comm)-[:HAS_INSIGHT]->(i)
                        """,
                        id=str(ins.id),
                        insight_type=ins.insight_type,
                        severity=ins.severity,
                        status=ins.status,
                        title=ins.title,
                        summary=ins.summary,
                        detected_at=ins.detected_at.isoformat(),
                        user_id=str(user_id),
                        comm_id=str(ins.commitment_id),
                    )
                    nodes_count += 1
                    relationships_count += 1

                # 8. Insight Evidence -> Transaction (EVIDENCED_BY)
                for ie in insight_evidences:
                    session.run(
                        """
                        MATCH (i:CommitmentInsight {id: $insight_id})
                        MATCH (t:Transaction {id: $tx_id})
                        MERGE (i)-[:EVIDENCED_BY]->(t)
                        """,
                        insight_id=str(ie.insight_id),
                        tx_id=str(ie.transaction_id),
                    )
                    relationships_count += 1

                # 9. Cancellation Events
                for canc in cancellations:
                    session.run(
                        """
                        MERGE (ce:CancellationEvent {id: $id})
                        SET ce.event_source = $event_source,
                            ce.confirmation_type = $confirmation_type,
                            ce.event_timestamp = $timestamp,
                            ce.user_id = $user_id
                        WITH ce
                        MATCH (comm:Commitment {id: $comm_id})
                        MERGE (comm)-[:HAS_CANCELLATION_EVENT]->(ce)
                        """,
                        id=str(canc.id),
                        event_source=canc.event_source,
                        confirmation_type=canc.confirmation_type,
                        timestamp=canc.event_timestamp.isoformat(),
                        user_id=str(user_id),
                        comm_id=str(canc.commitment_id),
                    )
                    nodes_count += 1
                    relationships_count += 1

        except Exception as e:
            logger.error(f"Neo4j sync failed: {e}")
            raise Neo4jSyncError(f"Failed to synchronize graph to Neo4j: {e}")

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return GraphSyncResponse(
            status="success",
            nodes_synced=nodes_count,
            relationships_synced=relationships_count,
            execution_time_ms=execution_time_ms,
            last_sync_at=now,
        )

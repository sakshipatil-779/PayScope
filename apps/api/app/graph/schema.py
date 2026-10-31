"""Neo4j graph schema constraints and index definitions."""
import logging
from neo4j import Driver

logger = logging.getLogger(__name__)

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT descriptor_id_unique IF NOT EXISTS FOR (d:DescriptorAlias) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT commitment_id_unique IF NOT EXISTS FOR (c:Commitment) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT insight_id_unique IF NOT EXISTS FOR (i:CommitmentInsight) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT cancellation_id_unique IF NOT EXISTS FOR (ce:CancellationEvent) REQUIRE ce.id IS UNIQUE",
]

SCHEMA_INDEXES = [
    "CREATE INDEX user_workspace_idx IF NOT EXISTS FOR (u:User) ON (u.workspace_key)",
    "CREATE INDEX merchant_category_idx IF NOT EXISTS FOR (m:Merchant) ON (m.category)",
    "CREATE INDEX commitment_status_idx IF NOT EXISTS FOR (c:Commitment) ON (c.status)",
    "CREATE INDEX transaction_date_idx IF NOT EXISTS FOR (t:Transaction) ON (t.transaction_date)",
]


def initialize_graph_schema(driver: Driver, database: str = "neo4j") -> None:
    """Creates schema constraints and indexes idempotently."""
    with driver.session(database=database) as session:
        for stmt in SCHEMA_CONSTRAINTS:
            try:
                session.run(stmt)
            except Exception as e:
                logger.warning(f"Could not apply constraint '{stmt}': {e}")

        for stmt in SCHEMA_INDEXES:
            try:
                session.run(stmt)
            except Exception as e:
                logger.warning(f"Could not apply index '{stmt}': {e}")

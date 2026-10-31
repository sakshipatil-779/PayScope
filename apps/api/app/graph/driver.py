"""Neo4j driver connection management."""
from typing import Optional
import logging
from neo4j import GraphDatabase, Driver
from app.graph.config import neo4j_settings
from app.graph.exceptions import Neo4jConnectionError, Neo4jDisabledError

logger = logging.getLogger(__name__)

_driver_instance: Optional[Driver] = None


def get_neo4j_driver() -> Optional[Driver]:
    """Returns singleton Neo4j driver or None if disabled."""
    global _driver_instance

    if not neo4j_settings.ENABLED:
        return None

    if _driver_instance is None:
        try:
            _driver_instance = GraphDatabase.driver(
                neo4j_settings.URI,
                auth=(neo4j_settings.USERNAME, neo4j_settings.PASSWORD),
                max_connection_lifetime=neo4j_settings.MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=neo4j_settings.MAX_CONNECTION_POOL_SIZE,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j driver: {e}")
            _driver_instance = None
            raise Neo4jConnectionError(f"Could not connect to Neo4j at {neo4j_settings.URI}: {e}")

    return _driver_instance


def close_neo4j_driver() -> None:
    """Closes the Neo4j driver connection pool."""
    global _driver_instance
    if _driver_instance:
        try:
            _driver_instance.close()
        except Exception as e:
            logger.warning(f"Error closing Neo4j driver: {e}")
        finally:
            _driver_instance = None


def check_neo4j_connection() -> bool:
    """Verifies connectivity with the configured Neo4j instance."""
    if not neo4j_settings.ENABLED:
        return False

    driver = get_neo4j_driver()
    if not driver:
        return False

    try:
        driver.verify_connectivity()
        return True
    except Exception as e:
        logger.warning(f"Neo4j connectivity check failed: {e}")
        return False

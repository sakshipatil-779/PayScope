"""Exceptions for Neo4j Graph operations."""


class Neo4jError(Exception):
    """Base exception for Neo4j errors."""
    pass


class Neo4jDisabledError(Neo4jError):
    """Raised when an operation is attempted while Neo4j is disabled."""
    pass


class Neo4jConnectionError(Neo4jError):
    """Raised when connection to Neo4j database fails or times out."""
    pass


class Neo4jSyncError(Neo4jError):
    """Raised when graph projection synchronization fails."""
    pass


class Neo4jQueryError(Neo4jError):
    """Raised when a Cypher query execution fails."""
    pass

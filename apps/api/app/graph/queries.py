"""Parameterized Cypher queries for PayScope Relationship Intelligence."""

# Query 1: Merchant Descriptor Discovery
# Find all transaction descriptors and aliases associated with a canonical merchant
QUERY_MERCHANT_DESCRIPTORS = """
MATCH (m:Merchant {id: $merchant_id})
OPTIONAL MATCH (d:DescriptorAlias)-[r1:ALIAS_OF]->(m)
OPTIONAL MATCH (t:Transaction)-[r2:HAS_DESCRIPTOR]->(d)
OPTIONAL MATCH (t2:Transaction)-[r3:PAID_TO]->(m)
RETURN m, collect(DISTINCT d) AS aliases, collect(DISTINCT t) + collect(DISTINCT t2) AS transactions
"""

# Query 2: Merchant Commitment Map
# Explore all recurring commitments associated with a merchant for a user
QUERY_MERCHANT_COMMITMENTS = """
MATCH (u:User {id: $user_id})-[:HAS_COMMITMENT]->(c:Commitment)-[:ASSOCIATED_WITH]->(m:Merchant {id: $merchant_id})
OPTIONAL MATCH (c)-[r_ins:HAS_INSIGHT]->(i:CommitmentInsight)
OPTIONAL MATCH (c)-[r_tx:SUPPORTED_BY]->(t:Transaction)
RETURN m, collect(DISTINCT c) AS commitments, collect(DISTINCT i) AS insights, collect(DISTINCT t) AS transactions
"""

# Query 3: Commitment Evidence Trace
# Retrieve supporting transactions, insights, and cancellation events for a commitment
QUERY_COMMITMENT_EVIDENCE = """
MATCH (c:Commitment {id: $commitment_id, user_id: $user_id})
OPTIONAL MATCH (c)-[:ASSOCIATED_WITH]->(m:Merchant)
OPTIONAL MATCH (c)-[r_tx:SUPPORTED_BY]->(t:Transaction)
OPTIONAL MATCH (c)-[r_ins:HAS_INSIGHT]->(i:CommitmentInsight)
OPTIONAL MATCH (c)-[r_canc:HAS_CANCELLATION_EVENT]->(ce:CancellationEvent)
RETURN c, m, collect(DISTINCT t) AS transactions, collect(DISTINCT i) AS insights, collect(DISTINCT ce) AS cancellations
"""

# Query 4: Financial Insight Relationship
# Trace an insight to commitment, merchant, and underlying transaction evidence
QUERY_INSIGHT_RELATIONSHIP = """
MATCH (i:CommitmentInsight {id: $insight_id, user_id: $user_id})
MATCH (c:Commitment)-[:HAS_INSIGHT]->(i)
OPTIONAL MATCH (c)-[:ASSOCIATED_WITH]->(m:Merchant)
OPTIONAL MATCH (i)-[:EVIDENCED_BY]->(t_ev:Transaction)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(t_supp:Transaction)
RETURN i, c, m, collect(DISTINCT t_ev) AS evidence_transactions, collect(DISTINCT t_supp) AS supporting_transactions
"""

# Query 5: Category Relationship Exploration
# Explore commitments and canonical merchants within a category for a user
QUERY_CATEGORY_RELATIONSHIPS = """
MATCH (u:User {id: $user_id})-[:HAS_COMMITMENT]->(c:Commitment)
MATCH (c)-[:ASSOCIATED_WITH]->(m:Merchant {category: $category})
OPTIONAL MATCH (c)-[:HAS_INSIGHT]->(i:CommitmentInsight)
RETURN m, collect(DISTINCT c) AS commitments, collect(DISTINCT i) AS insights
"""

# Query 6: Payment Relationship Overview (Full User Network Projection)
QUERY_PAYMENT_OVERVIEW = """
MATCH (u:User {id: $user_id})
OPTIONAL MATCH (u)-[:OWNS_ACCOUNT]->(a:Account)
OPTIONAL MATCH (a)-[:HAS_TRANSACTION]->(t:Transaction)
OPTIONAL MATCH (u)-[:HAS_COMMITMENT]->(c:Commitment)
OPTIONAL MATCH (c)-[:ASSOCIATED_WITH]->(m:Merchant)
OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(t_supp:Transaction)
OPTIONAL MATCH (c)-[:HAS_INSIGHT]->(i:CommitmentInsight)
RETURN u, 
       collect(DISTINCT a) AS accounts, 
       collect(DISTINCT c) AS commitments, 
       collect(DISTINCT m) AS merchants, 
       collect(DISTINCT i) AS insights,
       collect(DISTINCT t_supp)[0..30] AS transactions
"""

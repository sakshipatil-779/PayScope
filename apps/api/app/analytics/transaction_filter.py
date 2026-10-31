"""Filter for transactions eligible for recurrence analysis."""
from typing import List
from app.models.transaction import Transaction


def filter_eligible_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """Filter raw transactions for those eligible for recurring commitment detection.
    
    Eligibility rules:
    - Direction must be 'debit' (excludes salary credits, refunds, reversals).
    - Status must be 'successful' (excludes failed, pending, cancelled).
    - Amount must be strictly greater than 0.00 (excludes zero-value auth pings).
    - Must have a valid transaction_date.
    
    Returns:
        List of eligible Transaction objects sorted by transaction_date ascending.
    """
    eligible = [
        txn
        for txn in transactions
        if txn.direction == "debit"
        and txn.transaction_status == "successful"
        and txn.amount is not None
        and float(txn.amount) > 0.0
        and txn.transaction_date is not None
    ]
    
    # Sort deterministically by transaction_date and id
    eligible.sort(key=lambda t: (t.transaction_date, str(t.id)))
    return eligible

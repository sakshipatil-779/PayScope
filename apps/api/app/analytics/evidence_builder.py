"""Evidence builder linking transactions to discovered commitments."""
from decimal import Decimal
from typing import List
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.transaction import Transaction


def build_commitment_evidence(
    commitment: Commitment,
    transactions: List[Transaction],
) -> List[CommitmentTransaction]:
    """Build junction evidence records linking transactions to the commitment.
    
    Args:
        commitment: The Commitment instance.
        transactions: List of constituent transactions in the stream.
        
    Returns:
        List of unpersisted CommitmentTransaction junction records.
    """
    evidence_records: List[CommitmentTransaction] = []
    rep_amount = commitment.representative_amount or Decimal("0.00")

    for txn in transactions:
        txn_amt = txn.amount or Decimal("0.00")
        diff = abs(txn_amt - rep_amount)

        # Check for amount change evidence
        if rep_amount > Decimal("0.00") and diff >= Decimal("1.00"):
            role = "amount_change_evidence"
            reason = f"Billing amount {txn_amt} differs from representative {rep_amount}"
        else:
            role = "recurrence_evidence"
            reason = f"Periodic debit evidence matching {commitment.cadence} cadence"

        evidence = CommitmentTransaction(
            commitment_id=commitment.id,
            transaction_id=txn.id,
            relationship_role=role,
            match_confidence=commitment.confidence_score or Decimal("100.00"),
            reason=reason,
        )
        evidence_records.append(evidence)

    return evidence_records

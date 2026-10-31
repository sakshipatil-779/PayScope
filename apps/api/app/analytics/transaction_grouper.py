"""Grouping logic to cluster eligible transactions into payee candidate streams."""
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from app.models.transaction import Transaction


@dataclass
class TransactionStream:
    """A clustered stream of transactions for a single potential recurring payee."""
    group_key: str
    user_id: uuid.UUID
    merchant_id: Optional[uuid.UUID]
    display_name: str
    merchant_category: Optional[str]
    currency: str
    payment_channels: Set[str] = field(default_factory=set)
    transactions: List[Transaction] = field(default_factory=list)


def group_transactions_by_stream(
    user_id: uuid.UUID,
    transactions: List[Transaction],
) -> List[TransactionStream]:
    """Group transactions into candidate recurring streams.
    
    Grouping strategy:
    1. If transaction has a matched `merchant_id`, group by `(merchant_id, currency)`.
       This automatically groups multi-descriptor variants of the same merchant
       (e.g. StreamPulse Direct and STRPULSE*MONTHLY) into one stream.
    2. If `merchant_id` is null, group by `(cleaned normalised_descriptor, currency)`.
    
    Args:
        user_id: The UUID of the workspace user.
        transactions: Pre-filtered eligible transactions.
        
    Returns:
        List of TransactionStream instances, each containing sorted transactions.
    """
    streams_map: Dict[str, TransactionStream] = {}

    for txn in transactions:
        curr = txn.currency or "INR"
        if txn.merchant_id is not None:
            group_key = f"m_{txn.merchant_id}_{curr}"
            if group_key not in streams_map:
                merchant_name = txn.merchant.canonical_name if txn.merchant else "Unknown Merchant"
                category = txn.merchant.category if txn.merchant else None
                streams_map[group_key] = TransactionStream(
                    group_key=group_key,
                    user_id=user_id,
                    merchant_id=txn.merchant_id,
                    display_name=merchant_name,
                    merchant_category=category,
                    currency=curr,
                )
        else:
            norm = (txn.normalised_descriptor or txn.raw_descriptor or "Unknown").strip()
            group_key = f"d_{norm.lower()}_{curr}"
            if group_key not in streams_map:
                streams_map[group_key] = TransactionStream(
                    group_key=group_key,
                    user_id=user_id,
                    merchant_id=None,
                    display_name=norm,
                    merchant_category=None,
                    currency=curr,
                )

        stream = streams_map[group_key]
        stream.transactions.append(txn)
        if txn.payment_channel:
            stream.payment_channels.add(txn.payment_channel)

    # Sort transactions in each stream chronologically
    for stream in streams_map.values():
        stream.transactions.sort(key=lambda t: (t.transaction_date, str(t.id)))

    return list(streams_map.values())

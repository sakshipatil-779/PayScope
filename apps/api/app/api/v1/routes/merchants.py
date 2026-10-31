"""Merchant catalogue and descriptor resolution endpoints."""
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.matching.normalizer import DescriptorNormalizer
from app.matching.reprocessor import TransactionReprocessor
from app.matching.resolver import MerchantResolver
from app.matching.schemas import (
    CandidateMerchantResponse,
    DescriptorAliasResponse,
    MerchantResponse,
    ReprocessRequest,
    ResolveDescriptorRequest,
    ResolveDescriptorResponse,
)
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("", response_model=List[MerchantResponse], status_code=status.HTTP_200_OK)
def list_merchants(
    q: Optional[str] = Query(None, description="Search query across canonical names and categories"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve canonical merchant reference catalogue with alias and transaction metrics."""
    stmt = select(Merchant)
    if q:
        stmt = stmt.where(
            Merchant.canonical_name.ilike(f"%{q.strip()}%") | Merchant.category.ilike(f"%{q.strip()}%")
        )
    if category:
        stmt = stmt.where(Merchant.category == category.strip())

    stmt = stmt.order_by(Merchant.canonical_name.asc()).limit(limit).offset(offset)
    merchants = list(db.scalars(stmt).all())

    # Collect alias counts and transaction counts in batch
    results = []
    for m in merchants:
        alias_cnt = db.scalar(
            select(func.count(DescriptorAlias.id)).where(DescriptorAlias.merchant_id == m.id)
        ) or 0
        txn_cnt = db.scalar(
            select(func.count(Transaction.id)).where(Transaction.merchant_id == m.id)
        ) or 0

        results.append(
            MerchantResponse(
                id=m.id,
                canonical_name=m.canonical_name,
                category=m.category,
                commitment_type_default=m.commitment_type_default,
                website_url=m.website_url,
                support_url=m.support_url,
                is_fictional_demo_merchant=m.is_fictional_demo_merchant,
                reference_source=m.reference_source,
                alias_count=alias_cnt,
                transaction_count=txn_cnt,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )

    return results


@router.get("/{merchant_id}", response_model=MerchantResponse, status_code=status.HTTP_200_OK)
def get_merchant(
    merchant_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve detailed metadata for a specific canonical merchant."""
    merchant = db.scalar(select(Merchant).where(Merchant.id == merchant_id))
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found.")

    alias_cnt = db.scalar(
        select(func.count(DescriptorAlias.id)).where(DescriptorAlias.merchant_id == merchant.id)
    ) or 0
    txn_cnt = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.merchant_id == merchant.id)
    ) or 0

    return MerchantResponse(
        id=merchant.id,
        canonical_name=merchant.canonical_name,
        category=merchant.category,
        commitment_type_default=merchant.commitment_type_default,
        website_url=merchant.website_url,
        support_url=merchant.support_url,
        is_fictional_demo_merchant=merchant.is_fictional_demo_merchant,
        reference_source=merchant.reference_source,
        alias_count=alias_cnt,
        transaction_count=txn_cnt,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
    )


@router.get("/{merchant_id}/aliases", response_model=List[DescriptorAliasResponse], status_code=status.HTTP_200_OK)
def list_merchant_aliases(
    merchant_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve all descriptor aliases associated with a canonical merchant."""
    merchant = db.scalar(select(Merchant).where(Merchant.id == merchant_id))
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found.")

    stmt = select(DescriptorAlias).where(DescriptorAlias.merchant_id == merchant_id).order_by(DescriptorAlias.created_at.asc())
    aliases = list(db.scalars(stmt).all())
    return aliases


@router.post("/resolve", response_model=ResolveDescriptorResponse, status_code=status.HTTP_200_OK)
def resolve_descriptor_preview(
    req: ResolveDescriptorRequest,
    db: Session = Depends(get_db),
):
    """Diagnostic and preview resolution endpoint for arbitrary raw descriptors."""
    resolver = MerchantResolver.from_db(db)
    result = resolver.resolve(req.raw_descriptor)

    candidate_responses = [
        CandidateMerchantResponse(
            merchant_id=c.merchant_id,
            canonical_name=c.canonical_name,
            category=c.category,
            score=c.score,
            method=c.method,
            confidence_band=c.confidence_band,
        )
        for c in result.candidates
    ]

    return ResolveDescriptorResponse(
        raw_descriptor=result.raw_descriptor,
        normalised_descriptor=result.normalised_descriptor,
        status=result.status,
        merchant_id=result.merchant_id,
        merchant_name=result.merchant_name,
        category=result.category,
        match_method=result.match_method,
        score=result.score,
        confidence_band=result.confidence_band,
        explanation=result.explanation,
        is_ambiguous=result.is_ambiguous,
        candidates=candidate_responses,
    )


@router.post("/reprocess-unmatched", status_code=status.HTTP_200_OK)
def reprocess_unmatched_transactions(
    req: Optional[ReprocessRequest] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reprocess stored transactions through the merchant intelligence engine."""
    user = UserRepository.get_or_create_demo_user(db)
    force = req.force_all if req else False
    result = TransactionReprocessor.reprocess(db, user.id, force_all=force)
    return result

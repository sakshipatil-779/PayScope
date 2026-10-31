"""Descriptor alias management endpoints."""
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.matching.config import DEFAULT_MATCHING_CONFIG
from app.matching.normalizer import DescriptorNormalizer
from app.matching.regex_matcher import RegexMatcher
from app.matching.schemas import CreateAliasRequest, DescriptorAliasResponse, UpdateAliasRequest
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant

router = APIRouter(prefix="/merchant-aliases", tags=["Merchant Aliases"])


@router.post("", response_model=DescriptorAliasResponse, status_code=status.HTTP_201_CREATED)
def create_descriptor_alias(
    req: CreateAliasRequest,
    db: Session = Depends(get_db),
):
    """Add a new descriptor alias to a canonical merchant."""
    merchant = db.scalar(select(Merchant).where(Merchant.id == req.merchant_id))
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target merchant not found.")

    norm_alias = DescriptorNormalizer.normalize(req.alias_text)
    if not norm_alias:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alias text cannot be empty.")

    # Validate pattern if regex
    if req.matcher_type == "regex" and req.pattern:
        is_valid, err = RegexMatcher.validate_pattern(req.pattern, DEFAULT_MATCHING_CONFIG)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    # Check for duplicate alias on this merchant
    existing = db.scalar(
        select(DescriptorAlias).where(
            DescriptorAlias.merchant_id == req.merchant_id,
            DescriptorAlias.normalised_alias == norm_alias,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already exists for this merchant.")

    new_alias = DescriptorAlias(
        merchant_id=req.merchant_id,
        alias_text=req.alias_text,
        normalised_alias=norm_alias,
        matcher_type=req.matcher_type,
        pattern=req.pattern,
        confidence_band=req.confidence_band,
        reference_source="user_added",
        is_active=True,
    )
    db.add(new_alias)
    db.commit()
    db.refresh(new_alias)
    return new_alias


@router.patch("/{alias_id}", response_model=DescriptorAliasResponse, status_code=status.HTTP_200_OK)
def update_descriptor_alias(
    alias_id: uuid.UUID,
    req: UpdateAliasRequest,
    db: Session = Depends(get_db),
):
    """Update settings or activation status of a descriptor alias."""
    alias = db.scalar(select(DescriptorAlias).where(DescriptorAlias.id == alias_id))
    if not alias:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found.")

    if req.matcher_type is not None:
        alias.matcher_type = req.matcher_type
    if req.pattern is not None:
        if alias.matcher_type == "regex":
            is_valid, err = RegexMatcher.validate_pattern(req.pattern, DEFAULT_MATCHING_CONFIG)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
        alias.pattern = req.pattern
    if req.confidence_band is not None:
        alias.confidence_band = req.confidence_band
    if req.is_active is not None:
        alias.is_active = req.is_active

    db.commit()
    db.refresh(alias)
    return alias

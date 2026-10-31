"""Exact canonical and known alias matcher."""
from typing import List, Optional
from app.matching.normalizer import DescriptorNormalizer
from app.matching.schemas import MatchCandidate
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


class ExactMatcher:
    """Evaluates Stage 1 (Exact Canonical) and Stage 2 (Exact Curated Alias) matches."""

    @classmethod
    def match_canonical(
        cls,
        normalised_desc: str,
        merchants: List[Merchant],
    ) -> Optional[MatchCandidate]:
        """Stage 1: Check if normalised descriptor exactly matches any canonical merchant name."""
        for merchant in merchants:
            norm_canonical = DescriptorNormalizer.normalize(merchant.canonical_name)
            if normalised_desc == norm_canonical:
                return MatchCandidate(
                    merchant_id=merchant.id,
                    canonical_name=merchant.canonical_name,
                    category=merchant.category,
                    score=100.0,
                    method="exact_canonical",
                    confidence_band="high",
                    matched_alias=merchant.canonical_name,
                )
        return None

    @classmethod
    def match_alias(
        cls,
        normalised_desc: str,
        aliases: List[DescriptorAlias],
        merchants_by_id: dict,
    ) -> Optional[MatchCandidate]:
        """Stage 2: Check if normalised descriptor exactly matches any active curated alias."""
        for alias in aliases:
            if not alias.is_active:
                continue
            if alias.matcher_type == "exact" and normalised_desc == alias.normalised_alias:
                merchant = merchants_by_id.get(alias.merchant_id)
                if merchant:
                    return MatchCandidate(
                        merchant_id=merchant.id,
                        canonical_name=merchant.canonical_name,
                        category=merchant.category,
                        score=100.0,
                        method="exact_alias",
                        confidence_band=alias.confidence_band or "high",
                        matched_alias=alias.alias_text,
                        matched_alias_id=alias.id,
                    )
        return None

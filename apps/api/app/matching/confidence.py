"""Confidence evaluation, ambiguity detection, and status assignment."""
import re
from typing import List, Optional
from app.matching.config import MatchingConfig
from app.matching.schemas import MatchCandidate, MatchResolutionResult


class ConfidenceEvaluator:
    """Evaluates candidates, detects ambiguity/aggregators, and assigns resolution status."""

    # Aggregator prefixes and patterns that should not resolve automatically without merchant signal
    GENERIC_AGGREGATOR_PATTERNS = [
        re.compile(r"^billdesk\b", re.IGNORECASE),
        re.compile(r"^razorpay\s*(merch|gateway|pg|intl)?\b", re.IGNORECASE),
        re.compile(r"^payu\s*(biz|money|in)?\b", re.IGNORECASE),
        re.compile(r"^ccavenue\b", re.IGNORECASE),
        re.compile(r"^cashfree\b", re.IGNORECASE),
    ]

    @classmethod
    def is_generic_aggregator(cls, normalised_desc: str) -> bool:
        """Check if descriptor is an ambiguous aggregator payment descriptor."""
        for pattern in cls.GENERIC_AGGREGATOR_PATTERNS:
            if pattern.search(normalised_desc):
                return True
        return False

    @classmethod
    def evaluate(
        cls,
        raw_descriptor: str,
        normalised_descriptor: str,
        exact_candidate: Optional[MatchCandidate],
        pattern_candidates: List[MatchCandidate],
        fuzzy_candidates: List[MatchCandidate],
        config: MatchingConfig,
    ) -> MatchResolutionResult:
        """Combine all matcher stages into a final explainable resolution result."""
        # 1. Exact canonical or verified alias match (Stages 1 & 2)
        if exact_candidate is not None:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="MATCHED_HIGH",
                merchant_id=exact_candidate.merchant_id,
                merchant_name=exact_candidate.canonical_name,
                category=exact_candidate.category,
                matched_alias_id=exact_candidate.matched_alias_id,
                match_method=exact_candidate.method,
                score=exact_candidate.score,
                confidence_band="high",
                explanation=f"Exact match on {exact_candidate.method.replace('_', ' ')}: '{exact_candidate.matched_alias}'.",
                is_ambiguous=False,
                candidates=[exact_candidate],
            )

        # 2. Check for generic aggregator pattern (Scenario 12)
        if cls.is_generic_aggregator(normalised_descriptor):
            # Consolidate candidate list
            all_candidates = pattern_candidates + fuzzy_candidates
            top_cand = all_candidates[0] if all_candidates else None
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="NEEDS_REVIEW",
                merchant_id=top_cand.merchant_id if top_cand else None,
                merchant_name=top_cand.canonical_name if top_cand else None,
                category=top_cand.category if top_cand else None,
                matched_alias_id=top_cand.matched_alias_id if top_cand else None,
                match_method="aggregator_pattern",
                score=top_cand.score if top_cand else 50.0,
                confidence_band="low",
                explanation="Generic payment aggregator descriptor detected. Routed to manual review to confirm downstream merchant.",
                is_ambiguous=True,
                candidates=all_candidates[:5],
            )

        # 3. Combine pattern and fuzzy candidates, deduplicating by merchant_id (best score wins)
        merged: dict[str, MatchCandidate] = {}
        for cand in pattern_candidates + fuzzy_candidates:
            mid_str = str(cand.merchant_id)
            if mid_str not in merged or cand.score > merged[mid_str].score:
                merged[mid_str] = cand

        all_candidates = sorted(merged.values(), key=lambda c: c.score, reverse=True)

        # 4. If no candidate met minimum threshold
        if not all_candidates or all_candidates[0].score < config.min_match_threshold:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="UNRESOLVED",
                score=all_candidates[0].score if all_candidates else 0.0,
                confidence_band="none",
                explanation="No reference merchant matched the descriptor within acceptable similarity thresholds.",
                is_ambiguous=False,
                candidates=all_candidates[:5],
            )

        top_cand = all_candidates[0]

        # 5. Ambiguity check: Compare #1 vs #2 candidate score difference
        if len(all_candidates) > 1:
            second_cand = all_candidates[1]
            margin = top_cand.score - second_cand.score
            if margin < config.min_ambiguity_margin and second_cand.score >= config.medium_confidence_threshold:
                return MatchResolutionResult(
                    raw_descriptor=raw_descriptor,
                    normalised_descriptor=normalised_descriptor,
                    status="NEEDS_REVIEW",
                    merchant_id=top_cand.merchant_id,
                    merchant_name=top_cand.canonical_name,
                    category=top_cand.category,
                    matched_alias_id=top_cand.matched_alias_id,
                    match_method=top_cand.method,
                    score=top_cand.score,
                    confidence_band="medium",
                    explanation=(
                        f"Ambiguous candidates: '{top_cand.canonical_name}' ({top_cand.score:.1f}%) and "
                        f"'{second_cand.canonical_name}' ({second_cand.score:.1f}%) are too close "
                        f"(margin {margin:.1f} < {config.min_ambiguity_margin:.1f})."
                    ),
                    is_ambiguous=True,
                    candidates=all_candidates[:5],
                )

        # 6. Clear candidate: classify based on score threshold
        if top_cand.score >= config.high_confidence_threshold:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="MATCHED_HIGH",
                merchant_id=top_cand.merchant_id,
                merchant_name=top_cand.canonical_name,
                category=top_cand.category,
                matched_alias_id=top_cand.matched_alias_id,
                match_method=top_cand.method,
                score=top_cand.score,
                confidence_band="high",
                explanation=f"High confidence match via {top_cand.method.replace('_', ' ')} (score: {top_cand.score:.1f}%).",
                is_ambiguous=False,
                candidates=all_candidates[:5],
            )
        elif top_cand.score >= config.medium_confidence_threshold:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="MATCHED_MEDIUM",
                merchant_id=top_cand.merchant_id,
                merchant_name=top_cand.canonical_name,
                category=top_cand.category,
                matched_alias_id=top_cand.matched_alias_id,
                match_method=top_cand.method,
                score=top_cand.score,
                confidence_band="medium",
                explanation=f"Medium confidence candidate via {top_cand.method.replace('_', ' ')} (score: {top_cand.score:.1f}%).",
                is_ambiguous=False,
                candidates=all_candidates[:5],
            )
        else:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_descriptor,
                status="NEEDS_REVIEW",
                merchant_id=top_cand.merchant_id,
                merchant_name=top_cand.canonical_name,
                category=top_cand.category,
                matched_alias_id=top_cand.matched_alias_id,
                match_method=top_cand.method,
                score=top_cand.score,
                confidence_band="low",
                explanation=f"Low confidence candidate (score: {top_cand.score:.1f}%). Routed to manual review.",
                is_ambiguous=False,
                candidates=all_candidates[:5],
            )

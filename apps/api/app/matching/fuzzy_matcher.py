"""RapidFuzz fuzzy matching engine."""
from typing import Dict, List
from rapidfuzz import fuzz
from app.matching.config import MatchingConfig
from app.matching.normalizer import DescriptorNormalizer
from app.matching.schemas import MatchCandidate
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


class FuzzyMatcher:
    """Evaluates Stage 4 (RapidFuzz string similarity) matches."""

    @classmethod
    def match(
        cls,
        normalised_desc: str,
        merchants: List[Merchant],
        aliases: List[DescriptorAlias],
        config: MatchingConfig,
    ) -> List[MatchCandidate]:
        """Compute fuzzy scores across all canonical merchants and active aliases."""
        if not normalised_desc or len(normalised_desc.strip()) < 3:
            return []

        # Map merchant ID to best score candidate
        best_per_merchant: Dict[str, MatchCandidate] = {}

        # 1. Compare against Canonical Names
        for m in merchants:
            norm_name = DescriptorNormalizer.normalize(m.canonical_name)
            score_ts = fuzz.token_set_ratio(normalised_desc, norm_name)
            score_sort = fuzz.token_sort_ratio(normalised_desc, norm_name)
            score_w = fuzz.WRatio(normalised_desc, norm_name)

            best_score = max(score_ts, score_sort, score_w)
            if best_score >= config.min_match_threshold:
                conf = (
                    "high"
                    if best_score >= config.high_confidence_threshold
                    else "medium"
                    if best_score >= config.medium_confidence_threshold
                    else "low"
                )
                best_per_merchant[str(m.id)] = MatchCandidate(
                    merchant_id=m.id,
                    canonical_name=m.canonical_name,
                    category=m.category,
                    score=float(best_score),
                    method="rapidfuzz_canonical",
                    confidence_band=conf,
                    matched_alias=m.canonical_name,
                )

        # 2. Compare against Known Aliases
        merchants_by_id = {m.id: m for m in merchants}
        for alias in aliases:
            if not alias.is_active:
                continue

            merchant = merchants_by_id.get(alias.merchant_id)
            if not merchant:
                continue

            score_ts = fuzz.token_set_ratio(normalised_desc, alias.normalised_alias)
            score_sort = fuzz.token_sort_ratio(normalised_desc, alias.normalised_alias)
            score_w = fuzz.WRatio(normalised_desc, alias.normalised_alias)

            best_score = max(score_ts, score_sort, score_w)
            if best_score >= config.min_match_threshold:
                current_best = best_per_merchant.get(str(merchant.id))
                if current_best is None or best_score > current_best.score:
                    conf = (
                        "high"
                        if best_score >= config.high_confidence_threshold
                        else "medium"
                        if best_score >= config.medium_confidence_threshold
                        else "low"
                    )
                    best_per_merchant[str(merchant.id)] = MatchCandidate(
                        merchant_id=merchant.id,
                        canonical_name=merchant.canonical_name,
                        category=merchant.category,
                        score=float(best_score),
                        method="rapidfuzz_alias",
                        confidence_band=conf,
                        matched_alias=alias.alias_text,
                        matched_alias_id=alias.id,
                    )

        # Sort descending by score
        candidates = list(best_per_merchant.values())
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

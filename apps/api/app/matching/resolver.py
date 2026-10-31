"""Main descriptor resolution orchestrator."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.matching.confidence import ConfidenceEvaluator
from app.matching.config import DEFAULT_MATCHING_CONFIG, MatchingConfig
from app.matching.exact_matcher import ExactMatcher
from app.matching.fuzzy_matcher import FuzzyMatcher
from app.matching.normalizer import DescriptorNormalizer
from app.matching.regex_matcher import RegexMatcher
from app.matching.schemas import MatchResolutionResult
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


class MerchantResolver:
    """Orchestrates multi-stage deterministic and fuzzy descriptor resolution."""

    def __init__(
        self,
        merchants: Optional[List[Merchant]] = None,
        aliases: Optional[List[DescriptorAlias]] = None,
        config: MatchingConfig = DEFAULT_MATCHING_CONFIG,
    ):
        self.config = config
        self.merchants = merchants or []
        self.aliases = aliases or []
        self.merchants_by_id = {m.id: m for m in self.merchants}

    @classmethod
    def from_db(cls, db: Session, config: MatchingConfig = DEFAULT_MATCHING_CONFIG) -> "MerchantResolver":
        """Instantiate resolver pre-loaded with active database merchants and aliases."""
        merchants = list(db.scalars(select(Merchant)).all())
        aliases = list(db.scalars(select(DescriptorAlias).where(DescriptorAlias.is_active == True)).all())
        return cls(merchants=merchants, aliases=aliases, config=config)

    def resolve(self, raw_descriptor: str) -> MatchResolutionResult:
        """Resolve a raw descriptor through the 6-stage merchant intelligence pipeline."""
        normalised_desc = DescriptorNormalizer.normalize(raw_descriptor)

        if not normalised_desc:
            return MatchResolutionResult(
                raw_descriptor=raw_descriptor or "",
                normalised_descriptor="",
                status="UNRESOLVED",
                score=0.0,
                confidence_band="none",
                explanation="Empty or null descriptor cannot be resolved.",
                is_ambiguous=False,
                candidates=[],
            )

        # Stage 1: Exact Canonical Match
        exact_canonical = ExactMatcher.match_canonical(normalised_desc, self.merchants)
        if exact_canonical:
            return ConfidenceEvaluator.evaluate(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_desc,
                exact_candidate=exact_canonical,
                pattern_candidates=[],
                fuzzy_candidates=[],
                config=self.config,
            )

        # Stage 2: Exact Curated Alias Match
        exact_alias = ExactMatcher.match_alias(normalised_desc, self.aliases, self.merchants_by_id)
        if exact_alias:
            return ConfidenceEvaluator.evaluate(
                raw_descriptor=raw_descriptor,
                normalised_descriptor=normalised_desc,
                exact_candidate=exact_alias,
                pattern_candidates=[],
                fuzzy_candidates=[],
                config=self.config,
            )

        # Stage 3: Regex & Prefix Matching
        pattern_candidates = RegexMatcher.match(normalised_desc, self.aliases, self.merchants_by_id, self.config)

        # Stage 4: RapidFuzz Matching
        fuzzy_candidates = FuzzyMatcher.match(normalised_desc, self.merchants, self.aliases, self.config)

        # Stages 5 & 6: Candidate Comparison, Ambiguity Check & Classification
        return ConfidenceEvaluator.evaluate(
            raw_descriptor=raw_descriptor,
            normalised_descriptor=normalised_desc,
            exact_candidate=None,
            pattern_candidates=pattern_candidates,
            fuzzy_candidates=fuzzy_candidates,
            config=self.config,
        )

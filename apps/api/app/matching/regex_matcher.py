"""Regex, prefix, and token-pattern matcher with safety validation."""
import re
from typing import List, Optional
from app.matching.config import MatchingConfig
from app.matching.schemas import MatchCandidate
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


class RegexMatcher:
    """Evaluates Stage 3 (Prefix, Regex, and Token-pattern) matches."""

    @classmethod
    def validate_pattern(cls, pattern_str: str, config: MatchingConfig) -> tuple[bool, Optional[str]]:
        """Validate a regex pattern before compilation or persistence."""
        if not pattern_str or len(pattern_str.strip()) == 0:
            return False, "Pattern cannot be empty."

        if len(pattern_str) > config.max_regex_pattern_length:
            return False, f"Pattern exceeds maximum length of {config.max_regex_pattern_length} characters."

        # Detect high-risk nested quantifiers prone to catastrophic backtracking
        if re.search(r"\([^)]*(\+|\*)[^)]*\)(\+|\*)", pattern_str):
            return False, "High-risk nested quantifier detected (catastrophic backtracking risk)."

        try:
            re.compile(pattern_str, re.IGNORECASE)
            return True, None
        except re.error as e:
            return False, f"Invalid regular expression syntax: {str(e)}"

    @classmethod
    def match(
        cls,
        normalised_desc: str,
        aliases: List[DescriptorAlias],
        merchants_by_id: dict,
        config: MatchingConfig,
    ) -> List[MatchCandidate]:
        """Find candidate matches using active prefix, token_pattern, and regex aliases."""
        candidates: List[MatchCandidate] = []
        tokens = set(normalised_desc.split())

        for alias in aliases:
            if not alias.is_active:
                continue

            merchant = merchants_by_id.get(alias.merchant_id)
            if not merchant:
                continue

            # --- Type A: Prefix matcher ---
            if alias.matcher_type == "prefix":
                prefix = alias.normalised_alias.strip()
                if normalised_desc.startswith(prefix) or f" {prefix} " in f" {normalised_desc} ":
                    score = 95.0 if normalised_desc.startswith(prefix) else 90.0
                    candidates.append(
                        MatchCandidate(
                            merchant_id=merchant.id,
                            canonical_name=merchant.canonical_name,
                            category=merchant.category,
                            score=score,
                            method="prefix_pattern",
                            confidence_band=alias.confidence_band or "high",
                            matched_alias=alias.alias_text,
                            matched_alias_id=alias.id,
                        )
                    )

            # --- Type B: Token pattern matcher ---
            elif alias.matcher_type == "token_pattern":
                alias_tokens = set(alias.normalised_alias.split())
                if alias_tokens and alias_tokens.issubset(tokens):
                    # Exact subset of tokens matched
                    candidates.append(
                        MatchCandidate(
                            merchant_id=merchant.id,
                            canonical_name=merchant.canonical_name,
                            category=merchant.category,
                            score=92.0,
                            method="token_pattern",
                            confidence_band=alias.confidence_band or "high",
                            matched_alias=alias.alias_text,
                            matched_alias_id=alias.id,
                        )
                    )

            # --- Type C: Regex matcher ---
            elif alias.matcher_type == "regex" and alias.pattern:
                is_valid, _ = cls.validate_pattern(alias.pattern, config)
                if not is_valid:
                    continue

                try:
                    compiled = re.compile(alias.pattern, re.IGNORECASE)
                    if compiled.search(normalised_desc):
                        candidates.append(
                            MatchCandidate(
                                merchant_id=merchant.id,
                                canonical_name=merchant.canonical_name,
                                category=merchant.category,
                                score=95.0,
                                method="regex_pattern",
                                confidence_band=alias.confidence_band or "high",
                                matched_alias=alias.alias_text,
                                matched_alias_id=alias.id,
                            )
                        )
                except Exception:
                    # Failsafe: ignore runtime regex errors
                    continue

        return candidates

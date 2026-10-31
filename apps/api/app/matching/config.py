"""Matching engine configuration and threshold parameters."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingConfig:
    """Configurable thresholds for deterministic and fuzzy descriptor resolution."""

    matcher_version: str = "v1.0"

    # RapidFuzz scoring thresholds (0-100)
    exact_match_score: float = 100.0
    high_confidence_threshold: float = 90.0
    medium_confidence_threshold: float = 75.0
    min_match_threshold: float = 60.0

    # Ambiguity margin: if (top_score - second_score) < margin, flag as ambiguous
    min_ambiguity_margin: float = 10.0

    # Max length of descriptor input to prevent DoS
    max_descriptor_length: int = 500

    # Max regex compilation execution timeout / safety
    max_regex_pattern_length: int = 100


DEFAULT_MATCHING_CONFIG = MatchingConfig()

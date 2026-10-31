"""Configuration for synthetic data generation."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class GeneratorConfig:
    """Settings controlling deterministic synthetic dataset generation."""

    seed: int = 42
    start_date: date = date(2026, 5, 1)
    end_date: date = date(2026, 10, 31)
    currency: str = "INR"
    user_workspace_key: str = "demo_workspace_primary"
    min_transactions: int = 80
    min_notifications: int = 15

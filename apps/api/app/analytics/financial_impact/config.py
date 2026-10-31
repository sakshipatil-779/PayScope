"""Configuration constants for Phase 7 Financial Impact & Savings Intelligence."""
from decimal import Decimal

# Cadence annual multipliers
CADENCE_ANNUAL_MULTIPLIERS = {
    "weekly": Decimal("52.0"),
    "fortnightly": Decimal("26.0"),
    "monthly": Decimal("12.0"),
    "quarterly": Decimal("4.0"),
    "annual": Decimal("1.0"),
}

# Cadence monthly multipliers (amount * multiplier = monthly cost)
CADENCE_MONTHLY_MULTIPLIERS = {
    "weekly": Decimal("52") / Decimal("12"),       # ~4.333333
    "fortnightly": Decimal("26") / Decimal("12"),  # ~2.166667
    "monthly": Decimal("1.0"),
    "quarterly": Decimal("1") / Decimal("3"),      # ~0.333333
    "annual": Decimal("1") / Decimal("12"),        # ~0.083333
}

# Commitment classification boundaries
CONFIRMED_STATUSES = {"active", "user_confirmed"}
CANDIDATE_STATUSES = {"candidate"}
INACTIVE_STATUSES = {"inactive", "ended_user_recorded", "marked_not_recurring"}
REVIEW_STATUSES = {"review_required"}

CONFIRMED_CONFIDENCE_BANDS = {"high", "medium"}
UNCONFIRMED_CONFIDENCE_BANDS = {"low", "needs_review"}

# Savings classifications
SAVINGS_CLASS_POTENTIAL = "POTENTIAL"
SAVINGS_CLASS_USER_SELECTED = "USER_SELECTED"
SAVINGS_CLASS_REALIZED = "REALIZED"

# Historical periods in days
HISTORICAL_PERIODS = {
    "30d": 30,
    "90d": 90,
    "180d": 180,
    "365d": 365,
    "all": None,
}


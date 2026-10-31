"""Savings Intelligence engine: opportunity discovery, evidence linking, and what-if calculations."""
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.analytics.financial_impact.commitment_costs import get_user_commitment_costs
from app.analytics.financial_impact.config import (
    SAVINGS_CLASS_POTENTIAL,
    SAVINGS_CLASS_USER_SELECTED,
)
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.schemas import (
    SavingsCalculateRequest,
    SavingsCalculateResponse,
    SavingsOpportunityItem,
    SavingsSummaryResponse,
)
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.insight_evidence import InsightEvidence
from app.models.price_event import PriceEvent
from app.models.usage_coverage import UsageCoverage


def get_user_savings_opportunities(
    db: Session,
    user_id: uuid.UUID,
) -> List[SavingsOpportunityItem]:
    """Discover explainable savings opportunities for the user.

    Sources:
    1. Sustained price increases (Price events & insights).
    2. Potentially unused commitments (Verified usage coverage only).
    3. Category duplicate services (Multiple active commitments in same category).

    Guarantees:
    - Never labels potential savings as realized.
    - Excludes unverified or insufficient usage coverage.
    - Preserves links to insights, price events, and coverage evidence.
    """
    cost_items = get_user_commitment_costs(db, user_id)
    cost_map = {item.commitment_id: item for item in cost_items}
    confirmed_items = [item for item in cost_items if item.is_confirmed]

    opportunities: List[SavingsOpportunityItem] = []

    # ----------------------------------------------------
    # 1. Price Increase Opportunities
    # ----------------------------------------------------
    price_events_stmt = (
        select(PriceEvent)
        .join(Commitment, PriceEvent.commitment_id == Commitment.id)
        .options(joinedload(PriceEvent.commitment).joinedload(Commitment.merchant))
        .where(
            Commitment.user_id == user_id,
            PriceEvent.event_type.in_(["amount_increase", "PRICE_INCREASE"]),
        )
        .order_by(PriceEvent.effective_or_detected_at.desc())
    )
    price_events = db.scalars(price_events_stmt).unique().all()

    price_insights_stmt = (
        select(CommitmentInsight)
        .where(
            CommitmentInsight.user_id == user_id,
            CommitmentInsight.insight_type.ilike("%price%"),
            CommitmentInsight.status.in_(["open", "acknowledged", "OPEN", "ACKNOWLEDGED"]),
        )
    )
    price_insights = db.scalars(price_insights_stmt).all()
    c_insight_map = {pi.commitment_id: pi for pi in price_insights}

    seen_price_commitment_ids: Set[uuid.UUID] = set()

    for pe in price_events:
        c = pe.commitment
        if not c or c.id in seen_price_commitment_ids:
            continue
        seen_price_commitment_ids.add(c.id)

        c_item = cost_map.get(c.id)
        current_monthly = c_item.normalized_monthly_cost if c_item else (pe.new_amount or Decimal("0.00"))
        current_annual = c_item.annualized_cost if c_item else (current_monthly * Decimal("12"))

        monthly_increase = pe.absolute_change or Decimal("0.00")
        annual_impact = monthly_increase * Decimal("12")

        merchant_name = c.merchant.canonical_name if c.merchant else c.display_name
        linked_insight = c_insight_map.get(c.id)
        insight_id = linked_insight.id if linked_insight else None

        opp_id = f"opp_price_{pe.id}"
        pct_change = float(pe.percentage_change or 0.0)
        prev_amt = pe.previous_amount or Decimal("0.00")
        new_amt = pe.new_amount or Decimal("0.00")
        dt_str = pe.effective_or_detected_at.strftime("%d-%b-%Y")

        opportunities.append(
            SavingsOpportunityItem(
                id=opp_id,
                opportunity_type="PRICE_INCREASE",
                classification=SAVINGS_CLASS_POTENTIAL,
                commitment_id=c.id,
                commitment_name=c.display_name,
                merchant_name=merchant_name,
                category=c.commitment_type,
                current_monthly_cost=round_currency(current_monthly),
                current_annual_cost=round_currency(current_annual),
                potential_monthly_saving=round_currency(monthly_increase),
                potential_annual_saving=round_currency(annual_impact),
                evidence_summary=(
                    f"Price increased from ₹{prev_amt:,.2f} to ₹{new_amt:,.2f} "
                    f"(+{pct_change:.1f}%) on {dt_str}. "
                    f"Annual incremental impact is ₹{annual_impact:,.2f}."
                ),
                insight_id=insight_id,
                price_event_id=pe.id,
                details={
                    "previous_amount": float(prev_amt),
                    "new_amount": float(new_amt),
                    "absolute_increase": float(monthly_increase),
                    "percentage_increase": pct_change,
                    "detected_at": pe.effective_or_detected_at.isoformat(),
                },
            )
        )

    # ----------------------------------------------------
    # 2. Potentially Unused Commitments (Verified Coverage Only)
    # ----------------------------------------------------
    unused_insights_stmt = (
        select(CommitmentInsight)
        .options(
            joinedload(CommitmentInsight.commitment).joinedload(Commitment.merchant),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.usage_coverage),
        )
        .where(
            CommitmentInsight.user_id == user_id,
            CommitmentInsight.insight_type.ilike("%unused%"),
            CommitmentInsight.status.in_(["open", "acknowledged", "OPEN", "ACKNOWLEDGED"]),
        )
    )
    unused_insights = db.scalars(unused_insights_stmt).unique().all()

    for ui in unused_insights:
        c = ui.commitment
        if not c:
            continue

        cov: Optional[UsageCoverage] = None
        for ev in ui.evidence_items:
            if ev.usage_coverage:
                cov = ev.usage_coverage
                break

        if not cov:
            cov_stmt = (
                select(UsageCoverage)
                .where(UsageCoverage.commitment_id == c.id)
                .order_by(UsageCoverage.coverage_end.desc())
            )
            cov = db.scalars(cov_stmt).first()

        if not cov:
            continue

        # STRICT REQUIREMENT: Only verified coverage (coverage_complete == True)
        # Exclude incomplete, unverified or absent coverage
        is_complete = getattr(cov, "coverage_complete", False)
        if not is_complete:
            continue

        c_item = cost_map.get(c.id)
        current_monthly = c_item.normalized_monthly_cost if c_item else (c.representative_amount or Decimal("0.00"))
        current_annual = c_item.annualized_cost if c_item else (current_monthly * Decimal("12"))

        merchant_name = c.merchant.canonical_name if c.merchant else c.display_name

        cov_start = getattr(cov, "coverage_start", None)
        cov_end = getattr(cov, "coverage_end", None)
        days_inactive = (cov_end - cov_start).days if (cov_start and cov_end) else getattr(cov, "days_without_activity", 0)
        src_label = getattr(cov, "source_label", "activity_tracker")
        cov_start_str = cov_start.strftime("%d-%b-%Y") if cov_start else ""
        cov_end_str = cov_end.strftime("%d-%b-%Y") if cov_end else ""

        opp_id = f"opp_unused_{ui.id}"
        opportunities.append(
            SavingsOpportunityItem(
                id=opp_id,
                opportunity_type="POTENTIALLY_UNUSED",
                classification=SAVINGS_CLASS_POTENTIAL,
                commitment_id=c.id,
                commitment_name=c.display_name,
                merchant_name=merchant_name,
                category=c.commitment_type,
                current_monthly_cost=round_currency(current_monthly),
                current_annual_cost=round_currency(current_annual),
                potential_monthly_saving=round_currency(current_monthly),
                potential_annual_saving=round_currency(current_annual),
                evidence_summary=(
                    f"No recorded activity detected across {days_inactive} days "
                    f"({cov_start_str} to {cov_end_str}) via {src_label}. "
                    f"Potential annual saving of ₹{current_annual:,.2f} if discontinued."
                ),
                insight_id=ui.id,
                usage_coverage_id=cov.id,
                details={
                    "coverage_source": src_label,
                    "coverage_complete": is_complete,
                    "coverage_status": "COMPLETE",
                    "days_without_activity": days_inactive,
                    "coverage_start": cov_start.isoformat() if cov_start else None,
                    "coverage_end": cov_end.isoformat() if cov_end else None,
                },
            )
        )

    # ----------------------------------------------------
    # 3. Category Duplicate Services (Multiple Active Services)
    # ----------------------------------------------------
    category_map: Dict[str, List[Any]] = {}
    for item in confirmed_items:
        cat = (item.commitment_type or "other").lower()
        category_map.setdefault(cat, []).append(item)

    for cat, items in category_map.items():
        if len(items) > 1:
            sorted_items = sorted(items, key=lambda x: x.annualized_cost)
            for secondary in sorted_items[:-1]:
                opp_id = f"opp_dup_{secondary.commitment_id}"
                opportunities.append(
                    SavingsOpportunityItem(
                        id=opp_id,
                        opportunity_type="CATEGORY_DUPLICATE",
                        classification=SAVINGS_CLASS_POTENTIAL,
                        commitment_id=secondary.commitment_id,
                        commitment_name=secondary.display_name,
                        merchant_name=secondary.merchant_name,
                        category=secondary.commitment_type,
                        current_monthly_cost=secondary.normalized_monthly_cost,
                        current_annual_cost=secondary.annualized_cost,
                        potential_monthly_saving=secondary.normalized_monthly_cost,
                        potential_annual_saving=secondary.annualized_cost,
                        evidence_summary=(
                            f"Multiple active commitments found in category '{cat.title()}' "
                            f"({len(items)} services active). Review whether {secondary.display_name} "
                            f"is duplicative."
                        ),
                        details={
                            "category": cat,
                            "active_category_count": len(items),
                            "other_services": [x.display_name for x in items if x.commitment_id != secondary.commitment_id],
                        },
                    )
                )

    return opportunities


def get_user_savings_summary(
    db: Session,
    user_id: uuid.UUID,
) -> SavingsSummaryResponse:
    """Return total potential savings aggregated by opportunity type with full opportunity breakdown."""
    opps = get_user_savings_opportunities(db, user_id)

    price_inc_savings = Decimal("0.00")
    unused_savings = Decimal("0.00")
    dup_savings = Decimal("0.00")

    commitment_max_savings: Dict[uuid.UUID, Decimal] = {}
    for opp in opps:
        t = opp.opportunity_type
        if t == "PRICE_INCREASE":
            price_inc_savings += opp.potential_annual_saving
        elif t == "POTENTIALLY_UNUSED":
            unused_savings += opp.potential_annual_saving
        elif t == "CATEGORY_DUPLICATE":
            dup_savings += opp.potential_annual_saving

        current_max = commitment_max_savings.get(opp.commitment_id, Decimal("0.00"))
        if opp.potential_annual_saving > current_max:
            commitment_max_savings[opp.commitment_id] = opp.potential_annual_saving

    total_annual = sum(commitment_max_savings.values(), Decimal("0.00"))
    total_monthly = round_currency(total_annual / Decimal("12"))

    return SavingsSummaryResponse(
        currency="INR",
        total_potential_annual_savings=round_currency(total_annual),
        total_potential_monthly_savings=round_currency(total_monthly),
        price_increase_savings=round_currency(price_inc_savings),
        unused_commitment_savings=round_currency(unused_savings),
        duplicate_service_savings=round_currency(dup_savings),
        opportunities_count=len(opps),
        opportunities=opps,
    )


def calculate_what_if_projection(
    db: Session,
    user_id: uuid.UUID,
    selected_opportunity_ids: List[str],
) -> SavingsCalculateResponse:
    """Calculate interactive what-if financial projection with double-counting and non-negative safeguards."""
    cost_items = get_user_commitment_costs(db, user_id)
    confirmed_items = [item for item in cost_items if item.is_confirmed]
    baseline_annual = sum((item.annualized_cost for item in confirmed_items), Decimal("0.00"))
    cost_lookup = {item.commitment_id: item.annualized_cost for item in cost_items}

    all_opps = get_user_savings_opportunities(db, user_id)
    opp_lookup = {opp.id: opp for opp in all_opps}

    safeguards: List[str] = [
        "Baseline expenditure excludes unconfirmed/candidate commitments.",
    ]

    savings_by_commitment: Dict[uuid.UUID, Decimal] = {}
    selected_count = 0

    for opp_id in selected_opportunity_ids:
        opp = opp_lookup.get(opp_id)
        if not opp:
            continue

        selected_count += 1
        c_id = opp.commitment_id
        current_saved = savings_by_commitment.get(c_id, Decimal("0.00"))
        max_cost = cost_lookup.get(c_id, opp.current_annual_cost)

        new_saved = current_saved + opp.potential_annual_saving
        if new_saved > max_cost:
            savings_by_commitment[c_id] = max_cost
            if "Double-count protection applied: savings capped at commitment annual cost." not in safeguards:
                safeguards.append("Double-count protection applied: savings capped at commitment annual cost.")
        else:
            savings_by_commitment[c_id] = new_saved

    total_annual_savings = sum(savings_by_commitment.values(), Decimal("0.00"))
    total_monthly_savings = round_currency(total_annual_savings / Decimal("12"))

    projected_annual = baseline_annual - total_annual_savings
    if projected_annual < Decimal("0.00"):
        projected_annual = Decimal("0.00")
        safeguards.append("Non-negative safeguard applied: projected annual cost floored at ₹0.00.")

    projected_monthly = round_currency(projected_annual / Decimal("12"))

    pct_reduction = Decimal("0.00")
    if baseline_annual > Decimal("0.00"):
        pct_reduction = round_currency((total_annual_savings / baseline_annual) * Decimal("100.0"))

    return SavingsCalculateResponse(
        currency="INR",
        baseline_annual_cost=round_currency(baseline_annual),
        selected_annual_savings=round_currency(total_annual_savings),
        selected_monthly_savings=round_currency(total_monthly_savings),
        projected_annual_cost=round_currency(projected_annual),
        projected_monthly_cost=round_currency(projected_monthly),
        percentage_reduction=pct_reduction,
        selected_count=selected_count,
        safeguards_applied=safeguards,
    )

"""API endpoints for Phase 7 Savings Intelligence, What-If Calculator, and Scenario persistence."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.financial_impact import (
    SavingsCalculateRequest,
    SavingsCalculateResponse,
    SavingsOpportunityItem,
    SavingsScenarioCreateRequest,
    SavingsScenarioResponse,
    SavingsScenarioUpdateRequest,
    SavingsSummaryResponse,
    calculate_what_if_projection,
    get_user_savings_opportunities,
    get_user_savings_summary,
)
from app.db.session import get_db
from app.models.savings_scenario import SavingsScenario
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/savings", tags=["Savings Intelligence"])


def _resolve_user_id(db: Session, user_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """Resolve explicit user_id or fallback to default workspace demo user."""
    if user_id:
        return user_id
    user = UserRepository.get_or_create_demo_user(db)
    return user.id


@router.get("/opportunities", response_model=List[SavingsOpportunityItem])
def list_savings_opportunities(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[SavingsOpportunityItem]:
    """List transparent savings opportunities from price increases, verified unused commitments, and duplicates."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_savings_opportunities(db, target_user_id)


@router.get("/summary", response_model=SavingsSummaryResponse)
def get_savings_summary(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> SavingsSummaryResponse:
    """Get total potential savings and breakdown by opportunity type."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_savings_summary(db, target_user_id)


@router.post("/calculate", response_model=SavingsCalculateResponse)
def calculate_scenario(
    payload: SavingsCalculateRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> SavingsCalculateResponse:
    """Calculate interactive what-if financial projection with double-counting safeguards."""
    target_user_id = _resolve_user_id(db, user_id)
    return calculate_what_if_projection(db, target_user_id, payload.selected_opportunity_ids)


@router.post("/scenarios", response_model=SavingsScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: SavingsScenarioCreateRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> SavingsScenarioResponse:
    """Save a what-if savings scenario for user simulation."""
    target_user_id = _resolve_user_id(db, user_id)

    # Calculate metrics
    calc_res = calculate_what_if_projection(db, target_user_id, payload.selected_opportunity_ids)

    # Find associated commitment IDs
    all_opps = get_user_savings_opportunities(db, target_user_id)
    opp_map = {o.id: o for o in all_opps}
    selected_c_ids = list(
        {
            str(opp_map[oid].commitment_id)
            for oid in payload.selected_opportunity_ids
            if oid in opp_map
        }
    )

    scenario = SavingsScenario(
        user_id=target_user_id,
        name=payload.name,
        description=payload.description,
        selected_opportunity_ids=payload.selected_opportunity_ids,
        selected_commitment_ids=selected_c_ids,
        baseline_annual_cost=calc_res.baseline_annual_cost,
        projected_annual_cost=calc_res.projected_annual_cost,
        annual_savings=calc_res.selected_annual_savings,
        monthly_savings=calc_res.selected_monthly_savings,
        percentage_reduction=calc_res.percentage_reduction,
        parameters=payload.parameters or {},
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return scenario


@router.get("/scenarios", response_model=List[SavingsScenarioResponse])
def list_scenarios(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[SavingsScenarioResponse]:
    """List persisted what-if savings scenarios for the user."""
    target_user_id = _resolve_user_id(db, user_id)
    stmt = (
        select(SavingsScenario)
        .where(SavingsScenario.user_id == target_user_id)
        .order_by(SavingsScenario.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/scenarios/{scenario_id}", response_model=SavingsScenarioResponse)
def get_scenario(
    scenario_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> SavingsScenarioResponse:
    """Get details of a specific saved what-if scenario."""
    target_user_id = _resolve_user_id(db, user_id)
    stmt = select(SavingsScenario).where(
        SavingsScenario.id == scenario_id,
        SavingsScenario.user_id == target_user_id,
    )
    scenario = db.scalar(stmt)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario


@router.patch("/scenarios/{scenario_id}", response_model=SavingsScenarioResponse)
def update_scenario(
    scenario_id: uuid.UUID,
    payload: SavingsScenarioUpdateRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> SavingsScenarioResponse:
    """Update name, description, or selected opportunities in a saved scenario."""
    target_user_id = _resolve_user_id(db, user_id)
    stmt = select(SavingsScenario).where(
        SavingsScenario.id == scenario_id,
        SavingsScenario.user_id == target_user_id,
    )
    scenario = db.scalar(stmt)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    if payload.name is not None:
        scenario.name = payload.name
    if payload.description is not None:
        scenario.description = payload.description
    if payload.parameters is not None:
        scenario.parameters = payload.parameters

    if payload.selected_opportunity_ids is not None:
        scenario.selected_opportunity_ids = payload.selected_opportunity_ids
        # Recompute projection metrics
        calc_res = calculate_what_if_projection(db, target_user_id, payload.selected_opportunity_ids)
        scenario.baseline_annual_cost = calc_res.baseline_annual_cost
        scenario.projected_annual_cost = calc_res.projected_annual_cost
        scenario.annual_savings = calc_res.selected_annual_savings
        scenario.monthly_savings = calc_res.selected_monthly_savings
        scenario.percentage_reduction = calc_res.percentage_reduction

        all_opps = get_user_savings_opportunities(db, target_user_id)
        opp_map = {o.id: o for o in all_opps}
        scenario.selected_commitment_ids = list(
            {
                str(opp_map[oid].commitment_id)
                for oid in payload.selected_opportunity_ids
                if oid in opp_map
            }
        )

    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a saved what-if scenario."""
    target_user_id = _resolve_user_id(db, user_id)
    stmt = select(SavingsScenario).where(
        SavingsScenario.id == scenario_id,
        SavingsScenario.user_id == target_user_id,
    )
    scenario = db.scalar(stmt)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")

    db.delete(scenario)
    db.commit()
    return None


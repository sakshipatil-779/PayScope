"""Instruction builder formatting cancellation steps and progress checklists."""
from typing import List
from app.analytics.cancellations.schemas import CancellationStep, Playbook


def build_cancellation_checklist(
    playbook: Playbook,
    completed_step_ids: List[str],
) -> List[CancellationStep]:
    """Decorates playbook steps with real-time completion state for user tracking."""
    completed_set = set(completed_step_ids or [])
    checklist: List[CancellationStep] = []

    for step in playbook.steps:
        checklist.append(
            CancellationStep(
                id=step.id,
                step_number=step.step_number,
                title=step.title,
                instruction=step.instruction,
                action_type=step.action_type,
                warning=step.warning,
                verification_tip=step.verification_tip,
                is_completed=step.id in completed_set,
            )
        )
    return checklist


def calculate_progress_percentage(
    total_steps: int,
    completed_steps_count: int,
) -> int:
    """Calculates integer percentage of completion."""
    if total_steps <= 0:
        return 0
    return min(100, int((completed_steps_count / total_steps) * 100))

"""CarePlan API Endpoints.

Implements M1B.5 CarePlan basics:
- GET /v1/careplan/tasks: list user's wellness tasks and completion history
- POST /v1/careplan/tasks: create a new wellness task (validates zero medication)
- PUT /v1/careplan/tasks/{id}: update task title, category, frequency, reminder, or toggle completion
- DELETE /v1/careplan/tasks/{id}: delete a task

Adheres strictly to:
- CARE-01, CARE-02: Self-directed general wellness tasks (water, food, exercise, sleep).
  Zero medication or supplement reminders (C-08, C-22).
- CARE-03: Completion toggle and history.
- CARE-04: In-app reminder disclosure notice.
- PROF-02: Authenticated ownership enforcement; User A cannot access User B's tasks (403).
- AUTH-05: Cascading delete on account deletion.
"""

from datetime import datetime
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.models.user import CarePlanItem
from app.schemas.careplan import (
    CarePlanDeleteResponse,
    CarePlanItemCreate,
    CarePlanItemResponse,
    CarePlanItemUpdate,
    CarePlanListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/careplan/tasks", response_model=CarePlanListResponse)
def list_care_plan_tasks(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all wellness tasks created by the authenticated user."""
    try:
        tasks = (
            db.query(CarePlanItem)
            .filter(CarePlanItem.user_id == current_user.uid)
            .order_by(CarePlanItem.created_at.desc())
            .all()
        )
    except Exception as exc:
        logger.error("Database error listing care plan tasks: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    items = [
        CarePlanItemResponse(
            id=t.id,
            title=t.title,
            category=t.category,
            target_frequency=t.target_frequency,
            reminder_time=t.reminder_time,
            is_completed=t.is_completed,
            completed_at=t.completed_at,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]

    completed_count = sum(1 for t in items if t.is_completed)

    return CarePlanListResponse(
        tasks=items,
        total_count=len(items),
        completed_count=completed_count,
    )


@router.post(
    "/careplan/tasks",
    response_model=CarePlanItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_care_plan_task(
    payload: CarePlanItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a user-defined general wellness task.

    Rejects any task containing medication, supplement, or prescription terms (C-08, C-22).
    """
    task_id = f"task_{uuid.uuid4().hex[:16]}"
    task = CarePlanItem(
        id=task_id,
        user_id=current_user.uid,
        title=payload.title,
        category=payload.category,
        target_frequency=payload.target_frequency,
        reminder_time=payload.reminder_time,
        is_completed=False,
        completed_at=None,
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception as exc:
        db.rollback()
        logger.error("Database error creating care plan task: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to save wellness task.",
        )

    return CarePlanItemResponse(
        id=task.id,
        title=task.title,
        category=task.category,
        target_frequency=task.target_frequency,
        reminder_time=task.reminder_time,
        is_completed=task.is_completed,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.put("/careplan/tasks/{task_id}", response_model=CarePlanItemResponse)
def update_care_plan_task(
    task_id: str,
    payload: CarePlanItemUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates task attributes or toggles completion state.

    Enforces ownership (403 Forbidden if task belongs to another user).
    """
    try:
        task = db.query(CarePlanItem).filter(CarePlanItem.id == task_id).first()
    except Exception as exc:
        logger.error("Database error retrieving task for update: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    if task.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this task.",
        )

    if payload.title is not None:
        task.title = payload.title
    if payload.category is not None:
        task.category = payload.category
    if payload.target_frequency is not None:
        task.target_frequency = payload.target_frequency
    if payload.reminder_time is not None:
        task.reminder_time = payload.reminder_time
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed
        if payload.is_completed:
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None

    try:
        db.commit()
        db.refresh(task)
    except Exception as exc:
        db.rollback()
        logger.error("Database error updating task: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to update task.",
        )

    return CarePlanItemResponse(
        id=task.id,
        title=task.title,
        category=task.category,
        target_frequency=task.target_frequency,
        reminder_time=task.reminder_time,
        is_completed=task.is_completed,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/careplan/tasks/{task_id}", response_model=CarePlanDeleteResponse)
def delete_care_plan_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a wellness task.

    Enforces ownership (403 Forbidden if task belongs to another user).
    """
    try:
        task = db.query(CarePlanItem).filter(CarePlanItem.id == task_id).first()
    except Exception as exc:
        logger.error("Database error retrieving task for deletion: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    if task.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this task.",
        )

    try:
        db.delete(task)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Database error deleting task: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to delete task.",
        )

    return CarePlanDeleteResponse(
        status="deleted",
        id=task_id,
        message="Wellness task deleted successfully.",
    )

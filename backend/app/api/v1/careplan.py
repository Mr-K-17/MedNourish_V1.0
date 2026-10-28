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
import hashlib
import json
import logging
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.models.user import (
    CarePlanItem,
    CarePlanMealLog,
    CarePlanMealPlan,
    CarePlanPrefs,
    SavedSummary,
)
from app.schemas.careplan import (
    CarePlanDeleteResponse,
    CarePlanItemCreate,
    CarePlanItemResponse,
    CarePlanItemUpdate,
    CarePlanListResponse,
    MealLogRequest,
    MealNutrientsResponse,
    MealPlanPreferencesRequest,
    MealPlanPreferencesResponse,
)
from app.services.meal_plan_service import (
    generate_deterministic_meal_plan,
    get_day_nutrients,
    get_nutrition_guidance_cards,
    get_user_conditions,
    get_user_preferences,
    save_user_preferences,
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
            is_auto=bool(getattr(t, "is_auto", False)),
            nutrient=getattr(t, "nutrient", None),
            is_stale=bool(getattr(t, "is_stale", False)),
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


# ============================================================================
# Phase 5 / C-39 Deterministic Meal Planning Endpoints
# ============================================================================

@router.get("/careplan/meal-plan")
def get_meal_plan(
    day: Optional[int] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the user's active 7-day meal plan and meal logs."""
    plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )
    if not plan:
        # Check if user has latest SavedSummary
        latest_summary = (
            db.query(SavedSummary)
            .filter(SavedSummary.user_id == current_user.uid)
            .order_by(SavedSummary.created_at.desc())
            .first()
        )
        focus_list = []
        source_id = "initial"
        if latest_summary and latest_summary.snapshot_scores_json:
            source_id = latest_summary.id
            try:
                scores = json.loads(latest_summary.snapshot_scores_json)
                focus_list = [
                    {"nutrient": k, "final_pct": v.get("final_pct", 0)}
                    for k, v in scores.items()
                    if v.get("final_pct", 0) >= 30.0
                ]
            except Exception:
                pass

        prefs = get_user_preferences(db, current_user.uid)
        conds = get_user_conditions(db, current_user.uid)
        plan_dict = generate_deterministic_meal_plan(
            user_id=current_user.uid,
            focus_nutrients=focus_list,
            user_conditions=conds,
            preferences=prefs,
        )
        plan_id = f"plan_{hashlib.sha256(f'{current_user.uid}_{source_id}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
        plan = CarePlanMealPlan(
            id=plan_id,
            user_id=current_user.uid,
            source_entry_id=source_id,
            created_at=datetime.utcnow(),
            status="active",
            focus_json=json.dumps(plan_dict["focus_nutrients"]),
            prefs_json=json.dumps(plan_dict["preferences"]),
            plan_json=json.dumps(plan_dict),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

    plan_data = json.loads(plan.plan_json)
    plan_data["plan_id"] = plan.id
    plan_data["created_at"] = plan.created_at.isoformat()
    plan_data["status"] = plan.status

    # Attach meal logs for this plan
    logs = (
        db.query(CarePlanMealLog)
        .filter(CarePlanMealLog.user_id == current_user.uid, CarePlanMealLog.plan_id == plan.id)
        .all()
    )
    plan_data["logs"] = [
        {
            "id": log.id,
            "plan_date": log.plan_date,
            "slot": log.slot,
            "option_index": log.option_index,
            "done": log.done,
            "done_at": log.done_at.isoformat() if log.done_at else None,
        }
        for log in logs
    ]

    if day is not None and 0 <= day < len(plan_data.get("days", [])):
        return {
            "plan_id": plan.id,
            "day": plan_data["days"][day],
            "preferences": plan_data.get("preferences"),
            "focus_nutrients": plan_data.get("focus_nutrients"),
            "doctor_note": plan_data.get("doctor_note"),
            "logs": plan_data["logs"],
        }

    return plan_data


@router.post("/careplan/meal-plan/generate")
def force_generate_meal_plan(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Force regenerates active meal plan from latest reports and preferences."""
    old_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )
    if old_plan:
        old_plan.status = "stale"
        db.add(old_plan)

    latest_summary = (
        db.query(SavedSummary)
        .filter(SavedSummary.user_id == current_user.uid)
        .order_by(SavedSummary.created_at.desc())
        .first()
    )
    focus_list = []
    source_id = "manual_regen"
    if latest_summary and latest_summary.snapshot_scores_json:
        source_id = latest_summary.id
        try:
            scores = json.loads(latest_summary.snapshot_scores_json)
            focus_list = [
                {"nutrient": k, "final_pct": v.get("final_pct", 0)}
                for k, v in scores.items()
                if v.get("final_pct", 0) >= 30.0
            ]
        except Exception:
            pass

    prefs = get_user_preferences(db, current_user.uid)
    conds = get_user_conditions(db, current_user.uid)
    plan_dict = generate_deterministic_meal_plan(
        user_id=current_user.uid,
        focus_nutrients=focus_list,
        user_conditions=conds,
        preferences=prefs,
    )
    plan_id = f"plan_{hashlib.sha256(f'{current_user.uid}_{source_id}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
    plan = CarePlanMealPlan(
        id=plan_id,
        user_id=current_user.uid,
        source_entry_id=source_id,
        created_at=datetime.utcnow(),
        status="active",
        focus_json=json.dumps(plan_dict["focus_nutrients"]),
        prefs_json=json.dumps(plan_dict["preferences"]),
        plan_json=json.dumps(plan_dict),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    plan_data = json.loads(plan.plan_json)
    plan_data["plan_id"] = plan.id
    plan_data["logs"] = []
    return plan_data


@router.get("/careplan/meal-plan/preferences", response_model=MealPlanPreferencesResponse)
def get_meal_plan_preferences_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves user meal planning preferences."""
    prefs = get_user_preferences(db, current_user.uid)
    return MealPlanPreferencesResponse(**prefs)


@router.put("/careplan/meal-plan/preferences", response_model=MealPlanPreferencesResponse)
def update_meal_plan_preferences_endpoint(
    payload: MealPlanPreferencesRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates user meal planning preferences and refreshes active plan."""
    updated = save_user_preferences(
        db, current_user.uid, payload.diet_pref, payload.cuisine, payload.meal_times
    )
    active_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )
    if active_plan:
        conds = get_user_conditions(db, current_user.uid)
        focus = json.loads(active_plan.focus_json)
        new_plan_dict = generate_deterministic_meal_plan(
            user_id=current_user.uid,
            focus_nutrients=focus,
            user_conditions=conds,
            preferences=updated,
        )
        active_plan.prefs_json = json.dumps(updated)
        active_plan.plan_json = json.dumps(new_plan_dict)
        db.add(active_plan)
        db.commit()

    return MealPlanPreferencesResponse(**updated)


@router.post("/careplan/meal-plan/log")
def log_meal_option(
    payload: MealLogRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggles or sets the completion status for a specific meal option."""
    log_item = (
        db.query(CarePlanMealLog)
        .filter(
            CarePlanMealLog.user_id == current_user.uid,
            CarePlanMealLog.plan_id == payload.plan_id,
            CarePlanMealLog.plan_date == payload.plan_date,
            CarePlanMealLog.slot == payload.slot,
        )
        .first()
    )
    if not log_item:
        log_item = CarePlanMealLog(
            id=f"log_{uuid.uuid4().hex[:16]}",
            user_id=current_user.uid,
            plan_id=payload.plan_id,
            plan_date=payload.plan_date,
            slot=payload.slot,
            option_index=payload.option_index,
            done=payload.done,
            done_at=datetime.utcnow() if payload.done else None,
        )
        db.add(log_item)
    else:
        log_item.option_index = payload.option_index
        log_item.done = payload.done
        log_item.done_at = datetime.utcnow() if payload.done else None
        db.add(log_item)
    db.commit()
    db.refresh(log_item)
    return {
        "status": "success",
        "id": log_item.id,
        "slot": log_item.slot,
        "option_index": log_item.option_index,
        "done": log_item.done,
    }


@router.get("/careplan/meal-plan/nutrients", response_model=MealNutrientsResponse)
def get_meal_nutrients_status(
    date: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns covered and pending nutrients for that date computed from ticked options."""
    active_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )
    if not active_plan:
        return MealNutrientsResponse(date=date, covered=[], pending=["Dietary Fiber"], progress_pct=0.0)

    nutrients_data = get_day_nutrients(db, current_user.uid, active_plan.id, date)
    return MealNutrientsResponse(**nutrients_data)


@router.get("/careplan/nutrition-guidance")
def get_nutrition_guidance(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns curated focus nutrient guidance cards."""
    active_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )
    focus = []
    if active_plan:
        try:
            focus = json.loads(active_plan.focus_json)
        except Exception:
            pass

    guidance_cards = get_nutrition_guidance_cards(focus)
    return {
        "focus_nutrients": focus,
        "cards": guidance_cards,
        "disclaimer": "General food ideas, not a prescribed diet.",
    }


@router.get("/careplan/export/ics")
@router.get("/careplan/meal-plan/ics")
def export_careplan_ics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports active CarePlan tasks and chosen meals as an iCalendar (.ics) feed."""
    tasks = (
        db.query(CarePlanItem)
        .filter(CarePlanItem.user_id == current_user.uid)
        .all()
    )
    active_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == current_user.uid, CarePlanMealPlan.status == "active")
        .first()
    )

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedNourish//CarePlan MealPlanner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    today_str = datetime.utcnow().strftime("%Y%m%d")

    for t in tasks:
        time_part = t.reminder_time.replace(":", "") + "00" if t.reminder_time else "080000"
        dt_start = f"{today_str}T{time_part}Z"
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:task-{t.id}@mednourish.local",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{dt_start}",
            f"SUMMARY:Wellness: {t.title}",
            "DESCRIPTION:General wellness routine via MedNourish.",
            "RRULE:FREQ=DAILY",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    if active_plan:
        try:
            plan_data = json.loads(active_plan.plan_json)
            logs = {
                (l.plan_date, l.slot): l.option_index
                for l in db.query(CarePlanMealLog)
                .filter(CarePlanMealLog.user_id == current_user.uid, CarePlanMealLog.plan_id == active_plan.id)
                .all()
            }
            prefs = json.loads(active_plan.prefs_json) if active_plan.prefs_json else {}
            meal_times = prefs.get("meal_times", {"breakfast": "08:00", "lunch": "12:30", "dinner": "19:30"})

            for day in plan_data.get("days", []):
                day_date_str = day.get("date", "").replace("-", "")
                if not day_date_str:
                    continue
                meals = day.get("meals", {})
                for slot in ("breakfast", "lunch", "dinner"):
                    slot_data = meals.get(slot, {})
                    options = slot_data.get("options", [])
                    if not options:
                        continue
                    chosen_idx = logs.get((day.get("date"), slot), 0)
                    chosen_opt = options[chosen_idx] if chosen_idx < len(options) else options[0]
                    t_str = meal_times.get(slot, "12:00").replace(":", "") + "00"
                    dt_start = f"{day_date_str}T{t_str}Z"
                    ics_lines.extend([
                        "BEGIN:VEVENT",
                        f"UID:meal-{day_date_str}-{slot}@mednourish.local",
                        f"DTSTAMP:{now_stamp}",
                        f"DTSTART:{dt_start}",
                        f"SUMMARY:MedNourish Meal: {chosen_opt.get('name', slot.capitalize())}",
                        f"DESCRIPTION:{chosen_opt.get('prep_note', 'Planned meal')}",
                        "STATUS:CONFIRMED",
                        "END:VEVENT",
                    ])
        except Exception:
            pass

    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines) + "\r\n"
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=mednourish_careplan.ics"},
    )



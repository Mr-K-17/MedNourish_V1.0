"""Milestone M1B.7: End-to-End User Journey and Hardening Tests.

Verifies the 8 core user journeys across MedNourish:
Journey 1: Account registration, adult confirmation gate, and profile retrieval.
Journey 2: Symptom Explorer matching, inspection of evidence tags, and disclaimer integrity.
Journey 3: Saving Explorer reference match summary to Reports.
Journey 4: MedBot guided questionnaire (Simple/Standard), evaluation, and assessment saving.
Journey 5: CarePlan wellness task creation, completion toggle, and reminder banner integrity.
Journey 6: NurseBot scripted help topic navigation, breadcrumbs, and emergency guidance.
Journey 7: Cross-user data isolation and rejection of unauthorized data access across all modules.
Journey 8: Complete account deletion cascading to profile, consent log, saved summaries, and care plan items.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.models.user import CarePlanItem, SavedSummary, UserConsentLog, UserProfile
from tests.conftest import TestingSessionLocal


@pytest.mark.anyio
async def test_complete_end_to_end_user_lifecycle_journey():
    """Executes a full multi-step user lifecycle test from registration to cascade deletion."""
    primary_uid = "journey_user_main"
    primary_email = "primary@mednourish.local"
    primary_user = AuthenticatedUser(uid=primary_uid, email=primary_email)

    app.dependency_overrides[get_current_user] = lambda: primary_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------------------------------------------------------
        # Journey 1: Registration and Adult Confirmation
        # ---------------------------------------------------------
        # Unconfirmed profile must be rejected
        res_reject = await client.post(
            "/v1/profile",
            json={
                "display_name": "Test User",
                "is_adult_confirmed": False,
                "terms_consent_version": "v1.0",
            },
        )
        assert res_reject.status_code == 422

        # Valid adult confirmation creates profile and records immutable consent
        res_create = await client.post(
            "/v1/profile",
            json={
                "display_name": "Verified Adult",
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "gender": "prefer_not_to_say",
                "height_cm": 175.0,
                "weight_kg": 70.0,
            },
        )
        assert res_create.status_code == 201
        profile_data = res_create.json()
        assert profile_data["id"] == primary_uid
        assert profile_data["display_name"] == "Verified Adult"
        assert profile_data["is_adult_confirmed"] is True
        # Verify no age/dob fields exposed
        assert "date_of_birth" not in profile_data
        assert "age" not in profile_data

        # Verify profile retrieval
        res_get_profile = await client.get("/v1/profile")
        assert res_get_profile.status_code == 200
        assert res_get_profile.json()["display_name"] == "Verified Adult"

        # ---------------------------------------------------------
        # Journey 2: Symptom Explorer Matching
        # ---------------------------------------------------------
        res_match = await client.post(
            "/v1/explorer/match",
            json={"body_region": "EYES", "selected_tags": ["nightblindness", "eyedryness"]},
        )
        assert res_match.status_code == 200
        match_data = res_match.json()
        assert "disclaimer" in match_data
        assert "matched_entries" in match_data
        assert len(match_data["matched_entries"]) >= 1

        top_match = match_data["matched_entries"][0]
        assert "class_label" in top_match
        assert "vitamin_deficiency_association" in top_match
        assert top_match["review_status"] == "unreviewed draft"

        # Prohibited diagnostic claims check
        match_text = str(match_data).lower()
        assert "you have" not in match_text
        assert "risk score" not in match_text
        assert "probability" not in match_text

        # ---------------------------------------------------------
        # Journey 3: Saving Explorer Reference Match Summary
        # ---------------------------------------------------------
        explorer_summary_payload = {
            "session_type": "Explorer",
            "body_region_filter": "EYES",
            "selected_tags": ["nightblindness", "eyedryness"],
            "matched_entries": match_data["matched_entries"],
            "package_version": match_data["package_version"],
            "matcher_version": match_data["matcher_version"],
        }
        res_save_explorer = await client.post(
            "/v1/reports/summaries",
            json=explorer_summary_payload,
        )
        assert res_save_explorer.status_code == 201
        explorer_summary = res_save_explorer.json()
        explorer_summary_id = explorer_summary["id"]
        assert explorer_summary["session_type"] == "Explorer"
        assert explorer_summary["id"].startswith("sum_")

        # ---------------------------------------------------------
        # Journey 4: MedBot Guided Questionnaire & Assessment
        # ---------------------------------------------------------
        # Get question config
        res_questions_simple = await client.get("/v1/medbot/questions?mode=simple")
        assert res_questions_simple.status_code == 200
        q_simple = res_questions_simple.json()
        assert len(q_simple["questions"]) > 0

        res_questions_std = await client.get("/v1/medbot/questions?mode=standard")
        assert res_questions_std.status_code == 200
        q_std = res_questions_std.json()
        assert len(q_std["questions"]) > 0

        # Evaluate answers in Simple mode
        eval_payload = {
            "mode": "simple",
            "answers": [
                {
                    "question_id": "q_eyes",
                    "selected_option_ids": ["opt_eyes_yes"],
                    "skipped": False,
                },
                {
                    "question_id": "q_general_energy",
                    "selected_option_ids": ["opt_gen_yes"],
                    "skipped": False,
                },
            ],
        }
        res_eval = await client.post("/v1/medbot/evaluate", json=eval_payload)
        assert res_eval.status_code == 200
        medbot_eval = res_eval.json()
        assert len(medbot_eval["matched_entries"]) >= 1
        assert "disclaimer" in medbot_eval

        # Save MedBot Assessment
        medbot_save_payload = {
            "session_type": "MedBot",
            "body_region_filter": None,
            "selected_tags": medbot_eval["collected_symptom_tags"],
            "matched_entries": medbot_eval["matched_entries"],
            "package_version": medbot_eval["package_version"],
            "matcher_version": medbot_eval["matcher_version"],
        }
        res_save_medbot = await client.post("/v1/medbot/save", json=medbot_save_payload)
        assert res_save_medbot.status_code == 201
        medbot_summary = res_save_medbot.json()
        medbot_summary_id = medbot_summary["id"]
        assert medbot_summary["session_type"] == "MedBot"

        # Check reports listing contains both Explorer and MedBot summaries
        res_summaries = await client.get("/v1/reports/summaries")
        assert res_summaries.status_code == 200
        user_summaries = res_summaries.json()
        assert user_summaries["total_count"] >= 2
        summary_ids = [s["id"] for s in user_summaries["summaries"]]
        assert explorer_summary_id in summary_ids
        assert medbot_summary_id in summary_ids

        # ---------------------------------------------------------
        # Journey 5: CarePlan Wellness Tasks Lifecycle
        # ---------------------------------------------------------
        # Create wellness task
        res_task = await client.post(
            "/v1/careplan/tasks",
            json={
                "title": "Drink 8 glasses of fresh water daily",
                "category": "water",
                "notes": "Carry a refillable water flask",
            },
        )
        assert res_task.status_code == 201
        task_data = res_task.json()
        task_id = task_data["id"]
        assert task_data["is_completed"] is False

        # Rejection of medication or supplement terms in task creation
        res_bad_task = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Take 500mg Vitamin C supplement daily", "category": "general"},
        )
        assert res_bad_task.status_code == 422

        # Toggle task completion
        res_toggle = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"is_completed": True},
        )
        assert res_toggle.status_code == 200
        assert res_toggle.json()["is_completed"] is True
        assert res_toggle.json()["completed_at"] is not None

        # Verify listing contains reminder notice
        res_list_tasks = await client.get("/v1/careplan/tasks")
        assert res_list_tasks.status_code == 200
        tasks_resp = res_list_tasks.json()
        assert len(tasks_resp["tasks"]) >= 1
        assert "reminder_notice" in tasks_resp
        assert "reminders only alert while this app is open" in tasks_resp["reminder_notice"].lower()
        assert "disclaimer" in tasks_resp

        # ---------------------------------------------------------
        # Journey 6: NurseBot Scripted Help & Emergency Guidance
        # ---------------------------------------------------------
        res_menu = await client.get("/v1/nursebot/menu")
        assert res_menu.status_code == 200
        menu = res_menu.json()
        assert len(menu["topics"]) >= 5
        assert "categories" in menu
        assert "app_usage" in menu["categories"]

        # Emergency topic response check
        res_emerg = await client.get("/v1/nursebot/topics/refusal_emergency_urgent")
        assert res_emerg.status_code == 200
        emerg_data = res_emerg.json()
        assert emerg_data["is_safety_refusal"] is True
        assert "local emergency services" in emerg_data["content"].lower()
        # Ensure no hardcoded foreign numbers per SAF-04
        assert "911" not in emerg_data["content"]
        assert "112" not in emerg_data["content"]
        assert "999" not in emerg_data["content"]

        # ---------------------------------------------------------
        # Journey 7: Cross-User Data Isolation
        # ---------------------------------------------------------
        other_user = AuthenticatedUser(uid="journey_user_secondary", email="other@mednourish.local")
        app.dependency_overrides[get_current_user] = lambda: other_user

        # Other user cannot see primary user's summaries
        res_other_summaries = await client.get("/v1/reports/summaries")
        assert res_other_summaries.status_code == 200
        assert res_other_summaries.json()["total_count"] == 0
        assert res_other_summaries.json()["summaries"] == []

        # Other user cannot read primary user's summary directly
        res_other_get = await client.get(f"/v1/reports/summaries/{explorer_summary_id}")
        assert res_other_get.status_code in (403, 404)

        # Other user cannot delete primary user's summary
        res_other_del = await client.delete(f"/v1/reports/summaries/{explorer_summary_id}")
        assert res_other_del.status_code in (403, 404)

        # Other user cannot read primary user's care plan tasks
        res_other_tasks = await client.get("/v1/careplan/tasks")
        assert res_other_tasks.status_code == 200
        assert res_other_tasks.json()["tasks"] == []

        # Other user cannot modify primary user's care plan task
        res_other_put = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"is_completed": False},
        )
        assert res_other_put.status_code in (403, 404)

        # ---------------------------------------------------------
        # Journey 8: Account Deletion Cascading Purge
        # ---------------------------------------------------------
        # Switch back to primary user
        app.dependency_overrides[get_current_user] = lambda: primary_user

        # Delete account
        res_del_account = await client.delete("/v1/profile")
        assert res_del_account.status_code == 200
        assert res_del_account.json()["status"] == "deleted"

        # Verify database has purged all associated records for primary user
        db = TestingSessionLocal()
        assert db.query(UserProfile).filter(UserProfile.id == primary_uid).first() is None
        assert db.query(UserConsentLog).filter(UserConsentLog.user_id == primary_uid).count() == 0
        assert db.query(SavedSummary).filter(SavedSummary.user_id == primary_uid).count() == 0
        assert db.query(CarePlanItem).filter(CarePlanItem.user_id == primary_uid).count() == 0
        db.close()

        # Subsequent profile retrieval yields 404
        res_post_del = await client.get("/v1/profile")
        assert res_post_del.status_code == 404

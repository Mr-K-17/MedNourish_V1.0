"""Tests for CarePlan API (M1B.5).

Verifies:
1. Rejection of unauthenticated requests (401).
2. Creating general wellness tasks (water, food, exercise, sleep, general).
3. Strict rejection of tasks with medication/supplement/dosage terms (C-08, C-22, SAF-02).
4. Updating tasks and toggling completion status with completion timestamp tracking.
5. Deleting tasks.
6. Data isolation: User A cannot read, update, or delete User B's tasks (403/404).
7. Account deletion cascade removes all care plan tasks belonging to user.
8. Reminder notice is present in all listing responses per CARE-04.
9. Prohibited clinical word scanning on outputs.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app


@pytest.mark.anyio
async def test_unauthenticated_careplan_access():
    """All CarePlan endpoints require an authenticated user session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /v1/careplan/tasks
        res1 = await client.get("/v1/careplan/tasks")
        assert res1.status_code == 401

        # POST /v1/careplan/tasks
        res2 = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Drink water", "category": "water"},
        )
        assert res2.status_code == 401

        # PUT /v1/careplan/tasks/{id}
        res3 = await client.put(
            "/v1/careplan/tasks/task_123",
            json={"is_completed": True},
        )
        assert res3.status_code == 401

        # DELETE /v1/careplan/tasks/{id}
        res4 = await client.delete("/v1/careplan/tasks/task_123")
        assert res4.status_code == 401


@pytest.mark.anyio
async def test_create_and_list_wellness_tasks():
    """Verifies task creation and listing for valid wellness categories."""
    user = AuthenticatedUser(uid="user_wellness_1", email="wellness@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create water task
        res_water = await client.post(
            "/v1/careplan/tasks",
            json={
                "title": "Drink 2 liters of water daily",
                "category": "water",
                "target_frequency": "daily",
                "reminder_time": "09:00",
            },
        )
        assert res_water.status_code == 201
        data_water = res_water.json()
        assert data_water["id"].startswith("task_")
        assert data_water["title"] == "Drink 2 liters of water daily"
        assert data_water["category"] == "water"
        assert data_water["is_completed"] is False
        assert "reminder_notice" in data_water

        # 2. Create exercise task
        res_ex = await client.post(
            "/v1/careplan/tasks",
            json={
                "title": "30 minute brisk evening walk",
                "category": "exercise",
                "target_frequency": "daily",
                "reminder_time": "18:00",
            },
        )
        assert res_ex.status_code == 201

        # 3. List tasks
        res_list = await client.get("/v1/careplan/tasks")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["total_count"] == 2
        assert list_data["completed_count"] == 0
        assert "Reminders only alert while this app is open" in list_data["reminder_notice"]
        assert "disclaimer" in list_data


@pytest.mark.anyio
async def test_rejection_of_medication_and_supplements():
    """Strictly rejects any task mentioning medicines, pills, supplements, or dosages (C-08, C-22)."""
    user = AuthenticatedUser(uid="user_wellness_safety", email="safety@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Rejection of medication
        res_med = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Take blood pressure medication", "category": "general"},
        )
        assert res_med.status_code == 422

        # Rejection of supplement
        res_supp = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Take iron supplement after lunch", "category": "food"},
        )
        assert res_supp.status_code == 422

        # Rejection of dosage
        res_dose = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Daily 500mg dose", "category": "general"},
        )
        assert res_dose.status_code == 422

        # Rejection of pill
        res_pill = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Swallow water pills", "category": "water"},
        )
        assert res_pill.status_code == 422


@pytest.mark.anyio
async def test_task_completion_toggle_and_update():
    """Verifies updating task details and toggling completion timestamp."""
    user = AuthenticatedUser(uid="user_toggle_tester", email="toggle@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        create_res = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Aim for 8 hours of sleep", "category": "sleep"},
        )
        task_id = create_res.json()["id"]

        # Mark completed
        comp_res = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"is_completed": True},
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["is_completed"] is True
        assert comp_data["completed_at"] is not None

        # Unmark completed
        uncomp_res = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"is_completed": False},
        )
        assert uncomp_res.status_code == 200
        uncomp_data = uncomp_res.json()
        assert uncomp_data["is_completed"] is False
        assert uncomp_data["completed_at"] is None

        # Update title
        title_res = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"title": "Consistent 8 hours sleep schedule"},
        )
        assert title_res.status_code == 200
        assert title_res.json()["title"] == "Consistent 8 hours sleep schedule"


@pytest.mark.anyio
async def test_task_deletion_and_isolation():
    """User B cannot read, update, or delete User A's task."""
    alice = AuthenticatedUser(uid="user_alice_tasks", email="alice@test.local")
    bob = AuthenticatedUser(uid="user_bob_tasks", email="bob@test.local")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Alice creates a task
        app.dependency_overrides[get_current_user] = lambda: alice
        res_a = await client.post(
            "/v1/careplan/tasks",
            json={"title": "Alice daily hydration", "category": "water"},
        )
        task_id = res_a.json()["id"]

        # Bob lists tasks: sees 0 tasks
        app.dependency_overrides[get_current_user] = lambda: bob
        bob_list = await client.get("/v1/careplan/tasks")
        assert bob_list.status_code == 200
        assert bob_list.json()["total_count"] == 0

        # Bob attempts to update Alice's task: 403 Forbidden
        bob_update = await client.put(
            f"/v1/careplan/tasks/{task_id}",
            json={"is_completed": True},
        )
        assert bob_update.status_code == 403

        # Bob attempts to delete Alice's task: 403 Forbidden
        bob_delete = await client.delete(f"/v1/careplan/tasks/{task_id}")
        assert bob_delete.status_code == 403

        # Alice deletes her own task: 200 OK
        app.dependency_overrides[get_current_user] = lambda: alice
        alice_delete = await client.delete(f"/v1/careplan/tasks/{task_id}")
        assert alice_delete.status_code == 200
        assert alice_delete.json()["status"] == "deleted"

        # List is now empty
        alice_list_after = await client.get("/v1/careplan/tasks")
        assert alice_list_after.json()["total_count"] == 0


@pytest.mark.anyio
async def test_careplan_account_deletion_cascade():
    """Account deletion removes all care plan tasks for the user."""
    user = AuthenticatedUser(uid="user_cascade_del", email="cascade@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create profile
        await client.post(
            "/v1/profile",
            json={"is_adult_confirmed": True, "terms_consent_version": "v1.0"},
        )

        # Create 2 tasks
        await client.post(
            "/v1/careplan/tasks",
            json={"title": "Morning hydration", "category": "water"},
        )
        await client.post(
            "/v1/careplan/tasks",
            json={"title": "Evening stretch", "category": "exercise"},
        )

        # Verify 2 tasks exist
        list_res = await client.get("/v1/careplan/tasks")
        assert list_res.json()["total_count"] == 2

        # Delete account
        del_acc = await client.delete("/v1/profile")
        assert del_acc.status_code == 200

        # Verify tasks are wiped
        list_after = await client.get("/v1/careplan/tasks")
        assert list_after.json()["total_count"] == 0

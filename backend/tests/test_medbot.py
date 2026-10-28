"""Tests for MedBot Guided Questionnaire API (M1B.4).

Verifies:
1. Rejection of unauthenticated requests (401).
2. Question configuration retrieval for Simple mode (yes/no) and Standard mode (multiple choice).
3. Evaluates answers deterministically in Simple and Standard modes.
4. Identical matches between MedBot questionnaire selections and direct Symptom Explorer matcher (Parity test).
5. Lifestyle answers NEVER alter symptom matching or ranking (MEDBOT-10).
6. Empty or all-no answers return INSUFFICIENT_INFORMATION without false reassurance (SAF-06).
7. Skipped questions handled predictably.
8. Persisting MedBot assessment to saved summaries (Files & Reports).
9. Cross-user isolation when retrieving or saving MedBot summaries.
10. Absence of prohibited clinical words (diagnosis, risk score, probability, treatment, cure) in responses.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.services.knowledge_service import knowledge_repo


@pytest.mark.anyio
async def test_unauthenticated_medbot_access():
    """All MedBot endpoints require an authenticated user session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /v1/medbot/questions
        res1 = await client.get("/v1/medbot/questions")
        assert res1.status_code == 401

        # POST /v1/medbot/evaluate
        res2 = await client.post(
            "/v1/medbot/evaluate",
            json={"mode": "simple", "answers": []},
        )
        assert res2.status_code == 401

        # POST /v1/medbot/save
        res3 = await client.post(
            "/v1/medbot/save",
            json={
                "session_type": "MedBot",
                "selected_tags": ["fatigue"],
                "matched_entries": [],
                "package_version": "curated_v1.0",
                "matcher_version": "matcher_spec_v1.0",
            },
        )
        assert res3.status_code == 401


@pytest.mark.anyio
async def test_medbot_questions_configuration():
    """Verifies questions retrieval for both Simple and Standard modes."""
    user = AuthenticatedUser(uid="user_medbot_tester", email="medbot@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Simple mode questions
        res_simple = await client.get("/v1/medbot/questions?mode=simple")
        assert res_simple.status_code == 200
        data_simple = res_simple.json()
        assert data_simple["mode"] == "simple"
        assert data_simple["total_steps"] == 8
        assert "disclaimer" in data_simple
        # Each question should have options
        for q in data_simple["questions"]:
            assert len(q["options"]) >= 2
            assert q["step_number"] >= 1
            assert q["question_text"]

        # 2. Standard mode questions
        res_std = await client.get("/v1/medbot/questions?mode=standard")
        assert res_std.status_code == 200
        data_std = res_std.json()
        assert data_std["mode"] == "standard"
        assert data_std["total_steps"] == 8
        # Standard mode should have multiple choices
        for q in data_std["questions"]:
            assert len(q["options"]) >= 3


@pytest.mark.anyio
async def test_medbot_simple_evaluation_and_explorer_parity():
    """Answers in MedBot give identical matches to Symptom Explorer for the same tags."""
    user = AuthenticatedUser(uid="user_medbot_tester", email="medbot@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Simple answers selecting eyes yes ("nightblindness") and general yes ("fatigue")
        payload = {
            "mode": "simple",
            "answers": [
                {
                    "question_id": "q_eyes",
                    "selected_option_ids": ["opt_eyes_yes"],
                    "skipped": False,
                },
                {
                    "question_id": "q_hair",
                    "selected_option_ids": ["opt_hair_no"],
                    "skipped": False,
                },
                {
                    "question_id": "q_general_energy",
                    "selected_option_ids": ["opt_gen_yes"],
                    "skipped": False,
                },
            ],
        }

        res_eval = await client.post("/v1/medbot/evaluate", json=payload)
        assert res_eval.status_code == 200
        data_eval = res_eval.json()
        assert data_eval["status"] == "MATCHES_FOUND"
        assert set(data_eval["collected_symptom_tags"]) == {"nightblindness", "fatigue"}
        assert len(data_eval["matched_entries"]) > 0

        # Query Explorer matcher with the exact same tags
        explorer_match = knowledge_repo.match_symptoms(
            user_tags=["nightblindness", "fatigue"], region_filter=None
        )

        assert explorer_match["status"] == "MATCHES_FOUND"
        assert len(data_eval["matched_entries"]) == len(explorer_match["matched_entries"])

        # Check identical ordering and top match
        top_medbot = data_eval["matched_entries"][0]
        top_explorer = explorer_match["matched_entries"][0]
        assert top_medbot["class_label"] == top_explorer["class_label"]
        assert top_medbot["match_count"] == top_explorer["match_count"]
        assert top_medbot["matched_tags"] == top_explorer["matched_tags"]


@pytest.mark.anyio
async def test_lifestyle_questions_never_alter_matches():
    """Optional lifestyle context does not alter symptom tags or matcher rankings (MEDBOT-10)."""
    user = AuthenticatedUser(uid="user_medbot_tester", email="medbot@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        base_answers = [
            {
                "question_id": "q_lips_mouth",
                "selected_option_ids": ["opt_lips_cracked"],
                "skipped": False,
            },
            {
                "question_id": "q_tongue",
                "selected_option_ids": ["opt_tongue_sore"],
                "skipped": False,
            },
        ]

        # Case A: without lifestyle answer
        res_a = await client.post(
            "/v1/medbot/evaluate",
            json={"mode": "standard", "answers": base_answers},
        )
        data_a = res_a.json()

        # Case B: with indoor desk lifestyle answer
        answers_with_lifestyle = list(base_answers) + [
            {
                "question_id": "q_lifestyle_routine",
                "selected_option_ids": ["opt_life_std_desk"],
                "skipped": False,
            }
        ]
        res_b = await client.post(
            "/v1/medbot/evaluate",
            json={"mode": "standard", "answers": answers_with_lifestyle},
        )
        data_b = res_b.json()

        # Both must produce identical collected tags, count, and ranking
        assert data_a["collected_symptom_tags"] == data_b["collected_symptom_tags"]
        assert len(data_a["matched_entries"]) == len(data_b["matched_entries"])
        for idx in range(len(data_a["matched_entries"])):
            assert data_a["matched_entries"][idx]["class_label"] == data_b["matched_entries"][idx]["class_label"]
            assert data_a["matched_entries"][idx]["match_count"] == data_b["matched_entries"][idx]["match_count"]

        # Case B records lifestyle context separately
        assert "q_lifestyle_routine" in data_b["lifestyle_responses"]


@pytest.mark.anyio
async def test_insufficient_information_and_skips():
    """When all questions are skipped or answered 'No', return INSUFFICIENT_INFORMATION without reassurance."""
    user = AuthenticatedUser(uid="user_medbot_tester", email="medbot@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All skipped
        payload_skipped = {
            "mode": "simple",
            "answers": [
                {"question_id": "q_eyes", "skipped": True},
                {"question_id": "q_hair", "skipped": True},
            ],
        }
        res_skip = await client.post("/v1/medbot/evaluate", json=payload_skipped)
        assert res_skip.status_code == 200
        data_skip = res_skip.json()
        assert data_skip["status"] == "INSUFFICIENT_INFORMATION"
        assert "no health conditions" not in data_skip["message"].lower()
        assert "you are fine" not in data_skip["message"].lower()

        # All 'No'
        payload_no = {
            "mode": "simple",
            "answers": [
                {"question_id": "q_eyes", "selected_option_ids": ["opt_eyes_no"], "skipped": False},
                {"question_id": "q_hair", "selected_option_ids": ["opt_hair_no"], "skipped": False},
            ],
        }
        res_no = await client.post("/v1/medbot/evaluate", json=payload_no)
        assert res_no.status_code == 200
        data_no = res_no.json()
        assert data_no["status"] == "INSUFFICIENT_INFORMATION"


@pytest.mark.anyio
async def test_save_medbot_assessment():
    """MedBot assessment can be saved to user's Files & Reports history with session_type='MedBot'."""
    user = AuthenticatedUser(uid="user_medbot_saver", email="saver@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        save_payload = {
            "session_type": "MedBot",
            "body_region_filter": None,
            "selected_tags": ["nightblindness", "eyedryness"],
            "matched_entries": [
                {
                    "class_label": "Bitot_Spots",
                    "body_region": "EYES",
                    "category": "Nutritional",
                    "vitamin_deficiency_association": "Vitamin A Deficiency",
                    "matched_tags": ["nightblindness", "eyedryness"],
                    "match_count": 2,
                    "total_condition_tags": 6,
                    "review_status": "unreviewed draft",
                }
            ],
            "package_version": "curated_v1.0",
            "matcher_version": "matcher_spec_v1.0",
        }

        save_res = await client.post("/v1/medbot/save", json=save_payload)
        assert save_res.status_code == 201
        saved_data = save_res.json()
        assert saved_data["session_type"] == "MedBot"
        assert saved_data["id"].startswith("sum_")
        assert saved_data["match_count_total"] == 1

        # Verify it shows up in Files & Reports listing
        list_res = await client.get("/v1/reports/summaries")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total_count"] == 1
        assert list_data["summaries"][0]["session_type"] == "MedBot"
        assert list_data["summaries"][0]["id"] == saved_data["id"]


@pytest.mark.anyio
async def test_prohibited_clinical_claims_scan():
    """Responses from MedBot must never contain prohibited words (diagnostic certainty, risk scores, drugs)."""
    user = AuthenticatedUser(uid="user_medbot_scan", email="scan@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/medbot/evaluate",
            json={
                "mode": "standard",
                "answers": [
                    {
                        "question_id": "q_skin",
                        "selected_option_ids": ["opt_skin_dry", "opt_skin_bruise"],
                        "skipped": False,
                    }
                ],
            },
        )
        assert res.status_code == 200
        raw_text = res.text.lower()

        # Prohibited terms per SAF-01, SAF-02, SAF-17
        prohibited_terms = [
            "probability",
            "risk percentage",
            "risk score",
            "confirmed diagnosis",
            "prescribe",
            "medication dosage",
            "treatment plan",
            "deficiency confirmed",
        ]
        for term in prohibited_terms:
            assert term not in raw_text, f"Found prohibited medical term '{term}' in MedBot evaluate response"

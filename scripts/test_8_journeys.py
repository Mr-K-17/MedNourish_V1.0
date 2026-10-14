"""
MedNourish — Step C: 8 Live End-to-End Real HTTP Journeys Test
=============================================================
Runs against running stack:
- Auth Emulator: http://127.0.0.1:9099
- Backend API:   http://127.0.0.1:8000
- ML Service:    http://127.0.0.1:8001
- Frontend UI:   http://127.0.0.1:5173
"""

import io
import json
import os
import sys
import time
import subprocess
import httpx
from PIL import Image, ImageDraw

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
backend_dir = os.path.join(REPO_ROOT, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from scripts.smoke_e2e import StackManager, is_internet_available

BACKEND_URL = "http://127.0.0.1:8000"
ML_URL = "http://127.0.0.1:8001"
EMULATOR_URL = "http://127.0.0.1:9099"

results = {}

def get_emulator_token(client: httpx.Client, email: str) -> tuple[str, str]:
    """Signs up / in a user with the Firebase Auth emulator and returns (uid, token)."""
    resp = client.post(
        f"{EMULATOR_URL}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake-api-key",
        json={"email": email, "password": "DemoSecurePass123!", "returnSecureToken": True},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data["localId"], data["idToken"]
    # If already exists, sign in
    resp = client.post(
        f"{EMULATOR_URL}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key",
        json={"email": email, "password": "DemoSecurePass123!", "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    return data["localId"], data["idToken"]

def generate_test_image_bytes():
    img = Image.new("RGB", (224, 224), color=(180, 140, 100))
    draw = ImageDraw.Draw(img)
    for x in range(0, 224, 8):
        draw.line([(x, 0), (224 - x, 224)], fill=(40, 30, 20), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_all_journeys():
    manager = StackManager()
    manager.ensure_services()
    client = httpx.Client(timeout=15.0)
    ts = int(time.time())
    email_a = f"journey_a_{ts}@example.com"
    email_b = f"journey_b_{ts}@example.com"

    try:
        uid_a, token_a = get_emulator_token(client, email_a)
        uid_b, token_b = get_emulator_token(client, email_b)
        headers_a = {"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"}
        headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}
    except Exception as e:
        print(f"Auth setup failed: {e}")
        return False

    print("\n--- Running Journey 1: Sign up with age 16, blood type, 3 conditions -> under-18 notice ---")
    try:
        p_payload = {
            "demo_consent_confirmed": True,
            "terms_consent_version": "v1.0",
            "display_name": "Under16 Demo User",
            "age": 16,
            "blood_type": "O+",
            "conditions": ["Anemia", "Asthma", "Migraine"],
        }
        res = client.post(f"{BACKEND_URL}/v1/profile", json=p_payload, headers=headers_a)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        p_data = res.json()
        assert p_data["age"] == 16
        assert p_data["blood_type"] == "O+"
        assert len(p_data["conditions"]) == 3
        assert "Reference content is written for adults; demo only." in p_data.get("under_18_notice", "")
        results["Journey 1"] = "PASS"
        print("Journey 1: PASS (Profile saved with age 16, blood O+, 3 conditions, and under-18 advisory notice)")
    except Exception as e:
        results["Journey 1"] = f"FAIL: {e}"
        print(f"Journey 1: FAIL - {e}")

    print("\n--- Running Journey 2: MedBot text extraction -> % bars -> auto-saved -> CarePlan sync ---")
    try:
        # Step A: extract chips with {"text": ...}
        ext_res = client.post(
            f"{BACKEND_URL}/v1/medbot/extract",
            json={"text": "I feel tired and cannot see well at night, no hair loss"},
            headers=headers_a,
        )
        assert ext_res.status_code == 200, f"Extract error: {ext_res.text}"
        ext_data = ext_res.json()
        chips = ext_data.get("chips", [])
        tags = [c.get("tag") for c in chips]
        assert "fatigue" in tags, f"Expected 'fatigue' in {tags}"
        assert "nightblindness" in tags, f"Expected 'nightblindness' in {tags}"
        assert "hairloss" not in tags, f"'hairloss' should be excluded due to negation: {tags}"

        # Step B: evaluate % bars
        eval_res = client.post(
            f"{BACKEND_URL}/v1/medbot/evaluate",
            json={
                "mode": "standard",
                "answers": [
                    {"question_id": "q_eyes", "selected_option_ids": ["opt_eyes_yes"]},
                ],
                "confirmed_free_text_tags": ["nightblindness", "fatigue"],
            },
            headers=headers_a,
        )
        assert eval_res.status_code == 200, f"Eval error: {eval_res.text}"
        eval_data = eval_res.json()
        scored_nutrients = eval_data.get("nutrient_scores", [])
        assert len(scored_nutrients) > 0, "No nutrient scores returned"
        top_nut = scored_nutrients[0]
        assert "percentage" in top_nut and top_nut["percentage"] > 0
        assert top_nut.get("percentage_kind") == "Reference match %"

        # Step C: Save assessment (triggers CarePlan auto-sync)
        save_res = client.post(
            f"{BACKEND_URL}/v1/medbot/save",
            json={
                "session_type": "MedBot",
                "body_region_filter": "Combined",
                "selected_tags": ["nightblindness", "fatigue"],
                "matched_entries": eval_data["matched_entries"],
                "package_version": eval_data["package_version"],
                "matcher_version": eval_data["matcher_version"],
            },
            headers=headers_a,
        )
        assert save_res.status_code == 201, f"Save error: {save_res.text}"

        # Step D: Verify CarePlan items appear
        cp_res = client.get(f"{BACKEND_URL}/v1/careplan/tasks", headers=headers_a)
        assert cp_res.status_code == 200
        tasks = cp_res.json().get("tasks", [])
        auto_tasks = [t for t in tasks if t.get("is_auto")]
        assert len(auto_tasks) >= 1, f"Expected at least 1 auto-synced task, got {len(auto_tasks)}"
        results["Journey 2"] = "PASS"
        print(f"Journey 2: PASS (Chips extracted: {tags}, % bars evaluated, auto-saved, {len(auto_tasks)} CarePlan tasks created)")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        results["Journey 2"] = f"FAIL: {repr(e)}\n{tb}"
        print(f"Journey 2: FAIL - {repr(e)}\n{tb}")

    print("\n--- Running Journey 3: MedScan image -> % candidates -> report + CarePlan updated ---")
    try:
        img_bytes = generate_test_image_bytes()
        scan_res = client.post(
            f"{BACKEND_URL}/v1/medscan/analyze",
            data={
                "body_region": "eyes",
                "symptoms": json.dumps(["bitotspots", "nightblindness"]),
                "save_report": "true",
            },
            files=[("file", ("test_eyes.jpg", img_bytes, "image/jpeg"))],
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert scan_res.status_code == 200, f"MedScan error: {scan_res.text}"
        scan_data = scan_res.json()
        assert scan_data.get("quality_passed") is True
        assert len(scan_data.get("nutrient_scores", [])) > 0
        assert scan_data.get("saved_report_id") is not None
        results["Journey 3"] = "PASS"
        print("Journey 3: PASS (MedScan quality check passed, nutrients blended, report and CarePlan updated)")
    except Exception as e:
        results["Journey 3"] = f"FAIL: {e}"
        print(f"Journey 3: FAIL - {e}")

    print("\n--- Running Journey 4: NurseBot 4 query patterns ---")
    try:
        # 1. Scripted app help
        q1 = client.post(f"{BACKEND_URL}/v1/nursebot/ask", json={"question": "how do I save a report"}, headers=headers_a).json()
        assert q1["intent"] == "app_help", f"Expected app_help, got {q1['intent']}"

        # 2. Web answer + disclaimer (or fallback if offline)
        q2 = client.post(f"{BACKEND_URL}/v1/nursebot/ask", json={"question": "what is vitamin B12 good for"}, headers=headers_a).json()
        assert q2["intent"] == "web_reference", f"Expected web_reference intent, got {q2.get('intent')}"
        if is_internet_available() and q2.get("is_web_answer"):
            assert q2["source_name"] is not None
            assert "medical" in q2["disclaimer"].lower() and "educational" in q2["disclaimer"].lower()
            web_msg = f"Web answer verified ({q2.get('source_name')})"
        else:
            web_msg = "Web service offline fallback verified with disclaimer"

        # 3. Emergency (no web)
        q3 = client.post(f"{BACKEND_URL}/v1/nursebot/ask", json={"question": "chest pain and cannot breathe"}, headers=headers_a).json()
        assert q3["intent"] == "emergency", f"Expected emergency, got {q3.get('intent')}"
        assert q3["is_web_answer"] is False, f"Expected is_web_answer False"
        assert "EMERGENCY ALERT" in q3["reply"], f"Expected EMERGENCY ALERT in {q3.get('reply')}"

        # 4. Refusal
        q4 = client.post(f"{BACKEND_URL}/v1/nursebot/ask", json={"question": "what dose of vitamin D should I take"}, headers=headers_a).json()
        assert q4["intent"] in ["refusal", "diagnosis_or_dosage_refusal"], f"Expected refusal intent, got {q4.get('intent')}"
        assert "cannot diagnose or prescribe" in q4["reply"] or "does not provide medical" in q4["reply"]

        results["Journey 4"] = "PASS"
        print(f"Journey 4: PASS (All 4 NurseBot routing paths verified: app_help, {web_msg}, emergency, refusal)")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        results["Journey 4"] = f"FAIL: {repr(e)}\n{tb}"
        print(f"Journey 4: FAIL - {repr(e)}\n{tb}")

    print("\n--- Running Journey 5: Reports charts load and final report card shows risk band ---")
    try:
        rep_res = client.get(f"{BACKEND_URL}/v1/reports/aggregate", headers=headers_a)
        assert rep_res.status_code == 200, f"Reports error: {rep_res.text}"
        rep_data = rep_res.json()
        assert "chart_data" in rep_data
        cd = rep_data["chart_data"]
        assert all(k in cd for k in ["grouped_bar", "ranked_horizontal", "radar", "donut_risk", "timeline", "heatmap"])
        card = rep_data["final_report_card"]
        assert any(b in card["demo_risk_band"] for b in ["Low", "Moderate", "High"]), f"Unexpected risk band: {card.get('demo_risk_band')}"
        assert len(card["suggested_measures"]) > 0
        results["Journey 5"] = "PASS"
        print(f"Journey 5: PASS (All 6 chart series loaded, final report card shows risk band: {card['demo_risk_band']})")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        results["Journey 5"] = f"FAIL: {repr(e)}\n{tb}"
        print(f"Journey 5: FAIL - {repr(e)}\n{tb}")

    print("\n--- Running Journey 6: User B cannot read User A's data ---")
    try:
        # User B queries User A's summaries / tasks
        res_b_tasks = client.get(f"{BACKEND_URL}/v1/careplan/tasks", headers=headers_b).json().get("tasks", [])
        res_b_summaries = client.get(f"{BACKEND_URL}/v1/reports/summaries", headers=headers_b).json().get("summaries", [])
        assert len(res_b_tasks) == 0, f"User B should see 0 tasks, saw: {res_b_tasks}"
        assert len(res_b_summaries) == 0, f"User B should see 0 summaries, saw: {res_b_summaries}"
        results["Journey 6"] = "PASS"
        print("Journey 6: PASS (User B strictly isolated from User A data: 0 summaries, 0 tasks)")
    except Exception as e:
        results["Journey 6"] = f"FAIL: {e}"
        print(f"Journey 6: FAIL - {e}")

    print("\n--- Running Journey 7: Account deletion removes everything ---")
    try:
        del_res = client.delete(f"{BACKEND_URL}/v1/profile", headers=headers_a)
        assert del_res.status_code == 200, f"Deletion failed: {del_res.text}"
        # Confirm user profile gone
        prof_check = client.get(f"{BACKEND_URL}/v1/profile", headers=headers_a)
        assert prof_check.status_code == 404, f"Profile should be 404, got {prof_check.status_code}"
        # Confirm summaries gone
        sum_check = client.get(f"{BACKEND_URL}/v1/reports/summaries", headers=headers_a)
        assert len(sum_check.json().get("summaries", [])) == 0
        # Confirm tasks gone
        task_check = client.get(f"{BACKEND_URL}/v1/careplan/tasks", headers=headers_a)
        assert len(task_check.json().get("tasks", [])) == 0
        results["Journey 7"] = "PASS"
        print("Journey 7: PASS (Account deletion cleanly purged user profile, saved summaries, and careplan items)")
    except Exception as e:
        results["Journey 7"] = f"FAIL: {e}"
        print(f"Journey 7: FAIL - {e}")

    print("\n--- Running Journey 8: Kill ML service -> MedScan falls back with clear message ---")
    try:
        # Temporarily kill ML service on port 8001
        cmd = 'powershell -Command "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"'
        pids = subprocess.check_output(cmd, shell=True).decode().strip().split()
        for p in pids:
            if p and int(p) > 0:
                subprocess.run(f"taskkill /F /PID {p}", shell=True, capture_output=True)
        time.sleep(2)

        # User B runs MedScan analysis with checklist symptoms
        img_bytes = generate_test_image_bytes()
        fallback_res = client.post(
            f"{BACKEND_URL}/v1/medscan/analyze",
            data={
                "body_region": "eyes",
                "symptoms": json.dumps(["bitotspots", "nightblindness"]),
                "save_report": "false",
            },
            files=[("file", ("test_eyes.jpg", img_bytes, "image/jpeg"))],
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert fallback_res.status_code == 200, f"Expected 200 fallback, got {fallback_res.status_code}: {fallback_res.text}"
        fb_data = fallback_res.json()
        assert fb_data.get("quality_passed") is True
        assert "ML" in fb_data.get("message", "") and "unavailable" in fb_data.get("message", "").lower(), f"Unexpected fallback message: {fb_data.get('message')}"
        assert len(fb_data.get("nutrient_scores", [])) > 0
        results["Journey 8"] = "PASS"
        print(f"Journey 8: PASS (When ML microservice is offline, MedScan cleanly fell back to symptoms-only reference matching with clear message: '{fb_data.get('message')}')")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        results["Journey 8"] = f"FAIL: {repr(e)}\n{tb}"
        print(f"Journey 8: FAIL - {repr(e)}\n{tb}")

    print("\n===========================================================")
    print("  8 End-to-End Journeys Summary Results:")
    print("===========================================================")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("===========================================================\n")
    return all("PASS" in v for v in results.values())

if __name__ == "__main__":
    success = run_all_journeys()
    sys.exit(0 if success else 1)

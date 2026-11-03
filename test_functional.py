import requests
import sys

BASE_URL = "http://localhost:5000/api"

def test_app():
    print("--- 1. Testing Health Endpoint ---")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    health_json = res.json()
    assert health_json.get("status") == "healthy"
    assert health_json.get("database") == "connected"
    print("[PASS] Health Check Passed:", health_json)

    print("\n--- 2. Testing Existing Admin Login ---")
    res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    admin_data = res.json()
    admin_token = admin_data["access_token"]
    assert admin_data["user"]["username"] == "admin"
    print("[PASS] Admin Login Passed. Token acquired.")

    print("\n--- 3. Testing Invalid Credentials Rejection ---")
    res = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("[PASS] Invalid Login Correctly Rejected with 401.")

    print("\n--- 4. Testing New Student User Registration ---")
    import random
    test_num = random.randint(1000, 9999)
    test_username = f"student_{test_num}"
    test_email = f"student_{test_num}@campus.edu"
    reg_payload = {
        "username": test_username,
        "email": test_email,
        "password": "Password123!",
        "full_name": f"Student Test {test_num}",
        "role": "student"
    }
    res = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    student_data = res.json()
    student_token = student_data["access_token"]
    assert student_data["user"]["username"] == test_username
    print(f"[PASS] New User '{test_username}' Registered Successfully.")

    print("\n--- 5. Testing Student Profile Retrieval & Update ---")
    headers = {"Authorization": f"Bearer {student_token}"}
    res = requests.get(f"{BASE_URL}/students/profile", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    profile = res.json()["profile"]
    print("[PASS] Default Profile Retrieved:", profile.get("roll_number"), profile.get("department_code"))

    update_payload = {
        "roll_number": f"2026CS{test_num}",
        "department_code": "CS",
        "cgpa": 8.75,
        "backlogs": 0,
        "internships_count": 2,
        "projects_count": 3,
        "certifications_count": 2,
        "coding_score": 88.0,
        "communication_score": 85.0
    }
    res = requests.put(f"{BASE_URL}/students/profile", json=update_payload, headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    updated_profile = res.json()["profile"]
    assert updated_profile["cgpa"] == 8.75
    assert updated_profile["coding_score"] == 88.0
    print("[PASS] Student Profile Successfully Updated & Persisted.")

    print("\n--- 6. Testing ML Placement Prediction (XGBoost) ---")
    pred_payload = {
        "cgpa": 8.75,
        "backlogs": 0,
        "internships": 2,
        "projects": 3,
        "coding_score": 88.0,
        "communication_score": 85.0,
        "department_code": "CS",
        "model_name": "XGBoost"
    }
    res = requests.post(f"{BASE_URL}/predictions", json=pred_payload, headers=headers)
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    pred = res.json()["prediction"]
    prob = pred["placement_probability"]
    status = pred["predicted_status"]
    print(f"[PASS] XGBoost Prediction: Probability = {prob*100:.1f}%, Status = {status}, Risk = {pred['risk_level']}")
    assert prob >= 0.70

    print("\n--- 7. Testing Prediction History ---")
    res = requests.get(f"{BASE_URL}/predictions/history", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    hist = res.json()
    assert hist["total_records"] >= 1
    print(f"[PASS] Prediction History Verified: {hist['total_records']} record(s) found.")

    print("\n--- 8. Testing Protected Analytics Endpoint ---")
    res = requests.get(f"{BASE_URL}/analytics", headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    analytics = res.json()
    print("[PASS] Analytics Computed Successfully:")
    print("   Total Users:", analytics["overview"]["total_users"])
    print("   Total Predictions:", analytics["overview"]["total_predictions"])
    print("   Campus Classrooms:", analytics["campus_infrastructure"]["total_classrooms"])
    print("   Campus Faculty:", analytics["campus_infrastructure"]["total_faculty"])

    print("\n--- 9. Testing Unauthenticated Request Rejection ---")
    res = requests.get(f"{BASE_URL}/students/profile")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("[PASS] Unauthenticated Access Successfully Blocked with 401.")

    print("\n--- 10. Testing AI Chatbot Endpoint ---")
    chat_payload = {"message": "How can I improve my placement probability above 90%?"}
    res = requests.post(f"{BASE_URL}/ai/chat", json=chat_payload, headers=headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chat_data = res.json()
    assert "reply" in chat_data
    print(f"[PASS] AI Chatbot Responded Successfully via {chat_data.get('model_used')}.")

    print("\n==========================================")
    print("ALL TESTS PASSED SUCCESSFULLY! 100% OPERATIONAL")
    print("==========================================")

if __name__ == "__main__":
    test_app()

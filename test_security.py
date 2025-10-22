import requests
import pytest
import time

# IMPORTANT: You MUST change this base URL to the address where your voter system application is running.
BASE_URL = "http://localhost:8000"

# --- 1. Unauthorized Access Test (Criteria: 401/403) ---

def test_unauthorized_access():
    """Tests access to a protected route without authentication/authorization."""
    
    # Replace with a real protected administrative or user-specific route
    protected_route = f"{BASE_URL}/admin/dashboard" 

    # Simulate an unauthenticated request (no login credentials)
    response = requests.get(protected_route)

    # REQ-19 Criteria: Unauthorized call to protected route -> 401/403
    assert response.status_code in [401, 403], \
        f"FAIL: Expected 401 (Unauthorized) or 403 (Forbidden), got {response.status_code} for {protected_route}"


# --- 2. SQL Injection Test (Criteria: 422/400) ---

def test_malicious_sql_input():
    """Tests if malicious SQL input results in a client error code instead of crashing the server."""
    
    # Replace with an actual route that handles user input (e.g., login or search)
    input_route = f"{BASE_URL}/api/login" 
    
    # Example of classic SQL Injection payload
    malicious_payload = {
        "username": "admin' OR '1'='1", 
        "password": "anypassword"
    }

    response = requests.post(input_route, json=malicious_payload)

    # REQ-19 Criteria: Malicious SQL input -> 422/400
    assert response.status_code in [422, 400], \
        f"FAIL: Expected 422 (Unprocessable Entity) or 400 (Bad Request), got {response.status_code}"


# --- 3. Rate Limiting Test (Criteria: 429) ---

def test_rate_limit_blocking():
    """Tests rapid login attempts to check rate-limiting is active."""
    
    # Replace with the endpoint that should be rate-limited (usually login)
    login_route = f"{BASE_URL}/api/login"
    
    # Send a number of requests designed to exceed the application's rate limit
    ATTEMPTS = 15 # Send enough requests to guarantee the limiter is hit
    
    print(f"\nTesting Rate Limit: Sending {ATTEMPTS} rapid requests to {login_route}...")
    
    responses = []
    for _ in range(ATTEMPTS):
        # Use a simple, non-malicious payload
        responses.append(requests.post(login_route, json={"username": "test", "password": "password"}))

    # REQ-19 Criteria: Rapid login attempts -> 429
    # The test passes if *at least one* of the responses is the 429 code.
    assert any(r.status_code == 429 for r in responses), \
        "FAIL: Expected at least one 429 response code (Too Many Requests). Rate limiter may be disabled."
import requests
import pytest

def test_create_user(api_base_url):
    user_data = {
        "name": "John Doe",
        "username": "johndoe",
        "email": "john.doe@example.com"
    }
    
    response = requests.post(f"{api_base_url}/users", json=user_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    # Verify response data
    response_data = response.json()
    assert "id" in response_data
    assert response_data["name"] == user_data["name"]
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]
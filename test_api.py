import requests
import json

print("Testing Mock API...")

# Test 1: Missing email (should fail with 400)
try:
    response1 = requests.post('http://localhost:5000/users', 
                             json={"name": "John Doe", "username": "johndoe"})
    print(f"Missing email: {response1.status_code} - {response1.text}")
except Exception as e:
    print(f"Error testing without email: {e}")

# Test 2: Missing username (should fail with 400)
try:
    response2 = requests.post('http://localhost:5000/users',
                             json={"name": "John Doe", "email": "john@example.com"})
    print(f"Missing username: {response2.status_code} - {response2.text}")
except Exception as e:
    print(f"Error testing without username: {e}")

# Test 3: All fields present (should succeed with 201)
try:
    response3 = requests.post('http://localhost:5000/users',
                             json={"name": "John Doe", "username": "johndoe", "email": "john@example.com"})
    print(f"All fields: {response3.status_code} - {response3.text}")
except Exception as e:
    print(f"Error testing with all fields: {e}")

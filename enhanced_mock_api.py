# enhanced_mock_api.py
from flask import Flask, request, jsonify
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# Rate limiting storage (in production, use Redis)
rate_limits = {}

def check_rate_limit(endpoint, user_id="default", max_requests=5, window_seconds=60):
    """Check if request exceeds rate limit"""
    now = datetime.now()
    key = f"{endpoint}:{user_id}"
    
    if key not in rate_limits:
        rate_limits[key] = []
    
    # Clean old requests
    rate_limits[key] = [req_time for req_time in rate_limits[key] 
                       if now - req_time < timedelta(seconds=window_seconds)]
    
    if len(rate_limits[key]) >= max_requests:
        return False
    
    rate_limits[key].append(now)
    return True

@app.route('/users', methods=['POST'])
def create_user():
    """Enhanced user creation with sophisticated constraints"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Rate limiting check (more lenient for testing)
    if not check_rate_limit('/users', max_requests=10, window_seconds=30):
        return jsonify({
            "error": "Rate limit exceeded: maximum 10 requests per 30 seconds for user creation"
        }), 429
    
    # Basic required fields
    if not data.get('name'):
        return jsonify({"error": "name field is required"}), 400
    
    if not data.get('username'):
        return jsonify({"error": "username field is required"}), 400
    
    # CONDITIONAL REQUIREMENT: email required when account_type is 'premium'
    if data.get('account_type') == 'premium' and not data.get('email'):
        return jsonify({
            "error": "email is required when account_type is 'premium'"
        }), 400
    
    # MUTUAL EXCLUSIVITY: either email OR phone, not both
    has_email = 'email' in data and data['email']
    has_phone = 'phone' in data and data['phone']
    
    if has_email and has_phone:
        return jsonify({
            "error": "Cannot specify both email and phone. Please provide only one contact method."
        }), 400
    
    if not has_email and not has_phone:
        return jsonify({
            "error": "Either email or phone must be provided as contact method"
        }), 400
    
    # FORMAT DEPENDENCY: email format required when contact_type is 'email'
    if data.get('contact_type') == 'email':
        email = data.get('email', '')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                "error": "Valid email format required when contact_type is 'email'"
            }), 400
    
    # BUSINESS RULE: age must be at least 18
    if 'age' in data:
        try:
            age = int(data['age'])
            if age < 18:
                return jsonify({
                    "error": "age must be at least 18 for account creation"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "age must be a valid number"
            }), 400
    
    # BUSINESS RULE: username pattern validation
    username = data.get('username', '')
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({
            "error": "username must be 3-20 characters and contain only letters, numbers, and underscores"
        }), 400
    
    # Success case
    new_user = {
        "id": 123,
        "name": data['name'],
        "username": data['username'],
        "account_type": data.get('account_type', 'basic'),
        "contact_method": "email" if has_email else "phone"
    }
    
    if has_email:
        new_user['email'] = data['email']
    if has_phone:
        new_user['phone'] = data['phone']
    
    return jsonify(new_user), 201

@app.route('/orders', methods=['POST'])
def create_order():
    """Order creation with business rule constraints"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Rate limiting
    if not check_rate_limit('/orders', max_requests=10, window_seconds=60):
        return jsonify({
            "error": "Rate limit exceeded: maximum 10 orders per minute"
        }), 429
    
    # CONDITIONAL REQUIREMENT: billing_address required when payment_method is 'credit_card'
    if data.get('payment_method') == 'credit_card' and not data.get('billing_address'):
        return jsonify({
            "error": "billing_address is required when payment_method is 'credit_card'"
        }), 400
    
    # BUSINESS RULE: total_amount must be greater than 0
    if 'total_amount' in data:
        try:
            amount = float(data['total_amount'])
            if amount <= 0:
                return jsonify({
                    "error": "total_amount must be greater than 0"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "total_amount must be a valid number"
            }), 400
    
    return jsonify({
        "id": 456,
        "status": "created",
        "total_amount": data.get('total_amount', 0),
        "payment_method": data.get('payment_method', 'cash')
    }), 201

@app.route('/products', methods=['POST'])
def create_product():
    """Product creation for format validation testing (no rate limits)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # FORMAT VALIDATION: email format when contact_email provided
    if 'contact_email' in data:
        email = data.get('contact_email', '')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                "error": "contact_email must be a valid email format"
            }), 400
    
    # Success case
    new_product = {
        "id": 789,
        "name": data.get("name", "Default Product"),
        "contact_email": data.get("contact_email"),
        "created_at": "2025-08-01T10:00:00Z"
    }
    
    return jsonify(new_product), 201

@app.route('/profiles', methods=['POST'])  
def create_profile():
    """Profile creation for required field testing (no rate limits)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # REQUIRED FIELD: username is required
    if not data.get('username'):
        return jsonify({"error": "username field is required"}), 400
    
    # Success case
    new_profile = {
        "id": 101,
        "username": data.get("username"),
        "bio": data.get("bio", ""),
        "created_at": "2025-08-01T10:00:00Z"
    }
    
    return jsonify(new_profile), 201

if __name__ == '__main__':
    app.run(port=5000, debug=True)

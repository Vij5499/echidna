from flask import Flask, request, jsonify

app = Flask(__name__)

# This line is now syntactically correct with the required value.
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    # This is our strict rule. 'email' MUST be present.
    if not data or 'email' not in data or 'name' not in data or 'username' not in data:
        return jsonify({
            "error": "Missing required fields. 'name', 'username', and 'email' are required."
        }), 400 # Return a "Bad Request" error

    # If all fields are present, return success
    new_user = {
        "id": 11, # A mock ID
        "name": data['name'],
        "username": data['username'],
        "email": data['email']
    }
    return jsonify(new_user), 201 # Return a "Created" success status

if __name__ == '__main__':
    # Run the server on localhost, port 5000
    app.run(port=5000, debug=True)
from flask import Blueprint, jsonify, request, session
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.auth import add_cors_headers

session_bp = Blueprint('session', __name__)

@session_bp.route('/api/user/check-session', methods=['GET', 'OPTIONS'])
def check_session():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return add_cors_headers(response)
        
    if 'user_id' in session:
        return add_cors_headers(jsonify({
            'status': 'authenticated',
            'user_id': session['user_id'],
            'username': session['username'],
            'email': session.get('email', '')
        }))
    else:
        return add_cors_headers(jsonify({
            'status': 'unauthenticated',
            'redirect': '/login'
        })), 401

from flask import Blueprint, jsonify
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# OPTIONS endpoints to handle CORS preflight requests
cors_bp = Blueprint('cors', __name__)

@cors_bp.route('/api/questions/<int:question_number>', methods=['OPTIONS'])
@cors_bp.route('/api/answers', methods=['OPTIONS'])
@cors_bp.route('/api/register', methods=['OPTIONS'])
@cors_bp.route('/api/login', methods=['OPTIONS'])
@cors_bp.route('/api/logout', methods=['OPTIONS'])
@cors_bp.route('/api/user', methods=['OPTIONS'])
@cors_bp.route('/api/user/wrong-questions', methods=['OPTIONS'])
@cors_bp.route('/api/user/progress', methods=['OPTIONS'])
@cors_bp.route('/api/user/check-session', methods=['OPTIONS'])
def handle_options():
    from utils.auth import add_cors_headers
    response = jsonify({'status': 'ok'})
    return add_cors_headers(response)

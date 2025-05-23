from flask import Blueprint, jsonify, request, session
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.auth import add_cors_headers
from utils.user_tier import check_and_reset_daily_limit

session_bp = Blueprint('session', __name__)

@session_bp.route('/api/user/check-session', methods=['GET', 'OPTIONS'])
def check_session():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return add_cors_headers(response)
        
    if 'user_id' in session:
        # 如果用戶已登入，檢查並更新每日題目限制
        if 'user_id' in session and 'daily_quiz_limit' in session:
            from utils.user_tier import check_and_reset_daily_limit
            user_id = session['user_id']
            daily_limit = session['daily_quiz_limit']
            was_reset = check_and_reset_daily_limit(user_id, daily_limit)
            
            # 如果限制被重置，更新會話中的剩餘問題數
            if was_reset:
                session['remaining_daily_questions'] = daily_limit
                session.modified = True
        
        return add_cors_headers(jsonify({
            'status': 'authenticated',
            'user_id': session['user_id'],
            'username': session['username'],
            'email': session.get('email', ''),            'tier': {
                'id': session.get('user_tier_id', 1),
                'name': session.get('tier_name', '免費版'),
                'remaining_daily_questions': session.get('remaining_daily_questions', 10),
                'daily_quiz_limit': session.get('daily_quiz_limit', 10),
                'has_advanced_analytics': session.get('has_advanced_analytics', False),
                'has_wrong_questions_review': session.get('has_wrong_questions_review', False),
                'has_mock_exam': session.get('has_mock_exam', False),
                'question_bank_size': session.get('question_bank_size', 200)
            },
            'is_admin': session.get('is_admin', 0)
        }))
    else:
        return add_cors_headers(jsonify({
            'status': 'unauthenticated',
            'redirect': '/login'
        })), 401

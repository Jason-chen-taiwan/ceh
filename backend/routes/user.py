from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_db_connection
from utils.auth import login_required, add_cors_headers
from utils.user_tier import check_and_reset_daily_limit
import mysql.connector

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return add_cors_headers(jsonify({
            'error': '所有欄位都是必填的',
            'status': 'error'
        })), 400
    
    # 對密碼進行加密
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({
            'error': '資料庫連接錯誤',
            'status': 'error'
        })), 500
    
    try:
        cursor = conn.cursor()
        try:
            # 使用預設的 user_tier_id = 1 (免費版)
            cursor.execute('''
                INSERT INTO users (username, password, email, user_tier_id)
                VALUES (%s, %s, %s, 1)
            ''', (username, hashed_password, email))
            conn.commit()
            
            return add_cors_headers(jsonify({
                'message': '註冊成功',
                'status': 'success',
                'redirect': '/login'
            }))
            
        except mysql.connector.IntegrityError as e:
            if 'Duplicate entry' in str(e):
                if 'username' in str(e):
                    error_message = '此使用者名稱已被使用'
                elif 'email' in str(e):
                    error_message = '此電子郵件已被註冊'
                else:
                    error_message = '註冊資訊重複'
                return add_cors_headers(jsonify({
                    'error': error_message,
                    'status': 'error'
                })), 409
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@user_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        print(f"Login attempt for email: {email}")
        
        if not email or not password:
            return add_cors_headers(jsonify({
                'error': '請提供電子郵件和密碼',
                'status': 'error'
            })), 400
        
        conn = get_db_connection()
        if not conn:
            return add_cors_headers(jsonify({
                'error': '資料庫連接錯誤',
                'status': 'error'
            })), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT u.*, ut.* FROM users u
                JOIN user_tiers ut ON u.user_tier_id = ut.id
                WHERE u.email = %s
            ''', (email,))
            
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                # 登入成功，設置會話
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_tier'] = user['tier_name']
                session['is_admin'] = user.get('is_admin', 0)
                session['has_advanced_analytics'] = user['has_advanced_analytics']
                session['has_wrong_questions_review'] = user['has_wrong_questions_review']
                session['has_mock_exam'] = user['has_mock_exam']
                session.permanent = True
                
                # 檢查並重置每日題目限制
                check_and_reset_daily_limit(user['id'], user['daily_quiz_limit'])
                
                return add_cors_headers(jsonify({
                    'message': '登入成功',
                    'status': 'success',
                    'redirect': '/dashboard',
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'tier': user['tier_name']
                    }
                }))
            else:
                return add_cors_headers(jsonify({
                    'error': '電子郵件或密碼錯誤',
                    'status': 'error'
                })), 401
                
        except mysql.connector.Error as e:
            print(f"Database error during login: {e}")
            return add_cors_headers(jsonify({
                'error': '資料庫錯誤',
                'status': 'error'
            })), 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return add_cors_headers(jsonify({
            'error': '登入過程發生錯誤',
            'status': 'error'
        })), 500

# 檢查並重置用戶每日題目限制
def check_and_reset_daily_limit(user_id, daily_limit):
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 檢查上次重置日期
        cursor.execute('''
            SELECT last_reset_date FROM users WHERE id = %s
        ''', (user_id,))
        result = cursor.fetchone()
        
        # 將日期轉換為字符串以進行比較
        from datetime import date
        today = date.today()
        last_reset = result['last_reset_date']
        
        # 如果不是今天，則重置每日限制
        if last_reset.strftime('%Y-%m-%d') != today.strftime('%Y-%m-%d'):
            cursor.execute('''
                UPDATE users 
                SET remaining_daily_questions = %s, last_reset_date = %s
                WHERE id = %s
            ''', (daily_limit, today, user_id))
            conn.commit()
            return True
        
        return False
    except mysql.connector.Error as e:
        print(f"Error checking daily limit: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@user_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return add_cors_headers(jsonify({
        'message': 'Logout successful',
        'redirect': '/'  # 添加重定向到首頁
    }))

@user_bp.route('/api/user', methods=['GET'])
@login_required
def get_user():
    return add_cors_headers(jsonify({
        'user': {
            'id': session['user_id'],
            'username': session['username']
        }
    }))

# 用戶錯題本
@user_bp.route('/api/user/wrong-questions', methods=['GET'])
@login_required
def get_user_wrong_questions():
    user_id = session['user_id']
    is_admin = session.get('is_admin', False)
    has_wrong_questions_review = True if is_admin else session.get('has_wrong_questions_review', False)
    
    print(f"Wrong questions API - User ID: {user_id}, Is Admin: {is_admin}, Has Review: {has_wrong_questions_review}")  # 調試日誌
    
    # 檢查用戶是否有權限訪問錯題本
    if not has_wrong_questions_review:
        return add_cors_headers(jsonify({
            'error': 'Feature not available',
            'message': '錯題集與重點複習功能僅限標準版或專業版用戶使用，請升級您的帳戶以獲取此功能！'
        })), 403
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 查詢用戶的錯題
        cursor.execute('''
            SELECT q.id, q.question_number, q.question_text, q.correct_answer, 
                   w.wrong_answer, w.created_at
            FROM questions q
            JOIN wrong_answers w ON q.id = w.question_id
            WHERE w.user_id = %s
            ORDER BY w.created_at DESC
        ''', (user_id,))
        
        wrong_questions = cursor.fetchall()
        
        # 獲取每個問題的選項
        result = []
        for wq in wrong_questions:
            cursor.execute('''
                SELECT choice_letter, choice_text 
                FROM choices 
                WHERE question_id = %s 
                ORDER BY choice_letter
            ''', (wq['id'],))
            choices = cursor.fetchall()
            
            question_data = {
                'question_number': wq['question_number'],
                'question_text': wq['question_text'],
                'choices': choices,
                'correct_answer': wq['correct_answer'],
                'wrong_answer': wq['wrong_answer'],
                'answered_at': wq['created_at']
            }
            result.append(question_data)
        
        return add_cors_headers(jsonify(result))
    
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# 用戶學習進度
@user_bp.route('/api/user/progress', methods=['GET'])
@login_required
def get_user_progress():
    user_id = session['user_id']
    is_admin = session.get('is_admin', False)
    has_advanced_analytics = True if is_admin else session.get('has_advanced_analytics', False)
    
    print(f"Progress API - User ID: {user_id}, Is Admin: {is_admin}")  # 調試日誌
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 統計總體進度
        cursor.execute('''
            SELECT 
                IFNULL(COUNT(*), 0) as total_answered,
                IFNULL(SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END), 0) as correct_count
            FROM user_progress
            WHERE user_id = %s
        ''', (user_id,))
        
        overall = cursor.fetchone()
        
        # 獲取最近的答題記錄
        cursor.execute('''
            SELECT up.is_correct, up.answer_time, q.question_number, q.question_text
            FROM user_progress up
            JOIN questions q ON up.question_id = q.id
            WHERE up.user_id = %s
            ORDER BY up.answer_time DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_activities = cursor.fetchall()
        
        # 基本進度數據對所有用戶都可用        # 初始化基礎回應數據
        total_answered = int(overall['total_answered']) if overall else 0
        correct_count = int(overall['correct_count']) if overall else 0
        response = {
            'overall': {
                'total_answered': total_answered,
                'correct_count': correct_count,
                'accuracy': (correct_count / total_answered * 100) if total_answered > 0 else 0
            },
            'recent_activities': recent_activities or [],
            'user_tier': {
                'name': '專業版',
                'is_admin': is_admin,
                'has_advanced_analytics': True,
                'has_wrong_questions_review': True,
                'has_mock_exam': True,
                'daily_quiz_limit': 999,
                'question_bank_size': 999
            } if is_admin else {
                'name': session.get('tier_name', '免費版'),
                'is_admin': is_admin,
                'has_advanced_analytics': session.get('has_advanced_analytics', False),
                'has_wrong_questions_review': session.get('has_wrong_questions_review', False),
                'has_mock_exam': session.get('has_mock_exam', False),
                'daily_quiz_limit': session.get('daily_quiz_limit', 10),
                'question_bank_size': session.get('question_bank_size', 200)
            }
        }
        
        # 管理員或高級會員可見的分析功能
        if is_admin or has_advanced_analytics:
            # 獲取類別進度分析
            cursor.execute('''
                SELECT c.category_name,
                       COUNT(*) as total_questions,
                       SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
                FROM user_progress up
                JOIN questions q ON up.question_id = q.id
                JOIN question_categories qc ON q.id = qc.question_id
                JOIN categories c ON qc.category_id = c.id
                WHERE up.user_id = %s
                GROUP BY c.category_name
            ''', (user_id,))
            
            category_progress = cursor.fetchall()
            
            # 添加類別進度到回應
            response['category_progress'] = category_progress
            
            # 添加弱項分析
            if category_progress:
                # 計算每個類別的正確率
                for category in category_progress:
                    if category['total_questions'] > 0:
                        category['accuracy'] = (category['correct_count'] / category['total_questions']) * 100
                    else:
                        category['accuracy'] = 0
                
                # 找出正確率最低的三個類別
                weak_areas = sorted(category_progress, key=lambda x: x['accuracy'])[:3]
                response['weak_areas'] = weak_areas
        
        return add_cors_headers(jsonify(response))
    
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# 用戶儀表板數據
@user_bp.route('/api/user/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    user_id = session['user_id']
    is_admin = session.get('is_admin', False)
    has_advanced_analytics = session.get('has_advanced_analytics', False)
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 基礎統計數據
        cursor.execute('''
            SELECT 
                COUNT(*) as total_answered,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                MAX(answer_time) as last_answer_time
            FROM user_progress
            WHERE user_id = %s
        ''', (user_id,))
        
        stats = cursor.fetchone()
        
        # 獲取最近的活動記錄
        cursor.execute('''
            SELECT up.is_correct, up.answer_time, q.question_text,
                   q.question_number
            FROM user_progress up
            JOIN questions q ON up.question_id = q.id
            WHERE up.user_id = %s
            ORDER BY up.answer_time DESC
            LIMIT 5
        ''', (user_id,))
        
        recent_activities = cursor.fetchall()
        
        response = {
            'stats': {
                'totalAnswered': stats['total_answered'] if stats else 0,
                'correctCount': stats['correct_count'] if stats else 0,
                'accuracy': round((stats['correct_count'] / stats['total_answered'] * 100), 2) if stats and stats['total_answered'] > 0 else 0,
                'lastAnswerTime': stats['last_answer_time'].strftime('%Y-%m-%d %H:%M:%S') if stats and stats['last_answer_time'] else None
            },
            'recentActivities': recent_activities
        }
        
        # 如果用戶有高級分析權限，添加更多詳細數據
        if has_advanced_analytics or is_admin:
            cursor.execute('''
                SELECT 
                    c.category_name,
                    COUNT(*) as total_questions,
                    SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
                FROM user_progress up
                JOIN questions q ON up.question_id = q.id
                JOIN question_categories qc ON q.id = qc.question_id
                JOIN categories c ON qc.category_id = c.id
                WHERE up.user_id = %s
                GROUP BY c.category_name
            ''', (user_id,))
            
            category_progress = cursor.fetchall()
            
            # 計算每個類別的正確率
            for category in category_progress:
                category['accuracy'] = round((category['correct_count'] / category['total_questions'] * 100), 2) if category['total_questions'] > 0 else 0
            
            response['categoryProgress'] = category_progress
            
            # 找出最弱的三個類別
            weak_areas = sorted(category_progress, key=lambda x: x['accuracy'])[:3]
            response['weakAreas'] = weak_areas
        
        return add_cors_headers(jsonify(response))
    
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

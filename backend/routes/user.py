from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_db_connection
from utils.auth import login_required, add_cors_headers
import mysql.connector

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return add_cors_headers(jsonify({'error': 'Missing required fields'})), 400
    
    # 對密碼進行加密
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email) 
                VALUES (%s, %s, %s)
            ''', (username, hashed_password, email))
            conn.commit()
            return add_cors_headers(jsonify({'message': 'User registered successfully'}))
        except mysql.connector.IntegrityError as e:
            # 處理用戶名或郵箱已存在的情況
            if 'Duplicate entry' in str(e):
                if 'username' in str(e):
                    return add_cors_headers(jsonify({'error': 'Username already exists'})), 409
                elif 'email' in str(e):
                    return add_cors_headers(jsonify({'error': 'Email already exists'})), 409
            return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@user_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')  # 改為使用 email 登入
    password = data.get('password')
    
    print(f"Login attempt for email: {email}")
    
    if not email or not password:
        print("Missing email or password")
        return add_cors_headers(jsonify({'error': 'Missing email or password'})), 400
    
    conn = get_db_connection()
    if not conn:
        print("Database connection failed")
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, username, password, email 
            FROM users 
            WHERE email = %s
        ''', (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User not found with email: {email}")
            return add_cors_headers(jsonify({'error': 'Invalid email or password'})), 401
        
        is_valid = check_password_hash(user['password'], password)
        print(f"Password validation: {is_valid}")
        
        if not is_valid:
            print("Invalid password")
            return add_cors_headers(jsonify({'error': 'Invalid email or password'})), 401
            
        # 登入成功，設置會話
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session.modified = True  # 確保會話被保存
        
        print(f"Login successful for: {user['email']}")
        print(f"Session: {session}")
        
        # 檢查是否有next參數用於重定向
        next_url = data.get('next')
        
        response = jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            },
            'redirect': next_url if next_url else '/'  # 更改為首頁
        })
        
        return add_cors_headers(response)
        
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
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

@user_bp.route('/api/user/check-session', methods=['GET', 'OPTIONS'])
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

# 用戶錯題本
@user_bp.route('/api/user/wrong-questions', methods=['GET'])
@login_required
def get_user_wrong_questions():
    user_id = session['user_id']
    
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
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 統計總體進度
        cursor.execute('''
            SELECT 
                COUNT(*) as total_answered,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count
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
        
        return add_cors_headers(jsonify({
            'overall': {
                'total_answered': overall['total_answered'] if overall else 0,
                'correct_count': overall['correct_count'] if overall else 0,
                'accuracy': (overall['correct_count'] / overall['total_answered'] * 100) if overall and overall['total_answered'] > 0 else 0
            },
            'recent_activities': recent_activities
        }))
    
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

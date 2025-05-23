from flask import Blueprint, jsonify, request, session
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_db_connection
from utils.auth import login_required, add_cors_headers
import mysql.connector

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/api/questions/<int:question_number>', methods=['GET'])
@login_required
def get_question(question_number):
    # 檢查用戶是否已用完每日題目限制
    user_id = session['user_id']
    remaining_questions = session.get('remaining_daily_questions', 0)
    question_bank_size = session.get('question_bank_size', 200)
      # 如果用戶已用完每日題目限制，則返回錯誤
    if remaining_questions <= 0:
        daily_limit = session.get('daily_quiz_limit', 10)
        return add_cors_headers(jsonify({
            'error': 'Daily question limit reached',
            'message': f'您已達到今日免費題目限制（{daily_limit}題/天）。請明天再來繼續學習，或升級您的帳戶以獲得更高的每日題目限制。'
        })), 403
      # 如果問題編號超出用戶可訪問的題庫大小，則返回錯誤
    if question_number > question_bank_size:
        return add_cors_headers(jsonify({
            'error': 'Question not available',
            'message': f'此題目僅限高級用戶訪問。免費用戶只能訪問前 {question_bank_size} 題，請升級您的帳戶以解鎖全部題庫。'
        })), 403
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 獲取問題詳情
        cursor.execute('''
            SELECT id, question_number, question_text, correct_answer
            FROM questions 
            WHERE question_number = %s
        ''', (question_number,))
        question = cursor.fetchone()
        
        if question is None:
            return add_cors_headers(jsonify({'error': 'Question not found'})), 404
            
        # 獲取選項
        cursor.execute('''
            SELECT choice_letter, choice_text 
            FROM choices 
            WHERE question_id = %s 
            ORDER BY choice_letter
        ''', (question['id'],))
        choices = cursor.fetchall()
        
        # 減少用戶剩餘的每日問題數量
        cursor.execute('''
            UPDATE users 
            SET remaining_daily_questions = remaining_daily_questions - 1
            WHERE id = %s
        ''', (user_id,))
        conn.commit()
        
        # 更新會話中的剩餘問題數
        session['remaining_daily_questions'] = remaining_questions - 1
        session.modified = True
        
        response = {
            'question_number': question['question_number'],
            'question_text': question['question_text'],
            'choices': choices,
            'correct_answer': question['correct_answer'] if session.get('has_advanced_analytics', False) else None,
            'remaining_daily_questions': remaining_questions - 1
        }
        
        return add_cors_headers(jsonify(response))
    
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@questions_bp.route('/api/questions/all', methods=['GET'])
@login_required
def get_all_questions():
    # 獲取用戶的問題庫大小限制
    question_bank_size = session.get('question_bank_size', 200)
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 獲取所有問題，但僅限於用戶可訪問的範圍
        cursor.execute('''
            SELECT id, question_number, question_text
            FROM questions 
            WHERE question_number <= %s
            ORDER BY question_number
        ''', (question_bank_size,))
        questions = cursor.fetchall()
        
        result = []
        for q in questions:
            # 獲取每個問題的選項
            cursor.execute('''
                SELECT choice_letter, choice_text 
                FROM choices 
                WHERE question_id = %s 
                ORDER BY choice_letter
            ''', (q['id'],))
            choices = cursor.fetchall()
            
            question_data = {
                'question_number': q['question_number'],
                'question_text': q['question_text'],
                'choices': choices
            }
            result.append(question_data)
        
        return add_cors_headers(jsonify(result))
    
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@questions_bp.route('/api/questions/random', methods=['GET'])
@login_required
def get_random_question():
    # 檢查用戶是否已用完每日題目限制
    user_id = session['user_id']
    remaining_questions = session.get('remaining_daily_questions', 0)
    question_bank_size = session.get('question_bank_size', 200)
      # 如果用戶已用完每日題目限制，則返回錯誤
    if remaining_questions <= 0:
        daily_limit = session.get('daily_quiz_limit', 10)
        return add_cors_headers(jsonify({
            'error': 'Daily question limit reached',
            'message': f'您已達到今日免費題目限制（{daily_limit}題/天）。請明天再來繼續學習，或升級您的帳戶以獲得更高的每日題目限制。'
        })), 403
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 隨機獲取一個問題，但僅限於用戶可訪問的題庫範圍內
        cursor.execute('''
            SELECT id, question_number, question_text 
            FROM questions 
            WHERE question_number <= %s
            ORDER BY RAND() 
            LIMIT 1
        ''', (question_bank_size,))
        question = cursor.fetchone()
        
        if question is None:
            return add_cors_headers(jsonify({'error': 'No questions found'})), 404
        
        # 獲取該問題的選項
        cursor.execute('''
            SELECT choice_letter, choice_text 
            FROM choices 
            WHERE question_id = %s 
            ORDER BY choice_letter
        ''', (question['id'],))
        choices = cursor.fetchall()
        
        # 減少用戶剩餘的每日問題數量
        cursor.execute('''
            UPDATE users 
            SET remaining_daily_questions = remaining_daily_questions - 1
            WHERE id = %s
        ''', (user_id,))
        conn.commit()
        
        # 更新會話中的剩餘問題數
        session['remaining_daily_questions'] = remaining_questions - 1
        session.modified = True
        
        response = {
            'question_number': question['question_number'],
            'question_text': question['question_text'],
            'choices': choices,
            'remaining_daily_questions': remaining_questions - 1
        }
        
        return add_cors_headers(jsonify(response))
    
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@questions_bp.route('/api/answers', methods=['POST'])
@login_required
def check_answer():
    data = request.json
    question_number = data.get('questionNumber')
    user_answer = data.get('answer')
    
    if not question_number or not user_answer:
        return add_cors_headers(jsonify({'error': 'Missing required fields'})), 400
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, correct_answer 
            FROM questions 
            WHERE question_number = %s
        ''', (question_number,))
        result = cursor.fetchone()
        
        if not result:
            return add_cors_headers(jsonify({'error': 'Question not found'})), 404
        
        is_correct = result['correct_answer'] == user_answer
        
        # 如果用戶已登入，則記錄答題情況
        if 'user_id' in session:
            user_id = session['user_id']
            question_id = result['id']
            
            # 更新用戶進度
            try:
                cursor.execute('''
                    INSERT INTO user_progress (user_id, question_id, is_correct) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE is_correct = %s, answer_time = CURRENT_TIMESTAMP
                ''', (user_id, question_id, is_correct, is_correct))
                
                # 如果答錯了，記錄錯題
                if not is_correct:
                    cursor.execute('''
                        INSERT INTO wrong_answers (user_id, question_id, wrong_answer)
                        VALUES (%s, %s, %s)
                    ''', (user_id, question_id, user_answer))
                
                conn.commit()
            except mysql.connector.Error as e:
                print(f"Error recording user progress: {e}")
        
        return add_cors_headers(jsonify({
            'correct': is_correct,
            'correct_answer': result['correct_answer']
        }))
        
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

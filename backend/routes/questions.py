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
        
        response = {
            'question_number': question['question_number'],
            'question_text': question['question_text'],
            'choices': choices,
            'correct_answer': question['correct_answer']
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
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 獲取所有問題
        cursor.execute('''
            SELECT id, question_number, question_text
            FROM questions 
            ORDER BY question_number
        ''')
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
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 隨機獲取一個問題
        cursor.execute('''
            SELECT id, question_number, question_text 
            FROM questions 
            ORDER BY RAND() 
            LIMIT 1
        ''')
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
        
        response = {
            'question_number': question['question_number'],
            'question_text': question['question_text'],
            'choices': choices
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

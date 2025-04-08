from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__, 
    template_folder='../frontend/templates',  # 指定模板目錄
    static_folder='../frontend/static'        # 指定靜態檔案目錄
)

# 允許所有來源的 CORS 請求
CORS(app)

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'  # 改為允許所有來源
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 處理 OPTIONS 請求
@app.route('/api/questions/<int:question_number>', methods=['OPTIONS'])
@app.route('/api/answers', methods=['OPTIONS'])
def handle_options():
    response = jsonify({'status': 'ok'})
    return add_cors_headers(response)

def get_db_connection():
    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'Alpha',
        'password': '&^%$#@1Secpaas',
        'database': 'ceh_quiz'
    }
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return jsonify({"message": "API is running"})

@app.route('/api/test')
def test_db():
    try:
        conn = get_db_connection()
        if not conn:
            return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        result = cursor.fetchone()
        count = result['count']
        
        cursor.close()
        conn.close()
        return add_cors_headers(jsonify({"status": "success", "question_count": count}))
    except Exception as e:
        return add_cors_headers(jsonify({"status": "error", "message": str(e)})), 500

@app.route('/api/questions/<int:question_number>', methods=['GET'])
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

@app.route('/api/questions/all', methods=['GET'])
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

@app.route('/api/questions/random', methods=['GET'])
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

@app.route('/api/answers', methods=['POST'])
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
            SELECT correct_answer 
            FROM questions 
            WHERE question_number = %s
        ''', (question_number,))
        result = cursor.fetchone()
        
        if not result:
            return add_cors_headers(jsonify({'error': 'Question not found'})), 404
        
        is_correct = result['correct_answer'] == user_answer
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

# 新增前端路由
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

# 確保所有回應都添加 CORS 標頭
@app.after_request
def after_request(response):
    return add_cors_headers(response)

if __name__ == '__main__':
    app.run(debug=True)

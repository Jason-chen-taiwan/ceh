from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'quiz_database.db'))
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
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
            return jsonify({'error': 'Database connection failed'}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "question_count": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        # Get question details
        cursor.execute('''
            SELECT q.*, GROUP_CONCAT(c.choice_letter || ':' || c.choice_text) as choices
            FROM questions q 
            LEFT JOIN choices c ON q.id = c.question_id
            WHERE q.id = ?
            GROUP BY q.id
        ''', (question_id,))
        question = cursor.fetchone()
        
        if question is None:
            return jsonify({'error': 'Question not found'}), 404
            
        # Parse the concatenated choices back into a list
        choices_list = []
        if question['choices']:
            for choice in question['choices'].split(','):
                letter, text = choice.split(':', 1)
                choices_list.append({'letter': letter, 'text': text})
            
        return jsonify({
            'id': question['id'],
            'question_number': question['question_number'],
            'question': question['question_text'],
            'choices': choices_list,
            'correct_answer': question['correct_answer']
        })
    
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/questions/all', methods=['GET'])
def get_all_questions():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT q.*, GROUP_CONCAT(c.choice_letter || ':' || c.choice_text) as choices
            FROM questions q 
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
        ''')
        questions = cursor.fetchall()
        
        result = []
        for q in questions:
            choices_list = []
            if q['choices']:
                for choice in q['choices'].split(','):
                    letter, text = choice.split(':', 1)
                    choices_list.append({'letter': letter, 'text': text})
            
            question_data = {
                'id': q['id'],
                'question_number': q['question_number'],
                'question': q['question_text'],
                'choices': choices_list
            }
            result.append(question_data)
        
        return jsonify(result)
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/questions/random', methods=['GET'])
def get_random_question():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT q.*, GROUP_CONCAT(c.choice_letter || ':' || c.choice_text) as choices
            FROM questions q 
            LEFT JOIN choices c ON q.id = c.question_id
            GROUP BY q.id
            ORDER BY RANDOM() 
            LIMIT 1
        ''')
        question = cursor.fetchone()
        
        if question is None:
            return jsonify({'error': 'No questions found'}), 404
        
        choices_list = []
        if question['choices']:
            try:
                for choice in question['choices'].split(','):
                    if ':' in choice:  # 確保選項格式正確
                        letter, text = choice.split(':', 1)
                        choices_list.append({'letter': letter, 'text': text})
            except Exception as e:
                print(f"Error parsing choices: {e}")
                # 如果解析失敗，直接查詢 choices 表
                cursor.execute('''
                    SELECT choice_letter, choice_text 
                    FROM choices 
                    WHERE question_id = ?
                    ORDER BY choice_letter
                ''', (question['id'],))
                choices = cursor.fetchall()
                choices_list = [{'letter': c['choice_letter'], 'text': c['choice_text']} for c in choices]
        
        return jsonify({
            'id': question['id'],
            'question_number': question['question_number'],
            'question': question['question_text'],
            'choices': choices_list
        })
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/answers', methods=['POST'])
def check_answer():
    data = request.json
    question_id = data.get('questionId')
    user_answer = data.get('answer')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answer FROM questions WHERE id = ?", (question_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        is_correct = result['correct_answer'] == user_answer
        return jsonify({
            'correct': is_correct,
            'correctAnswer': result['correct_answer']
        })
    return jsonify({'error': 'Question not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)

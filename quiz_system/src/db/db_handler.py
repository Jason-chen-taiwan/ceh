import sqlite3
from typing import List, Dict

class DatabaseHandler:
    def __init__(self, db_path: str = "quiz_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 創建問題表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_number TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    correct_answer TEXT NOT NULL
                )
            ''')
            
            # 創建選項表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS choices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    choice_letter TEXT NOT NULL,
                    choice_text TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
            ''')
            
            conn.commit()

    def insert_questions(self, questions: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for question in questions:
                # 插入問題
                cursor.execute('''
                    INSERT INTO questions (question_number, question_text, correct_answer)
                    VALUES (?, ?, ?)
                ''', (question['id'], question['question'], question['correct_answer']))
                
                question_id = cursor.lastrowid
                
                # 插入選項
                for letter, text in question['choices'].items():
                    cursor.execute('''
                        INSERT INTO choices (question_id, choice_letter, choice_text)
                        VALUES (?, ?, ?)
                    ''', (question_id, letter, text))
            
            conn.commit()

    def check_database_integrity(self) -> bool:
        """檢查數據庫表格是否正確創建"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 檢查表格是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND (name='questions' OR name='choices')
                """)
                tables = cursor.fetchall()
                return len(tables) == 2
        except sqlite3.Error:
            return False

    def get_all_questions(self) -> List[Dict]:
        """獲取所有問題及其選項"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            questions = []
            
            cursor.execute('''
                SELECT q.id, q.question_number, q.question_text, q.correct_answer
                FROM questions q
            ''')
            
            for row in cursor.fetchall():
                question = {
                    'id': row[1],
                    'question': row[2],
                    'correct_answer': row[3],
                    'choices': {}
                }
                
                # 獲取該問題的所有選項
                cursor.execute('''
                    SELECT choice_letter, choice_text
                    FROM choices
                    WHERE question_id = ?
                ''', (row[0],))
                
                for choice in cursor.fetchall():
                    question['choices'][choice[0]] = choice[1]
                
                questions.append(question)
            
            return questions

    def get_question_by_number(self, question_number: str) -> Dict:
        """獲取指定編號的問題"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.id, q.question_number, q.question_text, q.correct_answer
                FROM questions q
                WHERE q.question_number = ?
            ''', (question_number,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            question = {
                'id': row[1],
                'question': row[2],
                'correct_answer': row[3],
                'choices': {}
            }
            
            cursor.execute('''
                SELECT choice_letter, choice_text
                FROM choices
                WHERE question_id = ?
            ''', (row[0],))
            
            for choice in cursor.fetchall():
                question['choices'][choice[0]] = choice[1]
            
            return question

    def verify_data_integrity(self) -> Dict[str, bool]:
        """檢查資料完整性"""
        results = {
            'all_questions_have_choices': True,
            'all_choices_have_valid_questions': True,
            'all_correct_answers_exist': True
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查所有問題是否都有選項
            cursor.execute('''
                SELECT q.id 
                FROM questions q 
                LEFT JOIN choices c ON q.id = c.question_id 
                WHERE c.id IS NULL
            ''')
            if cursor.fetchone():
                results['all_questions_have_choices'] = False
            
            # 檢查所有選項是否都有對應的問題
            cursor.execute('''
                SELECT c.id 
                FROM choices c 
                LEFT JOIN questions q ON c.question_id = q.id 
                WHERE q.id IS NULL
            ''')
            if cursor.fetchone():
                results['all_choices_have_valid_questions'] = False
            
            # 檢查正確答案是否存在於選項中
            cursor.execute('''
                SELECT q.id 
                FROM questions q 
                LEFT JOIN choices c 
                ON q.id = c.question_id AND q.correct_answer = c.choice_letter 
                WHERE c.id IS NULL
            ''')
            if cursor.fetchone():
                results['all_correct_answers_exist'] = False
            
            return results

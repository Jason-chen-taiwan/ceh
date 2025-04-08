import mysql.connector
from typing import List, Dict

class DatabaseHandler:
    def __init__(self):
        self.db_config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'Alpha',
            'password': '&^%$#@1Secpaas',
            'database': 'ceh_quiz'
        }
        self.init_database()

    def init_database(self):
        """初始化資料庫表格"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # 先刪除現有的表格（如果存在）
            cursor.execute("DROP TABLE IF EXISTS choices")
            cursor.execute("DROP TABLE IF EXISTS questions")

            # 創建 questions 表
            cursor.execute('''
                CREATE TABLE questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_number INT NOT NULL,
                    question_text TEXT NOT NULL,
                    correct_answer CHAR(1) NOT NULL,
                    UNIQUE KEY unique_question_number (question_number)
                )
            ''')

            # 創建 choices 表
            cursor.execute('''
                CREATE TABLE choices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_id INT NOT NULL,
                    choice_letter CHAR(1) NOT NULL,
                    choice_text TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()
            print("資料庫表格已成功初始化")
        except mysql.connector.Error as err:
            print(f"資料庫初始化錯誤: {err}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def insert_questions(self, questions: List[Dict]):
        """插入問題及選項"""
        if not self.check_database_integrity():
            print("資料庫結構不完整，嘗試重新初始化...")
            self.init_database()

        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        try:
            for question in questions:
                # 插入問題
                cursor.execute('''
                    INSERT INTO questions 
                    (question_number, question_text, correct_answer)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    question_text = VALUES(question_text),
                    correct_answer = VALUES(correct_answer)
                ''', (
                    question['question_number'],
                    question['question_text'],
                    question['correct_answer']
                ))

                if cursor.lastrowid:
                    question_id = cursor.lastrowid
                else:
                    # 如果是更新現有記錄，獲取該記錄的 ID
                    cursor.execute('''
                        SELECT id FROM questions WHERE question_number = %s
                    ''', (question['question_number'],))
                    question_id = cursor.fetchone()[0]

                # 刪除該問題的現有選項
                cursor.execute('DELETE FROM choices WHERE question_id = %s', (question_id,))

                # 插入新選項
                for choice in question['choices']:
                    cursor.execute('''
                        INSERT INTO choices 
                        (question_id, choice_letter, choice_text)
                        VALUES (%s, %s, %s)
                    ''', (
                        question_id,
                        choice['choice_letter'],
                        choice['choice_text']
                    ))

            conn.commit()
            print(f"成功插入/更新 {len(questions)} 個問題")
        except mysql.connector.Error as err:
            print(f"插入問題時發生錯誤: {err}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def check_database_integrity(self) -> bool:
        """檢查數據庫表格是否正確創建"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("SHOW TABLES LIKE 'questions'")
            questions_table = cursor.fetchone()

            cursor.execute("SHOW TABLES LIKE 'choices'")
            choices_table = cursor.fetchone()

            cursor.close()
            conn.close()

            return questions_table is not None and choices_table is not None
        except mysql.connector.Error:
            return False

    def get_all_questions(self) -> List[Dict]:
        """獲取所有問題及其選項"""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)  # 使用 DictCursor

        cursor.execute("SELECT id, question_number, question_text, correct_answer FROM questions")
        questions_data = cursor.fetchall()

        questions = []
        for row in questions_data:
            question = {
                'question_number': row['question_number'],
                'question_text': row['question_text'],
                'correct_answer': row['correct_answer'],
                'choices': []
            }

            # 獲取該問題的所有選項
            cursor.execute("SELECT choice_letter, choice_text FROM choices WHERE question_id = %s", (row['id'],))
            choices = cursor.fetchall()

            for choice in choices:
                question['choices'].append({
                    'choice_letter': choice['choice_letter'],
                    'choice_text': choice['choice_text']
                })

            questions.append(question)

        cursor.close()
        conn.close()
        return questions

    def get_question_by_number(self, question_number: int) -> Dict:
        """獲取指定編號的問題"""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)  # 使用 DictCursor

        cursor.execute("SELECT id, question_number, question_text, correct_answer FROM questions WHERE question_number = %s", (question_number,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return None

        question = {
            'question_number': row['question_number'],
            'question_text': row['question_text'],
            'correct_answer': row['correct_answer'],
            'choices': []
        }

        cursor.execute("SELECT choice_letter, choice_text FROM choices WHERE question_id = %s", (row['id'],))
        choices = cursor.fetchall()

        for choice in choices:
            question['choices'].append({
                'choice_letter': choice['choice_letter'],
                'choice_text': choice['choice_text']
            })

        cursor.close()
        conn.close()
        return question

    def verify_data_integrity(self) -> Dict[str, bool]:
        """檢查資料完整性"""
        results = {
            'all_questions_have_choices': True,
            'all_choices_have_valid_questions': True,
            'all_correct_answers_exist': True
        }

        conn = mysql.connector.connect(**self.db_config)
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

        cursor.close()
        conn.close()
        return results

from backend.utils.db import get_db_connection
import mysql.connector

def init_db():
    conn = get_db_connection()
    if not conn:
        print("無法連接到資料庫進行初始化")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 創建用戶表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 創建用戶學習記錄表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            question_id INT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_question (user_id, question_id)
        )
        ''')
        
        # 創建錯題收集表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            question_id INT NOT NULL,
            wrong_answer CHAR(1) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        print("資料庫初始化成功")
        return True
    except mysql.connector.Error as e:
        print(f"資料庫初始化錯誤: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

import mysql.connector

def get_db_connection():
    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': 'mysqIg0zIn7hour',
        'database': 'ceh_quiz'
    }
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# 初始化資料庫，確保所需表格存在
def init_db():
    conn = get_db_connection()
    if not conn:
        print("無法連接到資料庫進行初始化")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 創建用戶級別表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tiers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tier_name VARCHAR(50) UNIQUE NOT NULL,
            daily_quiz_limit INT NOT NULL,
            has_advanced_analytics BOOLEAN NOT NULL DEFAULT FALSE,
            has_wrong_questions_review BOOLEAN NOT NULL DEFAULT FALSE,
            has_mock_exam BOOLEAN NOT NULL DEFAULT FALSE,
            question_bank_size INT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 檢查是否已存在用戶級別數據
        cursor.execute("SELECT COUNT(*) as count FROM user_tiers")
        result = cursor.fetchone()
          # 如果沒有數據，插入預設的用戶級別
        if result[0] == 0:
            cursor.execute('''
            INSERT INTO user_tiers (tier_name, daily_quiz_limit, has_advanced_analytics, 
                                  has_wrong_questions_review, has_mock_exam, question_bank_size, description)
            VALUES ('免費版', 10, FALSE, FALSE, FALSE, 200, '基本功能，每日限制10題')
            ''')
            
            # 添加高級用戶級別
            cursor.execute('''
            INSERT INTO user_tiers (tier_name, daily_quiz_limit, has_advanced_analytics, 
                                  has_wrong_questions_review, has_mock_exam, question_bank_size, description)
            VALUES ('標準版', 50, TRUE, TRUE, FALSE, 400, '標準功能，每日限制50題，包含進階分析和錯題本')
            ''')
            
            # 添加專業用戶級別
            cursor.execute('''
            INSERT INTO user_tiers (tier_name, daily_quiz_limit, has_advanced_analytics, 
                                  has_wrong_questions_review, has_mock_exam, question_bank_size, description)
            VALUES ('專業版', 999, TRUE, TRUE, TRUE, 999, '完整功能，無每日限制，包含所有題庫和模擬考試')
            ''')
            
            conn.commit()
            print("已創建默認用戶級別")
          # 創建用戶表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            user_tier_id INT NOT NULL DEFAULT 1,
            remaining_daily_questions INT DEFAULT 10,
            last_reset_date DATE DEFAULT (CURRENT_DATE),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_tier_id) REFERENCES user_tiers(id)
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

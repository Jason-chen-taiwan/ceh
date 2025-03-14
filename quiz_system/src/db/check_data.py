import sqlite3

def check_database():
    conn = sqlite3.connect("quiz_database.db")
    cursor = conn.cursor()
    
    # 檢查問題數量
    cursor.execute("SELECT COUNT(*) FROM questions")
    question_count = cursor.fetchone()[0]
    print(f"總問題數: {question_count}")
    
    # 顯示前5個問題
    cursor.execute("""
        SELECT q.question_number, q.question_text, q.correct_answer, 
               GROUP_CONCAT(c.choice_letter || '. ' || c.choice_text, '\n') as choices
        FROM questions q
        LEFT JOIN choices c ON q.id = c.question_id
        GROUP BY q.id
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print("\n問題編號:", row[0])
        print("問題內容:", row[1])
        print("選項:\n", row[3])
        print("正確答案:", row[2])
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    check_database()

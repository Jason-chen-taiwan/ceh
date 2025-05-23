from backend.utils.db import get_db_connection
from werkzeug.security import generate_password_hash

def create_admin():
    conn = get_db_connection()
    if not conn:
        print("無法連接到資料庫")
        return
    
    try:
        cursor = conn.cursor()
        
        # 檢查是否已有管理員用戶
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            # 更新現有用戶為管理員
            cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
            print("已將現有的 admin 用戶設為管理員")
        else:
            # 創建新的管理員用戶
            hashed_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO users 
                (username, email, password, user_tier_id, is_admin, remaining_daily_questions) 
                VALUES 
                ('admin', 'admin@example.com', %s, 3, 1, 999)
            """, (hashed_password,))
            print("已創建新的管理員用戶")
            print("用戶名: admin")
            print("密碼: admin123")
        
        conn.commit()
        print("完成")
    except Exception as e:
        print(f"創建管理員用戶時發生錯誤: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    create_admin()

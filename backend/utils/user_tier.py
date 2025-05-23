import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_db_connection
import mysql.connector
from datetime import date

# 檢查並重置用戶每日題目限制
def check_and_reset_daily_limit(user_id, daily_limit):
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 檢查上次重置日期
        cursor.execute('''
            SELECT last_reset_date FROM users WHERE id = %s
        ''', (user_id,))
        result = cursor.fetchone()
        
        # 將日期轉換為字符串以進行比較
        today = date.today()
        last_reset = result['last_reset_date']
        
        # 如果不是今天，則重置每日限制
        if last_reset.strftime('%Y-%m-%d') != today.strftime('%Y-%m-%d'):
            cursor.execute('''
                UPDATE users 
                SET remaining_daily_questions = %s, last_reset_date = %s
                WHERE id = %s
            ''', (daily_limit, today, user_id))
            conn.commit()
            return True
        
        return False
    except mysql.connector.Error as e:
        print(f"Error checking daily limit: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# 獲取用戶級別信息
def get_user_tier_info(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT u.user_tier_id, u.remaining_daily_questions, t.*
            FROM users u
            JOIN user_tiers t ON u.user_tier_id = t.id
            WHERE u.id = %s
        ''', (user_id,))
        
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as e:
        print(f"Error getting user tier info: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# 更新用戶剩餘每日問題數量
def update_remaining_questions(user_id, count):
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET remaining_daily_questions = remaining_daily_questions - %s
            WHERE id = %s
        ''', (count, user_id))
        
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Error updating remaining questions: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

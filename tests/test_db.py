import sys
import os
from pathlib import Path

# 將專案根目錄加入 Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from quiz_system.src.db.db_handler import DatabaseHandler

def test_database():
    # 初始化資料庫處理器
    db = DatabaseHandler()
    
    # 1. 檢查資料庫結構完整性
    print("\n1. 檢查資料庫結構:")
    if db.check_database_integrity():
        print("✓ 資料庫結構正確")
    else:
        print("✗ 資料庫結構有問題")

    # 2. 檢查資料完整性
    print("\n2. 檢查資料完整性:")
    integrity_results = db.verify_data_integrity()
    for check, result in integrity_results.items():
        print(f"{'✓' if result else '✗'} {check}")

    # 3. 列出所有問題
    # print("\n3. 資料庫內容:")
    # questions = db.get_all_questions()
    # print(f"總共有 {len(questions)} 個問題")
    
    # # 4. 顯示詳細問題內容
    # for q in questions:
    #     print(f"\n問題 {q['id']}:")
    #     print(f"問題內容: {q['question']}")
    #     print("選項:")
    #     for letter, text in q['choices'].items():
    #         print(f"  {letter}. {text}")
    #     print(f"正確答案: {q['correct_answer']}")

if __name__ == "__main__":
    test_database()
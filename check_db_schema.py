import sqlite3

def check_db_schema(db_path='quiz_database.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Database Tables:")
    print("---------------")
    
    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue
            
        print(f"\nTable: {table_name}")
        print("Schema:")
        
        # Get schema for each table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
            
        # Show sample data
        print("\nSample Data:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")
    
    # Check for empty choices and missing options
    print("\nChecking for problems in choices:")
    print("--------------------------------")
    
    # Get all questions and their choices
    cursor.execute("""
        SELECT q.id, q.question_text, GROUP_CONCAT(c.choice_letter)
        FROM questions q
        LEFT JOIN choices c ON q.id = c.question_id
        GROUP BY q.id
    """)
    questions = cursor.fetchall()
    
    # Check each question's choices
    for q_id, q_text, choices in questions:
        # Check for empty choice_text
        cursor.execute("""
            SELECT question_id, choice_letter 
            FROM choices 
            WHERE question_id = ? AND (choice_text IS NULL OR trim(choice_text) = '')
        """, (q_id,))
        empty_choices = cursor.fetchall()
        
        if empty_choices:
            print(f"\nQuestion {q_id} has empty choices:")
            for _, letter in empty_choices:
                print(f"  Option {letter} is empty")
        
        # Check for missing ABCD options
        if choices:
            choice_letters = set(choices.split(','))
            missing = set('ABCD') - choice_letters
            if missing:
                print(f"\nQuestion {q_id} is missing options: {', '.join(sorted(missing))}")
    
    conn.close()

if __name__ == "__main__":
    check_db_schema()

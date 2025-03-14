CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    correct_answer INTEGER NOT NULL
);

-- 插入測試數據
INSERT INTO questions (question_text, option1, option2, option3, option4, correct_answer)
VALUES 
('What is CEH?', 
'Certified Ethical Hacker', 
'Computer Engineering Hardware', 
'Cyber Security Expert Helper', 
'Computer Emergency Handler', 
1);

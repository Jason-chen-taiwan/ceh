from PyPDF2 import PdfReader
import re

def clean_text(text):
    # 更新pattern以更好地匹配頁碼和標題文字
    patterns = [
        r'\d+\s*IT Certification Guaranteed,\s*The Easy Way!\s*',  # 完整標題
        r'IT Certification Guaranteed,\s*The Easy Way!\s*',        # 只有標題
        r'(?<=\s)\d+(?=\s|$)',                                    # 單獨的頁碼
    ]
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    return ' '.join(cleaned_text.split())

def extract_questions_and_answers(pdf_path):
    questions_and_answers = []
    reader = PdfReader(pdf_path)
    
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # 添加原始文本樣本輸出以供診斷
    print("Raw text sample:")
    print(full_text[:500])
    
    # 修改問題匹配模式，使其更寬鬆
    questions = re.finditer(r'QUESTION\s*NO:?\s*(\d+|[A-Z])\s*(.*?)(?=(?:QUESTION\s*NO:|$))', 
                          full_text, 
                          re.DOTALL | re.IGNORECASE)
    
    count = 0
    for q in questions:
        count += 1
        question_number = q.group(1)
        # 如果問題編號不是數字，跳過
        if not question_number.isdigit():
            continue
            
        question_dict = {
            'question_number': int(question_number),
            'full_text': clean_text(q.group(2).strip()),
            'choices': [],
            'question_text': ''
        }
        
        # 輸出每個問題的原始文本以供診斷
        if count < 3:  # 只輸出前幾個問題作為樣本
            print(f"\nRaw question {question_number}:")
            print(question_dict['full_text'][:200])
        
        # 在處理full_text之前先移除Explanation部分
        full_text = re.split(r'Explanation:', question_dict['full_text'])[0].strip()
        question_dict['full_text'] = full_text
        
        # 提取題目文字（在第一個選項之前的所有文字）
        full_text = question_dict['full_text']
        try:
            # 先嘗試找到第一個選項的位置
            first_choice_match = re.search(r'[A-E]\.', full_text)
            if (first_choice_match):
                question_end = first_choice_match.start()
                question_dict['question_text'] = clean_text(full_text[:question_end].strip())
            else:
                # 如果找不到選項，整個文字可能就是問題
                question_dict['question_text'] = clean_text(full_text)
        except Exception as e:
            print(f"Error processing question {question_dict['question_number']}: {str(e)}")
            question_dict['question_text'] = "Error extracting question text"
        
        # 提取選項
        choices_text = question_dict['full_text']
        # 使用簡單的選項匹配模式
        choices = re.finditer(r'([A-D])\.\s*(.*?)(?=(?:[A-D]\.|Answer:|Explanation:|$))', 
                            choices_text, 
                            re.DOTALL)
        
        for choice in choices:
            choice_letter = choice.group(1)
            choice_text = clean_text(choice.group(2).strip())
            question_dict['choices'].append({
                'choice_letter': choice_letter,
                'choice_text': choice_text
            })
        
        # 提取答案（只處理單選題）
        answer_match = re.search(r'Answer:\s*([A-D])\s*(?:$|Explanation:)', 
                               question_dict['full_text'])
        
        # 如果是單選題才加入結果
        if answer_match and len(question_dict['choices']) == 4:
            question_dict['correct_answer'] = answer_match.group(1)
            # 移除不需要的 full_text 字段
            del question_dict['full_text']
            questions_and_answers.append(question_dict)
    
    # 改進診斷信息
    print(f"\nProcessing summary:")
    print(f"Total questions processed: {count}")
    if count == 0:
        print("Warning: No questions were found in the PDF!")
        print("This might be due to:")
        print("1. Unexpected question format")
        print("2. PDF text extraction issues")
        print("3. Encoding problems")
        print(f"\nFirst 200 characters of cleaned text:")
        print(clean_text(full_text)[:200])
    
    return questions_and_answers

if __name__ == "__main__":
    from pathlib import Path
    import sys
    
    # 添加父目錄到系統路徑
    sys.path.append(str(Path(__file__).parent.parent))
    
    from db.db_handler import DatabaseHandler
    
    pdf_path = r'/Users/chenyanxiang/ceh/312-50v12 V12.95_2023.pdf'
    print("Starting PDF processing...")
    print(f"Reading file: {pdf_path}")
    
    qa_list = extract_questions_and_answers(pdf_path)
    
    print(f"\nTotal questions extracted: {len(qa_list)}")
    
    # 初始化資料庫處理器
    try:
        db_handler = DatabaseHandler()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        sys.exit(1)
    
    # 將問題寫入資料庫
    try:
        db_handler.insert_questions(qa_list)
        print(f"Successfully inserted {len(qa_list)} questions into the database.")
    except Exception as e:
        print(f"Error inserting questions into database: {str(e)}")
        sys.exit(1)
    
    for qa in qa_list:
        print(f"\nQuestion {qa['question_number']}:")
        try:
            print(f"Question text: {qa['question_text']}")
            print("Choices:")
            for choice in qa['choices']:
                print(f"{choice['choice_letter']}. {choice['choice_text']}")
            if 'correct_answer' in qa:
                print(f"Correct Answer: {qa['correct_answer']}")
        except Exception as e:
            print(f"Error displaying question: {str(e)}")
        print("-" * 50)
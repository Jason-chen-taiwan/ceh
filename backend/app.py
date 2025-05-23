from flask import Flask, jsonify
from flask_cors import CORS
import secrets
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Blueprints
from routes.user import user_bp
from routes.questions import questions_bp
from routes.views import views_bp
from routes.cors import cors_bp
from routes.session import session_bp
from routes.admin import admin_bp

# Import utilities
from utils.db import init_db
from utils.auth import add_cors_headers

app = Flask(__name__, 
    template_folder='../frontend/templates',  # 指定模板目錄
    static_folder='../frontend/static'        # 指定靜態檔案目錄
)

# 設置密鑰用於會話加密
app.secret_key = secrets.token_hex(16)

# 設置會話的cookie選項，增強安全性
app.config['SESSION_COOKIE_SECURE'] = False  # 在生產環境中應該設為True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = None  # 允許跨站點 cookie
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 設置會話有效期為1天（秒）

# 允許所有來源的 CORS 請求
CORS(app, 
     supports_credentials=True,
     resources={r"/api/*": {"origins": "http://localhost:5000"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"]
)

# Register Blueprints
app.register_blueprint(user_bp)
app.register_blueprint(questions_bp)
app.register_blueprint(views_bp)
app.register_blueprint(cors_bp)
app.register_blueprint(session_bp)
app.register_blueprint(admin_bp)

# 確保所有回應都添加 CORS 標頭
@app.after_request
def after_request(response):
    return add_cors_headers(response)

# API endpoint for database test (kept in app.py for simplicity)
@app.route('/api/test')
def test_db():
    from utils.db import get_db_connection
    import mysql.connector
    
    try:
        conn = get_db_connection()
        if not conn:
            return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        result = cursor.fetchone()
        count = result['count']
        
        cursor.close()
        conn.close()
        return add_cors_headers(jsonify({"status": "success", "question_count": count}))
    except Exception as e:
        return add_cors_headers(jsonify({"status": "error", "message": str(e)})), 500

if __name__ == '__main__':
    # 初始化資料庫
    init_db()
    
    app.run(debug=True)

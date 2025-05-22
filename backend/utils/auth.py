from flask import session, request, redirect, url_for, jsonify
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # 如果是API請求，返回JSON回應
            if request.path.startswith('/api/'):
                return add_cors_headers(jsonify({
                    'error': 'Login required',
                    'status': 'unauthenticated',
                    'redirect': '/login'
                })), 401
            # 如果是前端頁面請求，重定向到登入頁面
            else:
                return redirect(url_for('views.login_page', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def add_cors_headers(response):
    origin = request.headers.get('Origin', 'http://localhost:5000')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'  # 允許憑證
    # 為了解決預檢請求（CORS preflight）問題，設置最大緩存時間
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

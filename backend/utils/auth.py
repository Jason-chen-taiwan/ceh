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

# 管理員權限驗證裝飾器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('is_admin', 0) != 1:
            # 檢查是否是API請求
            if request.path.startswith('/api/'):
                return add_cors_headers(jsonify({
                    'error': 'Admin access required',
                    'status': 'forbidden',
                    'redirect': '/dashboard'
                })), 403
            else:
                # 如果是網頁請求，則重定向到儀表板
                return redirect(url_for('views.dashboard_page'))
        return f(*args, **kwargs)
    return decorated_function

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

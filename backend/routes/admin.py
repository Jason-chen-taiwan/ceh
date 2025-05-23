from flask import Blueprint, jsonify, request, session, render_template
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_db_connection
from utils.auth import login_required, admin_required, add_cors_headers
import mysql.connector

admin_bp = Blueprint('admin', __name__, 
                    template_folder='../../frontend/templates',
                    static_folder='../../frontend/static')

@admin_bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def admin_users():
    return render_template('admin_users.html')

@admin_bp.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.created_at, 
                   u.user_tier_id, t.tier_name
            FROM users u
            JOIN user_tiers t ON u.user_tier_id = t.id
            ORDER BY u.id
        ''')
        users = cursor.fetchall()
        
        return add_cors_headers(jsonify(users))
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@admin_bp.route('/api/admin/user-tiers', methods=['GET'])
@login_required
@admin_required
def get_user_tiers():
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_tiers ORDER BY id')
        tiers = cursor.fetchall()
        
        return add_cors_headers(jsonify(tiers))
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

@admin_bp.route('/api/admin/users/<int:user_id>/tier', methods=['PUT'])
@login_required
@admin_required
def update_user_tier(user_id):
    data = request.json
    tier_id = data.get('tier_id')
    
    if not tier_id:
        return add_cors_headers(jsonify({'error': 'Missing tier_id'})), 400
    
    conn = get_db_connection()
    if not conn:
        return add_cors_headers(jsonify({'error': 'Database connection failed'})), 500
    
    try:
        cursor = conn.cursor()
        
        # 檢查用戶是否存在
        cursor.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if cursor.fetchone() is None:
            return add_cors_headers(jsonify({'error': 'User not found'})), 404
        
        # 檢查級別是否存在
        cursor.execute('SELECT id FROM user_tiers WHERE id = %s', (tier_id,))
        if cursor.fetchone() is None:
            return add_cors_headers(jsonify({'error': 'Tier not found'})), 404
        
        # 更新用戶級別
        cursor.execute('''
            UPDATE users 
            SET user_tier_id = %s
            WHERE id = %s
        ''', (tier_id, user_id))
        
        conn.commit()
        
        # 獲取更新後的用戶級別信息
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.user_tier_id, t.tier_name
            FROM users u
            JOIN user_tiers t ON u.user_tier_id = t.id
            WHERE u.id = %s
        ''', (user_id,))
        user = cursor.fetchone()
        
        return add_cors_headers(jsonify({
            'message': 'User tier updated successfully',
            'user': user
        }))
    except mysql.connector.Error as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

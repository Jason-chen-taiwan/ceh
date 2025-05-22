from flask import Blueprint, render_template, session, redirect, url_for
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.auth import login_required

views_bp = Blueprint('views', __name__, 
                    template_folder='../../frontend/templates',
                    static_folder='../../frontend/static')

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/quiz')
@login_required
def quiz():
    return render_template('quiz.html')

@views_bp.route('/login')
def login_page():
    return render_template('login.html')

@views_bp.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('user_dashboard.html')

@views_bp.route('/register')
def register_page():
    return render_template('login.html', register=True)

@views_bp.route('/contact')
def contact_page():
    return render_template('contact.html')

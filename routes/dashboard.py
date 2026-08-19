from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee, Payroll, User
from datetime import datetime
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin' and current_user.role != 'hr':
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal"""
    total_employees = Employee.query.filter_by(is_active=True).count()
    total_payrolls = Payroll.query.count()
    
    # Últimas nóminas
    recent_payrolls = Payroll.query.order_by(Payroll.created_at.desc()).limit(5).all()
    
    # Datos para gráficos
    total_salary_cost = db.session.query(db.func.sum(Employee.base_salary)).filter_by(is_active=True).scalar() or 0
    
    context = {
        'total_employees': total_employees,
        'total_payrolls': total_payrolls,
        'recent_payrolls': recent_payrolls,
        'total_salary_cost': total_salary_cost,
    }
    
    return render_template('dashboard.html', **context)

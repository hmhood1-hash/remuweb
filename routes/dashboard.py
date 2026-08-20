from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Employee, Payroll, VacationRequest, Loan, Settlement
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'hr']:
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
    total_salary_cost = db.session.query(db.func.sum(Employee.base_salary)).filter_by(is_active=True).scalar() or 0
    pending_vacations = VacationRequest.query.filter_by(status='pending').count()
    active_loans = Loan.query.filter_by(status='active').count()
    recent_settlements = Settlement.query.order_by(Settlement.created_at.desc()).limit(5).all()
    recent_payrolls = Payroll.query.order_by(Payroll.created_at.desc()).limit(5).all()
    employees_on_leave = Employee.query.filter_by(status='leave').count()
    processed_payrolls = Payroll.query.filter_by(status='processed').count()

    context = {
        'total_employees': total_employees,
        'total_payrolls': total_payrolls,
        'total_salary_cost': total_salary_cost,
        'pending_vacations': pending_vacations,
        'active_loans': active_loans,
        'recent_settlements': recent_settlements,
        'recent_payrolls': recent_payrolls,
        'employees_on_leave': employees_on_leave,
        'processed_payrolls': processed_payrolls,
    }

    return render_template('dashboard.html', **context)

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from models import db, Employee, Payroll
from utils import generate_payroll_pdf
from datetime import datetime, timedelta
from functools import wraps

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')


def admin_or_hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'hr']:
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@payroll_bp.route('/')
@login_required
@admin_or_hr_required
def list_payrolls():
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', '', type=int)
    status = request.args.get('status', '')

    query = Payroll.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if status:
        query = query.filter_by(status=status)

    payrolls = query.order_by(Payroll.period_start.desc()).paginate(page=page, per_page=10)
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('payroll/list.html', payrolls=payrolls, employees=employees, selected_employee=employee_id, selected_status=status)


@payroll_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_or_hr_required
def create_payroll():
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id', type=int)
            employee = Employee.query.get_or_404(employee_id)

            period_start = datetime.strptime(request.form.get('period_start'), '%Y-%m-%d')
            period_end = datetime.strptime(request.form.get('period_end'), '%Y-%m-%d')

            payroll = Payroll(
                employee_id=employee_id,
                period_start=period_start,
                period_end=period_end,
                base_salary=employee.base_salary,
                overtime_hours=float(request.form.get('overtime_hours', 0) or 0),
                bonuses=float(request.form.get('bonuses', 0) or 0),
                other_discounts=float(request.form.get('other_discounts', 0) or 0),
                notes=request.form.get('notes', '')
            )

            if payroll.overtime_hours > 0:
                hourly_rate = employee.base_salary / 30 / 8
                payroll.overtime_pay = payroll.overtime_hours * hourly_rate * current_app.config['OVERTIME_MULTIPLIER']

            payroll.calculate_totals(current_app.config)
            db.session.add(payroll)
            db.session.commit()

            flash('Nómina creada exitosamente.', 'success')
            return redirect(url_for('payroll.view_payroll', payroll_id=payroll.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear nómina: {str(e)}', 'danger')

    employees = Employee.query.filter_by(is_active=True).all()
    today = datetime.now()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    return render_template(
        'payroll/form.html',
        employees=employees,
        payroll=None,
        default_start=first_day.strftime('%Y-%m-%d'),
        default_end=last_day.strftime('%Y-%m-%d')
    )


@payroll_bp.route('/<int:payroll_id>/view')
@login_required
def view_payroll(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    return render_template('payroll/view.html', payroll=payroll)


@payroll_bp.route('/<int:payroll_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_hr_required
def edit_payroll(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)

    if request.method == 'POST':
        try:
            payroll.overtime_hours = float(request.form.get('overtime_hours', 0) or 0)
            payroll.bonuses = float(request.form.get('bonuses', 0) or 0)
            payroll.other_discounts = float(request.form.get('other_discounts', 0) or 0)
            payroll.notes = request.form.get('notes', '')

            if payroll.overtime_hours > 0:
                hourly_rate = payroll.base_salary / 30 / 8
                payroll.overtime_pay = payroll.overtime_hours * hourly_rate * current_app.config['OVERTIME_MULTIPLIER']
            else:
                payroll.overtime_pay = 0

            payroll.calculate_totals(current_app.config)
            db.session.commit()
            flash('Nómina actualizada exitosamente.', 'success')
            return redirect(url_for('payroll.view_payroll', payroll_id=payroll.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar nómina: {str(e)}', 'danger')

    return render_template('payroll/form.html', payroll=payroll, employees=[payroll.employee], default_start=None, default_end=None)


@payroll_bp.route('/<int:payroll_id>/process', methods=['POST'])
@login_required
@admin_or_hr_required
def process_payroll(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    try:
        payroll.status = 'processed'
        payroll.processed_at = datetime.utcnow()
        db.session.commit()
        flash('Nómina procesada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar nómina: {str(e)}', 'danger')

    return redirect(url_for('payroll.view_payroll', payroll_id=payroll.id))


@payroll_bp.route('/<int:payroll_id>/pdf')
@login_required
def download_payroll_pdf(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    if current_user.role == 'employee' and current_user.employee_id != payroll.employee_id:
        flash('No tienes permisos para descargar este recibo.', 'danger')
        return redirect(url_for('dashboard.index'))

    pdf_buffer = generate_payroll_pdf(payroll, payroll.employee)
    filename = f"recibo_{payroll.employee.id_number}_{payroll.period_start.strftime('%Y%m%d')}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)

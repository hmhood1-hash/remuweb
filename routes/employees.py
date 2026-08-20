from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee, SalaryHistory
from datetime import datetime
from functools import wraps

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')


def admin_or_hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['admin', 'hr']:
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def parse_date(date_string):
    if not date_string:
        return None
    return datetime.strptime(date_string, '%Y-%m-%d')


def apply_employee_form_data(employee):
    employee.first_name = request.form.get('first_name')
    employee.last_name = request.form.get('last_name')
    employee.email = request.form.get('email')
    employee.phone = request.form.get('phone')
    employee.id_number = request.form.get('id_number')
    employee.position = request.form.get('position')
    employee.department = request.form.get('department')
    employee.base_salary = float(request.form.get('base_salary', 0) or 0)
    employee.hire_date = parse_date(request.form.get('hire_date')) or employee.hire_date or datetime.utcnow()
    employee.birth_date = parse_date(request.form.get('birth_date'))
    employee.status = request.form.get('status', 'active')
    employee.address = request.form.get('address')
    employee.afp_provider = request.form.get('afp_provider')
    employee.health_provider = request.form.get('health_provider')
    employee.bank_name = request.form.get('bank_name')
    employee.bank_account = request.form.get('bank_account')
    employee.bank_account_type = request.form.get('bank_account_type')
    employee.emergency_contact_name = request.form.get('emergency_contact_name')
    employee.emergency_contact_phone = request.form.get('emergency_contact_phone')
    employee.notes = request.form.get('notes')
    employee.is_active = request.form.get('is_active') == 'on'
    if employee.status == 'terminated':
        employee.is_active = False
    employee.updated_at = datetime.utcnow()


@employees_bp.route('/')
@login_required
@admin_or_hr_required
def list_employees():
    """Listar empleados"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Employee.query

    if search:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.email.ilike(f'%{search}%'),
                Employee.id_number.ilike(f'%{search}%')
            )
        )

    employees = query.order_by(Employee.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('employees/list.html', employees=employees, search=search)


@employees_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_or_hr_required
def create_employee():
    """Crear nuevo empleado"""
    if request.method == 'POST':
        try:
            employee = Employee(hire_date=datetime.utcnow())
            apply_employee_form_data(employee)
            db.session.add(employee)
            db.session.commit()
            flash('Empleado creado exitosamente.', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear empleado: {str(e)}', 'danger')

    return render_template('employees/form.html', employee=None)


@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_hr_required
def edit_employee(employee_id):
    """Editar empleado"""
    employee = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        try:
            previous_salary = employee.base_salary
            apply_employee_form_data(employee)

            if previous_salary != employee.base_salary:
                history = SalaryHistory(
                    employee_id=employee.id,
                    old_salary=previous_salary,
                    new_salary=employee.base_salary,
                    reason=request.form.get('salary_change_reason') or 'Actualización manual de salario',
                    changed_by=current_user.id
                )
                db.session.add(history)

            db.session.commit()
            flash('Empleado actualizado exitosamente.', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar empleado: {str(e)}', 'danger')

    return render_template('employees/form.html', employee=employee)


@employees_bp.route('/<int:employee_id>/view')
@login_required
def view_employee(employee_id):
    """Ver detalles del empleado"""
    employee = Employee.query.get_or_404(employee_id)
    payrolls = sorted(employee.payrolls, key=lambda payroll: payroll.period_start, reverse=True)
    return render_template('employees/view.html', employee=employee, payrolls=payrolls)


@employees_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
@admin_or_hr_required
def delete_employee(employee_id):
    """Eliminar empleado"""
    employee = Employee.query.get_or_404(employee_id)

    try:
        employee.is_active = False
        employee.status = 'terminated'
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Empleado eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'danger')

    return redirect(url_for('employees.list_employees'))

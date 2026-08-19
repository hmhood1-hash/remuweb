from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee
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
    
    employees = query.paginate(page=page, per_page=10)
    
    return render_template('employees/list.html', employees=employees, search=search)

@employees_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_or_hr_required
def create_employee():
    """Crear nuevo empleado"""
    if request.method == 'POST':
        try:
            employee = Employee(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                id_number=request.form.get('id_number'),
                position=request.form.get('position'),
                department=request.form.get('department'),
                base_salary=float(request.form.get('base_salary', 0)),
            )
            
            db.session.add(employee)
            db.session.commit()
            flash('Empleado creado exitosamente.', 'success')
            return redirect(url_for('employees.list_employees'))
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
            employee.first_name = request.form.get('first_name')
            employee.last_name = request.form.get('last_name')
            employee.email = request.form.get('email')
            employee.phone = request.form.get('phone')
            employee.id_number = request.form.get('id_number')
            employee.position = request.form.get('position')
            employee.department = request.form.get('department')
            employee.base_salary = float(request.form.get('base_salary', 0))
            employee.is_active = request.form.get('is_active') == 'on'
            employee.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Empleado actualizado exitosamente.', 'success')
            return redirect(url_for('employees.list_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar empleado: {str(e)}', 'danger')
    
    return render_template('employees/form.html', employee=employee)

@employees_bp.route('/<int:employee_id>/view')
@login_required
def view_employee(employee_id):
    """Ver detalles del empleado"""
    employee = Employee.query.get_or_404(employee_id)
    payrolls = employee.payrolls
    return render_template('employees/view.html', employee=employee, payrolls=payrolls)

@employees_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
@admin_or_hr_required
def delete_employee(employee_id):
    """Eliminar empleado"""
    employee = Employee.query.get_or_404(employee_id)
    
    try:
        # Soft delete - marcar como inactivo
        employee.is_active = False
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Empleado eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'danger')
    
    return redirect(url_for('employees.list_employees'))

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils import log_audit
from models import db, Employee, VacationRequest, AuditLog
from datetime import datetime

vacations_bp = Blueprint('vacations', __name__, url_prefix='/vacations')




@vacations_bp.route('/')
@login_required
def list_vacations():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = VacationRequest.query

    if current_user.role == 'employee' and current_user.employee_id:
        query = query.filter_by(employee_id=current_user.employee_id)

    if status:
        query = query.filter_by(status=status)

    vacations = query.order_by(VacationRequest.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('vacations/list.html', vacations=vacations, selected_status=status)


@vacations_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_vacation():
    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            days = (end_date - start_date).days + 1
            employee_id = request.form.get('employee_id', type=int) or current_user.employee_id

            if days <= 0:
                raise ValueError('La fecha de término debe ser posterior o igual a la fecha de inicio.')

            vac = VacationRequest(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                days_requested=days,
                reason=request.form.get('reason', '')
            )
            db.session.add(vac)
            db.session.flush()
            log_audit(db, current_user, 'create', 'vacation', vac.id, f'Solicitud de vacaciones creada para empleado {employee_id}')
            db.session.commit()
            flash('Solicitud de vacaciones creada exitosamente.', 'success')
            return redirect(url_for('vacations.list_vacations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    employees = Employee.query.filter_by(is_active=True).order_by(Employee.first_name.asc()).all() if current_user.role in ['admin', 'hr'] else []
    return render_template('vacations/form.html', employees=employees)


@vacations_bp.route('/<int:vac_id>/approve', methods=['POST'])
@login_required
def approve_vacation(vac_id):
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('vacations.list_vacations'))

    vac = VacationRequest.query.get_or_404(vac_id)
    vac.status = 'approved'
    vac.approved_by = current_user.id
    vac.approved_at = datetime.utcnow()
    vac.rejection_reason = None
    log_audit(db, current_user, 'update', 'vacation', vac_id, 'Vacaciones aprobadas')
    db.session.commit()
    flash('Vacaciones aprobadas.', 'success')
    return redirect(url_for('vacations.list_vacations'))


@vacations_bp.route('/<int:vac_id>/reject', methods=['POST'])
@login_required
def reject_vacation(vac_id):
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('vacations.list_vacations'))

    vac = VacationRequest.query.get_or_404(vac_id)
    vac.status = 'rejected'
    vac.rejection_reason = request.form.get('rejection_reason', '')
    vac.approved_by = current_user.id
    vac.approved_at = datetime.utcnow()
    log_audit(db, current_user, 'update', 'vacation', vac_id, 'Vacaciones rechazadas')
    db.session.commit()
    flash('Vacaciones rechazadas.', 'success')
    return redirect(url_for('vacations.list_vacations'))

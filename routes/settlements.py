from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils import log_audit
from models import db, Employee, Settlement, AuditLog
from datetime import datetime

settlements_bp = Blueprint('settlements', __name__, url_prefix='/settlements')




@settlements_bp.route('/')
@login_required
def list_settlements():
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    settlements = Settlement.query.order_by(Settlement.created_at.desc()).all()
    return render_template('settlements/list.html', settlements=settlements)


@settlements_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_settlement():
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id', type=int)
            employee = Employee.query.get_or_404(employee_id)
            termination_date = datetime.strptime(request.form.get('termination_date'), '%Y-%m-%d')

            hire_date = employee.hire_date or termination_date
            years = max((termination_date - hire_date).days / 365.25, 0)

            reason = request.form.get('termination_reason', '')
            last_salary = employee.base_salary

            severance = 0
            if reason == 'despido_injustificado':
                severance = last_salary * min(years, 11)

            vac_days = (years % 1) * 15
            vac_payment = (last_salary / 30) * vac_days
            months_in_year = ((termination_date.month - 1) + (termination_date.day / 30))
            prop_bonus = last_salary * 0.25 * months_in_year / 12

            total_gross = severance + vac_payment + prop_bonus
            total_discounts = total_gross * 0.12
            total_net = total_gross - total_discounts

            settlement = Settlement(
                employee_id=employee_id,
                termination_date=termination_date,
                termination_reason=reason,
                last_salary=last_salary,
                years_of_service=round(years, 2),
                severance_pay=round(severance, 2),
                vacation_days_pending=round(vac_days, 2),
                vacation_payment=round(vac_payment, 2),
                proportional_bonus=round(prop_bonus, 2),
                total_gross=round(total_gross, 2),
                total_discounts=round(total_discounts, 2),
                total_net=round(total_net, 2),
                notes=request.form.get('notes', ''),
                created_by=current_user.id
            )
            employee.status = 'terminated'
            employee.is_active = False
            db.session.add(settlement)
            db.session.flush()
            log_audit(db, current_user, 'create', 'settlement', settlement.id, f'Finiquito creado para empleado {employee_id}')
            db.session.commit()
            flash('Finiquito calculado exitosamente.', 'success')
            return redirect(url_for('settlements.view_settlement', settlement_id=settlement.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    employees = Employee.query.filter_by(is_active=True).order_by(Employee.first_name.asc()).all()
    return render_template('settlements/form.html', employees=employees)


@settlements_bp.route('/<int:settlement_id>')
@login_required
def view_settlement(settlement_id):
    settlement = Settlement.query.get_or_404(settlement_id)
    return render_template('settlements/view.html', settlement=settlement)

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils import log_audit
from models import db, Employee, Loan, AuditLog

loans_bp = Blueprint('loans', __name__, url_prefix='/loans')




@loans_bp.route('/')
@login_required
def list_loans():
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    page = request.args.get('page', 1, type=int)
    loans = Loan.query.order_by(Loan.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('loans/list.html', loans=loans)


@loans_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_loan():
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0) or 0)
            total_installments = int(request.form.get('total_installments', 1) or 1)
            monthly_installment = amount / total_installments
            loan = Loan(
                employee_id=request.form.get('employee_id', type=int),
                amount=amount,
                monthly_installment=monthly_installment,
                total_installments=total_installments,
                remaining_balance=amount,
                purpose=request.form.get('purpose', ''),
                approved_by=current_user.id
            )
            db.session.add(loan)
            db.session.flush()
            log_audit(db, current_user, 'create', 'loan', loan.id, f'Préstamo creado: ${amount:.0f}')
            db.session.commit()
            flash('Préstamo creado exitosamente.', 'success')
            return redirect(url_for('loans.list_loans'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    employees = Employee.query.filter_by(is_active=True).order_by(Employee.first_name.asc()).all()
    return render_template('loans/form.html', employees=employees)


@loans_bp.route('/<int:loan_id>/pay', methods=['POST'])
@login_required
def pay_installment(loan_id):
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    loan = Loan.query.get_or_404(loan_id)
    if loan.status != 'active':
        flash('El préstamo no está activo.', 'warning')
        return redirect(url_for('loans.list_loans'))

    loan.paid_installments += 1
    loan.remaining_balance = max((loan.remaining_balance or 0) - loan.monthly_installment, 0)
    if loan.paid_installments >= loan.total_installments or loan.remaining_balance <= 0:
        loan.status = 'paid'
        loan.remaining_balance = 0
    log_audit(db, current_user, 'update', 'loan', loan_id, 'Cuota pagada')
    db.session.commit()
    flash('Cuota registrada.', 'success')
    return redirect(url_for('loans.list_loans'))

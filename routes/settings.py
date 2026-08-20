from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.role not in ['admin', 'hr']:
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            current_app.config['DISCOUNT_INCOME_TAX'] = float(request.form.get('discount_income_tax', current_app.config['DISCOUNT_INCOME_TAX']))
            current_app.config['DISCOUNT_AFP'] = float(request.form.get('discount_afp', current_app.config['DISCOUNT_AFP']))
            current_app.config['DISCOUNT_INSURANCE'] = float(request.form.get('discount_insurance', current_app.config['DISCOUNT_INSURANCE']))
            current_app.config['OVERTIME_MULTIPLIER'] = float(request.form.get('overtime_multiplier', current_app.config['OVERTIME_MULTIPLIER']))
            flash('Parámetros actualizados en memoria para la sesión actual.', 'success')
        except ValueError:
            flash('Revisa los valores numéricos ingresados.', 'danger')

    return render_template('settings/index.html')

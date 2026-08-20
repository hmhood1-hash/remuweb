from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')


@audit_bp.route('/')
@login_required
def list_logs():
    if current_user.role != 'admin':
        flash('Sin permisos.', 'danger')
        return redirect(url_for('dashboard.index'))

    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template('audit/list.html', logs=logs)

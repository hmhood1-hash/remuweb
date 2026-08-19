from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Employee, Payroll
from config import config
import os

app = Flask(__name__)
app.config.from_object(config['development'])

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registrar blueprints
def register_blueprints():
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.employees import employees_bp
    from routes.payroll import payroll_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(reports_bp)

@app.before_request
def before_request():
    """Antes de cada solicitud"""
    pass

@app.context_processor
def inject_user():
    """Inyecta el usuario actual en el contexto de templates"""
    return {'current_user': current_user}

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

def create_app():
    """Factory function para crear la aplicación"""
    with app.app_context():
        db.create_all()
        register_blueprints()
        
        # Crear usuario admin por defecto si no existe
        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', email='admin@payroll.local', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)

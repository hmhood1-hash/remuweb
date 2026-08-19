from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo de Usuario"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, hr, employee
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con empleado
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Employee(db.Model):
    """Modelo de Empleado"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    id_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    base_salary = db.Column(db.Float, nullable=False)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    payrolls = db.relationship('Payroll', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Employee {self.full_name}>'


class Payroll(db.Model):
    """Modelo de Nómina"""
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Valores base
    base_salary = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, default=0)
    overtime_pay = db.Column(db.Float, default=0)
    bonuses = db.Column(db.Float, default=0)
    
    # Descuentos
    income_tax = db.Column(db.Float, default=0)
    afp = db.Column(db.Float, default=0)
    insurance = db.Column(db.Float, default=0)
    other_discounts = db.Column(db.Float, default=0)
    
    # Totales
    gross_salary = db.Column(db.Float, default=0)
    total_discounts = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    
    status = db.Column(db.String(20), default='draft')  # draft, processed, paid
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def calculate_totals(self, config):
        """Calcula los totales de la nómina"""
        # Salario bruto
        self.gross_salary = self.base_salary + self.overtime_pay + self.bonuses
        
        # Descuentos automáticos
        self.income_tax = self.gross_salary * config.DISCOUNT_INCOME_TAX
        self.afp = self.gross_salary * config.DISCOUNT_AFP
        self.insurance = self.gross_salary * config.DISCOUNT_INSURANCE
        
        # Total descuentos
        self.total_discounts = self.income_tax + self.afp + self.insurance + self.other_discounts
        
        # Salario neto
        self.net_salary = self.gross_salary - self.total_discounts
    
    def __repr__(self):
        return f'<Payroll {self.employee_id} - {self.period_start.strftime("%Y-%m")}>'


class Attendance(db.Model):
    """Modelo de Asistencia"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    hours_worked = db.Column(db.Float, default=8)
    status = db.Column(db.String(20), default='present')  # present, absent, late, partial
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date.strftime("%Y-%m-%d")}>'


class PayrollTemplate(db.Model):
    """Modelo de Plantilla de Nómina (para descuentos personalizados)"""
    __tablename__ = 'payroll_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    income_tax_rate = db.Column(db.Float, default=0.10)
    afp_rate = db.Column(db.Float, default=0.10)
    insurance_rate = db.Column(db.Float, default=0.02)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PayrollTemplate {self.name}>'

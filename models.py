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
    status = db.Column(db.String(20), default='active')
    address = db.Column(db.String(200))
    birth_date = db.Column(db.DateTime)
    afp_provider = db.Column(db.String(100))
    health_provider = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(50))
    bank_account_type = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payrolls = db.relationship('Payroll', backref='employee', lazy=True, cascade='all, delete-orphan')
    salary_history = db.relationship(
        'SalaryHistory',
        backref='employee',
        lazy=True,
        cascade='all, delete-orphan',
        foreign_keys='SalaryHistory.employee_id',
        order_by='desc(SalaryHistory.change_date)'
    )

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

    base_salary = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, default=0)
    overtime_pay = db.Column(db.Float, default=0)
    bonuses = db.Column(db.Float, default=0)

    income_tax = db.Column(db.Float, default=0)
    afp = db.Column(db.Float, default=0)
    insurance = db.Column(db.Float, default=0)
    other_discounts = db.Column(db.Float, default=0)

    gross_salary = db.Column(db.Float, default=0)
    total_discounts = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)

    status = db.Column(db.String(20), default='draft')  # draft, processed, paid
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    def calculate_totals(self, config):
        """Calcula los totales de la nómina"""
        self.gross_salary = self.base_salary + self.overtime_pay + self.bonuses
        self.income_tax = self.gross_salary * config.get("DISCOUNT_INCOME_TAX", 0.10)
        self.afp = self.gross_salary * config.get("DISCOUNT_AFP", 0.10)
        self.insurance = self.gross_salary * config.get("DISCOUNT_INSURANCE", 0.02)
        self.total_discounts = self.income_tax + self.afp + self.insurance + self.other_discounts
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
        return f'<Attendance {self.employee_id} - {self.date.strftime("%Y-%m-%d")}> '


class PayrollTemplate(db.Model):
    """Modelo de Plantilla de Nómina"""
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


class SalaryHistory(db.Model):
    __tablename__ = 'salary_history'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    old_salary = db.Column(db.Float, nullable=False)
    new_salary = db.Column(db.Float, nullable=False)
    change_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(200))
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SalaryHistory {self.employee_id} {self.old_salary}->{self.new_salary}>'


class VacationRequest(db.Model):
    __tablename__ = 'vacation_requests'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref='vacation_requests', foreign_keys=[employee_id])

    def __repr__(self):
        return f'<VacationRequest {self.employee_id} {self.start_date:%Y-%m-%d}>'


class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    monthly_installment = db.Column(db.Float, nullable=False)
    total_installments = db.Column(db.Integer, nullable=False)
    paid_installments = db.Column(db.Integer, default=0)
    remaining_balance = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, paid, cancelled
    purpose = db.Column(db.String(200))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref='loans', foreign_keys=[employee_id])

    def __repr__(self):
        return f'<Loan {self.employee_id} {self.amount}>'


class Settlement(db.Model):
    __tablename__ = 'settlements'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    termination_date = db.Column(db.DateTime, nullable=False)
    termination_reason = db.Column(db.String(200))
    last_salary = db.Column(db.Float, nullable=False)
    years_of_service = db.Column(db.Float)
    severance_pay = db.Column(db.Float, default=0)
    vacation_days_pending = db.Column(db.Float, default=0)
    vacation_payment = db.Column(db.Float, default=0)
    proportional_bonus = db.Column(db.Float, default=0)
    total_gross = db.Column(db.Float, default=0)
    total_discounts = db.Column(db.Float, default=0)
    total_net = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, approved, paid
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref='settlements', foreign_keys=[employee_id])

    def __repr__(self):
        return f'<Settlement {self.employee_id} {self.total_net}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='audit_logs', foreign_keys=[user_id])

    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id}>'

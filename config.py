import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///payroll.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración de descuentos (porcentajes)
    DISCOUNT_INCOME_TAX = 0.10  # 10%
    DISCOUNT_AFP = 0.10         # 10%
    DISCOUNT_INSURANCE = 0.02   # 2%
    
    # Configuración de horas extras
    OVERTIME_MULTIPLIER = 1.5   # 1.5x el valor de la hora normal

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

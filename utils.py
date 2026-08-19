from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import locale

try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, 'C')


def generate_payroll_pdf(payroll, employee):
    """Genera un recibo de pago en PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Encabezado
    title = Paragraph("RECIBO DE PAGO - NÓMINA", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información del empleado
    info_data = [
        ['INFORMACIÓN DEL EMPLEADO', ''],
        ['Nombre:', employee.full_name],
        ['Cédula:', employee.id_number],
        ['Posición:', employee.position],
        ['Departamento:', employee.department or 'N/A'],
        ['Período:', f"{payroll.period_start.strftime('%d/%m/%Y')} - {payroll.period_end.strftime('%d/%m/%Y')}"],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Detalles de pago
    details_data = [
        ['CONCEPTO', 'CANTIDAD'],
        ['Salario Base', f"${payroll.base_salary:,.2f}"],
        ['Pago Horas Extras', f"${payroll.overtime_pay:,.2f}"],
        ['Bonificaciones', f"${payroll.bonuses:,.2f}"],
        ['', ''],
        ['SALARIO BRUTO', f"${payroll.gross_salary:,.2f}"],
    ]
    
    # Agregar descuentos
    discounts_data = [
        ['DESCUENTOS', 'CANTIDAD'],
        ['Impuesto sobre la Renta', f"${payroll.income_tax:,.2f}"],
        ['AFP (Pensión)', f"${payroll.afp:,.2f}"],
        ['Seguro', f"${payroll.insurance:,.2f}"],
        ['Otros Descuentos', f"${payroll.other_discounts:,.2f}"],
        ['TOTAL DESCUENTOS', f"${payroll.total_discounts:,.2f}"],
        ['', ''],
        ['SALARIO NETO', f"${payroll.net_salary:,.2f}"],
    ]
    
    details_table = Table(details_data, colWidths=[3*inch, 2.5*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (1, 0), 10),
        ('BACKGROUND', (0, 5), (1, 5), colors.lightblue),
        ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, 5), colors.white),
        ('GRID', (0, 0), (-1, 5), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Tabla de descuentos
    discounts_table = Table(discounts_data, colWidths=[3*inch, 2.5*inch])
    discounts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (1, 0), 10),
        ('BACKGROUND', (0, 5), (1, 5), colors.lightcoral),
        ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 7), (1, 7), colors.lightgreen),
        ('FONTNAME', (0, 7), (1, 7), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(discounts_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Pie de página
    footer_text = Paragraph(
        f"<i>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Sistema de Remuneraciones</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=1)
    )
    elements.append(footer_text)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def format_currency(value):
    """Formatea un valor como moneda"""
    return f"${value:,.2f}"


def format_date(date_obj):
    """Formatea una fecha"""
    if date_obj:
        return date_obj.strftime('%d/%m/%Y')
    return 'N/A'


def calculate_overtime_pay(hours, hourly_rate, overtime_multiplier):
    """Calcula el pago por horas extras"""
    if hours > 0:
        return hours * hourly_rate * overtime_multiplier
    return 0

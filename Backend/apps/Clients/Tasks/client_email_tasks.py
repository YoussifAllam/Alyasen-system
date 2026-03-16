from django.db.models import Sum, Q
from itertools import chain
from operator import attrgetter
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from apps.Clients.models import Client

def get_client_statement(client_id, start_date, end_date):
    client = Client.objects.get(id=client_id)
    
    # 1. حساب الرصيد الافتتاحي (ما قبل فترة البحث)
    past_invoices = ClientInvoice.objects.filter(client=client, invoice_date__lt=start_date).aggregate(Sum('invoice_total_amount'))['invoice_total_amount__sum'] or 0
    past_payments = InvoicePayment.objects.filter(client_fk=client, payment_date__lt=start_date).aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    
    opening_balance = past_invoices - past_payments

    # 2. جلب الحركات داخل الفترة المحددة
    invoices = ClientInvoice.objects.filter(client=client, invoice_date__range=[start_date, end_date])
    payments = InvoicePayment.objects.filter(client_fk=client, payment_date__range=[start_date, end_date])

    # 3. دمج القائمتين وترتيبهم حسب التاريخ
    # نقوم بإضافة خاصية type لتمييزهم في الـ Template
    for inv in invoices:
        inv.type = 'Invoice'
        inv.date = inv.invoice_date
        inv.amount = inv.invoice_total_amount
        
    for pay in payments:
        pay.type = 'Payment'
        pay.date = pay.payment_date
        pay.amount = pay.payment_amount

    # دمج وترتيب حسب التاريخ
    transactions = sorted(
        chain(invoices, payments),
        key=attrgetter('date')
    )

    # 4. حساب الرصيد التراكمي (Running Balance)
    statement_lines = []
    current_balance = opening_balance
    
    for trans in transactions:
        if trans.type == 'Invoice':
            current_balance += trans.amount
            debit = trans.amount
            credit = 0
        else: # Payment
            current_balance -= trans.amount
            debit = 0
            credit = trans.amount
            
        statement_lines.append({
            'date': trans.date,
            'type': trans.type,
            'ref': trans.invoice_number if trans.type == 'Invoice' else '-',
            'debit': debit,
            'credit': credit,
            'balance': current_balance
        })

    return {
        'client': client,
        'start_date': start_date,
        'end_date': end_date,
        'opening_balance': opening_balance,
        'transactions': statement_lines,
        'closing_balance': current_balance
    }

def generate_statement_pdf(buffer, context):
    """
    Generate PDF statement using ReportLab
    """
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"Statement of Account", styles['Title']))
    elements.append(Spacer(1, 12))

    # Client Info & Date Range
    client_info = [
        [f"Client: {context['client'].name}"],
        [f"Period: {context['start_date']} to {context['end_date']}"],
        [f"Opening Balance: {context['opening_balance']:,.2f}"]
    ]
    t_info = Table(client_info, colWidths=[400])
    t_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))

    # Transactions Table
    data = [['Date', 'Type', 'Ref', 'Debit', 'Credit', 'Balance']]
    
    for line in context['transactions']:
        data.append([
            str(line['date']),
            line['type'],
            str(line['ref']),
            f"{line['debit']:,.2f}" if line['debit'] else "-",
            f"{line['credit']:,.2f}" if line['credit'] else "-",
            f"{line['balance']:,.2f}"
        ])

    # Closing Balance Row
    data.append(['', '', 'Closing Balance', '', '', f"{context['closing_balance']:,.2f}"])

    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,-1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t)

    doc.build(elements)

def send_client_statement_email(client_id, start_date, end_date):
    """
    Generate PDF and email it to the client
    """
    # 1. Get Data
    context = get_client_statement(client_id, start_date, end_date)
    client = context['client']
    
    if not client.email:
        return {"status": "error", "message": "Client has no email address"}

    # 2. Generate PDF
    buffer = BytesIO()
    generate_statement_pdf(buffer, context)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # 3. Create Email
    subject = f"Statement of Account - {client.name}"
    body = f"""Dear {client.name},

Please find attached your statement of account for the period {start_date} to {end_date}.

Regards,
Factory System
"""
    
    email = EmailMessage(
        subject,
        body,
        settings.EMAIL_HOST_USER, # From email
        [client.email],
    )
    
    # 4. Attach PDF
    filename = f"Statement_{client.name}_{start_date}_{end_date}.pdf"
    email.attach(filename, pdf_content, 'application/pdf')
    
    # 5. Send
    try:
        email.send()
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
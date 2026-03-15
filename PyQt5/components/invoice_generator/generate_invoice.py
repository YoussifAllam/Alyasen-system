from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
import os

from arabic_reshaper import reshape
from bidi.algorithm import get_display
from pathlib import Path

from .printer import print_pdf

# from datetime import datetime
# from PyQt5.QtWidgets import QApplication, QTableWidget
# from PyQt5.QtCore import Qt
# from PyQt5.QtWidgets import QTableWidgetItem


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ArabicSalesInvoice:
    def __init__(
        self,
        company,
        email,
        phone,
        companyAddress,
        table,
        total,
        discount,
        payment,
        rest,
        client,
        clientAddress,
        invoiceNumber,
        invoice_date,
    ):

        try:
            pdfmetrics.registerFont(TTFont("Arabic", "Arial.ttf"))
            pdfmetrics.registerFont(TTFont("ArabicBold", "arialbd.ttf"))
            arabic_font = "Arabic"
            arabic_bold = "ArabicBold"
        except:  # noqa
            arabic_font = "Helvetica"
            arabic_bold = "Helvetica-Bold"

        # Modern color scheme - Based on Palemrees logo (olive green & gray)
        primary_color = HexColor("#5A6670")  # Charcoal gray (from logo text)
        secondary_color = HexColor("#8B9456")  # Olive green (from logo leaf)
        accent_color = HexColor("#6B7A3E")  # Darker olive for emphasis
        light_gray = HexColor("#F5F6F4")  # Soft warm gray
        dark_gray = HexColor("#7A8288")  # Medium gray

        logo = f"{BASE_DIR}/resources/real_logo.ico"
        save_path = f"{BASE_DIR}/invoices"

        # Create directory if it doesn't exist
        try:
            if not os.path.isdir(save_path):
                os.makedirs(save_path, exist_ok=True)

            # Verify the directory was created or exists
            if os.path.isdir(save_path):
                file = os.path.join(save_path, f"{invoiceNumber}_{client}.pdf")
            else:
                raise Exception(f"Failed to create directory: {save_path}")

        except Exception as e:  # noqa
            # return False, f"❌ Error creating directory: {e}"
            pass

        my_canvas = canvas.Canvas(file, pagesize=A4)

        def format_arabic(text):
            if text is None or text == "":
                return ""  # Return empty string instead of None
            reshaped_text = reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text

        # ==================== HEADER SECTION ====================
        # Top colored bar
        my_canvas.setFillColor(secondary_color)
        my_canvas.rect(0, 790, 595, 52, fill=1, stroke=0)

        # Company name in white
        my_canvas.setFillColor(Color(1, 1, 1))  # White
        my_canvas.setFont(arabic_bold, 26)
        my_canvas.drawRightString(555, 815, format_arabic(company))

        # Logo with white border
        try:
            if logo and os.path.exists(logo):
                my_canvas.setStrokeColor(Color(1, 1, 1))
                my_canvas.setLineWidth(2)
                my_canvas.drawImage(logo, 30, 786, width=200, height=60, mask="auto")

            else:
                my_canvas.setFillColor(light_gray)
                my_canvas.circle(54, 810, 28, fill=1, stroke=0)
                my_canvas.setFillColor(dark_gray)
                my_canvas.setFont(arabic_font, 8)
                my_canvas.drawCentredString(54, 807, "LOGO")
        except Exception as e:  # noqa
            # return False, f"Error drawing logo: {e}"
            pass

        # Reset colors
        my_canvas.setFillColor(Color(0, 0, 0))
        my_canvas.setStrokeColor(Color(0, 0, 0))

        # Company details box with light background
        my_canvas.setFillColor(light_gray)
        my_canvas.roundRect(380, 735, 191, 50, 5, fill=1, stroke=0)

        my_canvas.setFillColor(primary_color)
        my_canvas.setFont(arabic_font, 10)
        my_canvas.drawRightString(565, 770, format_arabic(companyAddress))
        my_canvas.setFont(arabic_font, 9)
        my_canvas.drawRightString(565, 755, phone)
        my_canvas.drawRightString(565, 742, email)

        # Reset fill color
        my_canvas.setFillColor(Color(0, 0, 0))

        # ==================== INVOICE TITLE ====================
        my_canvas.setFillColor(secondary_color)
        my_canvas.setFont(arabic_bold, 27)
        my_canvas.drawCentredString(297.5, 705, format_arabic("فاتورة مبيعات"))
        my_canvas.setFillColor(Color(0, 0, 0))

        # Decorative line under title
        my_canvas.setStrokeColor(secondary_color)
        my_canvas.setLineWidth(2)
        my_canvas.line(220, 700, 375, 700)
        my_canvas.setStrokeColor(Color(0, 0, 0))
        my_canvas.setLineWidth(0.5)

        # ==================== CLIENT & INVOICE INFO ====================
        # Left box - Invoice details
        my_canvas.setFillColor(light_gray)
        my_canvas.roundRect(24, 630, 180, 80, 5, fill=1, stroke=0)

        my_canvas.setFillColor(primary_color)
        my_canvas.setFont(arabic_bold, 10)
        my_canvas.drawString(35, 672, format_arabic("رقم الفاتورة:"))
        my_canvas.setFont(arabic_font, 10)
        my_canvas.drawString(35, 657, invoiceNumber)

        my_canvas.setFont(arabic_bold, 10)
        my_canvas.drawString(35, 642, format_arabic("التاريخ:"))
        my_canvas.setFont(arabic_font, 10)
        my_canvas.drawString(35, 627, invoice_date)

        # Right box - Client details (larger to fit address)
        my_canvas.setFillColor(light_gray)
        my_canvas.roundRect(391, 630, 180, 60, 5, fill=1, stroke=0)

        my_canvas.setFillColor(primary_color)
        my_canvas.setFont(arabic_bold, 10)
        my_canvas.drawRightString(565, 672, format_arabic("العميل:"))
        my_canvas.setFont(arabic_font, 10)
        my_canvas.drawRightString(565, 657, format_arabic(client))

        my_canvas.setFont(arabic_bold, 10)
        my_canvas.drawRightString(565, 642, format_arabic("العنوان:"))

        # Client Address - positioned inside the box
        my_canvas.setFont(arabic_font, 8)
        mystyle = ParagraphStyle(
            "my style", fontName=arabic_font, fontSize=8, leading=10, alignment=2, textColor=primary_color
        )
        p1 = Paragraph(format_arabic(clientAddress), mystyle)
        p1.wrapOn(my_canvas, 165, 30)
        p1.drawOn(my_canvas, 398, 622)

        my_canvas.setFillColor(Color(0, 0, 0))

        # ==================== TABLE SECTION ====================
        # Table header with gradient effect
        my_canvas.setFillColor(primary_color)
        my_canvas.rect(24, 590, 547, 25, fill=1, stroke=0)

        my_canvas.setFillColor(Color(1, 1, 1))
        my_canvas.setFont(arabic_bold, 14)
        my_canvas.drawCentredString(520, 598, format_arabic("رقم المنتج"))
        my_canvas.drawCentredString(410, 598, format_arabic("المنتج"))
        my_canvas.drawCentredString(290, 598, format_arabic("الكمية"))
        my_canvas.drawCentredString(180, 598, format_arabic("الوحدة"))
        # my_canvas.drawCentredString(70, 598, format_arabic("الأجمالي"))

        my_canvas.setFillColor(Color(0, 0, 0))
        my_canvas.setFont(arabic_font, 12)

        line_y = 590
        row = table.rowCount()
        alternate = True

        for i in range(row):
            if line_y <= 80:
                # New page
                my_canvas.showPage()
                my_canvas.setFont(arabic_font, 12)
                line_y = 800
                alternate = True

            # Alternate row colors
            if alternate:
                my_canvas.setFillColor(HexColor("#F8F9FA"))
                my_canvas.rect(24, line_y - 18, 547, 18, fill=1, stroke=0)

            my_canvas.setFillColor(Color(0, 0, 0))
            line_y = line_y - 13

            # Draw items with better spacing
            my_canvas.drawCentredString(520, line_y, table.item(i, 0).text())
            my_canvas.drawCentredString(410, line_y, format_arabic(table.item(i, 1).text()))
            my_canvas.drawCentredString(290, line_y, table.item(i, 2).text())
            my_canvas.drawCentredString(180, line_y, format_arabic(table.item(i, 3).text()))
            # my_canvas.drawCentredString(70, line_y, table.item(i, 4).text())

            line_y = line_y - 5
            alternate = not alternate

        # Table bottom border
        my_canvas.setStrokeColor(primary_color)
        my_canvas.setLineWidth(1)
        my_canvas.line(24, line_y, 571, line_y)
        my_canvas.setStrokeColor(Color(0, 0, 0))
        my_canvas.setLineWidth(0.5)

        if line_y <= 100:
            my_canvas.showPage()
            line_y = 800

        # ==================== TOTALS SECTION ====================
        line_y = line_y - 30

        # Totals box with border
        my_canvas.setStrokeColor(primary_color)
        my_canvas.setLineWidth(1.5)
        my_canvas.roundRect(370, line_y - 75, 201, 85, 5, fill=0, stroke=1)

        # Individual total rows
        my_canvas.setFont(arabic_bold, 11)
        my_canvas.setFillColor(primary_color)

        my_canvas.drawRightString(560, line_y - 10, format_arabic("المجموع:"))
        my_canvas.drawRightString(560, line_y - 30, format_arabic("الخصم:"))
        my_canvas.drawRightString(560, line_y - 50, format_arabic("المدفوع:"))

        # Final amount in accent color
        my_canvas.setFillColor(accent_color)
        my_canvas.setFont(arabic_bold, 12)
        my_canvas.drawRightString(560, line_y - 70, format_arabic("الباقي:"))

        # Values
        my_canvas.setFillColor(Color(0, 0, 0))
        my_canvas.setFont(arabic_font, 11)
        my_canvas.drawString(380, line_y - 10, total)
        my_canvas.drawString(380, line_y - 30, discount)
        my_canvas.drawString(380, line_y - 50, payment)

        my_canvas.setFillColor(accent_color)
        my_canvas.setFont(arabic_bold, 12)
        my_canvas.drawString(380, line_y - 70, rest)

        # ==================== FOOTER ====================
        my_canvas.setFillColor(dark_gray)
        my_canvas.setFont(arabic_font, 8)
        footer_text = format_arabic("شكراً لتعاملكم معنا")
        my_canvas.drawCentredString(297.5, 40, footer_text)

        my_canvas.save()
        print_pdf(file)


# def create_sample_invoice():
#     """Create a sample Arabic invoice with custom save path"""
#     app = QApplication([])  # noqa

#     # Create a sample table with Arabic product names
#     table = QTableWidget(5, 5)
#     sample_data = [
#         ["001", "جهاز كمبيوتر محمول", "1", "1200.00", "1200.00"],
#         ["002", "فأرة لاسلكية", "2", "25.00", "50.00"],
#         ["003", "لوحة مفاتيح", "1", "75.00", "75.00"],
#         ["004", "شاشة عرض", "1", "300.00", "300.00"],
#         ["005", "طابعة ليزر", "1", "450.00", "450.00"],
#     ]

#     for row, row_data in enumerate(sample_data):
#         for col, value in enumerate(row_data):
#             item = QTableWidgetItem(value)
#             item.setTextAlignment(Qt.AlignCenter)
#             table.setItem(row, col, item)

#     # Create the invoice with Arabic text
#     invoice_params = {
#         "company": "شركة الحلول التقنية",
#         "email": "sales@techsolutions.com",
#         "phone": "+1 (555) 123-4567",
#         "companyAddress": "123 حديقة التكنولوجيا، وادي السيليكون",
#         "table": table,
#         "total": "2075.00",
#         "discount": "75.00",
#         "payment": "1500.00",
#         "rest": "500.00",
#         "client": "الشركات العالمية المحدودة",
#         "clientAddress": "456 المنطقة التجارية، نيويورك، الولايات المتحدة",
#         "invoiceNumber": "INV-2024-001",
#         "invoice_date": "2024-01-01",
#     }

#     invoice = ArabicSalesInvoice(**invoice_params)  # noqa

#     # Check if file was created
#     expected_path = f"{BASE_DIR}/invoices/{invoice_params['invoiceNumber']}_{invoice_params['client']}.pdf"
#     if os.path.exists(expected_path):
#         print("🎉 تم إنشاء الفاتورة بنجاح!")
#         print(f"📄 الملف: {expected_path}")
#     else:
#         print("❌ حدث خطأ في إنشاء الفاتورة")


# if __name__ == "__main__":
#     create_sample_invoice()

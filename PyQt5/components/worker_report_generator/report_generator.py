from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
from datetime import datetime

from ..invoice_generator.generate_invoice import print_pdf

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ArabicSalaryReport:
    def __init__(self):
        self.logo_path = f"{BASE_DIR}/resources/real_logo.png"
        self.save_path = f"{BASE_DIR}/invoices"
        self.setup_arabic_font()

    def setup_arabic_font(self):
        """Setup Arabic font"""
        try:
            pdfmetrics.registerFont(TTFont("Arabic", "Arial.ttf"))
            pdfmetrics.registerFont(TTFont("Arabic-Bold", "ArialBD.ttf"))
        except:  # noqa
            print("Warning: Arabic font not found. Using default Helvetica.")

    def arabic_text(self, text):
        """Convert Arabic text for proper display"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:  # noqa
            return text

    def transform_api_response(self, api_response):
        """Transform API response to the format expected by generate_report"""
        data = api_response.get("data", {})
        basic_info = data.get("basic_info", {})

        # Calculate total deductions from deductions_data
        deductions_data = data.get("deductions_data", [])
        total_deductions = sum(d.get("deduction_amount", 0) for d in deductions_data)

        # Transform alternatives data
        alternatives = []
        for alt in data.get("alternatives_data", []):
            alternatives.append(
                {"type": alt.get("reason", ""), "date": alt.get("date", ""), "amount": alt.get("amount", 0)}
            )

        # Transform advances data
        advances = []
        for adv in data.get("advances_data", []):
            advances.append(
                {
                    "date": adv.get("advance_date", ""),
                    "amount": adv.get("advance_amount", 0),
                    "note": adv.get("advance_reason", "لا توجد ملاحظات"),
                }
            )

        # Transform deductions data
        deductions = []
        for ded in deductions_data:
            deductions.append(
                {
                    "date": ded.get("deduction_date", ""),
                    "amount": ded.get("deduction_amount", 0),
                    "reason": ded.get("deduction_reason", "لا يوجد سبب"),
                }
            )

        # Build worker_data dictionary
        worker_data = {
            "name": basic_info.get("name", ""),
            "phone": basic_info.get("phone", ""),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "process_type": "كشف حساب",
            "attendance_days": basic_info.get("total_days_of_work", 0),
            "absence_days": basic_info.get("total_days_of_absence", 0),
            "daily_salary": basic_info.get("daily_salary", 0),
            "total_deductions": total_deductions,
            "num_alternatives": len(alternatives),
            "remaining_salary": basic_info.get("remaining_salary", 0),
            "alternatives": alternatives,
            "advances": advances,
            "deductions": deductions,
        }

        return worker_data

    def generate_report_from_api(self, api_response, output_filename="salary_report.pdf"):
        """Generate report directly from API response"""
        worker_data = self.transform_api_response(api_response)
        self.generate_report(worker_data, output_filename)

    def generate_report(self, worker_data, output_filename="salary_report.pdf"):
        # 1. SET MARGINS TO 0 for full-width header
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=A4,
            rightMargin=0,
            leftMargin=0,
            topMargin=0,
            bottomMargin=0.5 * cm,
        )

        elements = []
        page_width = A4[0]

        # --- 2. HEADER (Full Width, No Margins, Reduced Height & Logo size) ---
        company_style = ParagraphStyle(
            "CompanyName",
            fontName="Arabic-Bold",
            fontSize=28,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#E0E0E0"),
            leading=32,
        )

        arabic_name = Paragraph(self.arabic_text("شركة بالميرس"), company_style)

        logo_width_col = 3.5 * cm
        text_width_col = page_width - logo_width_col

        try:
            logo = Image(self.logo_path, width=2.2 * cm, height=1.7 * cm)
            header_data = [[logo, arabic_name]]
        except:  # noqa
            print("Logo not found, skipping image")
            header_data = [["", arabic_name]]

        header_table = Table(header_data, colWidths=[logo_width_col, text_width_col])

        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#8B9456")),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (0, 0), 15),
                    ("RIGHTPADDING", (1, 0), (1, 0), 20),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 0.5 * cm))

        # --- Title ---
        title_style = ParagraphStyle(
            "ArabicTitle",
            fontName="Arabic-Bold",
            fontSize=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
            spaceAfter=5,
            spaceBefore=5,
        )

        title = Paragraph(self.arabic_text("كشف حساب العامل"), title_style)
        elements.append(title)

        # --- Decorative Line ---
        line_data = [[""]]
        line_table = Table(line_data, colWidths=[8 * cm], hAlign="CENTER")
        line_table.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 2.5, colors.HexColor("#4b5b38")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        elements.append(line_table)
        elements.append(Spacer(1, 0.5 * cm))

        # --- Basic Information ---
        basic_info = [
            [
                worker_data["phone"],
                self.arabic_text("الهاتف:"),
                self.arabic_text(worker_data["name"]),
                self.arabic_text("الاسم:"),
            ],
            [
                self.arabic_text(worker_data["process_type"]),
                self.arabic_text("نوع العملية:"),
                worker_data["date"],
                self.arabic_text("التاريخ:"),
            ],
            [
                str(worker_data["absence_days"]),
                self.arabic_text("أيام الغياب:"),
                str(worker_data["attendance_days"]),
                self.arabic_text("أيام الحضور:"),
            ],
            [
                f"{worker_data['total_deductions']} ج.م",
                self.arabic_text("إجمالي الخصومات:"),
                f"{worker_data['daily_salary']} ج.م",
                self.arabic_text("الراتب اليومي:"),
            ],
            [
                f"{worker_data['remaining_salary']} ج.م",
                self.arabic_text("الراتب المتبقي:"),
                str(worker_data["num_alternatives"]),
                self.arabic_text("عدد البدلات:"),
            ],
        ]

        basic_table = Table(basic_info, colWidths=[5 * cm, 3.5 * cm, 6 * cm, 3.5 * cm], hAlign="CENTER")
        basic_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Arabic", 11),
                    ("FONT", (1, 0), (1, -1), "Arabic-Bold", 11),
                    ("FONT", (3, 0), (3, -1), "Arabic-Bold", 11),
                    ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#e8f5e9")),
                    ("BACKGROUND", (3, 0), (3, -1), colors.HexColor("#e8f5e9")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4a5f3a")),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ALIGN", (2, 0), (2, -1), "LEFT"),
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 0), (0, -1), [colors.white, colors.HexColor("#f9fbf7")]),
                ]
            )
        )

        elements.append(basic_table)
        elements.append(Spacer(1, 0.4 * cm))

        # Common Style for Section Headers
        section_style = ParagraphStyle(
            "ArabicSection",
            fontName="Arabic-Bold",
            fontSize=15,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#2c3e28"),
            spaceAfter=4,
            spaceBefore=4,
            rightIndent=0.5 * cm,
        )

        # --- Worker Alternatives Table ---
        if worker_data.get("alternatives"):
            alt_title = Paragraph(self.arabic_text("البدلات"), section_style)
            elements.append(alt_title)
            elements.append(Spacer(1, 0.1 * cm))

            alt_data = [[self.arabic_text("النوع"), self.arabic_text("التاريخ"), self.arabic_text("المبلغ")]]
            for alt in worker_data["alternatives"]:
                alt_data.append([self.arabic_text(alt["type"]), alt["date"], f"{alt['amount']} ج.م"])

            total_alt = sum(alt["amount"] for alt in worker_data["alternatives"])
            alt_data.append([self.arabic_text("الإجمالي"), "", f"{total_alt} ج.م"])

            alt_table = Table(alt_data, colWidths=[8 * cm, 6 * cm, 6 * cm], hAlign="CENTER")
            alt_table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Arabic", 11),
                        ("FONT", (0, 0), (-1, 0), "Arabic-Bold", 12),
                        ("FONT", (0, -1), (-1, -1), "Arabic-Bold", 12),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a5f3a")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#c8e6c9")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4a5f3a")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("PADDING", (0, 0), (-1, -1), 7),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f9f3")]),
                    ]
                )
            )
            elements.append(alt_table)
            elements.append(Spacer(1, 0.4 * cm))

        # --- Advances Table ---
        if worker_data.get("advances"):
            adv_title = Paragraph(self.arabic_text("السلف"), section_style)
            elements.append(adv_title)
            elements.append(Spacer(1, 0.1 * cm))

            adv_data = [
                [self.arabic_text("التاريخ"), self.arabic_text("المبلغ"), self.arabic_text("ملاحظات")]
            ]
            for adv in worker_data["advances"]:
                adv_data.append([adv["date"], f"{adv['amount']} ج.م", self.arabic_text(adv["note"])])

            total_adv = sum(adv["amount"] for adv in worker_data["advances"])
            adv_data.append([self.arabic_text("الإجمالي"), f"{total_adv} ج.م", ""])

            adv_table = Table(adv_data, colWidths=[5 * cm, 5 * cm, 10 * cm], hAlign="CENTER")
            adv_table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Arabic", 11),
                        ("FONT", (0, 0), (-1, 0), "Arabic-Bold", 12),
                        ("FONT", (0, -1), (-1, -1), "Arabic-Bold", 12),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a5f3a")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff9c4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4a5f3a")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("PADDING", (0, 0), (-1, -1), 7),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f9f3")]),
                    ]
                )
            )
            elements.append(adv_table)
            elements.append(Spacer(1, 0.4 * cm))

        # --- Deductions Table ---
        if worker_data.get("deductions"):
            ded_title = Paragraph(self.arabic_text("الخصومات"), section_style)
            elements.append(ded_title)
            elements.append(Spacer(1, 0.1 * cm))

            ded_data = [[self.arabic_text("التاريخ"), self.arabic_text("المبلغ"), self.arabic_text("السبب")]]
            for ded in worker_data["deductions"]:
                ded_data.append([ded["date"], f"{ded['amount']} ج.م", self.arabic_text(ded["reason"])])

            total_ded = sum(ded["amount"] for ded in worker_data["deductions"])
            ded_data.append([self.arabic_text("الإجمالي"), f"{total_ded} ج.م", ""])

            ded_table = Table(ded_data, colWidths=[5 * cm, 5 * cm, 10 * cm], hAlign="CENTER")
            ded_table.setStyle(
                TableStyle(
                    [
                        ("FONT", (0, 0), (-1, -1), "Arabic", 11),
                        ("FONT", (0, 0), (-1, 0), "Arabic-Bold", 12),
                        ("FONT", (0, -1), (-1, -1), "Arabic-Bold", 12),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a5f3a")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffcccc")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4a5f3a")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("PADDING", (0, 0), (-1, -1), 7),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f9f3")]),
                    ]
                )
            )
            elements.append(ded_table)

        # Build PDF
        doc.build(elements)
        print_pdf(output_filename)
        print(f"Report generated successfully: {output_filename}")


# if __name__ == "__main__":
#     # Your API response
#     api_response = {
#         "status": "success",
#         "data": {
#             "basic_info": {
#                 "worker_id": 4,
#                 "name": "عامل رقم 4",
#                 "phone": "01006865823",
#                 "job": "عامل صيانه",
#                 "profile_picture": "/media/workers/rHxsAzXev548yAFd2uMYmcDgvFI_b3SSJVy_cHapt43.jpeg",
#                 "total_days_of_absence": 2,
#                 "total_days_of_work": 1,
#                 "is_in_vacation": False,
#                 "daily_salary": 150.0,
#                 "total_advance": 0,
#                 "total_deduction": 0,
#                 "total_alternatives_amount": 50.0,
#                 "remaining_salary": 200.0,
#                 "work_start_date": "2025-10-10",
#             },
#             "alternatives_data": [{"id": 8, "reason": "اصابة", "date": "2025-12-11", "amount": 50.0}],
#             "advances_data": [
#                 {"id": 6, "advance_date": "2025-10-16", "advance_amount": 50.0, "advance_reason": ""}
#             ],
#             "deductions_data": [
#                 {"id": 2, "deduction_date": "2025-10-10", "deduction_amount": 50.0,
# "deduction_reason": ""},
#                 {"id": 6, "deduction_date": "2025-10-10", "deduction_amount": 100.0,
# "deduction_reason": ""},
#                 {"id": 7, "deduction_date": "2025-10-16", "deduction_amount": 100.0,
# "deduction_reason": ""},
#                 {"id": 8, "deduction_date": "2025-10-16", "deduction_amount": 100.0,
# "deduction_reason": ""},
#             ],
#         },
#     }

#     # Generate report from API response
#     report = ArabicSalaryReport()
#     report.generate_report_from_api(api_response, f"{BASE_DIR}/worker_salary_report_test.pdf")

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QHeaderView,
    QFrame,
    QTableWidgetItem,
    QMessageBox,
    QWidget,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .mixture_materials_details_dialog import MixtureMaterialsDetailsDialog

# Import the ArabicSalesInvoice class
from ..invoice_generator.generate_invoice import ArabicSalesInvoice  # Adjust import path as needed


class InvoiceGeneratorWorker(QObject):
    """Worker thread for generating the PDF invoice."""

    finished = pyqtSignal()
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, invoice_params):
        super().__init__()
        self.invoice_params = invoice_params

    @pyqtSlot()
    def run(self):
        try:
            # Create the invoice
            result = ArabicSalesInvoice(**self.invoice_params)

            # Handle the return value from ArabicSalesInvoice
            if isinstance(result, tuple) and len(result) == 2:
                is_success, msg = result
                if is_success:
                    self.success.emit(msg)
                else:
                    self.error.emit(msg)
            else:
                # If ArabicSalesInvoice doesn't return a tuple, assume success
                self.success.emit("تم إنشاء الفاتورة بنجاح!")
        except Exception as e:
            import traceback

            traceback.print_exc()
            self.error.emit(f"فشل في إنشاء الفاتورة: {str(e)}")
        finally:
            self.finished.emit()


class MixtureDetailsWorker(QObject):
    """Worker thread for fetching mixture details for an invoice."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class InvoiceInfoWorker(QObject):
    """Worker thread for fetching invoice information."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, invoice_num):
        super().__init__()
        self.url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/info/?invoice_num={invoice_num}"

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class ClientInvoiceMaterialsDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.company_data = {}  # Store company data (fixed company info)
        self.invoice_info = {}  # Store invoice information from API
        self.setWindowTitle(f"تفاصيل خلطات الفاتورة: {invoice_num}")
        self.setMinimumSize(900, 600)
        self.setModal(True)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main Container
        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(f"تفاصيل خلطات الفاتورة رقم: {invoice_num}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.accept)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        # Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        # Updated headers to match the new item structure (ID, Name, Qty, Unit, Action)
        self.table.setHorizontalHeaderLabels(["كود المنتج", "اسم المنتج", "الكمية", "الوحدة", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(4, 200)
        self.table.verticalHeader().setDefaultSectionSize(70)
        content_layout.addWidget(self.table, 1)

        # ==================== ADDED: BUTTONS SECTION ====================
        buttons_layout = QHBoxLayout()

        # Create Invoice Button
        self.create_invoice_btn = QPushButton("إنشاء وطباعة فاتورة PDF")
        self.create_invoice_btn.setIcon(qta.icon("fa5s.file-pdf", color="#dc2626"))
        self.create_invoice_btn.clicked.connect(self.handle_create_invoice)
        self.create_invoice_btn.setEnabled(False)  # Disable until data is loaded

        # Close Button
        close_btn = QPushButton("إغلاق")
        close_btn.setIcon(qta.icon("fa5s.times", color="#6b7280"))
        close_btn.clicked.connect(self.accept)

        buttons_layout.addWidget(self.create_invoice_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        content_layout.addLayout(buttons_layout)
        # ==================== END BUTTONS SECTION ====================

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)

        # Store table data for invoice generation
        self.table_data = []

        self.fetch_mixture_details()
        self.fetch_invoice_info()  # Fetch invoice info as well

    def fetch_invoice_info(self):
        """Fetches the invoice information from the API."""
        self.thread_info = QThread()
        self.worker_info = InvoiceInfoWorker(self.invoice_num)
        self.worker_info.moveToThread(self.thread_info)
        self.thread_info.started.connect(self.worker_info.run)
        self.worker_info.success.connect(self.handle_invoice_info_success)
        self.worker_info.error.connect(self.show_error)
        self.worker_info.finished.connect(self.thread.quit)
        self.thread_info.start()

    def handle_invoice_info_success(self, response_data):
        """Handles successful invoice info response."""
        if response_data.get("status") == "success":
            self.invoice_info = response_data.get("data", {})
            # Enable button if table data is also ready
            if self.table_data:
                self.create_invoice_btn.setEnabled(True)
        else:
            self.show_error("فشل في تحميل معلومات الفاتورة")

    def fetch_mixture_details(self):
        """Fetches the mixture history for the given invoice number."""
        url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/materials/?invoice_num={self.invoice_num}"
        self.thread = QThread()
        self.worker = MixtureDetailsWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_table(self, response_data):
        data_obj = response_data.get("data", {}).get("data", {})
        results = data_obj.get("results", [])
        self.table.setRowCount(0)
        self.table_data = []  # Clear previous data

        for mixture in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Store data for invoice generation
            mixture_info = {
                "id": mixture.get("id"),
                "name": mixture.get("material_name", ""),
                "quantity": mixture.get("quantity_in_unit", 0),
                "unit": mixture.get("unit", ""),  # Changed from material_unit based on typical API response
                "price": mixture.get(
                    "total_price", 0
                ),  # Ensure price is stored if available, defaulting to 0
            }
            # Fallback if unit is under different key or empty
            if not mixture_info["unit"]:
                mixture_info["unit"] = mixture.get("material_unit", "")

            self.table_data.append(mixture_info)

            # Convert ID to string to ensure it displays
            items = [
                QTableWidgetItem(str(mixture_info["id"])),
                QTableWidgetItem(mixture_info["name"]),
                QTableWidgetItem(f"{mixture_info['quantity']:,.2f}"),
                QTableWidgetItem(f"{mixture_info['unit']}"),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

            # Add details button and pass the correct ID
            details_button = QPushButton("تفاصيل")  # Changed label to match context
            details_button.clicked.connect(
                lambda ch, mid=mixture_info["id"], mname=mixture_info["name"]: self.handle_show_details(
                    mid, mname
                )
            )
            button_container = QWidget()
            layout = QHBoxLayout(button_container)
            layout.addWidget(details_button)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_pos, 4, button_container)

        # Enable create invoice button if we have data and invoice info is loaded
        if self.table_data:
            self.create_invoice_btn.setEnabled(True)

    def handle_show_details(self, mixture_id, mixture_name):
        """Opens the dialog to show the materials for the selected mixture."""
        if mixture_id:
            dialog = MixtureMaterialsDetailsDialog(mixture_id, mixture_name, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على معرف الخلطة. يرجى التأكد من تحديث الخادم.")

    def handle_create_invoice(self):
        """Handle creating PDF invoice using ArabicSalesInvoice class."""
        if not self.table_data:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لإنشاء الفاتورة.")
            return

        # Disable button to indicate processing
        self.create_invoice_btn.setEnabled(False)
        self.create_invoice_btn.setText("جاري إنشاء الفاتورة...")

        try:
            # Create a QTableWidget with the data for the invoice
            # Updated to match the columns: ID, Name, Quantity, Unit, Price
            # Assuming 'ArabicSalesInvoice' takes a table with these columns
            invoice_table = QTableWidget(len(self.table_data), 5)

            # Populate the table with data
            for row, mixture in enumerate(self.table_data):
                # Calculate price per unit safely to avoid division by zero if needed,
                # but let's assume we want to show total price in the last column.
                # If price is missing from API, it defaults to 0.
                total_price = mixture.get("price", 0)

                items = [
                    QTableWidgetItem(str(mixture["id"])),  # Product ID/Code (Col 0)
                    QTableWidgetItem(mixture["name"]),  # Product name (Col 1)
                    QTableWidgetItem(f"{mixture['quantity']:,.2f}"),  # Quantity (Col 2)
                    QTableWidgetItem(mixture["unit"]),  # Unit (Col 3)
                    QTableWidgetItem(f"{total_price:,.2f}"),  # Total Price (Col 4) - Fixed IndexError
                ]

                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignCenter)
                    invoice_table.setItem(row, col, item)

            # Prepare invoice data using API response
            invoice_params = {
                "company": "شركه المهندس " or "",  # Ensure not None
                "email": "elmohandes@gmail.com" or "",
                "phone": "+01113938300" or "",
                "companyAddress": """مصر - الجيزة - الوراق - جزيرة محمد""" or "",
                "table": invoice_table,
                "total": f"{self.invoice_info.get('invoice_total_amount', 0):,.2f}" or "0.00",
                "discount": "0.00",
                "payment": f"{self.invoice_info.get('invoice_total_amount', 0):,.2f}" or "0.00",
                "rest": "0.00",
                "client": "عميل نقدي",  # Default for Segmental
                "clientAddress": "",
                "invoiceNumber": str(self.invoice_num) or "",
                "invoice_date": self.invoice_info.get("invoice_date", "") or "",
            }

            # Start worker thread
            self.gen_thread = QThread()
            self.gen_worker = InvoiceGeneratorWorker(invoice_params)
            self.gen_worker.moveToThread(self.gen_thread)
            self.gen_thread.started.connect(self.gen_worker.run)
            self.gen_worker.success.connect(self.on_invoice_gen_success)
            self.gen_worker.error.connect(self.on_invoice_gen_error)
            self.gen_worker.finished.connect(self.gen_thread.quit)
            self.gen_worker.finished.connect(self.gen_worker.deleteLater)
            self.gen_thread.finished.connect(self.gen_thread.deleteLater)
            self.gen_thread.start()

        except Exception as e:
            self.create_invoice_btn.setEnabled(True)
            self.create_invoice_btn.setText("إنشاء وطباعة فاتورة PDF")
            QMessageBox.critical(self, "خطأ", f"فشل في إعداد الفاتورة: {str(e)}")

    def on_invoice_gen_success(self, msg):
        self.create_invoice_btn.setEnabled(True)
        self.create_invoice_btn.setText("إنشاء وطباعة فاتورة PDF")
        QMessageBox.information(self, "نجاح", msg)

    def on_invoice_gen_error(self, msg):
        self.create_invoice_btn.setEnabled(True)
        self.create_invoice_btn.setText("إنشاء وطباعة فاتورة PDF")
        QMessageBox.critical(self, "خطأ", msg)

    def show_error(self, message):
        QMessageBox.critical(self, "خطأ", message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "old_pos") and self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

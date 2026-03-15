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

# Import the ArabicSalesInvoice class
from ..invoice_generator.generate_invoice import ArabicSalesInvoice  # Adjust import path as needed


class MockTableItem:
    """Mock item to simulate QTableWidgetItem behavior for the report generator."""
    def __init__(self, text):
        self._text = str(text)

    def text(self):
        return self._text


class MockTable:
    """Mock table to simulate QTableWidget behavior for the report generator."""
    def __init__(self):
        self._rows = []

    def rowCount(self):
        return len(self._rows)

    def item(self, row, col):
        if 0 <= row < len(self._rows) and 0 <= col < len(self._rows[row]):
            return self._rows[row][col]
        return MockTableItem("")

    def add_row(self, items):
        row_items = [MockTableItem(item) for item in items]
        self._rows.append(row_items)


class InvoiceGenerationWorker(QThread):
    """Worker thread for generating the PDF invoice."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, invoice_params):
        super().__init__()
        self.invoice_params = invoice_params

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
            self.finished_signal.emit()


class MaterialDetailsWorker(QObject):
    """Worker thread for fetching invoice material details."""

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
        self.url = f"{BACKEND_BASE_URL}/suppliers/invoice/info/?invoice_num={invoice_num}"

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


class InvoiceMaterialsDetailsDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.invoice_info = {}  # Store invoice information from API
        self.setWindowTitle(f"تفاصيل خامات الفاتورة: {invoice_num}")
        self.setMinimumSize(800, 500)
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
        title_text = QLabel(f"تفاصيل خامات الفاتورة رقم: {invoice_num}")
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["اسم الخامة", "الكمية بالكيلو", "سعر الشراء", "الوحده"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        content_layout.addWidget(self.table)

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

        # Fetch both material details and invoice info
        self.fetch_invoice_info()
        self.fetch_material_details()

    def _to_float(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def fetch_invoice_info(self):
        """Fetches the invoice information from the API."""
        self.thread_info = QThread()
        self.worker_info = InvoiceInfoWorker(self.invoice_num)
        self.worker_info.moveToThread(self.thread_info)
        self.thread_info.started.connect(self.worker_info.run)
        self.worker_info.success.connect(self.handle_invoice_info_success)
        self.worker_info.error.connect(self.show_error)
        self.worker_info.finished.connect(self.thread_info.quit)
        self.thread_info.start()

    def handle_invoice_info_success(self, response_data):
        """Handles successful invoice info response."""
        if response_data.get("status") == "success":
            self.invoice_info = response_data.get("data", {})
        else:
            self.show_error("فشل في تحميل معلومات الفاتورة")

    def fetch_material_details(self):
        """Fetches the material history for the given invoice number."""
        url = f"{BACKEND_BASE_URL}/suppliers/invoice/materials/?invoice_num={self.invoice_num}"
        self.thread = QThread()
        self.worker = MaterialDetailsWorker(url)
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

        for material in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            # Store data for invoice generation
            material_info = {
                "name": material.get("material_name") or "",
                "quantity": self._to_float(material.get("quantity_in_unit")),
                "buy_price": self._to_float(material.get("buy_price_per_unit")),
                "unit": material.get("unit") or "",
            }
            self.table_data.append(material_info)

            items = [
                QTableWidgetItem(material_info["name"]),
                QTableWidgetItem(f"{material_info['quantity']:,.2f}"),
                QTableWidgetItem(f"{material_info['buy_price']:,.2f}"),
                QTableWidgetItem(material_info['unit']),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

        # Enable create invoice button if we have data and invoice info is loaded
        self.create_invoice_btn.setEnabled(len(self.table_data) > 0)

    def handle_create_invoice(self):
        """Handle creating PDF invoice using InvoiceGenerationWorker."""
        if not self.table_data or not self.invoice_info:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لإنشاء الفاتورة.")
            return

        self.create_invoice_btn.setEnabled(False)
        self.create_invoice_btn.setText("جاري إنشاء الفاتورة...")

        try:
            # Create a MockTable with the data for the invoice
            # We use MockTable because we cannot pass QWidgets (QTableWidget) to another thread
            invoice_table = MockTable()

            # Populate the table with data
            for row, material in enumerate(self.table_data):
                # Prepare row data
                items = [
                    str(row + 1),                              # Product number
                    material["name"],                          # Material name
                    f"{material['quantity']:,.2f}",            # Quantity
                    material['unit'],                          # Unit
                    "0"                                        # Extra fake column as requested
                ]
                invoice_table.add_row(items)

            # Get supplier info from API response (adjust field names based on your API)
            supplier_info = self.invoice_info.get("supplier_info", {})

            # Sanitize client name for filename
            client_name = supplier_info.get("name") or "مورد"
            safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()

            # Prepare invoice data using API response
            invoice_params = {
                "company": "شركه المهندس " or "",
                "email": "elmohandes@gmail.com" or "",
                "phone": "+01113938300" or "",
                "companyAddress": """مصر - الجيزة - الوراق - جزيرة محمد""" or "",
                "table": invoice_table,
                "total": f"{self._to_float(self.invoice_info.get('invoice_total_amount')):,.2f}",
                "discount": "0.00",
                "payment": f"{self._to_float(self.invoice_info.get('total_paid_amount')):,.2f}",
                "rest": f"0.00",
                "client": safe_client_name,
                "clientAddress": "",
                "invoiceNumber": str(self.invoice_num) or "",
                "invoice_date": self.invoice_info.get("invoice_date") or "",
            }

            # Start Worker
            self.invoice_worker = InvoiceGenerationWorker(invoice_params)
            self.invoice_worker.success.connect(self.handle_invoice_generation_success)
            self.invoice_worker.error.connect(self.show_error)
            # Use a separate slot for cleanup to ensure button state is restored
            self.invoice_worker.finished_signal.connect(self.on_invoice_generation_finished)
            self.invoice_worker.start()

        except Exception as e:
            self.create_invoice_btn.setEnabled(True)
            self.create_invoice_btn.setText("إنشاء وطباعة فاتورة PDF")
            QMessageBox.critical(self, "خطأ", f"فشل في تحضير الفاتورة: {str(e)}")
            import traceback
            traceback.print_exc()

    def handle_invoice_generation_success(self, msg):
        QMessageBox.information(self, "نجاح", msg)

    def on_invoice_generation_finished(self):
        self.create_invoice_btn.setEnabled(True)
        self.create_invoice_btn.setText("إنشاء وطباعة فاتورة PDF")


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

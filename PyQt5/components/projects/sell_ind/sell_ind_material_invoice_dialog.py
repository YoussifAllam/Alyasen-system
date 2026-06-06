from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QMessageBox,
    QWidget,
)
from PyQt5.QtCore import Qt, QDate, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ...Main_Ui_Components.constant import BACKEND_BASE_URL
from ...utils.api_errors import format_request_exception, parse_api_response
from ...validation import attach_number_formatter, clean_number


class SupplierFetchWorker(QObject):
    """Worker for fetching the list of suppliers."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            from requests import get

            response = get(self.url, timeout=15)
            ok, data = parse_api_response(response)
            if ok:
                self.success.emit(data)
            else:
                self.error.emit(data)
        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        finally:
            self.finished.emit()


class CreateInvoiceWorker(QObject):
    """Worker for creating a new material invoice."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request("POST", self.url, json=self.payload, timeout=15)
            ok, data = parse_api_response(response)
            if ok:
                self.success.emit(data)
            else:
                self.error.emit(data)
        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        finally:
            self.finished.emit()


class CreateMaterialInvoiceDialog(QDialog):
    invoice_saved = pyqtSignal()

    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("إضافة فاتورة خامات")
        self.setMinimumSize(500, 450)
        self.setModal(True)

        # Frameless Window Setup (Keeping consistency with other dialogs)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setup_ui()
        self.fetch_suppliers()

    def setup_ui(self):
        # Main Container
        container = QFrame()
        container.setObjectName("dialogContainer")
        # container.setStyleSheet(
        #     """
        #     #dialogContainer {
        #         background-color: #1a1d21;
        #         border: 1px solid #3f3f46;
        #         border-radius: 12px;
        #     }
        #     QLabel { color: #e4e4e7; font-size: 14px; }
        #     QLineEdit, QDateEdit, QComboBox {
        #         background-color: #27272a;
        #         border: 1px solid #3f3f46;
        #         border-radius: 6px;
        #         padding: 8px;
        #         color: #ffffff;
        #     }
        #     QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
        #         border-color: #00bc88;
        #     }
        #     QPushButton#primaryButton {
        #         background-color: #00bc88;
        #         color: white;
        #         font-weight: bold;
        #         border-radius: 6px;
        #         padding: 10px;
        #     }
        #     QPushButton#secondaryButton {
        #         background-color: #3f3f46;
        #         color: white;
        #         border-radius: 6px;
        #         padding: 10px;
        #     }
        #     #dialogTitleBar {
        #         background-color: #27272a;
        #         border-bottom: 1px solid #3f3f46;
        #         border-top-left-radius: 12px;
        #         border-top-right-radius: 12px;
        #     }
        # """
        # )

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Title Bar
        title_bar = QFrame()
        title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 10, 20, 10)

        title_text = QLabel("إضافة فاتورة خامات جديدة")
        title_text.setStyleSheet("font-weight: bold; font-size: 16px;")

        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa5s.times", color="#a1a1aa"))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent; border: none; padding: 5px;")
        close_btn.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Form Area
        content_area = QWidget()
        form_layout = QFormLayout(content_area)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.combo_supplier = QComboBox()
        self.combo_supplier.addItem("جاري تحميل الموردين...", None)

        self.date_invoice = QDateEdit()
        self.date_invoice.setCalendarPopup(True)
        self.date_invoice.setDate(QDate.currentDate())

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("0.00")
        attach_number_formatter(self.txt_amount)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("ملاحظات اختيارية...")

        form_layout.addRow("المورد:", self.combo_supplier)
        form_layout.addRow("تاريخ الفاتورة:", self.date_invoice)
        form_layout.addRow("إجمالي المبلغ:", self.txt_amount)
        form_layout.addRow("ملاحظات:", self.txt_notes)

        main_layout.addWidget(content_area)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(30, 0, 30, 30)
        btn_layout.setSpacing(15)

        self.btn_save = QPushButton("حفظ الفاتورة")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.handle_save)

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)

    def fetch_suppliers(self):
        url = f"{BACKEND_BASE_URL}/materials_suppliers/suppliers/"
        self.fetch_thread = QThread()
        self.fetch_worker = SupplierFetchWorker(url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.success.connect(self.populate_suppliers)
        self.fetch_worker.error.connect(
            lambda msg: QMessageBox.warning(self, "خطأ", f"فشل تحميل الموردين: {msg}")
        )
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_thread.start()

    def populate_suppliers(self, response_data):
        self.combo_supplier.clear()
        results = response_data.get("data", {}).get("results", [])
        if not results:
            self.combo_supplier.addItem("لا يوجد موردين", None)
            return

        for s in results:
            self.combo_supplier.addItem(s.get("name"), s.get("id"))

    def handle_save(self):
        supplier_id = self.combo_supplier.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "تنبيه", "برجاء اختيار مورد.")
            return

        amount_str = clean_number(self.txt_amount.text())
        if not amount_str:
            QMessageBox.warning(self, "تنبيه", "برجاء إدخال مبلغ الفاتورة.")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            QMessageBox.warning(self, "خطأ", "برجاء إدخال مبلغ صحيح.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "supplier_id": supplier_id,
            "invoice_date": self.date_invoice.date().toString("yyyy-MM-dd"),
            "invoice_total_amount": amount,
            "notes": self.txt_notes.text().strip(),
            "username": username,
            "CBP_id": self.project_id,  # This might be needed if the invoice is linked to a project
        }

        url = f"{BACKEND_BASE_URL}/materials_suppliers/invoice/"

        self.btn_save.setEnabled(False)
        self.btn_save.setText("جاري الحفظ...")

        self.save_thread = QThread()
        self.save_worker = CreateInvoiceWorker(url, payload)
        self.save_worker.moveToThread(self.save_thread)
        self.save_thread.started.connect(self.save_worker.run)
        self.save_worker.success.connect(self.on_save_success)
        self.save_worker.error.connect(self.on_save_error)
        self.save_worker.finished.connect(self.save_thread.quit)
        self.save_thread.start()

    def on_save_success(self, response):
        QMessageBox.information(self, "نجاح", "تم إضافة الفاتورة بنجاح.")
        self.invoice_saved.emit()
        self.accept()

    def on_save_error(self, message):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("حفظ الفاتورة")
        QMessageBox.critical(self, "خطأ", f"فشل حفظ الفاتورة:\n{message}")

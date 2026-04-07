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
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QUrl, QSettings
from PyQt5.QtGui import QDesktopServices
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class PaymentDetailsWorker(QObject):
    """Worker thread for fetching payment details."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, params=None):
        super().__init__()
        self.url = url
        self.params = params

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, params=self.params, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(
                    f"خطأ من الخادم: {response.status_code}\n{response.text}"
                )
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class ClearPaymentWorker(QObject):
    """Worker thread for clearing a check payment via PATCH."""

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
            response = request("PATCH", self.url, data=self.payload, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                data = response.json()
                msg = data.get("error", f"خطأ من الخادم: {response.status_code}")
                self.error.emit(msg)
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class InvoicePaymentDetailsDialog(QDialog):
    update_client_data = pyqtSignal()

    def __init__(self, client_id, project_id, project_type, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.project_id = project_id
        self.project_type = project_type
        self.setWindowTitle("تفاصيل دفعات المشروع")
        self.setMinimumSize(850, 600)
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
        title_text = QLabel(f"تفاصيل دفعات المشروع رقم: {project_id}")
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
        self.table.setColumnCount(8)
        headers = [
            "رقم الفاتورة",
            "المبلغ المدفوع",
            "تاريخ الدفعة",
            "ملاحظات",
            "طريقة الدفع",
            "تاريخ تسوية الشيك",
            "",
            "",
        ]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 200)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 200)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.verticalHeader().setDefaultSectionSize(80)
        content_layout.addWidget(self.table, 1)

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)

        self.fetch_payment_details()

    def fetch_payment_details(self):
        """Fetches the payment history for the given project_id and supplier_id."""
        url = f"{BACKEND_BASE_URL}/clients/projects/payments/"
        params = {
            "type": str(self.project_type).strip(),
            "project_id": str(self.project_id).strip(),
        }

        self.thread = QThread()
        self.worker = PaymentDetailsWorker(url, params=params)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_table(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.table.setRowCount(0)
        for payment in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            invoice_num = payment.get("portal_invoice_number", "")
            amount = payment.get("payment_amount", 0)
            date = payment.get("payment_date", "")
            notes = payment.get("notes") or ""
            payment_type = payment.get("payment_type", "")
            check_cleared_date = payment.get("check_cleared_date", "")
            is_cleared = payment.get("is_cleared")
            # file = payment.get("portal_invoice_file", "")

            items = [
                QTableWidgetItem(invoice_num),
                QTableWidgetItem(str(amount)),
                QTableWidgetItem(date),
                QTableWidgetItem(notes),
                QTableWidgetItem(payment_type),
                QTableWidgetItem(check_cleared_date),
                # QTableWidgetItem(file),
            ]

            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

            payment_id = payment.get("id")
            if not is_cleared and payment_type == "check":
                btn_clear = QPushButton("تسوية")
                btn_clear.setCursor(Qt.PointingHandCursor)
                btn_clear.setObjectName("primaryButton")
                btn_clear.clicked.connect(
                    lambda checked, pid=payment_id: self.handle_clear_payment(pid)
                )
                self.table.setCellWidget(row_pos, 6, btn_clear)
            else:
                btn_clear = QLabel("تم التسوية")
                btn_clear.setCursor(Qt.PointingHandCursor)
                btn_clear.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row_pos, 6, btn_clear)

            file_url = payment.get("portal_invoice_file")
            if file_url:
                btn_view = QPushButton("عرض الملف")
                btn_view.setCursor(Qt.PointingHandCursor)
                btn_view.clicked.connect(
                    lambda checked, url=file_url: self.open_file_url(url)
                )
                self.table.setCellWidget(row_pos, 7, btn_view)
            else:
                empty_item = QTableWidgetItem("لا يوجد ملف")
                empty_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, 7, empty_item)

    def handle_clear_payment(self, payment_id):
        """Initiate PATCH request to clear a check payment."""
        reply = QMessageBox.question(
            self,
            "تأكيد التسوية",
            "هل أنت متأكد من تسوية هذه الدفعة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        url = f"{BACKEND_BASE_URL}/clients/projects/payments/"
        payload = {
            "payment_id": str(payment_id),
            "user_name": "system",
        }

        self.clear_thread = QThread()
        self.clear_worker = ClearPaymentWorker(url, payload)
        self.clear_worker.moveToThread(self.clear_thread)
        self.clear_thread.started.connect(self.clear_worker.run)
        self.clear_worker.success.connect(self.on_clear_success)
        self.clear_worker.error.connect(self.on_clear_error)
        self.clear_worker.finished.connect(self.clear_thread.quit)
        self.clear_thread.start()

    def on_clear_success(self, response_data):
        """Handle successful check clearing."""
        QMessageBox.information(self, "نجاح", "تم تسوية الدفعة بنجاح.")
        self.update_client_data.emit()
        self.fetch_payment_details()

    def on_clear_error(self, message):
        """Handle check clearing error."""
        QMessageBox.critical(self, "خطأ", message)

    def open_file_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def show_error(self, message):
        QMessageBox.critical(self, "خطأ", message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (
            hasattr(self, "old_pos")
            and self.old_pos  # noqa
            and event.buttons() == Qt.LeftButton  # noqa
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

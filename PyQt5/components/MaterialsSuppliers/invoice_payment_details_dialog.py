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


class PaymentDetailsWorker(QObject):
    """Worker thread for fetching payment details."""

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


class InvoicePaymentDetailsDialog(QDialog):
    def __init__(self, supplier_id, parent=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.setWindowTitle(f"تفاصيل دفعات المورد رقم: {supplier_id}")
        self.setMinimumSize(700, 500)
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
        title_text = QLabel(f"تفاصيل دفعات المورد رقم: {supplier_id}")
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["المبلغ المدفوع", "تاريخ الدفعة", "ملاحظات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        content_layout.addWidget(self.table)

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)

        self.fetch_payment_details()

    def fetch_payment_details(self):
        """Fetches the payment history for the given invoice number."""
        url = f"{BACKEND_BASE_URL}/suppliers/invoice/payment/?supplier_id={self.supplier_id}"
        self.thread = QThread()
        self.worker = PaymentDetailsWorker(url)
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
        for payment in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(f"{payment.get('payment_amount', 0):,.2f}"),
                QTableWidgetItem(payment.get("payment_date", "")),
                QTableWidgetItem(str(payment.get("notes", ""))),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

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

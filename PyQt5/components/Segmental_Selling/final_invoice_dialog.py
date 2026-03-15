from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QWidget,
    QFormLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class SaveInvoiceWorker(QObject):
    """Worker to save the invoice total amount."""

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
            response = request("PATCH", self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code} - {response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class SaveInvoiceDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.setWindowTitle(f"حفظ الفاتورة: {invoice_num}")
        self.setMinimumSize(400, 250)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(f"حفظ الفاتورة رقم: {invoice_num}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.total_amount_input = QLineEdit()
        self.total_amount_input.setPlaceholderText("أدخل إجمالي الفاتورة")

        form_layout.addRow("إجمالي الفاتورة:", self.total_amount_input)

        content_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("حفظ")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.handle_save)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

    def handle_save(self):
        total_amount = self.total_amount_input.text().strip()
        if not total_amount:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال إجمالي الفاتورة.")
            return

        payload = {"invoice_num": self.invoice_num, "invoice_total_amount": total_amount}

        url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/invoices/"
        self._start_worker(url, payload)

    def _start_worker(self, url, payload):
        self.save_btn.setEnabled(False)
        self.thread = QThread()
        self.worker = SaveInvoiceWorker(url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_save_success)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.save_btn.setEnabled(True))
        self.thread.start()

    def on_save_success(self, response):
        QMessageBox.information(self, "نجاح", "تم حفظ إجمالي الفاتورة بنجاح.")
        self.accept()

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

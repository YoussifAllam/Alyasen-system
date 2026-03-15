from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QWidget,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class ClientInvoiceCreateWorker(QObject):
    """Worker thread to create a new client invoice via API."""

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
            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class CreateClientInvoiceDialog(QDialog):
    def __init__(self, client_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle("إنشاء فاتورة جديدة")
        self.setMinimumSize(400, 220)
        self.setModal(True)
        self.invoice_number = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel("إنشاء فاتورة جديدة")
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

        content_layout.addWidget(QLabel("ملاحظات:"))
        self.invoice_number_input = QLineEdit()
        content_layout.addWidget(self.invoice_number_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("حفظ")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save)
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

    def handle_save(self):
        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {"client_id": self.client_id, "username": username}
        url = f"{BACKEND_BASE_URL}/clients/invoice/invoices/"
        self._start_create_request(url, payload)

    def _start_create_request(self, url, payload):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = ClientInvoiceCreateWorker(url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_save_success)
        self.worker.error.connect(self.on_save_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_save_success(self, response_data):
        self._set_loading(False)
        self.invoice_number = response_data.get("invoice_number")
        self.accept()

    def on_save_error(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

    def _set_loading(self, is_loading):
        self.save_button.setDisabled(is_loading)
        # self.invoice_number_input.setDisabled(is_loading)
        self.save_button.setText("جاري الحفظ..." if is_loading else "حفظ")

    def get_invoice_number(self):
        return self.invoice_number

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

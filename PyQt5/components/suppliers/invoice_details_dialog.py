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


class InvoiceDetailsWorker(QObject):
    """Worker to fetch and update invoice details."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "GET":
                response = request("GET", self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(
                    f"خطأ من الخادم: {response.status_code} - {response.text}"
                )
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class InvoiceDetailsDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.setWindowTitle(f"تفاصيل الفاتورة: {invoice_num}")
        self.setMinimumSize(500, 500)
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
        title_text = QLabel(f"تفاصيل بيانات الفاتورة: {invoice_num}")
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

        self.karta_input = QLineEdit()
        self.first_weight_input = QLineEdit()
        self.second_weight_input = QLineEdit()
        self.driver_name_input = QLineEdit()
        self.driver_phone_input = QLineEdit()
        self.car_plate_input = QLineEdit()

        form_layout.addRow("رقم الكارتة:", self.karta_input)
        form_layout.addRow("الوزن الأول:", self.first_weight_input)
        form_layout.addRow("الوزن الثاني:", self.second_weight_input)
        form_layout.addRow("اسم السائق:", self.driver_name_input)
        form_layout.addRow("رقم السائق:", self.driver_phone_input)
        form_layout.addRow("رقم السيارة:", self.car_plate_input)

        content_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("حفظ ومتابعة")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.handle_save)

        self.cancel_btn = QPushButton("إغلاق")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.fetch_details()

    def fetch_details(self):
        url = (
            f"{BACKEND_BASE_URL}/suppliers/invoice/info/?invoice_num={self.invoice_num}"
        )
        self._start_worker("GET", url, on_success=self.populate_fields)

    def populate_fields(self, response):
        data = response.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        elif isinstance(data, list):
            data = {}

        self.karta_input.setText(str(data.get("karta_number") or ""))
        self.first_weight_input.setText(str(data.get("first_weight") or ""))
        self.second_weight_input.setText(str(data.get("second_weight") or ""))
        self.driver_name_input.setText(str(data.get("driver_name") or ""))
        self.driver_phone_input.setText(str(data.get("driver_phone") or ""))
        self.car_plate_input.setText(str(data.get("car_plate_number") or ""))

    def handle_save(self):
        payload = {
            "invoice_num": self.invoice_num,
            "karta_number": self.karta_input.text().strip(),
            "first_weight": self.first_weight_input.text().strip(),
            "second_weight": self.second_weight_input.text().strip(),
            "driver_name": self.driver_name_input.text().strip(),
            "driver_phone": self.driver_phone_input.text().strip(),
            "car_plate_number": self.car_plate_input.text().strip(),
        }

        url = f"{BACKEND_BASE_URL}/suppliers/invoice/info/"
        self._start_worker(
            "PATCH", url, payload=payload, on_success=self.on_save_success
        )

    def on_save_success(self, response):
        self.accept()  # Close dialog indicating success to parent

    def _start_worker(self, method, url, payload=None, on_success=None):
        self.save_btn.setEnabled(False)
        self.thread = QThread()
        self.worker = InvoiceDetailsWorker(method, url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if on_success:
            self.worker.success.connect(on_success)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.save_btn.setEnabled(True))
        self.thread.start()

    def show_error(self, message):
        QMessageBox.critical(self, "خطأ", message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (
            hasattr(self, "old_pos")
            and self.old_pos
            and event.buttons() == Qt.LeftButton
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

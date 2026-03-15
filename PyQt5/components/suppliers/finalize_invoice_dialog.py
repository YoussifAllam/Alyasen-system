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
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class FinalizeInvoiceWorker(QObject):
    """Worker to handle the final payment POST and subsequent GET request."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)  # Will emit the updated supplier info
    error = pyqtSignal(str)

    def __init__(self, supplier_id, payment_payload):
        super().__init__()
        self.supplier_id = supplier_id
        self.payment_payload = payment_payload
        self.payment_url = f"{BACKEND_BASE_URL}/suppliers/invoice/info/"
        self.supplier_info_url = f"{BACKEND_BASE_URL}/suppliers/info/?id={self.supplier_id}"

    @pyqtSlot()
    def run(self):
        try:
            # Step 1: Post the payment
            payment_response = request("PATCH", self.payment_url, json=self.payment_payload, timeout=15)
            if payment_response.status_code not in [200, 201]:
                self.error.emit(f"فشل حفظ الدفعة: {payment_response.text}")
                return

            # Step 2: If payment is successful, fetch the updated supplier info
            info_response = request("GET", self.supplier_info_url, timeout=15)
            if info_response.status_code == 200:
                self.success.emit(info_response.json())
            else:
                self.error.emit("تم حفظ الدفعة، ولكن فشل تحديث بيانات المورد.")

        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class FinalizeInvoiceDialog(QDialog):
    # This signal will carry the full, updated supplier data upon success
    invoice_finalized = pyqtSignal(dict)

    def __init__(self, invoice_num, supplier_id, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.supplier_id = supplier_id

        self.setWindowTitle("الدفعة المقدمة للفاتورة")
        self.setMinimumSize(400, 250)
        self.setModal(True)

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
        title_text = QLabel("الدفعة المقدمة")
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

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.total_display = QLineEdit("0")
        # self.total_display.setReadOnly(True)
        self.paid_input = QLineEdit("0")

        form_layout.addRow("إجمالي الفاتورة:", self.total_display)
        form_layout.addRow("المبلغ المدفوع:", self.paid_input)
        content_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("حفظ الفاتورة")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save)  # FIXED: Connect to the correct handler
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
        invoice_total_amount = self.total_display.text().strip()
        paid_amount_str = self.paid_input.text().strip()
        try:
            paid_amount = float(paid_amount_str)
            if paid_amount < 0:
                QMessageBox.warning(self, "خطأ", "لا يمكن أن يكون المبلغ المدفوع سالبًا.")
                return
        except (ValueError, TypeError):
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال مبلغ صحيح.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "invoice_num": self.invoice_num,
            "invoice_total_amount":invoice_total_amount ,
            "paid_amount": paid_amount_str,
            "username": username,
            "notes": "",
        }

        self._start_finalize_request(self.supplier_id, payload)

    def _start_finalize_request(self, supplier_id, payload):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = FinalizeInvoiceWorker(supplier_id, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_finalize_success)
        self.worker.error.connect(self.on_finalize_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_finalize_success(self, updated_supplier_data):
        self._set_loading(False)
        self.invoice_finalized.emit(updated_supplier_data)
        self.accept()

    def on_finalize_error(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

    def _set_loading(self, is_loading):
        self.save_button.setDisabled(is_loading)
        self.paid_input.setDisabled(is_loading)
        self.save_button.setText("جاري الحفظ..." if is_loading else "حفظ الفاتورة")

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

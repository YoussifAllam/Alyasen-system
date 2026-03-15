# Create a new file (e.g., alternative_dialog.py) and place this content inside.

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QWidget,
    QDateEdit,
    QTableWidget,
    QHeaderView,
    QGroupBox,
    QTableWidgetItem,
    QMessageBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QPoint, QDate, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

# Assuming this constant is accessible from this location
from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class AlternativeApiWorker(QObject):
    """Worker for handling API requests for alternatives."""

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
            response = request(self.method, self.url, json=self.payload, timeout=15)
            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            elif response.status_code == 204 and self.method == "DELETE":
                self.success.emit({"status": "deleted"})
            else:
                self.error.emit(f"خطأ من الخادم: {response.text}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class AlternativesDialog(QDialog):
    data_changed = pyqtSignal()

    def __init__(self, worker_name, worker_id, parent=None):
        super().__init__(parent)
        self.worker_name = worker_name
        self.worker_id = worker_id
        # Updated Title
        self.setWindowTitle(f"سجل بدائل العامل: {worker_name}")
        self.setMinimumSize(1000, 700)
        self.setModal(True)

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

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
        # Updated Title Bar Text
        title_text = QLabel(f"سجل بدائل العامل: {worker_name}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.accept)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Updated GroupBox Title
        form_group = QGroupBox("إضافة مبلغ بديل جديد")
        form_layout = QGridLayout(form_group)
        self.date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        # Renamed input variable for clarity, but the type is the same
        self.amount_input = QLineEdit(placeholderText="مبلغ البديل")
        self.reason_input = QLineEdit(placeholderText="سبب البديل (اختياري)")
        self.add_button = QPushButton("إضافة")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.handle_add_alternative)

        form_layout.addWidget(QLabel("التاريخ:"), 0, 0)
        form_layout.addWidget(self.date_input, 0, 1)
        form_layout.addWidget(QLabel("السبب:"), 0, 2)
        form_layout.addWidget(self.reason_input, 0, 3)
        form_layout.addWidget(QLabel("المبلغ:"), 1, 0)
        form_layout.addWidget(self.amount_input, 1, 1)
        form_layout.addWidget(self.add_button, 1, 3)
        content_layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        # Updated Table Headers
        self.table.setHorizontalHeaderLabels(["تاريخ البديل", "المبلغ", "السبب", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(3, 120)
        self.table.verticalHeader().setDefaultSectionSize(65)
        content_layout.addWidget(self.table, 1)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.next_button.clicked.connect(self.handle_next_page)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        content_layout.addLayout(pagination_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None
        self.fetch_alternatives()

    def handle_add_alternative(self):
        amount_str = self.amount_input.text().strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            # Updated Warning Message
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال مبلغ بديل صحيح وموجب.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "worker_id": self.worker_id,
            "date": self.date_input.date().toString("yyyy-MM-dd"),
            "reason": self.reason_input.text().strip(),
            "username": username,
            "amount": amount,
        }

        # Updated API Endpoint
        url = f"{BACKEND_BASE_URL}/workers/alternative/"
        self._start_api_request("POST", url, payload, self.on_add_success)

    def on_add_success(self, response):
        # Updated Success Message
        QMessageBox.information(self, "نجاح", "تم تسجيل مبلغ البديل بنجاح.")
        self.reason_input.clear()
        self.amount_input.clear()
        self.data_changed.emit()
        self.fetch_alternatives()

    def fetch_alternatives(self):
        # Updated API Endpoint
        url = f"{BACKEND_BASE_URL}/workers/alternative/?worker_id={self.worker_id}"
        self._start_api_request("GET", url, on_success=self.handle_api_response)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_api_request("GET", self.next_page_url, on_success=self.handle_api_response)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_api_request("GET", self.prev_page_url, on_success=self.handle_api_response)

    def handle_api_response(self, response_data):
        data = response_data.get("data", {})
        results = data.get("results", [])
        self.next_page_url = data.get("next")
        self.prev_page_url = data.get("previous")
        self.total_count = data.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()

    def populate_table(self, results):
        self.table.setRowCount(0)
        for item in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            alternative_id = item.get("id")

            # Updated Keys (assuming backend returns 'alternative_date' and 'alternative_amount')
            date_item = QTableWidgetItem(item.get("date", ""))
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setData(Qt.UserRole, alternative_id)
            amount_item = QTableWidgetItem(f"{item.get('amount', 0):,.2f}")
            amount_item.setTextAlignment(Qt.AlignCenter)
            reason_item = QTableWidgetItem(item.get("reason", ""))
            reason_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_pos, 0, date_item)
            self.table.setItem(row_pos, 1, amount_item)
            self.table.setItem(row_pos, 2, reason_item)

            delete_button = QPushButton("حذف")
            delete_button.setObjectName("dangerButton")
            delete_button.clicked.connect(lambda ch, aid=alternative_id: self.handle_delete_alternative(aid))
            button_container = QWidget()
            layout = QHBoxLayout(button_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(delete_button)
            self.table.setCellWidget(row_pos, 3, button_container)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"الإجمالي: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد مبالغ بدائل")  # Updated text

    def handle_delete_alternative(self, alternative_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            # Updated confirmation message
            "هل أنت متأكد من حذف مبلغ البديل هذا؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")
            # Updated Payload Key
            payload = {"alternative_id": alternative_id, "username": username}
            # Updated API Endpoint
            url = f"{BACKEND_BASE_URL}/workers/alternative/"
            self._start_api_request("DELETE", url, payload, on_success=self.on_delete_success)

    def on_delete_success(self, response):
        # Updated success message
        QMessageBox.information(self, "نجاح", "تم حذف مبلغ البديل.")
        self.data_changed.emit()
        self.fetch_alternatives()

    def _start_api_request(self, method, url, payload=None, on_success=None):
        self._set_loading(True)
        self.thread = QThread()
        # Updated Worker Class
        self.worker = AlternativeApiWorker(method, url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if on_success:
            self.worker.success.connect(on_success)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self._set_loading(False))
        self.thread.start()

    def _set_loading(self, is_loading):
        self.add_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.add_button.setText("جاري..." if is_loading else "إضافة")

    def show_error(self, message):
        self._set_loading(False)
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

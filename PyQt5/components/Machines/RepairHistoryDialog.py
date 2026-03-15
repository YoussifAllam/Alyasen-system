from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QLineEdit,
    QDialog,
    QFrame,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QWidget,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QObject,
    pyqtSlot,
    QThread,
    QPoint,
    QDate,
)
from requests import request, get, exceptions
import qtawesome as qta  # Import qtawesome

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class ApiWorker(QObject):
    """Worker for handling generic API requests (JSON/Image)."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    image_success = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, response_type="json"):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.response_type = response_type

    @pyqtSlot()
    def run(self):
        try:
            # Note: Using 'json' argument in requests handles the Content-Type header
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201, 204]:
                if self.response_type == "json":
                    self.success.emit(response.json() if response.content else {})
                elif self.response_type == "image":
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
                else:
                    self.success.emit({})
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_data.get("الخطاء", response.text))
                    if isinstance(error_msg, dict):
                        error_msg = next(iter(error_msg.values()))[0]
                    self.error.emit(str(error_msg) or f"خطأ من الخادم: {response.status_code}")
                except Exception:
                    self.error.emit(response.text or f"خطأ من الخادم: {response.status_code}")

        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class RepairHistoryDialog(QDialog):
    def __init__(self, machine_id, parent=None):
        super().__init__(parent)
        self.machine_id = machine_id
        self.setWindowTitle("سجل صيانة الآلة")
        self.setMinimumSize(800, 700)
        self.setModal(True)

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

        # --- References for API threads/workers ---
        self.api_thread = None
        self.api_worker = None

        # --- Frameless Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        # --- Main Layout (holds the container) ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Dialog Container ---
        dialog_container = QFrame()
        dialog_container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(dialog_container)
        container_layout.setContentsMargins(1, 1, 1, 1)  # Thin margin for the title bar
        container_layout.setSpacing(0)

        # --- 1. Custom Title Bar ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        self.title_bar.setMinimumHeight(40)
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 10, 0)

        title_text = QLabel("سجل صيانة الآلة")
        title_text.setObjectName("titleBarText")

        close_button = QPushButton()
        close_button.setObjectName("closeButton")  # Use "closeButton" for red hover
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))  # Example icon
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)

        container_layout.addWidget(self.title_bar)

        # --- 2. Content Area ---
        content_area = QWidget()
        content_area_layout = QVBoxLayout(content_area)
        content_area_layout.setContentsMargins(20, 20, 20, 20)  # Standard padding
        content_area_layout.setSpacing(15)

        # --- Form/Inputs ---
        form_grid = QHBoxLayout()
        form_grid.setSpacing(10)
        self.details_input = QLineEdit(placeholderText="تفاصيل الصيانة")
        self.amount_input = QLineEdit(placeholderText="التكلفة")

        self.date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.date_input.setFixedWidth(150)
        # self.date_input.setDisplayFormat("yyyy-MM-dd")

        self.btn_add_record = QPushButton("➕ إضافة")
        self.btn_add_record.setObjectName("primaryButton")
        self.btn_add_record.setFixedWidth(120)

        form_grid.addWidget(QLabel("التفاصيل:"))
        form_grid.addWidget(self.details_input, 1)
        form_grid.addWidget(QLabel("التكلفة:"))
        form_grid.addWidget(self.amount_input)
        form_grid.addWidget(QLabel("التاريخ:"))
        form_grid.addWidget(self.date_input)
        form_grid.addWidget(self.btn_add_record)
        content_area_layout.addLayout(form_grid)

        # --- Table Header ---
        table_header = QLabel("سجلات الصيانة الحالية")
        table_header.setObjectName("sectionHeader")  # Style like a section header
        content_area_layout.addWidget(table_header)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["كود", "التفاصيل", "التكلفة", "التاريخ", "إجراء"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(65)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(4, 130)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        content_area_layout.addWidget(self.table, 1)

        # --- Pagination ---
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(0, 10, 0, 0)
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل السجلات")
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.next_button.clicked.connect(self.handle_next_page)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        content_area_layout.addLayout(pagination_layout)

        # Add content area to container
        container_layout.addWidget(content_area)

        # Add container to the main dialog layout
        main_layout.addWidget(dialog_container)

        # --- Connect Signals ---
        self.btn_add_record.clicked.connect(self.handle_add_record)

        # --- Initial Data Fetch ---
        self.handle_fetch_history()

    # --- Mouse Move Events for Frameless Window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    # --- API and Logic Methods ---
    def handle_fetch_history(self):
        url = f"{BACKEND_BASE_URL}/machines/repair-history/?machine_id={self.machine_id}"
        self._start_api_fetch(url, self.handle_fetch_response)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_api_fetch(self.next_page_url, self.handle_fetch_response)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_api_fetch(self.prev_page_url, self.handle_fetch_response)

    def handle_fetch_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()

    def populate_table(self, records):
        self.table.setRowCount(0)
        for record in records:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            record_id = record.get("id")

            id_item = QTableWidgetItem(str(record_id))
            id_item.setData(Qt.UserRole, record_id)
            details_item = QTableWidgetItem(record.get("details", ""))
            amount_item = QTableWidgetItem(str(record.get("amount", "")))
            date_item = QTableWidgetItem(record.get("date", ""))

            btn_delete = QPushButton("🗑️ حذف")
            btn_delete.setObjectName("dangerButton")
            btn_delete.clicked.connect(lambda _, r_id=record_id: self.handle_delete_record(r_id))

            self.table.setItem(row_pos, 0, id_item)
            self.table.setItem(row_pos, 1, details_item)
            self.table.setItem(row_pos, 2, amount_item)
            self.table.setItem(row_pos, 3, date_item)
            self.table.setCellWidget(row_pos, 4, btn_delete)

            # Center alignment for items
            id_item.setTextAlignment(Qt.AlignCenter)
            details_item.setTextAlignment(Qt.AlignCenter)
            amount_item.setTextAlignment(Qt.AlignCenter)
            date_item.setTextAlignment(Qt.AlignCenter)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي السجلات: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد سجلات")

    def get_english_date_string(self, qdate):
        """Convert QDate to English format string for API"""
        return qdate.toString("yyyy-MM-dd")

    def handle_add_record(self):
        details = self.details_input.text().strip()
        amount = self.amount_input.text().strip()
        date = self.get_english_date_string(self.date_input.date())

        if not details or not amount:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال التفاصيل والتكلفة.")
            return

        try:
            float(amount)
        except ValueError:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال تكلفة صالحة (رقم).")
            return

        payload = {
            "machine_id": self.machine_id,
            "details": details,
            "amount": amount,
            "date": date,
        }
        url = f"{BACKEND_BASE_URL}/machines/repair-history/"
        self._start_api_fetch(
            url,
            on_success=self.on_add_success,
            method="POST",
            payload=payload,
        )

    def on_add_success(self, _):
        QMessageBox.information(self, "نجاح", "تم إضافة سجل الصيانة بنجاح.")
        self.details_input.clear()
        self.amount_input.clear()
        self.handle_fetch_history()

    def handle_delete_record(self, record_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا السجل؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            payload = {"machine_repair_history_id": record_id}
            url = f"{BACKEND_BASE_URL}/machines/repair-history/"
            self._start_api_fetch(
                url,
                on_success=self.on_delete_success,
                method="DELETE",
                payload=payload,
            )

    def on_delete_success(self, _):
        QMessageBox.information(self, "نجاح", "تم حذف السجل بنجاح.")
        self.handle_fetch_history()

    def _start_api_fetch(self, url, on_success, method="GET", payload=None):
        """Standard API fetch."""
        self._set_loading(True)
        self.api_thread = QThread()
        self.api_worker = ApiWorker(method, url, payload=payload, response_type="json")
        self.api_worker.moveToThread(self.api_thread)

        self.api_thread.started.connect(self.api_worker.run)
        self.api_worker.success.connect(on_success)
        self.api_worker.error.connect(self.show_error_message)
        self.api_worker.finished.connect(self.api_thread.quit)
        self.api_worker.finished.connect(lambda: self._set_loading(False))

        # Clean up
        self.api_worker.finished.connect(self.api_worker.deleteLater)
        self.api_thread.finished.connect(self.api_thread.deleteLater)

        self.api_thread.start()

    def _set_loading(self, is_loading):
        self.btn_add_record.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

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
)
from PyQt5.QtCore import Qt, QPoint, QDate, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..utils.api_errors import format_request_exception, parse_api_response


class AbsenceApiWorker(QObject):
    """Worker thread for handling GET, POST, and DELETE requests for absence data."""

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
            ok, data = parse_api_response(response)
            if ok:
                self.success.emit(data)
            else:
                self.error.emit(data)
        except exceptions.RequestException as exc:
            self.error.emit(format_request_exception(exc))
        finally:
            self.finished.emit()


class AbsenceDialog(QDialog):
    data_changed = pyqtSignal()  # Signal to notify the parent that data was modified

    def __init__(self, worker_name, worker_id, parent=None):
        super().__init__(parent)
        self.worker_name = worker_name
        self.worker_id = worker_id
        self.setWindowTitle(f"سجل غياب العامل: {worker_name}")
        self.setMinimumSize(1000, 600)
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
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(f"سجل غياب العامل: {worker_name}")
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

        form_group = QGroupBox("تسجيل غياب جديد")
        form_layout = QHBoxLayout(form_group)
        form_layout.setSpacing(15)

        self.absence_date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.absence_date_input.setDisplayFormat("yyyy/M/d")
        self.absence_reason_input = QLineEdit(placeholderText="سبب الغياب (اختياري)")
        self.add_button = QPushButton("إضافة")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.handle_add_absence)

        form_layout.addWidget(QLabel("تاريخ الغياب:"))
        form_layout.addWidget(self.absence_date_input)
        form_layout.addWidget(self.absence_reason_input, 1)
        form_layout.addWidget(self.add_button)
        content_layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["تاريخ الغياب", "سبب الغياب", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(2, 70)
        self.table.verticalHeader().setDefaultSectionSize(75)
        content_layout.addWidget(self.table, 1)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.fetch_absences()

    def handle_add_absence(self):
        """Validates inputs and starts the POST request to add an absence."""
        absence_date = self.absence_date_input.date().toString("yyyy-MM-dd")
        absence_reason = self.absence_reason_input.text().strip()

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "worker_id": self.worker_id,
            "absence_date": absence_date,
            "absence_reason": absence_reason,
            "username": username,
        }

        url = f"{BACKEND_BASE_URL}/workers/absence/"
        self._start_api_request("POST", url, payload, self.on_add_success)

    def on_add_success(self, response):
        QMessageBox.information(self, "نجاح", "تم تسجيل الغياب بنجاح.")
        self.absence_reason_input.clear()
        self.data_changed.emit()  # Notify parent
        self.fetch_absences()

    def fetch_absences(self):
        """Fetches the absence history for the worker."""
        url = f"{BACKEND_BASE_URL}/workers/absence/?worker_id={self.worker_id}"
        self._start_api_request("GET", url, on_success=self.populate_table)

    def _start_api_request(self, method, url, payload=None, on_success=None):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = AbsenceApiWorker(method, url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if on_success:
            self.worker.success.connect(on_success)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self._set_loading(False))
        self.thread.start()

    def populate_table(self, response_data):
        """Populates the table with absence data from the API."""
        data = response_data.get("data", {})
        results = data.get("results", [])
        self.table.setRowCount(0)
        for item in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            absence_id = item.get("id")
            date_item = QTableWidgetItem(item.get("absence_date", ""))
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setData(Qt.UserRole, absence_id)  # Store the ID

            reason_item = QTableWidgetItem(item.get("absence_reason", ""))
            reason_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_pos, 0, date_item)
            self.table.setItem(row_pos, 1, reason_item)

            delete_button = QPushButton("حذف")
            delete_button.setObjectName("dangerButton")
            delete_button.clicked.connect(lambda ch, aid=absence_id: self.handle_delete_absence(aid))

            button_container = QWidget()
            layout = QHBoxLayout(button_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(delete_button)
            self.table.setCellWidget(row_pos, 2, button_container)

    def handle_delete_absence(self, absence_id):
        """Asks for confirmation and starts the DELETE request."""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف يوم الغياب هذا؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")

            payload = {"absence_id": absence_id, "username": username}
            url = f"{BACKEND_BASE_URL}/workers/absence/"
            self._start_api_request("DELETE", url, payload, on_success=self.on_delete_success)

    def on_delete_success(self, response):
        QMessageBox.information(self, "نجاح", "تم حذف يوم الغياب.")
        self.data_changed.emit()  # Notify parent
        self.fetch_absences()

    def _set_loading(self, is_loading):
        self.add_button.setDisabled(is_loading)
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

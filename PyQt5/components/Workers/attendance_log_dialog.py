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
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QDateTime
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class AttendanceLogWorker(QObject):
    """Worker thread for fetching attendance log data."""

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


class AttendanceLogDialog(QDialog):
    def __init__(self, worker_name, worker_id, parent=None):
        super().__init__(parent)
        self.worker_id = worker_id
        self.setWindowTitle(f"سجل الحضور والانصراف: {worker_name}")
        self.setMinimumSize(800, 600)
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
        title_text = QLabel(f"سجل الحضور والانصراف: {worker_name}")
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

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["تاريخ ووقت الحضور", "تاريخ ووقت الانصراف"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        content_layout.addWidget(self.table)

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

        self.fetch_attendance_log()

    def fetch_attendance_log(self, url=None):
        if not url:
            url = f"{BACKEND_BASE_URL}/workers/attendance/?worker_id={self.worker_id}"

        self.thread = QThread()
        self.worker = AttendanceLogWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()

    def populate_table(self, results):
        self.table.setRowCount(0)
        for item in results:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            enter_date_str = item.get("enter_date")
            exit_date_str = item.get("exit_date")

            enter_dt = QDateTime.fromString(enter_date_str, Qt.ISODate)
            exit_dt = QDateTime.fromString(exit_date_str, Qt.ISODate)

            enter_item = QTableWidgetItem(enter_dt.toString("yyyy-MM-dd hh:mm AP"))
            exit_item = QTableWidgetItem(
                exit_dt.toString("yyyy-MM-dd hh:mm AP") if exit_date_str else "لم ينصرف بعد"
            )

            enter_item.setTextAlignment(Qt.AlignCenter)
            exit_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_pos, 0, enter_item)
            self.table.setItem(row_pos, 1, exit_item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي السجلات: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد سجلات")

    def handle_next_page(self):
        if self.next_page_url:
            self.fetch_attendance_log(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self.fetch_attendance_log(self.prev_page_url)

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

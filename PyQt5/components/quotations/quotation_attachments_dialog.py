from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QMessageBox,
    QFrame,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QThread, QUrl, QObject, pyqtSignal, pyqtSlot, QPoint
from PyQt5.QtGui import QDesktopServices
from requests import request, exceptions
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
import qtawesome as qta


class QuotationApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, files=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.files = files

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "POST" and self.files:
                response = request(
                    self.method,
                    self.url,
                    data=self.payload,
                    files=self.files,
                    timeout=15,
                )
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(
                    f"خطأ من الخادم: {response.status_code}\n{response.text}"
                )
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class QuotationAttachmentsDialog(QDialog):
    def __init__(self, q_id, parent=None):
        super().__init__(parent)
        self.q_id = q_id
        self.setWindowTitle(f"مرفقات عرض السعر (كود: {self.q_id})")
        self.resize(800, 400)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        # Load stylesheet logic from parent if needed, or rely on global app style
        self.setup_ui()
        self.load_attachments()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("dialogContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel(f"مرفقات عرض السعر (كود: {self.q_id})")
        title_text.setObjectName("titleBarText")

        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)

        layout.addWidget(self.title_bar)

        # Content Area Layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 0, 15, 15)
        content_layout.setSpacing(15)

        self.info_label = QLabel("جاري تحميل المرفقات...")
        self.info_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        headers = ["كود", "الرابط", "إجراءات"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setDefaultSectionSize(65)

        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(60)
        content_layout.addWidget(self.table)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        content_layout.addWidget(close_btn)

        layout.addLayout(content_layout)

        main_layout.addWidget(container)

    def load_attachments(self):
        url = f"{BACKEND_BASE_URL}/quotations/attachments/?q_id={self.q_id}"

        self.thread = QThread()
        self.worker = QuotationApiWorker("GET", url, payload=None)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def handle_api_response(self, response_data):
        self.info_label.hide()
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])

        if not results:
            self.info_label.setText("لا يوجد مرفقات لهذا العرض.")
            self.info_label.show()
            return

        self.populate_table(results)

    def populate_table(self, attachments):
        self.table.setRowCount(0)
        for att in attachments:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            att_id = str(att.get("id", ""))
            att_url = str(att.get("attachment", ""))

            id_item = QTableWidgetItem(att_id)
            id_item.setTextAlignment(Qt.AlignCenter)
            url_item = QTableWidgetItem(att_url)
            url_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            self.table.setItem(row_pos, 0, id_item)
            self.table.setItem(row_pos, 1, url_item)

            open_btn = QPushButton("فتح")
            open_btn.setObjectName("primaryButton")
            open_btn.clicked.connect(lambda _, url=att_url: self.open_attachment(url))
            self.table.setCellWidget(row_pos, 2, open_btn)

    def open_attachment(self, url):
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def show_error_message(self, message):
        self.info_label.setText("حدث خطأ أثناء تحميل البيانات.")
        QMessageBox.critical(self, "خطأ", message)

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and hasattr(self, "title_bar")  # noqa
            and self.title_bar.underMouse()  # noqa
        ):
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

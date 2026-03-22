import qtawesome as qta
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QMessageBox,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from requests import request, exceptions
from .Main_Ui_Components.constant import BACKEND_BASE_URL


class NotificationApiWorker(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, headers=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.headers = headers or {}

    def run(self):
        try:
            if self.method == "GET":
                response = request(
                    self.method,
                    self.url,
                    params=self.payload,
                    headers=self.headers,
                    timeout=15,
                )
            else:
                response = request(
                    self.method,
                    self.url,
                    json=self.payload,
                    headers=self.headers,
                    timeout=15,
                )

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get(
                        "error",
                        getattr(error_data, "message", f"HTTP {response.status_code}"),
                    )
                    self.error.emit(str(error_msg))
                except ValueError:
                    self.error.emit(
                        response.text or f"Server error: {response.status_code}"
                    )
        except exceptions.RequestException as e:
            self.error.emit(f"Connection failed: {e}")


class NotificationsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("الإشعارات")
        self.setMinimumSize(550, 650)
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
        title_text = QLabel("الإشعارات غير المقروءة")
        title_text.setObjectName("titleBarText")
        font = title_text.font()
        font.setPointSize(12)
        font.setBold(True)
        title_text.setFont(font)

        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)

        main_layout.addWidget(self.title_bar)

        # Content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.btn_mark_all_read = QPushButton("تحديد الكل كمقروء")
        self.btn_mark_all_read.setObjectName("primaryButton")
        self.btn_mark_all_read.clicked.connect(self.mark_all_as_read)
        header_layout.addWidget(self.btn_mark_all_read)
        content_layout.addLayout(header_layout)

        # Scroll area for notifications
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("QWidget { background: transparent; }")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content)
        content_layout.addWidget(self.scroll_area)

        # Loading label
        self.loading_label = QLabel("جاري تحميل الإشعارات...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.scroll_layout.addWidget(self.loading_label)

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        self.old_pos = None

    def showEvent(self, event):
        super().showEvent(event)
        self.load_notifications()

    def clear_notifications(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def set_loading(self, is_loading):
        self.clear_notifications()
        if is_loading:
            self.loading_label = QLabel("جاري تحميل الإشعارات...")
            self.loading_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(self.loading_label)

    def load_notifications(self):
        self.set_loading(True)
        url = f"{BACKEND_BASE_URL}/notifications/get-unreaded-notifications/"
        self.worker = NotificationApiWorker("GET", url)
        self.worker.success.connect(self.on_load_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_load_success(self, response_data):
        self.clear_notifications()
        notifications = response_data.get("data", [])

        if not notifications:
            empty_label = QLabel("لا توجد إشعارات غير مقروءة")
            empty_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
            self.btn_mark_all_read.setEnabled(False)
            return

        self.btn_mark_all_read.setEnabled(True)
        for notif in notifications:
            self.add_notification_item(notif)

        self.scroll_layout.addStretch()

    def add_notification_item(self, notif_data):
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setStyleSheet(
            """QFrame { border: 1px solid #d1d5db;
            border-radius: 4px; margin-bottom: 3px;
            padding: 3px;
            background-color: rgba(255, 255, 255, 0.05); } QLabel { border: none; background: transparent; }"""
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        title_label = QLabel(notif_data.get("title", ""))
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        title_label.setFont(font)

        msg_label = QLabel(notif_data.get("message", ""))
        msg_label.setWordWrap(True)
        font_msg = msg_label.font()
        font_msg.setPointSize(9)
        msg_label.setFont(font_msg)

        date_label = QLabel(
            notif_data.get("created_at", "")[:10]
            + " "
            + notif_data.get("created_at", "")[11:16]
        )
        font_date = date_label.font()
        font_date.setPointSize(8)
        date_label.setFont(font_date)
        date_label.setStyleSheet("color: #9ca3af;")

        btn_mark_read = QPushButton("مقروء")
        btn_mark_read.setCursor(Qt.PointingHandCursor)
        btn_mark_read.setStyleSheet(
            """QPushButton { background-color: #3b82f6; color: white; border-radius: 4px; padding: 4px 10px;
            font-size: 11px; font-weight: bold; }
            "QPushButton:hover { background-color: #2563eb; }"""
        )
        btn_mark_read.setIcon(qta.icon("fa5s.check", color="white"))
        btn_mark_read.clicked.connect(
            lambda _, uuid=notif_data.get("uuid"): self.mark_as_read(uuid)
        )

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(date_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_mark_read)

        layout.addWidget(title_label)
        layout.addWidget(msg_label)
        layout.addLayout(bottom_layout)

        self.scroll_layout.addWidget(frame)

    def mark_as_read(self, uuid):
        url = f"{BACKEND_BASE_URL}/notifications/mark-notification-as-read/"
        self.mark_worker = NotificationApiWorker(
            "PUT", url, payload={"notification_uuid": uuid}
        )
        self.mark_worker.success.connect(lambda response: self.load_notifications())
        self.mark_worker.error.connect(self.on_error)
        self.mark_worker.start()

    def mark_all_as_read(self):
        url = f"{BACKEND_BASE_URL}/notifications/mark-all-notifications-as-read/"
        self.mark_all_worker = NotificationApiWorker("PUT", url)
        self.mark_all_worker.success.connect(lambda response: self.load_notifications())
        self.mark_all_worker.error.connect(self.on_error)
        self.mark_all_worker.start()

    def on_error(self, error_msg):
        QMessageBox.warning(self, "خطأ", str(error_msg))

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

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QHeaderView,
    QStackedWidget,
    QWidget,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QPoint
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..utils.api_errors import format_request_exception, parse_api_response


class UserApiWorker(QObject):
    """Worker thread to handle GET, POST, and DELETE requests for user data."""

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
        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        finally:
            self.finished.emit()


class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إدارة المستخدمين")
        self.setMinimumSize(1200, 700)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel("إدارة المستخدمين")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.accept)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        self.main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        tabs_layout = QHBoxLayout()
        self.btn_current_users = QPushButton("المستخدمين الحاليين")
        self.btn_current_users.setObjectName("managementTabButton")
        self.btn_current_users.setCheckable(True)
        self.btn_pending_requests = QPushButton("طلبات التسجيل الجديدة")
        self.btn_pending_requests.setObjectName("managementTabButton")
        self.btn_pending_requests.setCheckable(True)
        tabs_layout.addWidget(self.btn_current_users)
        tabs_layout.addWidget(self.btn_pending_requests)
        tabs_layout.addStretch()

        self.stacked_widget = QStackedWidget()
        self.current_users_page = self.create_current_users_page()
        self.pending_requests_page = self.create_pending_requests_page()
        self.stacked_widget.addWidget(self.current_users_page)
        self.stacked_widget.addWidget(self.pending_requests_page)

        self.btn_current_users.clicked.connect(lambda: self.switch_tab(0))
        self.btn_pending_requests.clicked.connect(lambda: self.switch_tab(1))

        content_layout.addLayout(tabs_layout)
        content_layout.addWidget(self.stacked_widget)
        self.main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.switch_tab(0)

    def switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_current_users.setChecked(index == 0)
        self.btn_pending_requests.setChecked(index == 1)

        if index == 0:
            self.fetch_users(is_approved=True)
        else:
            self.fetch_users(is_approved=False)

    def fetch_users(self, is_approved):
        self._set_loading(True)
        url = f"{BACKEND_BASE_URL}/dashboard/users/?is_approvid={is_approved}"

        self.fetch_thread = QThread()
        self.fetch_worker = UserApiWorker("GET", url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)

        if is_approved:
            self.fetch_worker.success.connect(self.populate_current_users_table)
        else:
            self.fetch_worker.success.connect(self.populate_pending_requests_table)

        self.fetch_worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_worker.finished.connect(lambda: self._set_loading(False))
        self.fetch_thread.start()

    def create_current_users_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 15, 0, 0)
        self.current_users_table = QTableWidget()
        self.current_users_table.setColumnCount(5)
        self.current_users_table.setHorizontalHeaderLabels(
            ["الاسم", "البريد الإلكتروني", "نوع المستخدم", "تاريخ الانضمام", ""]
        )
        self.current_users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.current_users_table.setColumnWidth(4, 200)
        self.current_users_table.verticalHeader().setDefaultSectionSize(80)
        layout.addWidget(self.current_users_table)
        return page

    def create_pending_requests_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 15, 0, 0)
        self.pending_requests_table = QTableWidget()
        self.pending_requests_table.setColumnCount(5)
        self.pending_requests_table.setHorizontalHeaderLabels(
            ["الاسم", "البريد الإلكتروني", "نوع المستخدم", "تاريخ الطلب", ""]
        )
        self.pending_requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pending_requests_table.setColumnWidth(4, 220)
        self.pending_requests_table.verticalHeader().setDefaultSectionSize(80)
        layout.addWidget(self.pending_requests_table)
        return page

    def populate_current_users_table(self, response_data):
        users = response_data.get("data", [])
        table = self.current_users_table
        table.setRowCount(0)
        for user in users:
            row_pos = table.rowCount()
            table.insertRow(row_pos)
            user_uuid = user.get("uuid")
            name_item = QTableWidgetItem(user.get("name", ""))
            name_item.setData(Qt.UserRole, user_uuid)
            items = [
                name_item,
                QTableWidgetItem(user.get("email", "")),
                QTableWidgetItem(user.get("user_type", "")),
                QTableWidgetItem(user.get("created_Date", "")),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_pos, i, item)
            delete_button = QPushButton("حذف")
            delete_button.setObjectName("dangerButton")
            delete_button.clicked.connect(
                lambda ch, u=user_uuid, n=user.get("name"): self.handle_delete_user(u, n)
            )
            button_container = QWidget()
            layout = QHBoxLayout(button_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(delete_button)
            table.setCellWidget(row_pos, 4, button_container)

    def populate_pending_requests_table(self, response_data):
        users = response_data.get("data", [])
        table = self.pending_requests_table
        table.setRowCount(0)
        for user in users:
            row_pos = table.rowCount()
            table.insertRow(row_pos)
            user_uuid = user.get("uuid")
            name_item = QTableWidgetItem(user.get("name", ""))
            name_item.setData(Qt.UserRole, user_uuid)
            items = [
                name_item,
                QTableWidgetItem(user.get("email", "")),
                QTableWidgetItem(user.get("user_type", "")),
                QTableWidgetItem(user.get("created_Date", "")),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_pos, i, item)

            accept_button = QPushButton("قبول")
            accept_button.setObjectName("successButton")
            accept_button.clicked.connect(lambda ch, u=user_uuid: self.handle_accept_user(u))
            decline_button = QPushButton("رفض")
            decline_button.setObjectName("dangerButton")
            decline_button.clicked.connect(
                lambda ch, u=user_uuid, n=user.get("name"): self.handle_decline_user(u, n)
            )

            button_container = QWidget()
            layout = QHBoxLayout(button_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(accept_button)
            layout.addWidget(decline_button)
            table.setCellWidget(row_pos, 4, button_container)

    def handle_delete_user(self, user_uuid, user_name):
        if not user_uuid:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف المستخدم.")
            return
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من أنك تريد حذف المستخدم '{user_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            url = f"{BACKEND_BASE_URL}/dashboard/users/"
            payload = {"user_uuid": user_uuid}
            self._start_api_action_request("DELETE", url, payload, self.on_delete_success)

    def handle_accept_user(self, user_uuid):
        if not user_uuid:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف المستخدم.")
            return
        url = f"{BACKEND_BASE_URL}/dashboard/users/"
        payload = {"user_uuid": user_uuid}
        self._start_api_action_request("POST", url, payload, self.on_accept_success)

    def handle_decline_user(self, user_uuid, user_name):
        if not user_uuid:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف المستخدم.")
            return
        reply = QMessageBox.question(
            self,
            "تأكيد الرفض",
            f"هل أنت متأكد من أنك تريد رفض طلب '{user_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            url = f"{BACKEND_BASE_URL}/dashboard/users/"
            payload = {"user_uuid": user_uuid}
            self._start_api_action_request("DELETE", url, payload, self.on_decline_success)

    def _start_api_action_request(self, method, url, payload, on_success):
        self._set_loading(True)
        self.action_thread = QThread()
        self.action_worker = UserApiWorker(method, url, payload)
        self.action_worker.moveToThread(self.action_thread)
        self.action_thread.started.connect(self.action_worker.run)
        self.action_worker.success.connect(on_success)
        self.action_worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.action_worker.finished.connect(self.action_thread.quit)
        self.action_worker.finished.connect(lambda: self._set_loading(False))
        self.action_thread.start()

    def on_delete_success(self, response):
        QMessageBox.information(self, "نجاح", "تم حذف المستخدم بنجاح.")
        self.fetch_users(is_approved=True)

    def on_accept_success(self, response):
        QMessageBox.information(self, "نجاح", "تم قبول المستخدم بنجاح.")
        self.fetch_users(is_approved=False)

    def on_decline_success(self, response):
        QMessageBox.information(self, "نجاح", "تم رفض المستخدم بنجاح.")
        self.fetch_users(is_approved=False)

    def _set_loading(self, is_loading):
        self.btn_current_users.setDisabled(is_loading)
        self.btn_pending_requests.setDisabled(is_loading)

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

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QFormLayout,
    QWidget,
    QFileDialog,
    QDateEdit,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPoint, QDate, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class UpdateWorkerApiWorker(QObject):
    """Worker for handling the PATCH request for updating worker info."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, payload=None, files=None):
        super().__init__()
        self.url = url
        self.payload = payload
        self.files = files

    @pyqtSlot()
    def run(self):
        try:
            if self.files:
                response = request("PATCH", self.url, data=self.payload, files=self.files, timeout=15)
            else:
                response = request("PATCH", self.url, json=self.payload, timeout=15)

            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.text}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class UpdateWorkerDialog(QDialog):
    update_successful = pyqtSignal(dict)

    def __init__(self, worker_id, worker_data, parent=None):
        super().__init__(parent)
        self.worker_id = worker_id
        self.setWindowTitle("تعديل بيانات العامل")
        self.setMinimumSize(500, 550)
        self.setModal(True)
        self.new_profile_pic_path = None

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
        title_text = QLabel(f"تعديل بيانات: {worker_data.get('name', '')}")
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
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(worker_data.get("name", ""))
        self.phone_input = QLineEdit(worker_data.get("phone", ""))
        self.job_input = QLineEdit(worker_data.get("job", ""))
        self.daily_salary_input = QLineEdit(str(worker_data.get("daily_salary", 0.0)))

        start_date_str = worker_data.get("work_start_date", "")
        self.start_date_input = QDateEdit(calendarPopup=True)
        if start_date_str:
            self.start_date_input.setDate(QDate.fromString(start_date_str, "yyyy-MM-dd"))

        self.profile_pic_label = QLabel("اختر صورة جديدة (اختياري)")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setMinimumHeight(120)
        self.profile_pic_label.setObjectName("imagePreview")
        btn_choose_pic = QPushButton("اختيار صورة")
        btn_choose_pic.clicked.connect(self.choose_profile_picture)

        form_layout.addRow("الاسم:", self.name_input)
        form_layout.addRow("رقم الهاتف:", self.phone_input)
        form_layout.addRow("الوظيفة:", self.job_input)
        form_layout.addRow("الراتب اليومي:", self.daily_salary_input)
        form_layout.addRow("تاريخ بدء العمل:", self.start_date_input)
        form_layout.addRow(self.profile_pic_label)
        form_layout.addRow(btn_choose_pic)
        content_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("حفظ التعديلات")
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
        """Validates inputs and starts the update API request."""
        try:
            daily_salary = float(self.daily_salary_input.text().strip())
            if daily_salary < 0:
                raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال راتب يومي صالح.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "worker_id": self.worker_id,
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "job": self.job_input.text().strip(),
            "daily_salary": daily_salary,
            "work_start_date": self.start_date_input.date().toString("yyyy-MM-dd"),
            "username": username,
        }

        files = None
        if self.new_profile_pic_path:
            files = {"profile_picture": open(self.new_profile_pic_path, "rb")}

        url = f"{BACKEND_BASE_URL}/workers/info/"
        self._start_update_request(url, payload, files)

    def _start_update_request(self, url, payload, files):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = UpdateWorkerApiWorker(url, payload, files)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_update_success)
        self.worker.error.connect(self.on_update_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_update_success(self, response_data):
        self._set_loading(False)
        self.update_successful.emit(response_data)
        self.accept()

    def on_update_error(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ في التحديث", message)

    def _set_loading(self, is_loading):
        self.save_button.setDisabled(is_loading)
        self.save_button.setText("جاري الحفظ..." if is_loading else "حفظ التعديلات")

    def choose_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر صورة جديدة", "", "Image files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.new_profile_pic_path = file_path
            pixmap = QPixmap(file_path)
            self.profile_pic_label.setPixmap(
                pixmap.scaled(
                    self.profile_pic_label.width(),
                    self.profile_pic_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def get_data(self):
        """This function is not needed when the dialog handles its own API calls."""
        pass

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

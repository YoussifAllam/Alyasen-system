from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QMessageBox,
    QFrame,
    QWidget,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QObject, pyqtSlot
from requests import get, exceptions, request
from PyQt5.QtGui import QPixmap, QImage
import qtawesome as qta

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class ApiWorker(QObject):
    """Worker for handling API requests."""

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
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                if self.response_type == "json":
                    self.success.emit(response.json())
                else:
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
            else:
                self.error.emit(f"{response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class ProjectSelectionDialog(QDialog):
    project_selected = pyqtSignal(dict)  # Emits full project dictionary

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار مشروع")
        self.setFixedSize(500, 350)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.projects_list = []
        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        # Main Container
        container = QFrame()
        container.setObjectName("dialogContainer")
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel("اختيار مشروع")
        title_text.setObjectName("titleBarText")

        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)

        self.main_layout.addWidget(self.title_bar)

        # Content Area
        content_area = QWidget()
        layout = QVBoxLayout(content_area)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        header_label = QLabel("برجاء اختيار المشروع الذي ترغب في العمل عليه:")
        header_label.setObjectName("dialogHeader")
        layout.addWidget(header_label)

        self.project_combobox = QComboBox()
        self.project_combobox.setPlaceholderText("جاري التحميل...")
        self.project_combobox.setEnabled(False)
        layout.addWidget(self.project_combobox)

        btn_layout = QHBoxLayout()
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        self.next_button = QPushButton("التالي")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.handle_next)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.next_button)

        layout.addLayout(btn_layout)

        self.main_layout.addWidget(content_area)
        self.main_layout.addStretch()

        # Set the main layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(container)
        self.old_pos = None

    def load_projects(self):
        url = f"{BACKEND_BASE_URL}/projects/"
        self.thread = QThread()
        self.worker = ApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_projects_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_projects_loaded(self, response_data):
        data = response_data.get("data", {})
        self.projects_list = data.get("results", [])

        self.project_combobox.clear()
        if not self.projects_list:
            self.project_combobox.setPlaceholderText("لا توجد مشاريع متباحة")
            return

        self.project_combobox.setPlaceholderText("اختر المشروع...")
        for project in self.projects_list:
            self.project_combobox.addItem(project.get("name"), project)

        self.project_combobox.setEnabled(True)
        self.next_button.setEnabled(True)

    def on_error(self, message):
        self.project_combobox.setPlaceholderText("فشل تحميل المشاريع")
        QMessageBox.warning(self, "خطأ", f"فشل تحميل المشاريع:\n{message}")

    def handle_next(self):
        selected_project = self.project_combobox.currentData()
        if selected_project:
            self.project_selected.emit(selected_project)
            self.accept()
        else:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع أولاً.")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
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

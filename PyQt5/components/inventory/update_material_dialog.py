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
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class UpdateMaterialWorker(QObject):
    """Worker to update material name."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request("PATCH", self.url, json=self.payload, timeout=15)
            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code} - {response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class UpdateMaterialDialog(QDialog):
    def __init__(self, old_name, old_price, old_buy_price, parent=None):
        super().__init__(parent)
        self.old_name = old_name
        self.setWindowTitle("تعديل بيانات الخامة")
        self.setMinimumSize(450, 250)
        self.setModal(True)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

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

        title_text = QLabel(f"تعديل الخامة: {old_name}")
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
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.new_name_input = QLineEdit(old_name)
        self.new_buy_price_input = QLineEdit(str(old_buy_price))

        form_layout.addRow("(اختياري) الأسم الجديد:", self.new_name_input)
        form_layout.addRow("(اختياري) سعر الشراء الجديد:", self.new_buy_price_input)

        content_layout.addLayout(form_layout)

        # Action Buttons
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

        self.main_layout.addWidget(content_area)

        # Set the main layout for the dialog
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

    def handle_save(self):
        new_name = self.new_name_input.text().strip()
        new_buy_price = self.new_buy_price_input.text().strip()
        if not new_name and not new_buy_price:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم الخامة الجديد او سعر الشراء الجديد.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "old_material_name": self.old_name,
            "material_name": new_name,
            "buy_price_per_unit": new_buy_price,
            "username": username,
        }

        url = f"{BACKEND_BASE_URL}/material-warehouse/materials/"
        self._start_worker(url, payload)

    def _start_worker(self, url, payload):
        self.save_button.setEnabled(False)
        self.thread = QThread()
        self.worker = UpdateMaterialWorker(url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.save_button.setEnabled(True))
        self.thread.start()

    def on_success(self, response):
        QMessageBox.information(self, "نجاح", "تم تعديل بيانات الخامة بنجاح.")
        self.accept()

    def on_error(self, message):
        QMessageBox.critical(self, "خطأ", message)

    def get_data(self):
        """Returns the data entered in the dialog."""
        return {
            "new_name": self.new_name_input.text().strip(),
            "new_price": "0",
            "new_buy_price": "0",
        }

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

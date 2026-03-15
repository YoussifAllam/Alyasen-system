from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QFrame,
    QFormLayout,
    QWidget,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class MaterialNamesWorker(QObject):
    """Worker thread to fetch material names from the API."""

    finished = pyqtSignal()
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                material_names = data.get("data", [])
                self.success.emit(material_names)
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم لجلب قائمة الخامات.")
        finally:
            self.finished.emit()


class UpdateQuantityWorker(QObject):
    """Worker thread to POST the updated material quantity."""

    finished = pyqtSignal()
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request("POST", self.url, json=self.payload, timeout=15)
            if response.status_code in [200, 201]:
                self.success.emit()
            else:
                try:
                    error_data = response.json()
                    detail = next(iter(error_data.values()), f"HTTP {response.status_code}")
                    if isinstance(detail, list):
                        detail = detail[0]
                    self.error.emit(str(detail))
                except Exception:
                    self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class EditMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تعديل بيانات الخامة")
        self.setMinimumSize(450, 400)
        self.setModal(True)
        self.center()

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
        title_text = QLabel("تعديل / إضافة كمية للخامة")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        self.main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.material_combo = QComboBox()
        self.quantity_input = QLineEdit()
        self.driver_name_input = QLineEdit()
        self.car_plate_input = QLineEdit()

        form_layout.addRow("الخامة:", self.material_combo)
        form_layout.addRow("الكميه المراد اضافتها (بالكيلو):", self.quantity_input)
        form_layout.addRow("اسم السائق:", self.driver_name_input)
        form_layout.addRow("رقم السيارة:", self.car_plate_input)
        content_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("حفظ التعديلات")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save)  # Connect to save handler
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)
        self.main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)

        self.old_pos = None
        self.fetch_material_names()

    def handle_save(self):
        """Validates inputs and starts the API request to save changes."""
        quantity_str = self.quantity_input.text().strip()

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                QMessageBox.warning(self, "خطأ في الإدخال", "يجب أن تكون الكمية رقمًا موجبًا.")
                return
        except ValueError:
            QMessageBox.warning(self, "خطأ في الإدخال", "الرجاء إدخال رقم صالح للكمية.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "material_name": self.material_combo.currentText(),
            "quantity": quantity_str,
            "driver_name": self.driver_name_input.text().strip(),
            "car_plate_number": self.car_plate_input.text().strip(),
            "username": username,
        }

        url = f"{BACKEND_BASE_URL}/material-warehouse/material-quantity/"
        self._start_update_request(url, payload)

    def _start_update_request(self, url, payload):
        self._set_loading(True)
        self.update_thread = QThread()
        self.update_worker = UpdateQuantityWorker(url, payload)
        self.update_worker.moveToThread(self.update_thread)

        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.success.connect(self.on_update_success)
        self.update_worker.error.connect(self.on_update_error)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_thread.start()

    def on_update_success(self):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تم تحديث كمية الخامة بنجاح.")
        self.accept()

    def on_update_error(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", f"فشل تحديث الكمية:\n{message}")

    def _set_loading(self, is_loading):
        """Disables form elements while the API call is in progress."""
        self.save_button.setDisabled(is_loading)
        self.material_combo.setDisabled(is_loading)
        self.quantity_input.setDisabled(is_loading)
        self.driver_name_input.setDisabled(is_loading)
        self.car_plate_input.setDisabled(is_loading)
        self.save_button.setText("جاري الحفظ..." if is_loading else "حفظ التعديلات")

    def fetch_material_names(self):
        self.material_combo.setEnabled(False)
        self.material_combo.addItem("جاري التحميل...")
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials-names/"
        self.fetch_thread = QThread()
        self.fetch_worker = MaterialNamesWorker(url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.success.connect(self.populate_material_combo)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.start()

    def populate_material_combo(self, material_names):
        self.material_combo.clear()
        if material_names:
            self.material_combo.addItems(material_names)
            self.material_combo.setEnabled(True)
        else:
            self.material_combo.addItem("لا توجد خامات")

    def on_fetch_error(self, message):
        self.material_combo.clear()
        self.material_combo.addItem("فشل التحميل")
        QMessageBox.warning(self, "خطأ", f"فشل في جلب قائمة الخامات:\n{message}")

    def center(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2, (screen_geometry.height() - self.height()) // 2
        )

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

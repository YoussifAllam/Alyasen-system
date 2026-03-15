from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QLineEdit,  # New import for the dialog
    QDialog,  # New import for the dialog
    QFrame,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, pyqtSlot
from requests import request, get, exceptions

# Assuming these are defined elsewhere
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
                    # Handling Django/DRF style errors which might be nested
                    error_msg = error_data.get("error", error_data.get("الخطاء", response.text))
                    if isinstance(error_msg, dict):
                        # Extract the first message from the dict values
                        error_msg = next(iter(error_msg.values()))[0]
                    self.error.emit(str(error_msg) or f"خطأ من الخادم: {response.status_code}")
                except Exception:
                    self.error.emit(response.text or f"خطأ من الخادم: {response.status_code}")

        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class AddComponentDialog(QDialog):
    submit_request = pyqtSignal(str, str, dict)

    # Add a stylesheet parameter to the constructor
    def __init__(self, machine_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة مكون جديد")
        self.machine_id = machine_id

        # The QDialog's main layout (inherits QDialog styles)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)  # Remove QDialog default margins

        # 🌟 2. Create the container frame and set its object name
        dialog_container = QFrame()
        dialog_container.setObjectName("dialogContainer")  # Matches CSS selector #dialogContainer

        # The internal layout for the dialog content
        main_layout = QVBoxLayout(dialog_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Content (same as before) ---

        # 1. Input Field
        label = QLabel("اسم المكون الجديد:")
        label.setAlignment(Qt.AlignRight)
        self.name_input = QLineEdit()
        self.name_input.setObjectName("textInput")

        main_layout.addWidget(label)
        main_layout.addWidget(self.name_input)

        # 2. Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 3. Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.add_button = QPushButton("➕ إضافة")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.submit_component)

        cancel_button = QPushButton("إلغاء")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.add_button)

        main_layout.addLayout(button_layout)

        # --- End Content ---

        # Add the container frame to the QDialog's main layout
        dialog_layout.addWidget(dialog_container)

        self.setFixedSize(350, 200)

    def submit_component(self):
        """Prepares payload and emits signal to start API process."""
        component_name = self.name_input.text().strip()

        if not component_name:
            self.status_label.setText("⚠️ يرجى إدخال اسم المكون.")
            return

        self.status_label.setText("جاري الإضافة...")
        self.add_button.setDisabled(True)

        url = f"{BACKEND_BASE_URL}/machines/machine-components/"
        payload = {"name": component_name, "machine": self.machine_id}

        # Emit signal to parent to handle API call in its thread manager
        self.submit_request.emit("POST", url, payload)

    def handle_submission_success(self, response_data):
        """Called by the parent UI on successful API response."""
        QMessageBox.information(self, "نجاح", f"تم إضافة المكون: {self.name_input.text()} بنجاح.")
        self.accept()  # Accept closes the dialog

    def handle_submission_error(self, message):
        """Called by the parent UI on API error."""
        self.status_label.setText(f"❌ فشل: {message}")
        self.add_button.setDisabled(False)

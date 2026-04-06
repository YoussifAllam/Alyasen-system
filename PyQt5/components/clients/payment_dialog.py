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
    QTextEdit,
    QDateEdit,
    QFileDialog,
    QComboBox,
    QMessageBox,
)
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QDate,
    QObject,
    pyqtSignal,
    pyqtSlot,
    QThread,
    QSettings,
)
from requests import request
import qtawesome as qta
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..validation import (
    validate_positive_number,
    validate_combo_selected,
    run_validations,
    _clear_errors,
)


class ApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, data=None, files=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data
        self.files = files

    @pyqtSlot()
    def run(self):
        try:
            kwargs = {}
            if self.data:
                kwargs["data"] = self.data

            opened_files = {}
            if self.files:
                for key, path in self.files.items():
                    try:
                        opened_files[key] = open(path, "rb")
                    except Exception:
                        pass
                if opened_files:
                    kwargs["files"] = opened_files

            response = request(self.method, self.url, timeout=15, **kwargs)

            for file_obj in opened_files.values():
                file_obj.close()

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ: {response.text}")
        except Exception as e:
            self.error.emit(f"{e}")
        finally:
            self.finished.emit()


class PaymentDialog(QDialog):
    def __init__(self, project_id, project_type, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.project_type = project_type
        self.setWindowTitle("تسديد مبلغ للفاتورة")
        self.setMinimumSize(600, 600)
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

        title_text = QLabel(f"تسديد دفعة للمشروع رقم: {project_id}")
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

        self.payment_type_combo = QComboBox()
        self.payment_type_combo.addItem("اختر طريقة الدفع", "")
        self.payment_type_combo.addItem("كاش", "cash")
        self.payment_type_combo.addItem("فيزا", "visa")
        self.payment_type_combo.addItem("تحويل بنكي", "bank_transfer")
        self.payment_type_combo.addItem("شيك", "check")
        self.payment_type_combo.currentIndexChanged.connect(
            self.on_payment_type_changed
        )

        self.check_date_label = QLabel("تاريخ تحويل الشيك:")
        self.check_date_input = QDateEdit()
        self.check_date_input.setCalendarPopup(True)
        self.check_date_input.setDate(QDate.currentDate())
        self.check_date_input.setDisplayFormat("yyyy-MM-dd")
        self.check_date_label.hide()
        self.check_date_input.hide()

        self.amount_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")

        self.invoice_number_input = QLineEdit()

        self.file_path = ""
        self.file_label = QLabel("لم يتم اختيار ملف")
        self.file_button = QPushButton("اختيار ملف الفاتورة")
        self.file_button.clicked.connect(self.select_file)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_button)
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()

        form_layout.addRow("طريقة الدفع:", self.payment_type_combo)
        form_layout.addRow(self.check_date_label, self.check_date_input)
        form_layout.addRow("المبلغ المدفوع:", self.amount_input)
        form_layout.addRow("تاريخ الدفع:", self.date_input)
        form_layout.addRow("رقم فاتورة البوابة:", self.invoice_number_input)
        form_layout.addRow("ملف الفاتورة:", file_layout)
        form_layout.addRow("ملاحظات:", self.notes_input)

        content_layout.addLayout(form_layout)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("حفظ")
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

    def on_payment_type_changed(self):
        if self.payment_type_combo.currentData() == "check":
            self.check_date_label.show()
            self.check_date_input.show()
        else:
            self.check_date_label.hide()
            self.check_date_input.hide()

    def handle_save(self):
        fields = [self.payment_type_combo, self.amount_input]
        _clear_errors(fields)

        validations = [
            validate_combo_selected(self.payment_type_combo, "طريقة الدفع"),
            validate_positive_number(self.amount_input, "المبلغ المدفوع"),
        ]
        if not run_validations(self, validations):
            return

        amount_str = self.amount_input.text().strip()

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "system")

        form_data = {
            "project_id": str(self.project_id),
            "project_type": str(self.project_type),
            "payment_amount": amount_str,
            "payment_date": self.date_input.date().toString("yyyy-MM-dd"),
            "payment_type": self.payment_type_combo.currentData(),
            "notes": self.notes_input.toPlainText().strip(),
            "portal_invoice_number": self.invoice_number_input.text().strip(),
            "user_name": username,
        }

        # If check, include check_date
        if self.payment_type_combo.currentData() == "check":
            form_data["check_date"] = self.check_date_input.date().toString(
                "yyyy-MM-dd"
            )

        files = {}
        if self.file_path:
            files["portal_invoice_file"] = self.file_path

        url = f"{BACKEND_BASE_URL}/clients/projects/payments/"

        self.post_thread = QThread()
        self.post_worker = ApiWorker("POST", url, data=form_data, files=files)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_success)
        self.post_worker.error.connect(self.on_error)
        self.post_worker.finished.connect(self.post_thread.quit)

        self.save_button.setEnabled(False)
        self.post_thread.start()

    def on_success(self, response_data):
        self.accept()

    def on_error(self, message):
        self.save_button.setEnabled(True)
        QMessageBox.critical(self, "خطأ في الاتصال", message)

    def get_data(self):
        """Returns the data entered in the dialog."""
        return {
            "payment_type": self.payment_type_combo.currentData(),
            "check_date": (
                self.check_date_input.date().toString("yyyy-MM-dd")
                if self.payment_type_combo.currentData() == "check"
                else None
            ),
            "payment_amount": self.amount_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "payment_date": self.date_input.date().toString("yyyy-MM-dd"),
            "portal_invoice_number": self.invoice_number_input.text().strip(),
            "portal_invoice_file": self.file_path,
        }

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختيار ملف الفاتورة", "", "All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path.split("/")[-1])

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

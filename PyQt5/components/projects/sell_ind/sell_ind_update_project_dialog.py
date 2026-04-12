from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QDateEdit,
    QFormLayout,
    QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate, QThread, QPoint, QSettings
from ..ui_projects import ProjectApiWorker
from ...Main_Ui_Components.constant import BACKEND_BASE_URL
from ...validation import (
    validate_non_negative_number,
    run_validations,
)
import qtawesome as qta


class UpdateRentProjectDialog(QDialog):
    def __init__(self, project_id, current_data=None, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.current_data = current_data or {}
        self.setWindowTitle("تحديث بيانات المشروع")
        self.setMinimumWidth(500)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        self.setup_ui()

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

        title_text = QLabel("تحديث بيانات المشروع")
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
        content_layout.setContentsMargins(25, 10, 25, 25)
        content_layout.setSpacing(20)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.selling_price_input = QLineEdit()
        self.selling_price_input.setPlaceholderText("مثال: 15000")
        self.selling_price_input.setText(
            str(self.current_data.get("selling_price", ""))
        )

        self.vat_input = QLineEdit()
        self.vat_input.setPlaceholderText("مثال: 2000")
        self.vat_input.setText(str(self.current_data.get("value_added_tax", "")))

        self.profits_tax_input = QLineEdit()
        self.profits_tax_input.setPlaceholderText("مثال: 2000")
        self.profits_tax_input.setText(
            str(self.current_data.get("commercial_profits_tax", ""))
        )

        self.insurance_tax_input = QLineEdit()
        self.insurance_tax_input.setPlaceholderText("مثال: 2000")
        self.insurance_tax_input.setText(
            str(self.current_data.get("insurance_tax", ""))
        )

        self.insurance_date_input = QDateEdit()
        self.insurance_date_input.setCalendarPopup(True)
        self.insurance_date_input.setDisplayFormat("yyyy-MM-dd")
        date_str = self.current_data.get("insurance_tax_date")
        if date_str:
            self.insurance_date_input.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        else:
            self.insurance_date_input.setDate(QDate.currentDate())

        form_layout.addRow("سعر البيع:", self.selling_price_input)
        form_layout.addRow("ضريبة القيمة المضافة:", self.vat_input)
        form_layout.addRow("ضريبة الأرباح التجارية:", self.profits_tax_input)
        form_layout.addRow("تأمين المسترد:", self.insurance_tax_input)
        form_layout.addRow("تاريخ استلام التأمين:", self.insurance_date_input)

        content_layout.addLayout(form_layout)

        # Buttons
        btns_layout = QHBoxLayout()
        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("primaryButton")
        self.update_btn.setMinimumHeight(45)
        self.update_btn.clicked.connect(self.handle_update)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.clicked.connect(self.reject)

        btns_layout.addWidget(self.update_btn)
        btns_layout.addWidget(self.cancel_btn)
        content_layout.addLayout(btns_layout)

        layout.addLayout(content_layout)
        main_layout.addWidget(container)

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

    def handle_update(self):
        # Validation
        validations = [
            validate_non_negative_number(self.selling_price_input, "سعر البيع"),
            validate_non_negative_number(self.vat_input, "ضريبة القيمة المضافة"),
            validate_non_negative_number(
                self.profits_tax_input, "ضريبة الأرباح التجارية"
            ),
            validate_non_negative_number(self.insurance_tax_input, "التأمين"),
        ]

        if not run_validations(self, validations):
            return

        insurance_tax_val = self.insurance_tax_input.text().strip()

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "system")

        payload = {
            "CBP_id": str(self.project_id),
            "selling_price": self.selling_price_input.text().strip(),
            "value_added_tax": self.vat_input.text().strip(),
            "commercial_profits_tax": self.profits_tax_input.text().strip(),
            "insurance_tax": insurance_tax_val,
            "user_name": username,
        }

        # Don't send insurance_tax_date if insurance_tax is 0 or empty
        try:
            if insurance_tax_val and float(insurance_tax_val) != 0:
                payload["insurance_tax_date"] = (
                    self.insurance_date_input.date().toString("yyyy-MM-dd")
                )
        except ValueError:
            pass

        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/info/"

        # The API expects form-data as per curl --form
        # ProjectApiWorker uses json if files is None.
        # We can pass an empty dict to files to trigger the multipart/form-data logic in the worker
        # OR better, if the backend supports JSON, use JSON.
        # But wait, the curl showed --form, so it's safer to use form-data.
        # I'll pass an empty dict for files.

        self.update_btn.setEnabled(False)
        self.update_btn.setText("جاري التحديث...")

        self.thread = QThread()
        # Passing files={} to ensure it uses 'data=' instead of 'json=' in ProjectApiWorker
        self.worker = ProjectApiWorker("PATCH", url, payload, files={})
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_success(self, response):
        QMessageBox.information(self, "نجاح", "تمت تحديث بيانات المشروع بنجاح.")
        self.accept()

    def on_error(self, message):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("تحديث")
        QMessageBox.warning(self, "خطأ", f"فشل تحديث البيانات:\n{message}")

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QFrame,
    QMessageBox,
)
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QThread, pyqtSlot
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..utils.api_errors import format_request_exception, parse_api_response
from ..validation import (
    validate_not_empty,
    validate_email,
    validate_min_length,
    validate_password_match,
    run_validations,
    _clear_errors,
)


class SignupWidget(QFrame):
    """The UI card for the user registration page with a new, improved design."""

    back_to_login_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("loginCard")  # Reuse the same card style

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)

        # Title
        title = QLabel("إنشاء حساب جديد")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        # Form layout for better structure
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(
            placeholderText="الاسم بالكامل", objectName="inputField"
        )
        self.email_input = QLineEdit(
            placeholderText="البريد الإلكتروني", objectName="inputField"
        )
        self.password_input = QLineEdit(
            placeholderText="كلمة المرور",
            echoMode=QLineEdit.Password,
            objectName="inputField",
        )
        # --- ADDED: Confirm Password Field ---
        self.confirm_password_input = QLineEdit(
            placeholderText="تأكيد كلمة المرور",
            echoMode=QLineEdit.Password,
            objectName="inputField",
        )

        # --- New User Type Selection Design ---
        user_type_label = QLabel("نوع المستخدم:")
        user_type_label.setObjectName("userTypeLabel")

        self.user_type_group = QHBoxLayout()
        self.btn_accountant = QPushButton("محاسب")
        self.btn_accountant.setCheckable(True)
        self.btn_accountant.setObjectName("userTypeButton")

        self.btn_admin = QPushButton("ادمن")
        self.btn_admin.setCheckable(True)
        self.btn_admin.setObjectName("userTypeButton")

        self.btn_accountant.clicked.connect(
            lambda: self.handle_user_type_selection(self.btn_accountant)
        )
        self.btn_admin.clicked.connect(
            lambda: self.handle_user_type_selection(self.btn_admin)
        )

        self.user_type_group.addWidget(self.btn_admin)
        self.user_type_group.addWidget(self.btn_accountant)

        # Set a default selection
        self.btn_accountant.setChecked(True)

        # Add widgets to the form layout
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.confirm_password_input)  # Added to layout
        form_layout.addWidget(user_type_label)
        form_layout.addLayout(self.user_type_group)

        # Submit Button
        self.submit_button = QPushButton("تقديم الطلب")
        self.submit_button.setObjectName("loginButton")
        self.submit_button.clicked.connect(self.handle_signup)

        # Back to Login Link
        back_link_layout = QHBoxLayout()
        back_link_layout.addStretch()
        back_link = QPushButton("لديك حساب بالفعل؟ تسجيل الدخول")
        back_link.setObjectName("linkButton")
        back_link.clicked.connect(self.back_to_login_requested.emit)
        back_link_layout.addWidget(back_link)
        back_link_layout.addStretch()

        # Add all elements to the main layout
        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addSpacing(10)
        layout.addWidget(self.submit_button)
        layout.addLayout(back_link_layout)

    def handle_user_type_selection(self, selected_btn):
        """Ensures only one button is checked, like a radio button."""
        if selected_btn == self.btn_accountant:
            self.btn_admin.setChecked(False)
        else:
            self.btn_accountant.setChecked(False)
        # Ensure one is always selected
        if not self.btn_admin.isChecked() and not self.btn_accountant.isChecked():
            selected_btn.setChecked(True)

    def get_signup_parametrs_from_ui(self) -> list:
        name = self.name_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        email = self.email_input.text()
        user_type = "Accountant" if self.btn_accountant.isChecked() else "Admin"
        return name, email, user_type, password, confirm_password

    def validation_signup_parameters(
        self, name, email, password, confirm_password
    ) -> bool:
        if not all([name, email, password, confirm_password]):
            QMessageBox.warning(self, "خطأ", "الرجاء ملء جميع الحقول.")
            return False
        return True

    def handle_signup(self):
        """Validates form and shows a standard QMessageBox."""
        fields = [
            self.name_input,
            self.email_input,
            self.password_input,
            self.confirm_password_input,
        ]
        _clear_errors(fields)

        name, email, user_type, password, confirm_password = (
            self.get_signup_parametrs_from_ui()
        )

        validations = [
            validate_not_empty(self.name_input, "الاسم"),
            validate_email(self.email_input, "البريد الإلكتروني"),
            validate_min_length(self.password_input, "كلمة المرور", 6),
            validate_password_match(self.password_input, self.confirm_password_input),
        ]
        if not run_validations(self, validations):
            return

        url = f"{BACKEND_BASE_URL}/registertion/users/"
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "user_type": user_type,
        }

        self._start_signup_request(url, payload)

    def _set_loading(self, is_loading: bool):
        self.submit_button.setDisabled(is_loading)
        self.name_input.setDisabled(is_loading)
        self.email_input.setDisabled(is_loading)
        self.password_input.setDisabled(is_loading)
        self.confirm_password_input.setDisabled(is_loading)
        self.btn_admin.setDisabled(is_loading)
        self.btn_accountant.setDisabled(is_loading)
        self.submit_button.setText("جاري الإرسال..." if is_loading else "تقديم الطلب")

    def _start_signup_request(self, url: str, payload: dict):
        self._set_loading(True)

        class SignupWorker(QObject):
            finished = pyqtSignal()
            success = pyqtSignal()
            error = pyqtSignal(str)

            def __init__(self, url_value: str, payload_value: dict):
                super().__init__()
                self.url_value = url_value
                self.payload_value = payload_value

            @pyqtSlot()
            def run(self):
                try:
                    resp = request(
                        "POST",
                        self.url_value,
                        json=self.payload_value,
                        timeout=10,
                    )
                    ok, data = parse_api_response(resp)
                    if ok:
                        self.success.emit()
                    else:
                        self.error.emit(data)
                except exceptions.RequestException as e:
                    self.error.emit(format_request_exception(e))
                finally:
                    self.finished.emit()

        self._thread = QThread(self)
        self._worker = SignupWorker(url, payload)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)

        def on_success():
            self._set_loading(False)
            QMessageBox.information(
                self, "تم إرسال الطلب", "من فضلك انتظر حتى يوافق الادمن على طلب إضافتك."
            )
            self.back_to_login_requested.emit()

        def on_error(message: str):
            self._set_loading(False)
            QMessageBox.warning(self, "خطاء", message)

        def on_finished():
            self._thread.quit()
            self._thread.wait()
            self._worker.deleteLater()
            self._thread.deleteLater()

        self._worker.success.connect(on_success)
        self._worker.error.connect(on_error)
        self._worker.finished.connect(on_finished)

        self._thread.start()

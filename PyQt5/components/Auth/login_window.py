from requests import request
import qtawesome as qta
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QAction,
    QStackedWidget,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    pyqtSignal,
    QThread,
    QObject,
    pyqtSlot,
    QSettings,
)

from .signup_widget import SignupWidget
from ..Main_Ui_Components.constant import BACKEND_BASE_URL, BASE_DIR


class LoginWidget(QFrame):
    """The UI card for the user login page."""

    login_successful = pyqtSignal(str)  # UPDATED: Signal will carry the username string
    signup_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("loginCard")

        # Initialize QSettings to store persistent data
        self.settings = QSettings("FactorySystem")

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        logo_label = QLabel()
        pixmap = QPixmap(rf"{BASE_DIR}/resources/logo3.png")
        logo_label.setPixmap(
            pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        logo_label.setAlignment(Qt.AlignCenter)

        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title_label = QLabel("مرحباً بعودتك")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("الرجاء إدخال بياناتك لتسجيل الدخول")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        self.email_input = QLineEdit(
            placeholderText="البريد الإلكتروني", objectName="inputField"
        )
        self.password_input = QLineEdit(
            placeholderText="كلمة المرور",
            echoMode=QLineEdit.Password,
            objectName="inputField",
        )

        icon_lock_closed = qta.icon("fa5s.lock", color="#9ca3af")
        self.icon_lock_open = qta.icon("fa5s.lock-open", color="#d1d5db")
        self.toggle_action = QAction(icon_lock_closed, "Show/Hide Password")
        self.toggle_action.triggered.connect(self.toggle_password_visibility)
        self.password_input.addAction(self.toggle_action, QLineEdit.TrailingPosition)

        self.remember_me_checkbox = QCheckBox("تذكرني")
        self.remember_me_checkbox.setObjectName("rememberMeCheckbox")

        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.handle_login)

        links_layout = QHBoxLayout()
        forgot_link = QPushButton("هل نسيت كلمة المرور؟")
        forgot_link.setObjectName("linkButton")

        signup_link = QPushButton("ليس لديك حساب؟ إنشاء حساب")
        signup_link.setObjectName("linkButton")
        signup_link.clicked.connect(self.signup_requested.emit)

        links_layout.addWidget(forgot_link)
        links_layout.addStretch()
        links_layout.addWidget(signup_link)

        card_layout.addWidget(logo_label)
        card_layout.addWidget(header_container)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.remember_me_checkbox, 0, Qt.AlignRight)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.login_button)
        card_layout.addLayout(links_layout)

        self.load_credentials()

    def load_credentials(self):
        if self.settings.value("remember_me", "false", type=str) == "true":
            self.email_input.setText(self.settings.value("email", ""))
            self.password_input.setText(self.settings.value("password", ""))
            self.remember_me_checkbox.setChecked(True)

    def save_credentials(self, user_name=""):
        # UPDATED: Now accepts the username to save
        if self.remember_me_checkbox.isChecked():
            self.settings.setValue("email", self.email_input.text().strip())
            self.settings.setValue("password", self.password_input.text().strip())
            self.settings.setValue("remember_me", "true")
        else:
            self.settings.setValue("email", "")
            self.settings.setValue("password", "")
            self.settings.setValue("remember_me", "false")

        # Always save the username of the logged-in user
        self.settings.setValue("user_name", user_name)

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_action.setIcon(self.icon_lock_open)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_action.setIcon(qta.icon("fa5s.lock", color="#9ca3af"))

    def _set_loading(self, is_loading: bool):
        self.login_button.setDisabled(is_loading)
        self.email_input.setDisabled(is_loading)
        self.password_input.setDisabled(is_loading)
        self.login_button.setText("جاري الدخول..." if is_loading else "تسجيل الدخول")

    def _start_login_request(self, url: str, payload: dict):
        self._set_loading(True)

        class LoginWorker(QObject):
            finished = pyqtSignal()
            success = pyqtSignal(dict)  # UPDATED: Will emit the response dictionary
            error = pyqtSignal(str)

            def __init__(self, url_value: str, payload_value: dict):
                super().__init__()
                self.url_value = url_value
                self.payload_value = payload_value

            @pyqtSlot()
            def run(self):
                try:
                    resp = request(
                        "POST", self.url_value, json=self.payload_value, timeout=10
                    )
                    if resp.status_code == 200:
                        self.success.emit(
                            resp.json()
                        )  # UPDATED: Emit the JSON response
                    else:
                        # ... (error handling remains the same)
                        self.error.emit(f" {resp.text}")
                except Exception:
                    self.error.emit(
                        "فشل الاتصال بالخادم. يرجى التحقق من اتصالك بالإنترنت والمحاولة مرة أخرى."
                    )
                finally:
                    self.finished.emit()

        self._thread = QThread(self)
        self._worker = LoginWorker(url, payload)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)

        def on_success(response_data: dict):  # UPDATED: Receives the response
            user_name = response_data.get("name", "")  # Extract the name
            self.save_credentials(user_name)  # Save all credentials including the name
            self._set_loading(False)
            self.login_successful.emit(user_name)  # Emit the name

        def on_error(message: str):
            self._set_loading(False)
            QMessageBox.critical(self, "خطاء", message)

        def on_finished():
            self._thread.quit()
            self._thread.wait()
            self._worker.deleteLater()
            self._thread.deleteLater()

        self._worker.success.connect(on_success)
        self._worker.error.connect(on_error)
        self._worker.finished.connect(on_finished)
        self._thread.start()

    def handle_login(self):
        url = f"{BACKEND_BASE_URL}/registertion/user/login/"
        payload = {
            "email": self.email_input.text().strip(),
            "password": self.password_input.text().strip(),
        }
        self._start_login_request(url, payload)


class AuthWindow(QWidget):
    login_successful = pyqtSignal(str)  # UPDATED: Signal carries the username

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Factory System Auth")
        self.setGeometry(0, 0, 550, 750)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        self.stacked_widget = QStackedWidget()
        self.login_page = LoginWidget()
        self.signup_page = SignupWidget()
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        main_layout.addWidget(self.stacked_widget)

        # UPDATED: Connect the signal that carries the username
        self.login_page.login_successful.connect(self.login_successful.emit)
        self.login_page.signup_requested.connect(self.show_signup_page)
        self.signup_page.back_to_login_requested.connect(self.show_login_page)

        self.center()
        self.start_animation()

    def show_login_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_signup_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def center(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(
            (screen_geometry.width() - self.width()) // 2,
            (screen_geometry.height() - self.height()) // 2,
        )

    def start_animation(self):
        self.animation = QPropertyAnimation(
            self, b"windowOpacity", duration=600, startValue=0, endValue=1
        )
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

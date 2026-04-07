import qtawesome as qta
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QHBoxLayout,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, QSize, Qt

from .constant import BASE_DIR


class SidebarWidget(QWidget):
    page_changed = pyqtSignal(int)
    theme_changed = pyqtSignal()  # New signal for theme toggle
    logout_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(0)

        logo_label = QLabel()
        logo_path = rf"{BASE_DIR}/resources/logo3.png"
        pixmap = QPixmap(logo_path)
        # Scaled down to prevent the sidebar's minimum height from exceeding typical laptop screen heights
        logo_label.setPixmap(
            pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addSpacing(5)
        layout.addWidget(logo_label)
        layout.addSpacing(15)

        self.buttons = []
        button_data = [
            {"text": " لوحة التحكم", "icon": "fa5s.tachometer-alt"},
            {"text": " العملاء", "icon": "fa5s.user-friends"},
            {"text": " الموردين", "icon": "fa5s.truck"},
            {"text": " مصروفات", "icon": "fa5s.file-invoice-dollar"},
            # {"text": " جرد", "icon": "fa5s.clipboard-list"},
            {"text": " سجل العمليات", "icon": "fa5s.history"},
            {"text": "اصول الشركة", "icon": "fa5s.tools"},
            {"text": " الخزنة", "icon": "fa5s.money-bill-wave"},
            {"text": " المشاريع", "icon": "fa5s.building"},
            {"text": " عروض الاسعار", "icon": "fa5s.file-signature"},
            {"text": " حمله", "icon": "fa5s.bullhorn"},
        ]

        for i, data in enumerate(button_data):
            button = QPushButton(data["text"])
            button.setIcon(qta.icon(data["icon"], color="#d1d5db"))
            button.setIconSize(QSize(22, 22))
            button.clicked.connect(
                lambda checked, index=i: self.page_changed.emit(index)
            )
            layout.addWidget(button)
            self.buttons.append(button)

        layout.addStretch()

        self.theme_toggle_button = QPushButton(" الوضع الفاتح")
        self.theme_toggle_button.setIcon(qta.icon("fa5s.sun", color="#d1d5db"))
        self.theme_toggle_button.setIconSize(QSize(22, 22))
        self.theme_toggle_button.clicked.connect(self.theme_changed.emit)
        layout.addWidget(self.theme_toggle_button)

        user_frame = QFrame()
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(5, 5, 5, 5)

        user_info_layout = QVBoxLayout()
        self.logout_button = QPushButton(" تسجيل الخروج")
        self.logout_button.setObjectName("linkButton")
        self.logout_button.setIcon(qta.icon("fa5s.sign-out-alt", color="#00bc88"))
        self.logout_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #00bc88;
                font-size: 18px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
        """
        )
        self.logout_button.setIconSize(QSize(18, 18))
        self.logout_button.setCursor(Qt.PointingHandCursor)
        self.logout_button.clicked.connect(self.logout_clicked.emit)

        user_info_layout.addWidget(self.logout_button)
        user_layout.addLayout(user_info_layout)
        layout.addWidget(user_frame)

    def update_theme_button(self, theme_name):
        """Updates the theme button's icon and text."""
        if theme_name == "dark":
            self.theme_toggle_button.setText(" الوضع الفاتح")
            self.theme_toggle_button.setIcon(qta.icon("fa5s.sun", color="#d1d5db"))
        else:
            self.theme_toggle_button.setText(" الوضع الداكن")
            self.theme_toggle_button.setIcon(qta.icon("fa5s.moon", color="#374151"))

    def set_active_button(self, index):
        icon_color = "#d1d5db"
        active_icon_color = "#ffffff"

        for i, button in enumerate(self.buttons):
            icon_name = button.text().strip()
            current_icon_color = active_icon_color if i == index else icon_color

            icon_map = {
                "لوحة التحكم": "fa5s.tachometer-alt",  # NEW
                "العمال": "fa5s.users",
                "العملاء": "fa5s.user-friends",
                "الموردين": "fa5s.truck",
                "مصروفات": "fa5s.file-invoice-dollar",
                "تجارب الخلطات": "fa5s.flask",
                "جرد": "fa5s.clipboard-list",
                "مخزن الخامات": "fa5s.boxes",
                "سجل العمليات": "fa5s.history",
                "المشاريع": "fa5s.building",
                "عروض الاسعار": "fa5s.file-signature",
                "حمله": "fa5s.bullhorn",
            }

            if icon_name in icon_map:
                button.setIcon(qta.icon(icon_map[icon_name], color=current_icon_color))

            button.setObjectName("active" if i == index else "")

        self.style().polish(self)
        for button in self.buttons:
            self.style().polish(button)

    def set_user_name(self, name: str):
        name = (name or "").strip()
        self.user_name.setText(f"مرحباً، {name}" if name else "مرحباً")

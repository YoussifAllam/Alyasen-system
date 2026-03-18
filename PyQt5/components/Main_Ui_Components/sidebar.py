import qtawesome as qta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, QSize, Qt

from .constant import BASE_DIR


class SidebarWidget(QWidget):
    page_changed = pyqtSignal(int)
    theme_changed = pyqtSignal()  # New signal for theme toggle
    notifications_clicked = pyqtSignal()  # Signal for notification button

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)

        logo_label = QLabel()
        logo_path = rf"{BASE_DIR}/resources/logo1.png"
        pixmap = QPixmap(logo_path)
        logo_label.setPixmap(pixmap.scaled(270, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        layout.addSpacing(5)

        # title_label = QLabel("نظام المصنع")
        # title_label.setObjectName("sidebarTitle")
        # title_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(title_label)

        self.buttons = []
        button_data = [
            {"text": " لوحة التحكم", "icon": "fa5s.tachometer-alt"},  # NEW
            {"text": " العملاء", "icon": "fa5s.user-friends"},
            {"text": " الموردين", "icon": "fa5s.truck"},
            {"text": " مصروفات", "icon": "fa5s.file-invoice-dollar"},
            # {"text": " تجارب الخلطات", "icon": "fa5s.flask"},
            {"text": " جرد", "icon": "fa5s.clipboard-list"},
            {"text": "الخزنة", "icon": "fa5s.boxes"},
            {"text": " سجل العمليات", "icon": "fa5s.history"},
            {"text": "اصول الشركة", "icon": "fa5s.tools"},
            # {"text": "بيع قطاعي", "icon": "fa5s.shopping-cart"},
        ]

        for i, data in enumerate(button_data):
            button = QPushButton(data["text"])
            button.setIcon(qta.icon(data["icon"], color="#d1d5db"))
            button.setIconSize(QSize(22, 22))
            button.clicked.connect(lambda checked, index=i: self.page_changed.emit(index))
            layout.addWidget(button)
            self.buttons.append(button)

        layout.addStretch()

        self.notification_button = QPushButton(" الإشعارات")
        self.notification_button.setIcon(qta.icon("fa5s.bell", color="#d1d5db"))
        self.notification_button.setIconSize(QSize(22, 22))
        self.notification_button.clicked.connect(self.notifications_clicked.emit)
        layout.addWidget(self.notification_button)

        self.theme_toggle_button = QPushButton(" الوضع الفاتح")
        self.theme_toggle_button.setIcon(qta.icon("fa5s.sun", color="#d1d5db"))
        self.theme_toggle_button.setIconSize(QSize(22, 22))
        self.theme_toggle_button.clicked.connect(self.theme_changed.emit)
        layout.addWidget(self.theme_toggle_button)

        user_frame = QFrame()
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(5, 5, 5, 5)

        user_info_layout = QVBoxLayout()
        self.user_name = QLabel("مرحباً")
        self.user_name.setObjectName("userName")
        logout_link = QLabel("<a href='#'>تسجيل الخروج</a>")
        user_info_layout.addWidget(self.user_name)
        user_info_layout.addWidget(logout_link)
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

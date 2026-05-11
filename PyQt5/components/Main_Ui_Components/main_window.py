from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QApplication,
    QScrollArea,
)
from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QSettings, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter
import qtawesome as qta

# Import other UI components
from .sidebar import SidebarWidget
from ..notifications_dialog import NotificationsDialog, NotificationApiWorker
from ..dashboard.dashboard import DashboardUI  # NEW
from ..clients.ui_clients import ClientsUI
from ..projects.ui_projects import ProjectsUI
from ..quotations.ui_quotations import QuotationsUI
from ..campaine.ui_campaine import CampaignsUI
from ..MaterialsSuppliers.ui_suppliers import MaterialsSuppliersUI
from ..suppliers.ui_suppliers import SuppliersUI
from ..ui_expenses import ExpensesUI
from ..reports import ReportsUI
from ..program_log import ProgramLogUI
from ..Company_assets.ui_company_assets import CompanyAssetsUI
from ..ui_company_safe import CompanySafeUI

# from ..Segmental_Selling.Segmental_invoices_page import SegmentalInvoicesUI

from .stylesheet import load_dark_theme
from .light_stylesheet import load_light_theme


from .constant import BASE_DIR, APP_VERSION, BACKEND_BASE_URL


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Factory Management System")

        # Get available screen geometry (excludes taskbar)
        screen = QApplication.primaryScreen().availableGeometry()

        # Set window to use available screen space with small margins
        self.setGeometry(
            screen.x() + 10, screen.y() + 10, screen.width() - 20, screen.height() - 20
        )
        self.showMaximized()

        self.setWindowFlags(Qt.FramelessWindowHint)

        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        self.setCentralWidget(main_container)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0)

        app_icon = QLabel()
        app_icon.setFixedSize(30, 35)
        app_icon.setScaledContents(True)
        logo_path = rf"{BASE_DIR}/resources/logo1.png"
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            app_icon.setPixmap(pixmap)
        title_text = QLabel(f"الياسيين - {APP_VERSION}")
        title_text.setObjectName("titleBarText")

        self.minimize_button = QPushButton()
        self.minimize_button.setObjectName("titleBarButton")
        self.minimize_button.setIcon(qta.icon("fa5s.window-minimize", color="#9ca3af"))
        self.minimize_button.clicked.connect(self.showMinimized)

        self.maximize_button = QPushButton()
        self.maximize_button.setObjectName("titleBarButton")
        self.maximize_button.setIcon(qta.icon("fa5s.window-maximize", color="#9ca3af"))
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)

        self.close_button = QPushButton()
        self.close_button.setObjectName("closeButton")
        self.close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        self.close_button.clicked.connect(self.close)

        self.notification_button = QPushButton()
        self.notification_button.setObjectName("titleBarButton")
        self.notification_button.setIcon(qta.icon("fa5s.bell", color="#9ca3af"))
        self.notification_button.setToolTip("الإشعارات")
        self.notification_button.setIconSize(QSize(22, 22))

        # Connect button to show notifications dialog
        self.notification_button.clicked.connect(self.show_notifications)

        title_bar_layout.addWidget(self.close_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.notification_button)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addWidget(app_icon)
        main_container_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = SidebarWidget()
        content_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        main_container_layout.addWidget(content_area)

        self.sidebar.theme_changed.connect(self.toggle_theme)
        self.sidebar.logout_clicked.connect(self.logout_requested.emit)

        # Set initial theme based on settings
        self.settings = QSettings("FactorySystem")
        self.current_theme = self.settings.value("theme", "dark")
        self.update_theme()

        self.create_pages()
        self.sidebar.page_changed.connect(self.change_page)
        self.change_page(0)  # Default to dashboard
        self.old_pos = None

        self.setup_bell_animation()
        # Setup Notification Polling
        self.setup_notification_polling()

    def setup_notification_polling(self):
        self.notif_timer = QTimer(self)
        self.notif_timer.timeout.connect(self.check_notifications)
        # 10 minutes (10 * 60 * 1000 ms)
        self.notif_timer.start(10 * 60 * 1000)
        # Initial check right at startup
        self.check_notifications()

    def check_notifications(self):
        url = f"{BACKEND_BASE_URL}/notifications/get-unreaded-notifications/"
        self.notif_worker = NotificationApiWorker("GET", url)
        self.notif_worker.success.connect(self.update_notification_badge)
        self.notif_worker.start()

    def setup_bell_animation(self):
        self.bell_timer = QTimer(self)
        self.bell_timer.timeout.connect(self.animate_bell)
        # Angles for a fast ringing effect
        self.bell_angles = [0, 15, 20, 15, 0, -15, -20, -15]
        self.bell_anim_step = 0
        self.is_ringing = False

    def animate_bell(self):
        if not self.is_ringing:
            return

        angle = self.bell_angles[self.bell_anim_step]
        self.bell_anim_step = (self.bell_anim_step + 1) % len(self.bell_angles)
        self.notification_button.setIcon(self.get_rotated_bell_icon(angle, "#ef4444"))

    def get_rotated_bell_icon(self, angle, color):
        base_icon = qta.icon("fa5s.bell", color=color)
        pixmap = base_icon.pixmap(32, 32)

        rotated_pixmap = QPixmap(32, 32)
        rotated_pixmap.fill(Qt.transparent)

        painter = QPainter(rotated_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Pivot point slightly above center for a realistic bell pivot
        painter.translate(16, 8)
        painter.rotate(angle)
        painter.translate(-16, -8)

        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return QIcon(rotated_pixmap)

    def update_notification_badge(self, response_data):
        notifications = response_data.get("data", [])
        if notifications:
            self.is_ringing = True
            if not self.bell_timer.isActive():
                self.bell_timer.start(60)  # Fast ringing frame rate
        else:
            self.is_ringing = False
            self.bell_timer.stop()
            self.notification_button.setIcon(qta.icon("fa5s.bell", color="#9ca3af"))

    def wrap_in_scroll_area(self, widget):
        """
        Wraps a widget in a QScrollArea to make it scrollable.
        This ensures all pages fit properly regardless of screen size.
        """
        # Ensure the widget has proper background styling
        if not widget.objectName():
            widget.setObjectName("mainContent")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame border
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """
        )
        scroll_area.setWidget(widget)
        return scroll_area

    def toggle_theme(self):
        """Switches the application theme between light and dark."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.settings.setValue("theme", self.current_theme)
        self.update_theme()

    def update_theme(self):
        """Applies the current theme to the application."""
        stylesheet = (
            load_light_theme() if self.current_theme == "light" else load_dark_theme()
        )
        QApplication.instance().setStyleSheet(stylesheet)
        self.sidebar.update_theme_button(self.current_theme)

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

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

    def create_pages(self):
        self.page_definitions = [
            ("dashboard_page", DashboardUI, False),
            ("clients_page", ClientsUI, True),
            ("suppliers_page", SuppliersUI, True),
            ("expenses_page", ExpensesUI, True),
            # ("reports_page", ReportsUI, True),
            ("program_log_page", ProgramLogUI, True),
            ("company_assets_page", CompanyAssetsUI, True),
            ("company_safe_page", CompanySafeUI, True),
            ("projects_page", ProjectsUI, True),
            ("quotations_page", QuotationsUI, True),
            ("campaigns_page", CampaignsUI, True),
            ("materials_suppliers_page", MaterialsSuppliersUI, True),
        ]
        self.page_widgets = []

        for _ in self.page_definitions:
            placeholder = QWidget()
            self.page_widgets.append(placeholder)
            self.stacked_widget.addWidget(placeholder)

    def create_page_widget(self, index):
        page_attr, page_class, use_scroll_area = self.page_definitions[index]
        page = page_class()
        setattr(self, page_attr, page)
        return self.wrap_in_scroll_area(page) if use_scroll_area else page

    @pyqtSlot(int)
    def change_page(self, index):
        if index < 0 or index >= len(self.page_definitions):
            return

        old_widget = self.page_widgets[index]
        new_widget = self.create_page_widget(index)

        self.stacked_widget.removeWidget(old_widget)
        old_widget.deleteLater()
        self.stacked_widget.insertWidget(index, new_widget)
        self.page_widgets[index] = new_widget

        self.stacked_widget.setCurrentWidget(new_widget)
        self.sidebar.set_active_button(index)

    def show_notifications(self):
        dialog = NotificationsDialog(self)
        dialog.exec_()
        # Immediately re-check the badge after closing the dialog
        # to clear the red dot if they read them all.
        self.check_notifications()

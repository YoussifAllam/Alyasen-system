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
from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QSettings
from PyQt5.QtGui import QIcon, QPixmap
import qtawesome as qta

# Import other UI components
from .sidebar import SidebarWidget
from ..dashboard.dashboard import DashboardUI  # NEW
from ..clients.ui_clients import ClientsUI
from ..Workers.ui_workers import WorkersUI
from ..suppliers.ui_suppliers import SuppliersUI
from ..ui_expenses import ExpensesUI
from ..reports import ReportsUI
from ..Mixtures.ui_mixes import MixesUI
from ..inventory.materials_inventory import MaterialsInventoryUI
from ..program_log import ProgramLogUI
from ..Machines.ui_machines import MachinesUI
from ..Segmental_Selling.Segmental_invoices_page import SegmentalInvoicesUI

from .stylesheet import load_dark_theme
from .light_stylesheet import load_light_theme


from .constant import BASE_DIR, APP_VERSION


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Factory Management System")

        # Get available screen geometry (excludes taskbar)
        screen = QApplication.primaryScreen().availableGeometry()

        # Set window to use available screen space with small margins
        self.setGeometry(screen.x() + 10, screen.y() + 10, screen.width() - 20, screen.height() - 20)
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
        title_text = QLabel(f"المهندس - {APP_VERSION}")
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

        title_bar_layout.addWidget(self.close_button)
        title_bar_layout.addWidget(self.maximize_button)
        title_bar_layout.addWidget(self.minimize_button)
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

        # Set initial theme based on settings
        self.settings = QSettings("FactorySystem")
        self.current_theme = self.settings.value("theme", "dark")
        self.update_theme()

        self.create_pages()
        self.sidebar.page_changed.connect(self.change_page)
        self.change_page(0)  # Default to dashboard
        self.old_pos = None

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
        stylesheet = load_light_theme() if self.current_theme == "light" else load_dark_theme()
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

    def set_user_name(self, user_name: str):
        if hasattr(self.sidebar, "set_user_name"):
            self.sidebar.set_user_name(user_name)

    def create_pages(self):
        # Create all page instances
        self.dashboard_page = DashboardUI()
        self.workers_page = WorkersUI()
        self.clients_page = ClientsUI()
        self.suppliers_page = SuppliersUI()
        self.expenses_page = ExpensesUI()
        self.mixes_page = MixesUI()
        self.reports_page = ReportsUI()
        self.materials_page = MaterialsInventoryUI()
        self.program_log_page = ProgramLogUI()
        self.machines_page = MachinesUI()
        self.segmantel_invoices_page = SegmentalInvoicesUI()

        # Dashboard already has scroll implemented, so skip wrapping it
        self.stacked_widget.addWidget(self.dashboard_page)

        # Wrap all other pages in scroll areas
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.workers_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.clients_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.suppliers_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.expenses_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.mixes_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.reports_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.materials_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.program_log_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.machines_page))
        self.stacked_widget.addWidget(self.wrap_in_scroll_area(self.segmantel_invoices_page))

    @pyqtSlot(int)
    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.sidebar.set_active_button(index)

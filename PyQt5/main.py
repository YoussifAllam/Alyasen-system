import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSettings, QLocale  # Added QLocale

# Import the window classes that the controller will manage
from components.Auth.login_window import AuthWindow
from components.Main_Ui_Components.main_window import MainWindow
from components.Main_Ui_Components.stylesheet import load_dark_theme
from components.Main_Ui_Components.light_stylesheet import load_light_theme
from components.Main_Ui_Components.constant import BASE_DIR  # Import BASE_DIR


class AppController:
    """Manages the flow between the auth window and the main application window."""

    def __init__(self):
        self.auth_win = AuthWindow()
        self.main_win = MainWindow()

        # Connect the 'login_successful' signal from the auth window
        self.auth_win.login_successful.connect(self.show_main_window)

    def start(self):
        """Shows the initial authentication window to the user."""
        # self.main_win.show()
        self.auth_win.show()

    def show_main_window(self, user_name: str = ""):
        """Closes the auth window and shows the main application window."""
        if hasattr(self.main_win, "set_user_name"):
            self.main_win.set_user_name(user_name or "")
        self.main_win.show()
        self.auth_win.close()


if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    # --- Set Application-Wide Locale ---
    # Force English locale for consistent date/number formatting across all devices
    english_locale = QLocale(QLocale.English, QLocale.UnitedStates)
    QLocale.setDefault(english_locale)

    

    # --- Splash Screen Setup ---
    pixmap = QPixmap(rf"{BASE_DIR}/resources/banner.png").scaled(
        1000, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("جاري تحميل إعدادات النظام...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)

    # Process events to ensure the splash screen is displayed immediately
    app.processEvents()

    # --- Main Application Setup ---
    app.setLayoutDirection(Qt.RightToLeft)
    font = QFont("Cairo")
    app.setFont(font)

    settings = QSettings("FactorySystem")
    theme = settings.value("theme", "dark")

    if theme == "light":
        app.setStyleSheet(load_light_theme())
    else:
        app.setStyleSheet(load_dark_theme())

    # Simulate some loading time
    time.sleep(2)

    controller = AppController()
    controller.start()

    # Close the splash screen once the main authentication window is ready
    splash.finish(controller.auth_win)

    sys.exit(app.exec_())

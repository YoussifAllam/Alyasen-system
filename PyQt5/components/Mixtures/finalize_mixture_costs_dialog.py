from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QWidget,
    QFormLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class MixtureInfoWorker(QObject):
    """Worker thread to fetch mixture cost info."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class FinalizeMixtureCostsDialog(QDialog):
    def __init__(self, mixture_id, mixture_name, parent=None):
        super().__init__(parent)
        self.mixture_id = mixture_id
        self.mixture_name = mixture_name
        self.materials_cost = 0.0  # Will be updated from API

        self.setWindowTitle(f"تحديد تكاليف الخلطة: {mixture_name}")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_text = QLabel(f"تحديد تكاليف الخلطة: {mixture_name}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(15)

        self.materials_cost_display = QLineEdit("جاري التحميل...")
        self.materials_cost_display.setReadOnly(True)
        self.manufacturing_cost_input = QLineEdit("0")
        self.profit_input = QLineEdit("0")
        self.selling_price_display = QLineEdit("0.00")
        self.selling_price_display.setReadOnly(True)

        self.manufacturing_cost_input.textChanged.connect(self.calculate_selling_price)
        self.profit_input.textChanged.connect(self.calculate_selling_price)

        form_layout.addRow("تكلفة الخامات:", self.materials_cost_display)
        form_layout.addRow("تكلفة التصنيع:", self.manufacturing_cost_input)
        form_layout.addRow("الربح:", self.profit_input)
        form_layout.addRow("سعر البيع:", self.selling_price_display)
        content_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("حفظ")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.fetch_mixture_info()

    def fetch_mixture_info(self):
        """Fetches the mixture cost details from the API."""
        url = f"{BACKEND_BASE_URL}/mixtures/mixture_info/?mixture_id={self.mixture_id}"
        self.thread = QThread()
        self.worker = MixtureInfoWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_form)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_form(self, response_data):
        """Fills the form fields with data from the API."""
        data = response_data.get("data", {})
        self.materials_cost = data.get("materials_used_cost", 0.0)

        self.materials_cost_display.setText(f"{self.materials_cost:,.2f}")
        self.manufacturing_cost_input.setText(str(data.get("manufacturing_cost", 0.0)))
        self.profit_input.setText(str(data.get("profit", 0.0)))
        self.selling_price_display.setText(f"{data.get('selling_price', 0.0):,.2f}")

    def calculate_selling_price(self):
        try:
            manufacturing_cost = float(self.manufacturing_cost_input.text() or 0)
            profit = float(self.profit_input.text() or 0)
            total = self.materials_cost + manufacturing_cost + profit
            self.selling_price_display.setText(f"{total:,.2f}")
        except ValueError:
            self.selling_price_display.setText("قيم غير صالحة")

    def get_costs(self):
        """Returns the final cost data from the dialog."""
        return {
            "materials_used_cost": self.materials_cost,
            "manufacturing_cost": self.manufacturing_cost_input.text(),
            "profit": self.profit_input.text(),
            "selling_price": self.selling_price_display.text().replace(",", ""),
        }

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "old_pos") and self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

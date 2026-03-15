from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QHeaderView,
    QFrame,
    QTableWidgetItem,
    QMessageBox,
    QWidget,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class MaterialDetailsWorker(QObject):
    """Worker thread for fetching material details for a mixture."""

    finished = pyqtSignal()
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=15)
            if response.status_code == 200:
                response_data = response.json()

                # FIX: Extract results directly from data
                data_obj = response_data.get("data", {})
                results = data_obj.get("results", [])

                self.success.emit(results)
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {str(e)}")
        finally:
            self.finished.emit()


class MixtureMaterialsDetailsDialog(QDialog):
    def __init__(self, mixture_id, mixture_name, parent=None):
        super().__init__(parent)
        self.mixture_id = mixture_id
        self.mixture_name = mixture_name
        self.setWindowTitle(f"تفاصيل خامات الخلطة: {mixture_name}")
        self.setMinimumSize(900, 600)
        self.setModal(True)

        # Thread and worker management
        self.thread = None
        self.worker = None

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main Container
        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(f"تفاصيل خامات الخلطة: {mixture_name}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.accept)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        # Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["اسم الخامة", "الكمية المستخدمة", "سعر الشراء", "سعر البيع", "الإجمالي"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        content_layout.addWidget(self.table)

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)

        self.fetch_material_details()

    def fetch_material_details(self):
        """Fetches the material history for the given mixture ID."""
        url = f"{BACKEND_BASE_URL}/mixtures/materials/?mixture_id={self.mixture_id}"

        self.thread = QThread()
        self.worker = MaterialDetailsWorker(url)
        self.worker.moveToThread(self.thread)

        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def populate_table(self, materials):
        """Populates the table with a list of materials."""

        self.table.setRowCount(0)
        for material in materials:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(material.get("material_name", "")),
                QTableWidgetItem(f"{material.get('quantity_used', 0):,.2f}"),
                QTableWidgetItem(f"{material.get('material_buy_price_per_kilo', 0):,.2f}"),
                QTableWidgetItem(f"{material.get('material_sell_price_per_kilo', 0):,.2f}"),
                QTableWidgetItem(f"{material.get('total_price', 0):,.2f}"),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def show_error(self, message):
        QMessageBox.critical(self, "خطأ", message)

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

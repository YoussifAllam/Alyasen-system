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
from .mixture_materials_details_dialog import MixtureMaterialsDetailsDialog


class MixtureFetcherWorker(QObject):
    """Worker thread for fetching mixtures."""

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


class ChooseMixtureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختر خلطة")
        self.setMinimumSize(1000, 800)
        self.setModal(True)

        self.selected_mixture_id = None
        self.selected_mixture_name = None
        self.selected_mixture_unit = None  # Store the unit
        self.next_page_url = None
        self.prev_page_url = None

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
        title_text = QLabel("اختر خلطة من القائمة")
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

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["كود المنتج", "اسم المنتج", "الكمية المتاحة", "الوحدة", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 150)
        self.table.verticalHeader().setDefaultSectionSize(70)

        content_layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.next_button.clicked.connect(self.handle_next_page)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        content_layout.addLayout(pagination_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)

        self.handle_view_all()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials/"
        self._start_fetch_request(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(self.prev_page_url)

    def _start_fetch_request(self, url):
        self.thread = QThread()
        self.worker = MixtureFetcherWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {}).get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.populate_table(results)

    def populate_table(self, mixtures):
        self.table.setRowCount(0)
        for mixture in mixtures:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            mixture_id = mixture.get("id")
            mixture_name = mixture.get("material_name", "")
            mixture_unit = mixture.get("unit", "")  # Get the unit

            items = [
                QTableWidgetItem(str(mixture_id)),
                QTableWidgetItem(mixture_name),
                QTableWidgetItem(f"{mixture.get('quantity_in_unit', 0):,.2f}"),
                QTableWidgetItem(f"{mixture.get('unit')}"),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

            # Choose Button
            choose_button = QPushButton("اختر")
            choose_button.setObjectName("primaryButton")
            # Pass unit to the handler
            choose_button.clicked.connect(
                lambda ch, mid=mixture_id, mname=mixture_name, munit=mixture_unit: self.on_mixture_chosen(
                    mid, mname, munit
                )
            )
            choose_container = QWidget()
            choose_layout = QHBoxLayout(choose_container)
            choose_layout.addWidget(choose_button)
            choose_layout.setAlignment(Qt.AlignCenter)
            choose_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_pos, 4, choose_container)

            # Details Button
            details_button = QPushButton("تفاصيل")
            details_button.clicked.connect(
                lambda ch, mid=mixture_id, mname=mixture_name: self.handle_show_details(mid, mname)
            )
            details_container = QWidget()
            details_layout = QHBoxLayout(details_container)
            details_layout.addWidget(details_button)
            details_layout.setAlignment(Qt.AlignCenter)
            details_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_pos, 5, details_container)

    def handle_show_details(self, mixture_id, mixture_name):
        """Opens a dialog to show the materials for the selected mixture."""
        if mixture_id:
            dialog = MixtureMaterialsDetailsDialog(mixture_id, mixture_name, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على معرف الخلطة.")

    def on_mixture_chosen(self, mixture_id, mixture_name, mixture_unit):
        self.selected_mixture_id = mixture_id
        self.selected_mixture_name = mixture_name
        self.selected_mixture_unit = mixture_unit
        self.accept()

    def get_selected_mixture(self):
        # Return unit as well
        return self.selected_mixture_id, self.selected_mixture_name, self.selected_mixture_unit

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

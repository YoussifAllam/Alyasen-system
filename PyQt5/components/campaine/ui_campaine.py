from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from requests import request, exceptions
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .add_campaine_dialog import AddCampaignDialog


class CampaignApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request(self.method, self.url, json=self.payload, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class CampaignsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(15)

        # Ensure the widget can be shrunk/expanded without forcing the window's minimum/maximum size
        import PyQt5.QtWidgets as QtWidgets

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Header Section
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)

        title_vbox = QVBoxLayout()
        header = QLabel("إدارة الحملات")
        header.setObjectName("mainHeader")
        subheader = QLabel("عرض جميع الحملات المتاحة أو إضافة حملة جديدة.")
        subheader.setObjectName("mainSubheader")
        title_vbox.addWidget(header)
        title_vbox.addWidget(subheader)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        self.btn_add_campaign = QPushButton("إضافة حملة جديدة")
        self.btn_add_campaign.setObjectName("primaryButton")
        self.btn_show_all_campaigns = QPushButton("عرض الكل")
        self.btn_show_all_campaigns.setObjectName("primaryButton")
        self.btn_add_campaign.clicked.connect(self.show_add_dialog)
        self.btn_show_all_campaigns.clicked.connect(self.load_campaigns)
        header_layout.addWidget(self.btn_add_campaign)
        header_layout.addWidget(self.btn_show_all_campaigns)

        layout.addWidget(header_frame)

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "اسم الحملة", "العميل", "إجمالي التكلفة", "تاريخ الإنشاء"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Pagination controls
        self.pagination_layout = QHBoxLayout()
        self.btn_prev = QPushButton("السابق")
        self.btn_prev.setObjectName("secondaryButton")
        self.btn_prev.clicked.connect(self.load_previous)
        self.btn_prev.setEnabled(False)

        self.page_info = QLabel("الصفحة 1")
        self.page_info.setAlignment(Qt.AlignCenter)
        self.page_info.setStyleSheet("color: #9ca3af; font-size: 14px;")

        self.btn_next = QPushButton("التالي")
        self.btn_next.setObjectName("secondaryButton")
        self.btn_next.clicked.connect(self.load_next)
        self.btn_next.setEnabled(False)

        self.pagination_layout.addWidget(self.btn_prev)
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.page_info)
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.btn_next)

        layout.addLayout(self.pagination_layout)

        self.current_page = 1
        self.next_url = None
        self.previous_url = None

    def show_add_dialog(self):
        dialog = AddCampaignDialog(self)
        dialog.campaign_added.connect(self.load_campaigns)
        dialog.exec_()

    def load_campaigns(self):
        url = f"{BACKEND_BASE_URL}/campaine/"
        self.current_page = 1
        self.fetch_data(url)

    def load_next(self):
        if self.next_url:
            self.current_page += 1
            self.fetch_data(self.next_url)

    def load_previous(self):
        if self.previous_url:
            self.current_page -= 1
            self.fetch_data(self.previous_url)

    def fetch_data(self, url):
        self.worker_thread = QThread()
        self.worker = CampaignApiWorker("GET", url)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.start()

    def populate_table(self, response_data):
        data = response_data.get("data", {})
        campaigns = data.get("results", [])

        self.next_url = data.get("next")
        self.previous_url = data.get("previous")

        self.btn_next.setEnabled(bool(self.next_url))
        self.btn_prev.setEnabled(bool(self.previous_url))
        self.page_info.setText(f"الصفحة {self.current_page}")

        self.table.setRowCount(0)
        for camp in campaigns:
            row = self.table.rowCount()
            self.table.insertRow(row)

            items = [
                QTableWidgetItem(str(camp.get("id", ""))),
                QTableWidgetItem(camp.get("name", "")),
                QTableWidgetItem(camp.get("client_name", "")),
                QTableWidgetItem(f"{camp.get('total_cost', 0):,.2f}"),
                QTableWidgetItem(camp.get("created_date", "")),
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

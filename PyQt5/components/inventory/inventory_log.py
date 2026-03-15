from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QHeaderView,
    QGroupBox,
    QDateEdit,
    QCheckBox,
    QMessageBox,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QDate, QObject, QThread, pyqtSignal, pyqtSlot
from urllib.parse import urlencode
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class LogFetcherWorker(QObject):
    """Generic worker for fetching data."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url: str):
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
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class MaterialsLogUI(QWidget):
    # New signal to notify the parent to switch back
    back_to_inventory_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("سجل عمليات مخزن الخامات")
        header.setObjectName("mainHeader")
        subheader = QLabel("عرض سجل العمليات التي تمت على الخامات في المخزن.")
        subheader.setObjectName("mainSubheader")

        header_text_layout = QVBoxLayout()
        header_text_layout.addWidget(header)
        header_text_layout.addWidget(subheader)

        # Add back button to the header
        self.back_button = QPushButton("العودة للمخزن")
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.back_button)

        main_layout.addLayout(header_layout)

        # Form for filtering
        form_groupbox = QGroupBox("فلترة السجل")
        form_layout = QHBoxLayout(form_groupbox)
        form_layout.setSpacing(20)

        form_layout.addWidget(QLabel("اسم الخامة:"))
        self.name_search = QLineEdit()
        form_layout.addWidget(self.name_search)

        self.date_filter_checkbox = QCheckBox("فلترة بالتاريخ:")
        self.date_filter_checkbox.setObjectName("filterCheckbox")
        self.date_search = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.date_search.setEnabled(False)
        self.date_filter_checkbox.toggled.connect(self.date_search.setEnabled)

        form_layout.addWidget(self.date_search)
        form_layout.addWidget(self.date_filter_checkbox)
        form_layout.addStretch()

        # Action Buttons
        self.search_button = QPushButton("بحث")
        self.search_button.setObjectName("primaryButton")
        self.view_all_button = QPushButton("عرض الكل")
        self.view_today_button = QPushButton("عرض عمليات اليوم")

        form_layout.addWidget(self.search_button)
        form_layout.addWidget(self.view_all_button)
        form_layout.addWidget(self.view_today_button)

        # Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        headers = [
            "اسم الخامة",
            "العمليه",
            "التاريخ",
            "الكمية قبل",
            "الكمية بعد",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)

        main_layout.addWidget(form_groupbox)
        main_layout.addWidget(self.table)
        main_layout.addLayout(pagination_layout)

        # Connect signals
        self.search_button.clicked.connect(self.handle_search)
        self.view_all_button.clicked.connect(self.handle_view_all)
        self.view_today_button.clicked.connect(self.handle_view_today)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.back_button.clicked.connect(self.back_to_inventory_requested.emit)

    def handle_search(self):
        base_url = f"{BACKEND_BASE_URL}/material-warehouse-log/Warehouse-Transactions/"
        params = {}
        material_name = self.name_search.text().strip()
        if material_name:
            params["material_name"] = material_name

        if self.date_filter_checkbox.isChecked():
            params["transaction_date"] = self.date_search.date().toString("yyyy-MM-dd")

        url = f"{base_url}?{urlencode(params)}" if params else base_url
        self._start_fetch_request(url)

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/material-warehouse-log/Warehouse-Transactions/"
        self._start_fetch_request(url)

    def handle_view_today(self):
        """Fetches transactions for the current day."""
        url = f"{BACKEND_BASE_URL}/material-warehouse-log/Warehouse-today-Transactions/"
        self._start_fetch_request(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(self.prev_page_url)

    def _start_fetch_request(self, url):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = LogFetcherWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_table(self, logs):
        self.table.setRowCount(0)
        for log in logs:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            items = [
                QTableWidgetItem(str(log.get("material_name", ""))),
                QTableWidgetItem(str(log.get("transaction", ""))),
                QTableWidgetItem(str(log.get("transaction_date", ""))),
                QTableWidgetItem(str(log.get("quantity_before", ""))),
                QTableWidgetItem(str(log.get("quantity_after", ""))),
            ]

            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)

        if self.total_count > 0:
            try:
                page_size = self.table.rowCount()
                current_page = self.get_current_page()
                start_item = (current_page - 1) * page_size + 1
                end_item = start_item + page_size - 1
                if end_item > self.total_count:
                    end_item = self.total_count
                self.page_info_label.setText(f"عرض {start_item}-{end_item} من {self.total_count} سجل")
            except Exception:
                self.page_info_label.setText(f"إجمالي السجلات: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def get_current_page(self):
        if not self.prev_page_url:
            return 1
        try:
            if self.next_page_url:
                page_str = self.next_page_url.split("page=")[1].split("&")[0]
                return int(page_str) - 1
            if self.prev_page_url:
                page_str = self.prev_page_url.split("page=")[-1].split("&")[0]
                return int(page_str) + 1
        except (IndexError, ValueError):
            return 1
        return 1

    def _set_loading(self, is_loading):
        self.search_button.setDisabled(is_loading)
        self.view_all_button.setDisabled(is_loading)
        self.view_today_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        self.update_pagination_controls()
        QMessageBox.critical(self, "خطأ في الاتصال", message)

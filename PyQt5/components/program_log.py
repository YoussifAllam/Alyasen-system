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
    QMessageBox,
    QTableWidgetItem,
    QCheckBox,
)
from PyQt5.QtCore import QDate, QObject, QThread, pyqtSignal, pyqtSlot
from requests import request, exceptions

# We'll assume the base URL is in a constant file for good practice
from .Main_Ui_Components.constant import BACKEND_BASE_URL


class LogFetcherWorker(QObject):
    """
    Worker thread for fetching log data from the API asynchronously.
    """

    finished = pyqtSignal()
    success = pyqtSignal(dict)  # UPDATED: Now emits the entire dictionary response
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
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", str(error_data))
                    self.error.emit(f"خطأ من الخادم: {response.status_code}\n\n{detail}")
                except Exception:
                    self.error.emit(f"خطأ من الخادم: {response.status_code}\n\n{response.text}")

        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        except Exception as e:
            self.error.emit(f"حدث خطأ غير متوقع: {e}")
        finally:
            self.finished.emit()


class ProgramLogUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Initialize pagination state variables
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

        # Header
        header = QLabel("سجل عمليات البرنامج")
        header.setObjectName("mainHeader")
        subheader = QLabel("عرض وتصفية سجل العمليات التي تمت في النظام.")
        subheader.setObjectName("mainSubheader")
        main_layout.addWidget(header)
        main_layout.addWidget(subheader)

        # --- Search and Filter Section ---
        filter_groupbox = QGroupBox("أدوات البحث والتصفية")
        filter_layout = QHBoxLayout(filter_groupbox)
        filter_layout.setSpacing(15)

        filter_layout.addWidget(QLabel("اسم المستخدم:"))
        self.user_search = QLineEdit()
        filter_layout.addWidget(self.user_search)

        self.date_filter_checkbox = QCheckBox("فلترة بالتاريخ:")
        self.date_filter_checkbox.setObjectName("filterCheckbox")
        self.date_search = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.date_search.setEnabled(False)
        self.date_filter_checkbox.toggled.connect(self.date_search.setEnabled)

        filter_layout.addWidget(self.date_search)
        filter_layout.addWidget(self.date_filter_checkbox)
        filter_layout.addStretch()

        self.search_button = QPushButton("بحث")
        self.search_button.setObjectName("primaryButton")
        self.view_all_button = QPushButton("عرض الكل")

        filter_layout.addWidget(self.search_button)
        filter_layout.addWidget(self.view_all_button)

        # --- Data Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        headers = ["كود العمليه", "العمليه", "التاريخ", "اسم المستخدم"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # --- NEW: Pagination Controls ---
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")

        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)

        # Add all widgets to main layout
        main_layout.addWidget(filter_groupbox)
        main_layout.addWidget(self.table)
        main_layout.addLayout(pagination_layout)

        # --- Connect Signals ---
        self.view_all_button.clicked.connect(self.handle_view_all)
        self.search_button.clicked.connect(self.handle_search)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/transactions_log/transactions/"
        self._start_fetch_request(url)

    def handle_search(self):
        username = self.user_search.text().strip()
        base_url = f"{BACKEND_BASE_URL}/transactions_log/transactions/"
        params = []
        if username:
            params.append(f"username={username}")
        if self.date_filter_checkbox.isChecked():
            date = self.date_search.date().toString("yyyy-MM-dd")
            params.append(f"created_date={date}")
        url = f"{base_url}?{'&'.join(params)}" if params else base_url
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
        """Processes the full API response, including pagination links."""
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
        for log_entry in logs:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(str(log_entry.get("id", ""))))
            self.table.setItem(row_position, 1, QTableWidgetItem(log_entry.get("transaction", "")))
            self.table.setItem(row_position, 2, QTableWidgetItem(log_entry.get("created_date", "")))
            self.table.setItem(row_position, 3, QTableWidgetItem(log_entry.get("username", "")))

    def update_pagination_controls(self):
        """Enables/disables pagination buttons and updates the info label."""
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)

        start_item = self.table.rowCount() * (self.get_current_page() - 1) + 1
        end_item = start_item + self.table.rowCount() - 1

        if self.total_count > 0:
            self.page_info_label.setText(f"عرض {start_item}-{end_item} من {self.total_count} سجل")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def get_current_page(self):
        """A helper to estimate the current page number from the URL."""
        if not self.prev_page_url:
            return 1
        try:
            # Try to extract page number from 'next' URL
            if self.next_page_url:
                page_str = self.next_page_url.split("page=")[1].split("&")[0]
                return int(page_str) - 1
            # Try to extract from 'previous' URL if 'next' is null (last page)
            if self.prev_page_url:
                page_str = self.prev_page_url.split("page=")[-1].split("&")[0]
                return int(page_str) + 1
        except (IndexError, ValueError):
            return 1  # Fallback
        return 1

    def show_error_message(self, message):
        self._set_loading(False)
        self.update_pagination_controls()  # Also update controls on error
        QMessageBox.critical(self, "خطأ في الاتصال", message)

    def _set_loading(self, is_loading):
        self.search_button.setDisabled(is_loading)
        self.view_all_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

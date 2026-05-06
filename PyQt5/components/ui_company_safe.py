import sys
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QHeaderView,
    QGroupBox,
    QMessageBox,
    QTableWidgetItem,
    QFrame,
)
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QDate, Qt
from requests import request, exceptions

from .Main_Ui_Components.constant import BACKEND_BASE_URL


class SafeApiWorker(QObject):
    finished = pyqtSignal()
    balance_success = pyqtSignal(float)
    logs_success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, fetch_balance=False, logs_url=None):
        super().__init__()
        self.fetch_balance = fetch_balance
        self.logs_url = logs_url

    @pyqtSlot()
    def run(self):
        try:
            if self.fetch_balance:
                balance_url = f"{BACKEND_BASE_URL}/safe/safe/"
                resp = request("GET", balance_url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        self.balance_success.emit(float(data.get("data", 0.0)))
                else:
                    self.error.emit(f"خطأ في جلب الرصيد: {resp.status_code}")

            if self.logs_url:
                resp = request("GET", self.logs_url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data and isinstance(data["data"], dict):
                        self.logs_success.emit(data["data"])
                    elif "results" in data:
                        self.logs_success.emit(data)

        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        except Exception as e:
            self.error.emit(f"حدث خطأ غير متوقع: {e}")
        finally:
            self.finished.emit()


class CompanySafeUI(QWidget):
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
        header = QLabel("خزنة الشركة")
        header.setObjectName("mainHeader")
        subheader = QLabel("عرض رصيد الخزنة الحالي وسجل العمليات.")
        subheader.setObjectName("mainSubheader")
        main_layout.addWidget(header)
        main_layout.addWidget(subheader)

        # Current Balance Display
        balance_frame = QFrame()
        balance_frame.setStyleSheet(
            "QFrame { background-color: #f3f4f6; border-radius: 8px; padding: 15px; } QLabel { color: #1f2937; }"
        )
        balance_layout = QHBoxLayout(balance_frame)
        self.balance_label = QLabel("الرصيد الحالي: جاري التحميل...")
        self.balance_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #059669;"
        )
        balance_layout.addWidget(self.balance_label)
        main_layout.addWidget(balance_frame)

        # Filters
        filter_groupbox = QGroupBox("أدوات العرض")
        filter_layout = QHBoxLayout(filter_groupbox)
        filter_layout.setSpacing(15)

        self.show_all_button = QPushButton("عرض الكل")
        self.show_today_button = QPushButton("سجلات اليوم")
        self.show_today_button.setObjectName("primaryButton")

        filter_layout.addWidget(self.show_today_button)
        filter_layout.addWidget(self.show_all_button)
        filter_layout.addStretch()

        main_layout.addWidget(filter_groupbox)

        # Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        headers = ["العملية", "التاريخ"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        # Pagination Controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")

        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)

        main_layout.addLayout(pagination_layout)

        # Connect Signals
        self.show_all_button.clicked.connect(self.handle_show_all)
        self.show_today_button.clicked.connect(self.handle_show_today)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

        self.load_initial_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_initial_data()

    def load_initial_data(self):
        url = f"{BACKEND_BASE_URL}/safe/logs/"
        self._start_fetch_request(fetch_balance=True, logs_url=url)

    def handle_show_all(self):
        url = f"{BACKEND_BASE_URL}/safe/logs/"
        self._start_fetch_request(fetch_balance=False, logs_url=url)

    def handle_show_today(self):
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        url = f"{BACKEND_BASE_URL}/safe/logs/?date={today_str}"
        self._start_fetch_request(fetch_balance=False, logs_url=url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(fetch_balance=False, logs_url=self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(fetch_balance=False, logs_url=self.prev_page_url)

    def _start_fetch_request(self, fetch_balance=False, logs_url=None):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = SafeApiWorker(fetch_balance=fetch_balance, logs_url=logs_url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.balance_success.connect(self.update_balance)
        self.worker.logs_success.connect(self.handle_logs_response)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_balance(self, balance):
        self.balance_label.setText(f"الرصيد الحالي: {balance:,.2f} جنيه")

    def handle_logs_response(self, data_obj):
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

            transaction_val = log_entry.get("trnasaction", "")
            if not transaction_val:
                transaction_val = log_entry.get("transaction", "")

            date_val = log_entry.get("date", "")

            if "T" in date_val:
                dt_parts = date_val.split("T")
                date_str = dt_parts[0]
                time_str = dt_parts[1].split(".")[0]
                date_disp = f"{date_str} {time_str}"
            else:
                date_disp = date_val

            self.table.setItem(row_position, 0, QTableWidgetItem(transaction_val))
            self.table.setItem(row_position, 1, QTableWidgetItem(date_disp))

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)

        start_item = self.table.rowCount() * (self.get_current_page() - 1) + 1
        end_item = start_item + self.table.rowCount() - 1

        if self.total_count > 0:
            self.page_info_label.setText(
                f"عرض {start_item}-{end_item} من {self.total_count} سجل"
            )
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

    def show_error_message(self, message):
        self._set_loading(False)
        self.update_pagination_controls()
        QMessageBox.critical(self, "خطأ في الاتصال", message)

    def _set_loading(self, is_loading):
        self.show_all_button.setDisabled(is_loading)
        self.show_today_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

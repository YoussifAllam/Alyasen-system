from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QLineEdit,
    QTableWidget,
    QHeaderView,
    QGroupBox,
    QDateEdit,
    QTextEdit,
    QMessageBox,
    QTableWidgetItem,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QDate, QObject, QThread, pyqtSignal, pyqtSlot
from urllib.parse import urlencode

# We'll assume the base URL is in a constant file for good practice
from .Main_Ui_Components.constant import BACKEND_BASE_URL
from requests import request, exceptions
from .validation import (
    validate_not_empty,
    validate_positive_number,
    run_validations,
    _clear_errors,
)


class ExpenseFetcherWorker(QObject):
    """Worker thread for GETTING expense data from the API asynchronously."""

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


class ExpenseSummaryFetcherWorker(QObject):
    """Worker thread for fetching the expense summary."""

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


class ExpensePosterWorker(QObject):
    """Worker thread for POSTING new expense data to the API asynchronously."""

    finished = pyqtSignal()
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url: str, payload: dict):
        super().__init__()
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request("POST", self.url, json=self.payload, timeout=15)
            if response.status_code == 201 or response.status_code == 200:
                self.success.emit()
            else:
                try:
                    error_data = response.json()
                    detail = next(iter(error_data.values()), f"HTTP {response.status_code}")
                    if isinstance(detail, list):
                        detail = detail[0]
                    self.error.emit(str(detail))
                except Exception:
                    self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class ExpensesUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.is_first_load = True

        header = QLabel("إدارة المصروفات")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة وتعديل المصروفات العامة.")
        subheader.setObjectName("mainSubheader")
        main_layout.addWidget(header)
        main_layout.addWidget(subheader)

        top_section_layout = QHBoxLayout()

        form_groupbox = QGroupBox("بيانات المصروف")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        fields_grid = QGridLayout()
        fields_grid.setSpacing(15)

        self.name_input = QLineEdit()
        # self.permit_input = QLineEdit()  <-- Removed
        self.amount_input = QLineEdit()
        self.date_input = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)

        self.date_filter_checkbox = QCheckBox("فلترة بالتاريخ")
        self.date_filter_checkbox.setObjectName("filterCheckbox")
        self.date_input.setEnabled(True)  # Make sure it's enabled
        # self.date_filter_checkbox.toggled.connect(self.date_input.setEnabled) <-- Removed toggle connection

        fields_grid.addWidget(QLabel("الاسم"), 0, 0, 1, 2)
        fields_grid.addWidget(self.name_input, 1, 0, 1, 2)

        # Improved Layout:
        # Row 2: Amount Label (Col 0), Date Label (Col 1)
        fields_grid.addWidget(QLabel("المبلغ"), 2, 0)
        fields_grid.addWidget(QLabel("تاريخ العمليه"), 2, 1)

        # Row 3: Amount Input (Col 0), Date Input (Col 1)
        fields_grid.addWidget(self.amount_input, 3, 0)
        fields_grid.addWidget(self.date_input, 3, 1)

        # Row 4: Checkbox under Date Input (Col 1)
        fields_grid.addWidget(self.date_filter_checkbox, 4, 1, Qt.AlignLeft)

        form_layout.addLayout(fields_grid)
        form_layout.addWidget(QLabel("ملاحظات:"))
        form_layout.addWidget(self.notes_input)

        right_column_layout = QVBoxLayout()

        # --- Summary Card ---
        stats_groupbox = QGroupBox("ملخص المصروفات")
        stats_layout = QVBoxLayout(stats_groupbox)
        stats_layout.setSpacing(15)

        self.today_total_display = QLineEdit("0", readOnly=True)
        self.month_total_display = QLineEdit("0", readOnly=True)
        self.month_count_display = QLineEdit("0", readOnly=True)

        stats_layout.addWidget(QLabel("إجمالي المصروفات اليوم:"))
        stats_layout.addWidget(self.today_total_display)
        stats_layout.addWidget(QLabel("إجمالي المصروفات الشهر:"))
        stats_layout.addWidget(self.month_total_display)
        stats_layout.addWidget(QLabel("عدد المصروفات اليوم:"))
        stats_layout.addWidget(self.month_count_display)
        stats_layout.addStretch()

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        self.btn_add = QPushButton("أضافه")
        self.btn_add.setObjectName("primaryButton")
        self.btn_search = QPushButton("بحث")
        self.btn_view_all = QPushButton("عرض الكل")
        actions_layout.addWidget(self.btn_add)
        actions_layout.addWidget(self.btn_search)
        actions_layout.addWidget(self.btn_view_all)

        right_column_layout.addWidget(stats_groupbox)
        right_column_layout.addLayout(actions_layout)
        right_column_layout.addStretch()

        top_section_layout.addWidget(form_groupbox, 2)
        top_section_layout.addLayout(right_column_layout, 1)

        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Decreased column count as permit removed
        headers = ["الاسم", "التاريخ", "المبلغ", "ملاحظات"]  # Removed Permit
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Adjusted index

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")

        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)

        main_layout.addLayout(top_section_layout)
        main_layout.addWidget(self.table, 1)
        main_layout.addLayout(pagination_layout)

        self.btn_add.clicked.connect(self.handle_add_expense)
        self.btn_view_all.clicked.connect(self.handle_view_all)
        self.btn_search.clicked.connect(self.handle_search)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

    def showEvent(self, event):
        """Fetches initial data when the widget is first shown."""
        super().showEvent(event)
        if self.is_first_load:
            self.handle_fetch_summary()
            self.is_first_load = False

    def handle_fetch_summary(self):
        """Fetches the expense summary data."""
        url = f"{BACKEND_BASE_URL}/expenses/expenses_summery/"
        self.summary_thread = QThread()
        self.summary_worker = ExpenseSummaryFetcherWorker(url)
        self.summary_worker.moveToThread(self.summary_thread)
        self.summary_thread.started.connect(self.summary_worker.run)
        self.summary_worker.success.connect(self.update_summary_card)
        self.summary_worker.error.connect(self.show_error_message)
        self.summary_worker.finished.connect(self.summary_thread.quit)
        self.summary_worker.finished.connect(self.summary_worker.deleteLater)
        self.summary_thread.finished.connect(self.summary_thread.deleteLater)
        self.summary_thread.start()

    def update_summary_card(self, response):
        data = response.get("data", {})
        self.today_total_display.setText(f"{data.get('today_total_amount', 0):,.2f}")
        self.month_total_display.setText(f"{data.get('month_total_amount', 0):,.2f}")
        self.month_count_display.setText(str(data.get("month_count", 0)))

    def handle_add_expense(self):
        fields = [self.name_input, self.amount_input]
        _clear_errors(fields)

        validations = [
            validate_not_empty(self.name_input, "الاسم"),
            validate_positive_number(self.amount_input, "المبلغ"),
        ]
        if not run_validations(self, validations):
            return

        transaction = self.name_input.text().strip()
        amount = self.amount_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        payload = {
            "transaction": transaction,
            "amount": amount,
            "notes": notes,
            # "permit_number": permit_number, <-- Removed
            "created_date": self.date_input.date().toString(
                "yyyy-MM-dd"
            ),  # Always send date now? Assuming yes since input always enabled
        }
        url = f"{BACKEND_BASE_URL}/expenses/expenses/"
        self._start_post_request(url, payload)

    def _start_post_request(self, url, payload):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = ExpensePosterWorker(url, payload)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_add_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_worker.finished.connect(self.post_worker.deleteLater)
        self.post_thread.finished.connect(self.post_thread.deleteLater)
        self.post_thread.start()

    def on_add_success(self):
        QMessageBox.information(self, "نجاح", "تمت إضافة المصروف بنجاح.")
        self.name_input.clear()
        self.amount_input.clear()
        self.notes_input.clear()
        # self.permit_input.clear() <-- Removed
        self.handle_view_all()
        self.handle_fetch_summary()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/expenses/expenses/"
        self._start_fetch_request(url)

    def handle_search(self):
        base_url = f"{BACKEND_BASE_URL}/expenses/expenses/"
        params = {}
        transaction = self.name_input.text().strip()
        # permit_number = self.permit_input.text().strip() <-- Removed
        if transaction:
            params["transaction"] = transaction
        # if permit_number:
        #     params["permit_number"] = permit_number
        if self.date_filter_checkbox.isChecked():
            params["created_date"] = self.date_input.date().toString("yyyy-MM-dd")
        url = f"{base_url}?{urlencode(params)}" if params else base_url
        self._start_fetch_request(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(self.prev_page_url)

    def _start_fetch_request(self, url):
        self._set_loading(True)
        self.fetch_thread = QThread()
        self.fetch_worker = ExpenseFetcherWorker(url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.success.connect(self.handle_api_response)
        self.fetch_worker.error.connect(self.show_error_message)
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_table(self, expenses):
        self.table.setRowCount(0)
        for expense in expenses:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QTableWidgetItem(expense.get("transaction", "")))
            self.table.setItem(row_pos, 1, QTableWidgetItem(expense.get("created_date", "")))
            # self.table.setItem(row_pos, 2, QTableWidgetItem(expense.get("permit_number", ""))) <-- Removed
            self.table.setItem(row_pos, 2, QTableWidgetItem(str(expense.get("amount", ""))))  # Adjusted index
            self.table.setItem(row_pos, 3, QTableWidgetItem(str(expense.get("notes", ""))))  # Adjusted index

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
            except:  # noqa
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

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

    def _set_loading(self, is_loading):
        self.btn_view_all.setDisabled(is_loading)
        self.btn_search.setDisabled(is_loading)
        self.btn_add.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

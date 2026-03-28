from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGroupBox,
    QDateEdit,
    QStackedWidget,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QGridLayout,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate, QObject, QThread, pyqtSignal, pyqtSlot
from urllib.parse import urlencode
from requests import request, exceptions

from .Main_Ui_Components.constant import BACKEND_BASE_URL


class ReportFetcherWorker(QObject):
    """Worker thread for fetching report data."""

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


class ReportsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        # To store references to the report fields and their checkboxes
        self.report_fields = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        header = QLabel("تقارير الجرد")
        header.setObjectName("mainHeader")
        subheader = QLabel("عرض تقارير الجرد اليومية والشهرية والمخصصة.")
        subheader.setObjectName("mainSubheader")
        main_layout.addWidget(header)
        main_layout.addWidget(subheader)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        controls_panel = self.create_controls_panel()
        content_layout.addWidget(controls_panel, 1)
        results_panel = self.create_results_panel()
        content_layout.addWidget(results_panel, 2)
        main_layout.addLayout(content_layout, 1)

    def create_controls_panel(self):
        """Creates the left panel for selecting report type and date ranges."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        tabs_layout = QHBoxLayout()
        self.daily_button = QPushButton("جرد يومي")
        self.daily_button.setCheckable(True)
        self.daily_button.setObjectName("managementTabButton")
        self.monthly_button = QPushButton("جرد شهري")
        self.monthly_button.setCheckable(True)
        self.monthly_button.setObjectName("managementTabButton")
        self.range_button = QPushButton("جرد فترة محددة")
        self.range_button.setCheckable(True)
        self.range_button.setObjectName("managementTabButton")
        tabs_layout.addWidget(self.daily_button)
        tabs_layout.addWidget(self.monthly_button)
        tabs_layout.addWidget(self.range_button)

        self.date_stack = QStackedWidget()
        self.date_stack.addWidget(self.create_daily_date_widget())
        self.date_stack.addWidget(self.create_monthly_date_widget())
        self.date_stack.addWidget(self.create_range_date_widget())

        self.daily_button.clicked.connect(lambda: self.switch_date_mode(0))
        self.monthly_button.clicked.connect(lambda: self.switch_date_mode(1))
        self.range_button.clicked.connect(lambda: self.switch_date_mode(2))

        action_layout = QHBoxLayout()
        view_button = QPushButton("عرض التقرير")
        view_button.setObjectName("primaryButton")
        view_button.clicked.connect(self.handle_view_report)
        print_button = QPushButton("طباعة")
        action_layout.addWidget(view_button)
        action_layout.addWidget(print_button)

        layout.addLayout(tabs_layout)
        layout.addWidget(self.date_stack)
        layout.addLayout(action_layout)

        self.switch_date_mode(0)
        return panel

    def create_daily_date_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setLabelAlignment(Qt.AlignRight)
        self.daily_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        layout.addRow("اختر اليوم:", self.daily_date_edit)
        return widget

    def create_monthly_date_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setLabelAlignment(Qt.AlignRight)
        month_year_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{i:02d}" for i in range(1, 13)])
        self.year_edit = QLineEdit(str(QDate.currentDate().year()))
        month_year_layout.addWidget(self.year_edit)
        month_year_layout.addWidget(self.month_combo)
        layout.addRow("اختر الشهر والسنة:", month_year_layout)
        return widget

    def create_range_date_widget(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setLabelAlignment(Qt.AlignRight)
        self.from_date_edit = QDateEdit(
            calendarPopup=True, date=QDate.currentDate().addMonths(-1)
        )
        self.to_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        layout.addRow("من تاريخ:", self.from_date_edit)
        layout.addRow("إلى تاريخ:", self.to_date_edit)
        return widget

    def switch_date_mode(self, index):
        self.date_stack.setCurrentIndex(index)
        self.daily_button.setChecked(index == 0)
        self.monthly_button.setChecked(index == 1)
        self.range_button.setChecked(index == 2)

    def create_results_panel(self):
        """Creates the right panel for displaying report results with a new grid design."""
        card = QGroupBox("نتائج التقرير")
        grid_layout = QGridLayout(card)
        grid_layout.setSpacing(20)

        field_definitions = [
            ("suppliers_payment_report", "إجمالي عدد المشاريع:"),
            ("sells_amount_report", " إجمالي المشاريع النشطة:"),
            ("expenses_report", "إجمالي المصروفات:"),
            ("segmental_sells_amount_report", "إجمالي المبالغ لم تحصل بعد:"),
        ]

        positions = [(i, j) for i in range(3) for j in range(2)]

        for i, (flag, label_text) in enumerate(field_definitions):
            item_container = QFrame()
            item_container.setObjectName("reportItemCard")
            item_layout = QVBoxLayout(item_container)

            header_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setObjectName("reportItemLabel")
            checkbox = QCheckBox()
            checkbox.setObjectName("reportFieldCheckbox")
            header_layout.addWidget(label)
            header_layout.addStretch()
            header_layout.addWidget(checkbox)

            line_edit = QLineEdit("0.00", readOnly=True)
            line_edit.setObjectName("reportItemValue")
            if flag == "net_profit":
                line_edit.setObjectName("netProfitResult")

            item_layout.addLayout(header_layout)
            item_layout.addWidget(line_edit)

            self.report_fields[flag] = (line_edit, checkbox)

            row, col = positions[i]
            grid_layout.addWidget(item_container, row, col)

        return card

    def handle_view_report(self):
        """Builds the URL based on the selected tab and checkboxes, then fetches data."""
        flags_list = []
        for flag, (line_edit, checkbox) in self.report_fields.items():
            if checkbox.isChecked():
                flags_list.append(("flags_list", flag))

        if not flags_list:
            QMessageBox.warning(
                self, "خطأ", "الرجاء تحديد حقل واحد على الأقل لعرضه في التقرير."
            )
            return

        params = []
        base_url = ""

        if self.daily_button.isChecked():
            base_url = f"{BACKEND_BASE_URL}/reports/daily-report/"
            start_date = self.daily_date_edit.date().toString("yyyy-MM-dd")
            params = [("start_date", start_date)]

        elif self.monthly_button.isChecked():
            base_url = f"{BACKEND_BASE_URL}/reports/month-report/"
            year = self.year_edit.text().strip()
            month = self.month_combo.currentText()
            if not year.isdigit():
                QMessageBox.warning(self, "خطأ", "الرجاء إدخال سنة صالحة.")
                return
            params = [("year", year), ("month", month)]

        elif self.range_button.isChecked():
            base_url = f"{BACKEND_BASE_URL}/reports/year-report/"
            start_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            params = [("start_date", start_date), ("end_date", end_date)]

        else:
            return  # Should not happen

        # Combine date/month parameters with flags
        full_params = params + flags_list
        url = f"{base_url}?{urlencode(full_params)}"
        self._start_fetch_request(url)

    def _start_fetch_request(self, url):
        self.thread = QThread()
        self.worker = ReportFetcherWorker(url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_report_results)
        self.worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_report_results(self, response_data):
        """Populates the line edits with data from the API response."""
        data = response_data.get("data", {})

        for flag, (line_edit, checkbox) in self.report_fields.items():
            # Clear previous results first
            line_edit.setText("0.00")

            if flag in data:
                value = data[flag]
                if isinstance(value, (int, float)):
                    line_edit.setText(f"{value:,.2f}")
                else:
                    line_edit.setText(str(value))

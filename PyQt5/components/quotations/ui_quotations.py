from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QTableWidget,
    QHeaderView,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QDate, QObject, QThread, pyqtSignal, pyqtSlot
from requests import request, exceptions
from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class QuotationApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, files=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.files = files

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "POST" and self.files:
                response = request(
                    self.method,
                    self.url,
                    data=self.payload,
                    files=self.files,
                    timeout=15,
                )
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(
                    f"خطأ من الخادم: {response.status_code}\n{response.text}"
                )
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class QuotationsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.attachments_paths = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        layout_h = QHBoxLayout()
        form_panel = self.create_form_panel()
        table_panel = self.create_table_panel()

        layout_h.addWidget(form_panel, 1)
        layout_h.addWidget(table_panel, 2)

        main_layout.addLayout(layout_h)

    def create_form_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("عروض الاسعار")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة عرض سعر جديد.")
        subheader.setObjectName("mainSubheader")

        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("إضافة عرض سعر")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.client_name_input = QLineEdit(placeholderText="اسم العميل")
        self.company_name_input = QLineEdit(placeholderText="اسم الشركة")
        self.price_input = QLineEdit(placeholderText="السعر")

        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText("التفاصيل")
        self.details_input.setMaximumHeight(80)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")

        self.attachments_label = QLabel("لم يتم اختيار مرفقات")
        self.attachments_label.setAlignment(Qt.AlignCenter)
        self.attachments_label.setMinimumHeight(40)

        btn_choose_attachments = QPushButton("إضافة مرفقات")
        btn_choose_attachments.clicked.connect(self.choose_attachments)

        form_layout.addWidget(QLabel("اسم العميل:"))
        form_layout.addWidget(self.client_name_input)
        form_layout.addWidget(QLabel("اسم الشركة:"))
        form_layout.addWidget(self.company_name_input)
        form_layout.addWidget(QLabel("السعر:"))
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(QLabel("التفاصيل:"))
        form_layout.addWidget(self.details_input)
        form_layout.addWidget(QLabel("آخر موعد لعرض السعر:"))
        form_layout.addWidget(self.date_input)

        form_layout.addWidget(self.attachments_label)
        form_layout.addWidget(btn_choose_attachments)

        self.btn_add_quotation = QPushButton("إضافة عرض السعر")
        self.btn_add_quotation.setObjectName("primaryButton")
        self.btn_add_quotation.clicked.connect(self.handle_add_quotation)
        form_layout.addWidget(self.btn_add_quotation)

        layout.addWidget(form_groupbox)
        return container

    def create_table_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="ابحث باسم العميل...")
        self.search_button = QPushButton("بحث")
        self.search_button.clicked.connect(self.handle_search)

        self.view_all_button = QPushButton("عرض الكل")
        self.view_all_button.clicked.connect(self.handle_view_all)

        self.show_attachments_btn = QPushButton("عرض المرفقات لعرض السعر")
        self.show_attachments_btn.clicked.connect(self.handle_show_attachments)

        actions_layout.addWidget(self.search_input, 1)
        actions_layout.addWidget(self.search_button)
        actions_layout.addWidget(self.view_all_button)
        actions_layout.addWidget(self.show_attachments_btn)

        layout.addLayout(actions_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        headers = [
            "كود",
            "اسم العميل",
            "اسم الشركة",
            "السعر",
            "تاريخ ارسال العرض",
            "آخر موعد",
            "التفاصيل",
            "إجراءات",
        ]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.Fixed
        )
        self.table.setColumnWidth(7, 100)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(80)

        layout.addWidget(self.table, 1)
        return container

    def choose_attachments(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "اختر المرفقات", "", "All Files (*)"
        )
        if file_paths:
            self.attachments_paths = file_paths
            self.attachments_label.setText(
                f"تم اختيار {len(self.attachments_paths)} ملف/صورة"
            )

    def handle_add_quotation(self):
        # Placeholder for adding functionality
        client_name = self.client_name_input.text().strip()
        if not client_name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم العميل.")
            return

        QMessageBox.information(self, "نجاح", "تم إضافة عرض السعر بنجاح المبدئي.")

        # Add to table for demo purposes
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        self.table.setItem(row_pos, 0, QTableWidgetItem(str(row_pos + 1)))
        self.table.setItem(row_pos, 1, QTableWidgetItem(self.client_name_input.text()))
        self.table.setItem(row_pos, 2, QTableWidgetItem(self.company_name_input.text()))
        self.table.setItem(row_pos, 3, QTableWidgetItem(self.price_input.text()))
        self.table.setItem(
            row_pos, 4, QTableWidgetItem(self.date_input.date().toString("yyyy-MM-dd"))
        )
        self.table.setItem(
            row_pos, 5, QTableWidgetItem(self.details_input.toPlainText())
        )

        delete_btn = QPushButton("حذف")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.setStyleSheet("background-color: #ef4444; color: white;")
        delete_btn.clicked.connect(lambda _, r=row_pos: self.delete_row(r))
        self.table.setCellWidget(row_pos, 6, delete_btn)

        self.clear_form()

    def clear_form(self):
        self.client_name_input.clear()
        self.company_name_input.clear()
        self.price_input.clear()
        self.details_input.clear()
        self.date_input.setDate(QDate.currentDate())
        self.attachments_paths = []
        self.attachments_label.setText("لم يتم اختيار مرفقات")

    def handle_search(self):
        pass  # Placeholder for search backend call

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/quotations/"
        self._set_loading(True)
        self.thread = QThread()
        self.worker = QuotationApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.populate_table(results)
        self._set_loading(False)

    def populate_table(self, quotations):
        self.table.setRowCount(0)
        for quote in quotations:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(str(quote.get("id", ""))),
                QTableWidgetItem(quote.get("client_name", "")),
                QTableWidgetItem(quote.get("company_name", "")),
                QTableWidgetItem(str(quote.get("price", ""))),
                QTableWidgetItem(quote.get("created_at", "")),
                QTableWidgetItem(quote.get("quotation_last_date", "")),
                QTableWidgetItem(
                    quote.get("details", "")[:50]
                    + ("..." if len(quote.get("details", "")) > 50 else "")
                ),
            ]
            for item in items:
                item.setTextAlignment(Qt.AlignCenter)
            for i, item in enumerate(items):
                self.table.setItem(row_pos, i, item)

            delete_btn = QPushButton("حذف")
            delete_btn.setObjectName("deleteBtn")
            delete_btn.setStyleSheet("background-color: #ef4444; color: white;")
            delete_btn.clicked.connect(lambda _, r=row_pos: self.delete_row(r))
            self.table.setCellWidget(row_pos, 7, delete_btn)

    def _set_loading(self, is_loading):
        self.view_all_button.setEnabled(not is_loading)
        self.search_button.setEnabled(not is_loading)
        if is_loading:
            self.view_all_button.setText("جاري التحميل...")
        else:
            self.view_all_button.setText("عرض الكل")

    def show_error_message(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

    def handle_show_attachments(self):
        pass  # Placeholder for showing attachments

    def delete_row(self, row):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد أنك تريد حذف عرض السعر هذا؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.table.removeRow(row)

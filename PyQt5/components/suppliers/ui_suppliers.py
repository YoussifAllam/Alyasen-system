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
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QStackedWidget,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
from requests import request, exceptions
from urllib.parse import urlencode

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .supplier_profile import SupplierProfileUI
from ..validation import (
    validate_not_empty,
    validate_phone,
    validate_optional_email,
    validate_positive_number,
    run_validations,
    _clear_errors,
)


class SupplierApiWorker(QObject):
    """Generic worker for handling API requests for suppliers."""

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
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class SuppliersUI(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Stacked Widget to switch views ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create the pages
        self.main_page = self.create_main_page()
        self.profile_page = SupplierProfileUI()

        # Add pages to the stack
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.profile_page)

        # Connect the back signal from the profile page
        self.profile_page.back_to_list_requested.connect(self.show_main_page)

    def create_main_page(self):
        """Creates the main widget with the form and table."""
        main_widget = QWidget()
        main_widget.setObjectName("mainContent")

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.profile_pic_path = None

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        left_panel = self.create_form_panel()
        main_layout.addWidget(left_panel, 1)

        right_panel = self.create_table_panel()
        main_layout.addWidget(right_panel, 2)

        return main_widget

    def create_form_panel(self):
        """Creates the left panel for adding a new supplier."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        header = QLabel("إدارة الموردين")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة مورد جديد أو البحث عن مورد.")
        subheader.setObjectName("mainSubheader")

        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("إضافة مورد جديد")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(placeholderText="اسم المورد")
        self.phone_input = QLineEdit(placeholderText="رقم الهاتف")
        self.email_input = QLineEdit(placeholderText="(اختياري)البريد الإلكتروني")
        self.total_amount_due_input = QLineEdit(
            placeholderText="إجمالي المطلوب دفعة للمورد"
        )

        self.profile_pic_label = QLabel("لم يتم اختيار صورة")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setMinimumHeight(150)
        self.profile_pic_label.setObjectName("imagePreview")

        btn_choose_pic = QPushButton("اختيار صورة للمورد")
        btn_choose_pic.clicked.connect(self.choose_profile_picture)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.total_amount_due_input)
        form_layout.addWidget(self.profile_pic_label)
        form_layout.addWidget(btn_choose_pic)

        self.btn_add_supplier = QPushButton("إضافة المورد")
        self.btn_add_supplier.setObjectName("primaryButton")
        self.btn_add_supplier.clicked.connect(self.handle_add_supplier)
        form_layout.addWidget(self.btn_add_supplier)

        layout.addWidget(form_groupbox)
        layout.addStretch()
        return container

    def create_table_panel(self):
        """Creates the right panel with the table and action buttons."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="ابحث بالاسم أو رقم الهاتف...")
        self.search_button = QPushButton("بحث")
        self.search_button.clicked.connect(self.handle_search)
        actions_layout.addWidget(self.search_input, 1)
        actions_layout.addWidget(self.search_button)
        self.view_all_button = QPushButton("عرض الكل")
        self.view_all_button.clicked.connect(self.handle_view_all)
        actions_layout.addWidget(self.view_all_button)
        self.btn_show_profile = QPushButton("عرض ملف المورد")
        self.btn_show_profile.setEnabled(False)
        self.btn_show_profile.clicked.connect(self.handle_show_profile)
        actions_layout.addWidget(self.btn_show_profile)
        layout.addLayout(actions_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "كود",
                "اسم المورد",
                "رقم الهاتف",
                "البريد الإلكتروني",
                "اجمالي المستحق له",
                "اجمالي المطلوب منا",
                "اجمالي المدفوع",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
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
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(
            lambda: self.btn_show_profile.setEnabled(True)
        )
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
        layout.addWidget(self.table)
        layout.addLayout(pagination_layout)
        return container

    def handle_show_profile(self):
        """Fetches supplier data and switches to the profile page."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        supplier_id = self.table.item(selected_rows[0].row(), 0).text()
        url = f"{BACKEND_BASE_URL}/suppliers/info/?id={supplier_id}"
        self._start_fetch_request(url, is_profile_fetch=True)

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def handle_api_response(self, response_data, is_profile_fetch=False):
        if is_profile_fetch:
            self.profile_page.update_data(response_data)
            self.stacked_widget.setCurrentIndex(1)
            self._set_loading(False)
            return

        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def _start_fetch_request(self, url, is_profile_fetch=False):
        self._set_loading(True)
        self.fetch_thread = QThread()
        self.fetch_worker = SupplierApiWorker("GET", url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.success.connect(
            lambda data: self.handle_api_response(data, is_profile_fetch)
        )
        self.fetch_worker.error.connect(self.show_error_message)
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_thread.start()

    def choose_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر صورة", "", "Image files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.profile_pic_path = file_path
            pixmap = QPixmap(file_path)
            self.profile_pic_label.setPixmap(
                pixmap.scaled(
                    self.profile_pic_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def handle_add_supplier(self):
        fields = [self.name_input, self.phone_input, self.email_input, self.total_amount_due_input]
        _clear_errors(fields)

        validations = [
            validate_not_empty(self.name_input, "اسم المورد"),
            validate_phone(self.phone_input, "رقم الهاتف"),
            validate_optional_email(self.email_input, "البريد الإلكتروني"),
            validate_positive_number(self.total_amount_due_input, "إجمالي المطلوب دفعه"),
        ]
        if not run_validations(self, validations):
            return

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        total_amount_due = self.total_amount_due_input.text().strip()
        total_amount_payable = self.total_amount_due_input.text().strip()

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "name": name,
            "phone": phone,
            "email": email,
            "username": username,
            "total_amount_due": total_amount_due,
            "total_amount_payable": total_amount_payable,
        }

        files = None
        if self.profile_pic_path:
            files = {"profile_picture": open(self.profile_pic_path, "rb")}

        url = f"{BACKEND_BASE_URL}/suppliers/suppliers/"
        self._start_post_request(url, payload, files)

    def handle_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "خطأ في البحث", "الرجاء إدخال نص للبحث.")
            return

        params = urlencode({"q": query})
        url = f"{BACKEND_BASE_URL}/suppliers/suppliers/?{params}"
        self._start_fetch_request(url)

    def _start_post_request(self, url, payload, files):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = SupplierApiWorker("POST", url, payload, files)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_add_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_thread.start()

    def on_add_success(self):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تمت إضافة المورد بنجاح.")
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.profile_pic_label.setText("لم يتم اختيار صورة")
        self.profile_pic_path = None
        self.handle_view_all()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/suppliers/suppliers/"
        self._start_fetch_request(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(self.prev_page_url)

    def populate_table(self, suppliers):
        self.table.setRowCount(0)
        for supplier in suppliers:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(str(supplier.get("id", ""))),
                QTableWidgetItem(supplier.get("name", "")),
                QTableWidgetItem(supplier.get("phone", "")),
                QTableWidgetItem(supplier.get("email", "")),
                QTableWidgetItem(str(supplier.get("total_amount_due", ""))),
                QTableWidgetItem(str(supplier.get("total_amount_payable", ""))),
                QTableWidgetItem(str(supplier.get("total_paid_amount", ""))),
            ]
            for item in items:
                item.setTextAlignment(Qt.AlignCenter)
            for i, item in enumerate(items):
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي الموردين: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def _set_loading(self, is_loading):
        self.view_all_button.setDisabled(is_loading)
        self.search_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.btn_add_supplier.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

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
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QStackedWidget,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
from requests import request, exceptions
from urllib.parse import urlencode

from ..Main_Ui_Components.constant import BACKEND_BASE_URL

from .client_profile import ClientProfileUI


class ClientApiWorker(QObject):
    """Worker for handling API requests for clients (GET and POST with files)."""

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
                response = request(self.method, self.url, data=self.payload, files=self.files, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}\n{response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class ClientsUI(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.settings = QSettings("FactorySystem")

        # --- Stacked Widget to switch views ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create the pages
        self.main_page = self.create_main_page()
        self.profile_page = ClientProfileUI()

        # Add pages to the stack
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.profile_page)

        # Connect the back signal from the profile page
        self.profile_page.back_to_list_requested.connect(self.show_main_page)

    def create_main_page(self):
        main_widget = QWidget()
        main_widget.setObjectName("mainContent")
        self.profile_pic_path = None
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        left_panel = self.create_form_panel()
        main_layout.addWidget(left_panel, 1)

        right_panel = self.create_table_panel()
        main_layout.addWidget(right_panel, 2)

        return main_widget

    def create_form_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("إدارة العملاء")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة عميل جديد أو البحث عن عميل.")
        subheader.setObjectName("mainSubheader")

        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("إضافة عميل جديد")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(placeholderText="اسم العميل")
        self.phone_input = QLineEdit(placeholderText="رقم الهاتف")
        self.email_input = QLineEdit(placeholderText="(اختياري) البريد الإلكتروني")
        self.total_balance_owed_to_us_input = QLineEdit(placeholderText=" مبلغ مدينية العميل")

        self.profile_pic_label = QLabel("لم يتم اختيار صورة")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setMinimumHeight(150)
        self.profile_pic_label.setObjectName("imagePreview")

        btn_choose_pic = QPushButton("اختيار صورة للعميل")
        btn_choose_pic.clicked.connect(self.choose_profile_picture)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.total_balance_owed_to_us_input)
        form_layout.addWidget(self.profile_pic_label)
        form_layout.addWidget(btn_choose_pic)

        self.btn_add_client = QPushButton("إضافة العميل")
        self.btn_add_client.setObjectName("primaryButton")
        self.btn_add_client.clicked.connect(self.handle_add_client)
        form_layout.addWidget(self.btn_add_client)

        layout.addWidget(form_groupbox)
        return container

    def create_table_panel(self):
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

        self.btn_show_profile = QPushButton("عرض ملف العميل")
        self.btn_show_profile.setEnabled(False)
        self.btn_show_profile.clicked.connect(self.handle_show_profile)
        actions_layout.addWidget(self.btn_show_profile)

        layout.addLayout(actions_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        headers = [
            "كود",
            "اسم العميل",
            "رقم الهاتف",
            "البريد الألكتروني",
            "اجمالي المستحق لنا",
            "باقي المطلوب منه",
            "اجمالي المدفوع",
        ]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(lambda: self.btn_show_profile.setEnabled(True))

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

        layout.addWidget(self.table, 1)
        layout.addLayout(pagination_layout)
        return container

    def choose_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "اختر صورة", "", "Image files (*.png *.jpg *.jpeg)")
        if file_path:
            self.profile_pic_path = file_path
            pixmap = QPixmap(file_path)
            self.profile_pic_label.setPixmap(
                pixmap.scaled(
                    self.profile_pic_label.width(),
                    self.profile_pic_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def handle_add_client(self):
        """Validates form data and starts the POST request."""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        total_balance_owed_to_us = self.total_balance_owed_to_us_input.text().strip()

        if not name or not phone or not total_balance_owed_to_us:
            QMessageBox.warning(
                self, "خطأ", "الرجاء إدخال اسم العميل ورقم الهاتف و اجمالي المستحق لنا على الأقل."
            )
            return

        username = self.settings.value("user_name", "unknown_user")

        payload = {
            "name": name,
            "phone": phone,
            "email": email,
            "total_balance_owed_to_us": total_balance_owed_to_us,
            "total_remaining_balance_owed_to_us": total_balance_owed_to_us,
            "username": username,
        }

        files = None
        if self.profile_pic_path:
            files = {"profile_picture": open(self.profile_pic_path, "rb")}

        url = f"{BACKEND_BASE_URL}/clients/clients/"
        self._start_post_request(url, payload, files)

    def handle_search(self):
        """Handles searching for clients."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال نص للبحث.")
            return

        params = urlencode({"q": query})
        url = f"{BACKEND_BASE_URL}/clients/clients/?{params}"
        self._start_fetch_request(url)

    def on_add_success(self):
        """Handles successful addition of a client."""
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تمت إضافة العميل بنجاح.")
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.total_balance_owed_to_us_input.clear()
        self.profile_pic_label.setText("لم يتم اختيار صورة")
        self.profile_pic_path = None
        self.handle_view_all()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/clients/clients/"
        self._start_fetch_request(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_fetch_request(self.prev_page_url)

    def _start_fetch_request(self, url, on_success=None):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = ClientApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        # Use the provided success handler or the default one
        success_handler = on_success if on_success else self.handle_api_response
        self.worker.success.connect(success_handler)

        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _start_post_request(self, url, payload, files):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = ClientApiWorker("POST", url, payload, files)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_add_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_table(self, clients):
        self.table.setRowCount(0)
        for client in clients:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(str(client.get("id", ""))),
                QTableWidgetItem(client.get("name", "")),
                QTableWidgetItem(client.get("phone", "")),
                QTableWidgetItem(client.get("email", "")),
                QTableWidgetItem(f"{client.get('total_balance_owed_to_us', 0):,.2f}"),
                QTableWidgetItem(f"{client.get('total_remaining_balance_owed_to_us', 0):,.2f}"),
                QTableWidgetItem(f"{client.get('total_paid_amount', 0):,.2f}"),
            ]
            for item in items:
                item.setTextAlignment(Qt.AlignCenter)
            for i, item in enumerate(items):
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي العملاء: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def _set_loading(self, is_loading):
        self.view_all_button.setEnabled(not is_loading)
        self.search_button.setEnabled(not is_loading)
        self.next_button.setEnabled(not is_loading)
        self.prev_button.setEnabled(not is_loading)
        self.btn_add_client.setEnabled(not is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        # ... (This method remains the same)
        pass

    def show_main_page(self):
        """Switches the view back to the main client list."""
        self.stacked_widget.setCurrentIndex(0)

    def handle_show_profile(self):
        """Fetches client data and switches to the profile page."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        client_id = self.table.item(selected_rows[0].row(), 0).text()
        url = f"{BACKEND_BASE_URL}/clients/info/?id={client_id}"
        self._start_fetch_request(url, on_success=self.on_profile_fetch_success)

    def on_profile_fetch_success(self, data):
        self.profile_page.update_data(data)
        self.stacked_widget.setCurrentIndex(1)
        self._set_loading(False)

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

# from .machien_profile import MachineProfileUI


class MachineApiWorker(QObject):
    """Worker for handling API requests for workers."""

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
                try:
                    error_data = response.json()
                    if "الخطاء" in error_data:
                        error_msg = error_data["الخطاء"]
                    elif "error" in error_data:
                        error_msg = error_data["error"]
                    else:
                        error_msg = next(
                            iter(error_data.values()), f"HTTP {response.status_code}"
                        )
                        if isinstance(error_msg, list):
                            error_msg = error_msg[0]
                    self.error.emit(str(error_msg))
                except Exception:
                    self.error.emit(
                        response.text or f"خطأ من الخادم: {response.status_code}"
                    )
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class CompanyAssetsUI(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.main_page = self.create_main_page()
        # self.profile_page = MachineProfileUI()

        self.stacked_widget.addWidget(self.main_page)
        # self.stacked_widget.addWidget(self.profile_page)

        # self.profile_page.back_to_list_requested.connect(self.show_main_page)

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
        """Creates the left panel for adding a new worker."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("إدارة أصول الشركة")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة أصل جديد أو البحث عن أصل.")
        subheader.setObjectName("mainSubheader")

        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("اضافة أصل جديد")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(placeholderText="اسم ")
        self.price_input = QLineEdit(placeholderText="سعر ")
        self.details_input = QLineEdit(placeholderText="تفاصيل إضافية ")

        self.profile_pic_label = QLabel("لم يتم اختيار صورة")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setMinimumHeight(150)
        self.profile_pic_label.setObjectName("imagePreview")

        btn_choose_pic = QPushButton("اختيار صورة ")
        btn_choose_pic.clicked.connect(self.choose_profile_picture)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(self.details_input)
        form_layout.addWidget(self.profile_pic_label)
        form_layout.addWidget(btn_choose_pic)

        self.btn_add_machine = QPushButton("إضافة ")
        self.btn_add_machine.setObjectName("primaryButton")
        self.btn_add_machine.clicked.connect(self.handle_add_machine)
        form_layout.addWidget(self.btn_add_machine)

        layout.addWidget(form_groupbox)
        return container

    def create_table_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="ابحث بالاسم...")
        actions_layout.addWidget(self.search_input, 1)
        self.search_button = QPushButton("بحث")
        self.search_button.clicked.connect(self.handle_search)
        actions_layout.addWidget(self.search_button)
        self.view_all_button = QPushButton("عرض الكل")
        self.view_all_button.clicked.connect(self.handle_view_all)
        actions_layout.addWidget(self.view_all_button)
        self.show_attachments_button = QPushButton("عرض المرفقات")
        # self.show_attachments_button.clicked.connect(self.handle_show_attachments)
        actions_layout.addWidget(self.show_attachments_button)

        layout.addLayout(actions_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        headers = ["اسم ", "سعر", "تفاصيل إضافية"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
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

    def on_selection_changed(self):
        """Enables buttons when a table row is selected."""
        is_selected = bool(self.table.selectionModel().selectedRows())  # noqa

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def choose_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر صورة", "", "Image files (*.png *.jpg *.jpeg)"
        )
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

    def handle_add_machine(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم .")
            return
        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")
        payload = {"name": name, "username": username}
        files = None
        if self.profile_pic_path:
            files = {"image": open(self.profile_pic_path, "rb")}
        url = f"{BACKEND_BASE_URL}/company_assets/company-assets/"
        self._start_api_request(
            "POST", url, payload=payload, files=files, on_success=self.on_add_success
        )

    def on_add_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تمت إضافة الأله بنجاح.")
        self.name_input.clear()
        self.profile_pic_label.setText("لم يتم اختيار صورة")
        self.profile_pic_path = None
        self.handle_view_all()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/company_assets/company-assets/"
        self._start_api_request("GET", url, on_success=self.handle_api_response)

    def handle_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال نص للبحث.")
            return
        params = urlencode({"q": query})
        url = f"{BACKEND_BASE_URL}/company_assets/company-assets/?{params}"
        self._start_api_request("GET", url, on_success=self.handle_api_response)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_api_request(
                "GET", self.next_page_url, on_success=self.handle_api_response
            )

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_api_request(
                "GET", self.prev_page_url, on_success=self.handle_api_response
            )

    def _start_api_request(
        self, method, url, payload=None, files=None, on_success=None
    ):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = MachineApiWorker(method, url, payload, files)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if on_success:
            self.worker.success.connect(on_success)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self._set_loading(False))
        self.thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self.update_pagination_controls()

    def populate_table(self, machines):
        self.table.setRowCount(0)
        for machine in machines:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            machine_id = machine.get("id")

            # 1. Create the item for the ID column
            id_item = QTableWidgetItem(str(machine_id))

            # 2. *** CRITICAL: Store the actual ID in Qt.UserRole ***
            id_item.setData(Qt.UserRole, machine_id)

            items = [
                id_item,  # Column 0: ID
                QTableWidgetItem(machine.get("name", "")),  # Column 1: Name
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي الأصول: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def _set_loading(self, is_loading):
        self.search_button.setDisabled(is_loading)
        self.view_all_button.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.btn_add_machine.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

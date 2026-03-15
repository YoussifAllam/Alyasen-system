from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QTableWidget,
    QHeaderView,
    QGridLayout,
    QMessageBox,
    QTableWidgetItem,
    QDialog,  # New import for the dialog
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, pyqtSlot, QSettings
from requests import request, get, exceptions

# Assuming these are defined elsewhere
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .AddComponentDialog import AddComponentDialog
from .RepairHistoryDialog import RepairHistoryDialog


class ApiWorker(QObject):
    """Worker for handling generic API requests (JSON/Image)."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    image_success = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, response_type="json"):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.response_type = response_type

    @pyqtSlot()
    def run(self):
        try:
            # Note: Using 'json' argument in requests handles the Content-Type header
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201, 204]:
                if self.response_type == "json":
                    self.success.emit(response.json() if response.content else {})
                elif self.response_type == "image":
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
                else:
                    self.success.emit({})
            else:
                try:
                    error_data = response.json()
                    # Handling Django/DRF style errors which might be nested
                    error_msg = error_data.get("error", error_data.get("الخطاء", response.text))
                    if isinstance(error_msg, dict):
                        # Extract the first message from the dict values
                        error_msg = next(iter(error_msg.values()))[0]
                    self.error.emit(str(error_msg) or f"خطأ من الخادم: {response.status_code}")
                except Exception:
                    self.error.emit(response.text or f"خطأ من الخادم: {response.status_code}")

        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class MachineProfileUI(QWidget):
    back_to_list_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.machine_id = None
        self.machine_name = ""
        self.machine_status = ""
        self.last_repair_date = ""
        self.component_list_url = None
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.api_thread = None  # Initialize thread manager
        self.api_worker = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # --- 1. Header Section ---
        header_widget = self.create_header_widget()
        main_layout.addWidget(header_widget)

        # --- 2. Machine Info Section ---
        info_section = self.create_machine_info_section()
        main_layout.addWidget(info_section)

        # --- 3. Components Section ---
        components_section = self.create_components_section()
        main_layout.addWidget(components_section, 1)

        # --- 4. Pagination ---
        pagination_layout = self.create_pagination_controls()
        main_layout.addLayout(pagination_layout)

    # --- UI Creation Helpers (methods remain the same) ---
    def create_header_widget(self):
        # ... (implementation remains the same)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.name_label = QLabel("ملف الآلة")
        self.name_label.setObjectName("mainHeader")
        self.name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        back_button = QPushButton("⬅️ العودة للقائمة")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        back_button.setFixedWidth(150)
        layout.addWidget(self.name_label, 1)
        layout.addWidget(back_button)
        return widget

    def create_machine_info_section(self):
        # ... (implementation remains the same)
        section = QFrame()
        section.setObjectName("card")
        section.setMaximumHeight(200)

        layout = QHBoxLayout(section)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)

        image_frame = QFrame()
        image_frame.setObjectName("imageFrame")
        image_layout = QVBoxLayout(image_frame)
        image_layout.setAlignment(Qt.AlignCenter)
        image_layout.setSpacing(8)

        self.profile_pic = QLabel("جاري التحميل...")
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.profile_pic.setFixedSize(120, 120)
        self.profile_pic.setObjectName("imagePreview")

        self.machine_title_label = QLabel("---")
        self.machine_title_label.setObjectName("machineTitle")
        self.machine_title_label.setAlignment(Qt.AlignCenter)

        image_layout.addWidget(self.profile_pic)
        image_layout.addWidget(self.machine_title_label)

        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(15)

        details_grid = QGridLayout()
        details_grid.setHorizontalSpacing(20)
        details_grid.setVerticalSpacing(10)

        self.status_label = QLabel("الحالة:")
        self.status_value = QLabel("🔴 متوقف")
        self.status_value.setObjectName("statusLabel")

        self.maintenance_label = QLabel("آخر صيانة:")
        self.maintenance_value = QLabel("2025/11/01")

        details_grid.addWidget(self.status_label, 0, 0, Qt.AlignRight)
        details_grid.addWidget(self.status_value, 0, 1, Qt.AlignLeft)
        details_grid.addWidget(self.maintenance_label, 1, 0, Qt.AlignRight)
        details_grid.addWidget(self.maintenance_value, 1, 1, Qt.AlignLeft)

        details_layout.addLayout(details_grid)
        details_layout.addStretch()

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_add_component = QPushButton("➕ إضافة مكون")
        self.btn_add_component.setObjectName("primaryButton")
        self.btn_add_component.clicked.connect(self.handle_add_component)

        self.btn_repair_history = QPushButton("⚙️ سجل الصيانة")
        self.btn_repair_history.setObjectName("secondaryButton")
        self.btn_repair_history.clicked.connect(self.handle_show_repair_history)

        self.btn_delete_machine = QPushButton("🗑️ حذف الآلة")
        self.btn_delete_machine.setObjectName("dangerButton")
        self.btn_delete_machine.clicked.connect(self.handle_delete_machine)

        actions_layout.addWidget(self.btn_add_component)
        actions_layout.addWidget(self.btn_repair_history)
        actions_layout.addWidget(self.btn_delete_machine)
        actions_layout.addStretch()

        details_layout.addLayout(actions_layout)

        layout.addWidget(image_frame)
        layout.addWidget(details_frame, 1)

        return section

    def create_components_section(self):
        section = QFrame()
        section.setObjectName("card")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        components_header = QLabel("مكونات الآلة")
        components_header.setObjectName("sectionHeader")
        layout.addWidget(components_header)
        self.table = self.create_component_table()
        layout.addWidget(self.table, 1)
        return section

    def create_component_table(self):
        """Creates the QTableWidget for components."""
        table = QTableWidget()
        table.setColumnCount(3)
        headers = ["كود المكون", "اسم المكون", "إجراء"]
        table.setHorizontalHeaderLabels(headers)

        table.verticalHeader().setMinimumSectionSize(65)
        table.verticalHeader().setDefaultSectionSize(65)

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        table.horizontalHeader().resizeSection(2, 120)

        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        return table

    def create_pagination_controls(self):
        # ... (implementation remains the same)
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(0, 10, 0, 0)
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل المكونات")
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.next_button.clicked.connect(self.handle_next_page)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        return pagination_layout

    # --- Logic Methods (Modified/New) ---

    # In MachineProfileUI class
    @pyqtSlot()
    def handle_add_component(self):
        """Opens the AddComponentDialog."""
        if self.machine_id is None:
            QMessageBox.warning(self, "خطأ", "يجب تحميل ملف الآلة أولاً.")
            return

        dialog = AddComponentDialog(self.machine_id, self)

        # 🌟 KEY CHANGE: Connect the dialog's request signal to a new handler that takes the dialog instance.
        dialog.submit_request.connect(
            lambda method, url, payload: self._start_api_fetch_for_dialog(method, url, payload, dialog)
        )

        if dialog.exec_() == QDialog.Accepted:
            self.handle_show_components()

    # In MachineProfileUI class
    @pyqtSlot(str, str, dict, QDialog)
    def _start_api_fetch_for_dialog(self, method, url, payload, dialog: AddComponentDialog):
        """
        Starts an API fetch specifically for the dialog submission, connecting results
        directly back to the provided dialog instance.
        """
        self._set_loading(True)

        # Create the worker and thread as before
        self.api_thread = QThread()
        self.api_worker = ApiWorker(method, url, payload=payload, response_type="json")
        self.api_worker.moveToThread(self.api_thread)
        self.api_thread.started.connect(self.api_worker.run)

        # 🌟 KEY CHANGE: Connect success/error signals to the received 'dialog' object
        self.api_worker.success.connect(dialog.handle_submission_success)
        self.api_worker.error.connect(dialog.handle_submission_error)

        # Disconnect and clean up the thread when finished
        self.api_worker.finished.connect(self.api_thread.quit)
        self.api_worker.finished.connect(lambda: self._set_loading(False))
        self.api_thread.start()

    def update_data(self, machine_data, fetch_pic=True):
        # ... (implementation remains the same)
        data = machine_data.get("data", {})
        self.machine_id = data.get("id")
        self.machine_name = data.get("name", "")
        self.machine_status = data.get("status", "")
        self.last_repair_date = data.get("last_repair_date", "")

        self.name_label.setText(f"ملف الآلة: {self.machine_name}")
        self.machine_title_label.setText(self.machine_name)
        self.status_value.setText(self.machine_status)
        self.maintenance_value.setText(self.last_repair_date)

        self.component_list_url = (
            f"{BACKEND_BASE_URL}/machines/machine-components/?machine_id={self.machine_id}"
        )
        if fetch_pic:
            pic_url = data.get("image")
            if pic_url:
                self.fetch_image(pic_url)
            else:
                self.profile_pic.setText("No Image")

        self.table.setRowCount(0)
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.update_pagination_controls()
        self.handle_show_components()

    def fetch_image(self, url):
        self.image_thread = QThread()
        self.image_worker = ApiWorker("GET", url, response_type="image")
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_worker.image_success.connect(self.set_image)
        self.image_worker.error.connect(lambda msg: self.profile_pic.setText("فشل تحميل الصورة"))
        self.image_worker.finished.connect(self.image_thread.quit)
        self.image_thread.start()

    def set_image(self, pixmap):
        self.profile_pic.setPixmap(
            pixmap.scaled(self.profile_pic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def handle_show_components(self):
        if self.component_list_url:
            self._start_api_fetch(self.component_list_url, self.handle_component_response)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_api_fetch(self.next_page_url, self.handle_component_response)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_api_fetch(self.prev_page_url, self.handle_component_response)

    def handle_component_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_component_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_component_table(self, components):
        self.table.setRowCount(0)
        for component in components:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            component_id = component.get("id")
            id_item = QTableWidgetItem(str(component_id))
            id_item.setData(Qt.UserRole, component_id)
            name_item = QTableWidgetItem(component.get("name", ""))
            btn_delete = QPushButton("🗑️ حذف")
            btn_delete.setObjectName("dangerButton")
            btn_delete.clicked.connect(lambda _, c_id=component_id: self.handle_delete_component(c_id))
            self.table.setItem(row_pos, 0, id_item)
            self.table.setItem(row_pos, 1, name_item)
            self.table.setCellWidget(row_pos, 2, btn_delete)
            id_item.setTextAlignment(Qt.AlignCenter)
            name_item.setTextAlignment(Qt.AlignCenter)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي المكونات: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد مكونات")

    def handle_show_repair_history(self):
        if self.machine_id is None:
            QMessageBox.warning(self, "خطأ", "يجب تحميل ملف الآلة أولاً.")
            return

        dialog = RepairHistoryDialog(self.machine_id, self)
        dialog.exec_()

    def handle_delete_machine(self):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف الآلة: {self.machine_name}؟ هذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            url = f"{BACKEND_BASE_URL}/machines/machine/"
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")
            payload = {"machine_id": self.machine_id, "username": username}
            self._start_api_fetch(
                url, on_success=self.on_delete_machine_success, method="DELETE", payload=payload
            )

    def on_delete_machine_success(self, _):
        QMessageBox.information(self, "نجاح", "تم حذف الآلة بنجاح.")
        self.back_to_list_requested.emit()

    def handle_delete_component(self, component_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا المكون؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            payload = {"machine_component_id": component_id}
            url = f"{BACKEND_BASE_URL}/machines/machine-components/"
            self._start_api_fetch(
                url, on_success=self.on_delete_component_success, method="DELETE", payload=payload
            )

    def on_delete_component_success(self, _):
        QMessageBox.information(self, "نجاح", "تم حذف المكون بنجاح.")
        self.handle_show_components()

    def _start_api_fetch(self, url, on_success, method="GET", payload=None):
        """Standard API fetch for table loading and simple actions (not dialogs)."""
        self._set_loading(True)
        self.api_thread = QThread()
        self.api_worker = ApiWorker(method, url, payload=payload, response_type="json")
        self.api_worker.moveToThread(self.api_thread)
        self.api_thread.started.connect(self.api_worker.run)
        self.api_worker.success.connect(on_success)
        self.api_worker.error.connect(self.show_error_message)
        self.api_worker.finished.connect(self.api_thread.quit)
        self.api_worker.finished.connect(lambda: self._set_loading(False))
        self.api_thread.start()

    def _set_loading(self, is_loading):
        self.btn_add_component.setDisabled(is_loading)
        self.btn_repair_history.setDisabled(is_loading)
        self.btn_delete_machine.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)
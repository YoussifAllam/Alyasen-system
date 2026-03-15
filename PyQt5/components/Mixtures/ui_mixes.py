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
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from urllib.parse import urlencode
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .add_mixture_materials_dialog import AddMixtureMaterialsDialog
from .finalize_mixture_costs_dialog import FinalizeMixtureCostsDialog


class MixtureApiWorker(QObject):
    """Worker for handling GET, POST, and PATCH requests for mixtures."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload

    @pyqtSlot()
    def run(self):
        try:
            response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                self.success.emit(response.json())
            else:
                try:
                    error_data = response.json()
                    if "name" in error_data and isinstance(error_data["name"], list):
                        error_msg = error_data["name"][0]
                    elif "error" in error_data:
                        error_msg = error_data["error"]
                    else:
                        error_msg = f"خطأ من الخادم: {response.status_code}"
                    self.error.emit(error_msg)
                except Exception:
                    self.error.emit("استجابة غير متوقعة من الخادم.")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class MixesUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # --- Left Panel: Add/Update Mixture ---
        left_panel = self.create_form_panel()
        main_layout.addWidget(left_panel, 1)

        # --- Right Panel: Table and Search ---
        right_panel = self.create_table_panel()
        main_layout.addWidget(right_panel, 2)

        # Initialize pagination state
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

    def create_form_panel(self):
        """Creates the left panel for adding and updating mixture names."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("إدارة الخلطات")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة وتعديل أسماء الخلطات.")
        subheader.setObjectName("mainSubheader")
        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("إضافة / تعديل خلطة")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(placeholderText="اسم الخلطة")
        button_layout = QHBoxLayout()
        self.btn_add = QPushButton("إضافة")
        self.btn_add.setObjectName("primaryButton")
        self.btn_update_name = QPushButton("تعديل الاسم")

        self.btn_add.clicked.connect(self.handle_add)
        self.btn_update_name.clicked.connect(self.handle_update_name)

        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_update_name)

        form_layout.addWidget(self.name_input)
        form_layout.addLayout(button_layout)
        layout.addWidget(form_groupbox)
        return container

    def create_table_panel(self):
        """Creates the right panel with the table and action buttons."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="ابحث باسم الخلطة...")
        self.btn_search = QPushButton("بحث")
        self.btn_view_all = QPushButton("عرض الكل")
        self.btn_show_details = QPushButton("عرض تفاصيل الخلطة")
        self.btn_show_details.setEnabled(False)

        actions_layout.addWidget(self.search_input, 1)
        actions_layout.addWidget(self.btn_search)
        actions_layout.addWidget(self.btn_view_all)
        actions_layout.addWidget(self.btn_show_details)
        layout.addLayout(actions_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        headers = ["الاسم", "تكلفة الخامات", "تكلفة التصنيع", "الربح", "سعر البيع", "تاريخ بدئ الصنع"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(lambda: self.btn_show_details.setEnabled(True))

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")

        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)

        layout.addWidget(self.table, 1)
        layout.addLayout(pagination_layout)

        self.btn_view_all.clicked.connect(self.handle_view_all)
        self.btn_search.clicked.connect(self.handle_search)
        self.btn_show_details.clicked.connect(self.handle_show_details)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

        return container

    def handle_add(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم للخلطة.")
            return
        payload = {"name": name}
        url = f"{BACKEND_BASE_URL}/mixtures/mixtures/"
        self._start_api_request("POST", url, payload, on_success=self.on_add_success)

    def on_add_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تمت إضافة الخلطة بنجاح.")
        self.name_input.clear()
        self.handle_view_all()

    def handle_update_name(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد خلطة من الجدول لتعديلها.")
            return

        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال الاسم الجديد للخلطة.")
            return

        mixture_id = self.table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if not mixture_id:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف الخلطة المحددة.")
            return

        payload = {"id": mixture_id, "name": new_name}
        url = f"{BACKEND_BASE_URL}/mixtures/mixtures/"
        self._start_api_request("PATCH", url, payload, on_success=self.on_update_success)

    def on_update_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم تعديل اسم الخلطة بنجاح.")
        self.name_input.clear()
        self.handle_view_all()

    def handle_show_details(self):
        """Starts the multi-step dialog process for adding materials and costs."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        mixture_name_item = self.table.item(selected_rows[0].row(), 0)
        if not mixture_name_item:
            return

        mixture_name = mixture_name_item.text()
        mixture_id = mixture_name_item.data(Qt.UserRole)

        if mixture_id is None:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف الخلطة.")
            return

        # Step 1: Add Materials
        materials_dialog = AddMixtureMaterialsDialog(mixture_id, mixture_name, self)
        if materials_dialog.exec_() == QDialog.Accepted:
            # Step 2: Finalize Costs
            costs_dialog = FinalizeMixtureCostsDialog(mixture_id, mixture_name, self)
            if costs_dialog.exec_() == QDialog.Accepted:
                cost_data = costs_dialog.get_costs()

                # --- FINAL API CALL to save the costs ---
                payload = {
                    "mixture_id": mixture_id,
                    "profit": cost_data.get("profit"),
                    "manufacturing_cost": cost_data.get("manufacturing_cost"),
                }
                url = f"{BACKEND_BASE_URL}/mixtures/mixture_info/"
                self._start_api_request("PATCH", url, payload, on_success=self.on_finalize_success)

    def on_finalize_success(self, response_data):
        """Called after the final costs are saved."""
        QMessageBox.information(self, "نجاح", "تم حفظ بيانات وتكاليف الخلطة بنجاح.")
        self.handle_view_all()  # Refresh the main table

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/mixtures/mixtures/"
        self._start_api_request("GET", url, on_success=self.handle_api_response)

    def handle_search(self):
        name = self.search_input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم الخلطة للبحث.")
            return
        params = urlencode({"name": name})
        url = f"{BACKEND_BASE_URL}/mixtures/mixtures/?{params}"
        self._start_api_request("GET", url, on_success=self.handle_api_response)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_api_request("GET", self.next_page_url, on_success=self.handle_api_response)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_api_request("GET", self.prev_page_url, on_success=self.handle_api_response)

    def _start_api_request(self, method, url, payload=None, on_success=None):
        self._set_loading(True)
        self.thread = QThread()
        self.worker = MixtureApiWorker(method, url, payload)
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

    def populate_table(self, mixtures):
        self.table.setRowCount(0)
        for mixture in mixtures:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            name_item = QTableWidgetItem(mixture.get("name", ""))
            name_item.setData(Qt.UserRole, mixture.get("id"))  # Store ID

            items = [
                name_item,
                QTableWidgetItem(f"{mixture.get('materials_used_cost', 0):,.2f}"),
                QTableWidgetItem(f"{mixture.get('manufacturing_cost', 0):,.2f}"),
                QTableWidgetItem(f"{mixture.get('profit', 0):,.2f}"),
                QTableWidgetItem(f"{mixture.get('selling_price', 0):,.2f}"),
                QTableWidgetItem(mixture.get("created_date", "")),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي الخلطات: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def _set_loading(self, is_loading):
        buttons = [
            self.btn_add,
            self.btn_update_name,
            self.btn_search,
            self.btn_view_all,
            self.next_button,
            self.prev_button,
            self.btn_show_details,
        ]
        for button in buttons:
            button.setDisabled(is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

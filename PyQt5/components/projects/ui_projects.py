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
    QComboBox,
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtGui import QBrush, QColor
from requests import request, exceptions
from urllib.parse import urlencode

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class ProjectApiWorker(QObject):
    """Worker for handling API requests for projects."""

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


class ProjectsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("FactorySystem")
        self.contract_files_paths = []
        self.suppliers_list = []
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0

        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        layout_h = QHBoxLayout()
        left_panel = self.create_form_panel()
        right_panel = self.create_table_panel()

        layout_h.addWidget(left_panel, 1)
        layout_h.addWidget(right_panel, 2)

        main_layout.addLayout(layout_h)

    def create_form_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header = QLabel("إدارة المشاريع")
        header.setObjectName("mainHeader")
        subheader = QLabel("إضافة مشروع جديد أو البحث عن مشروع.")
        subheader.setObjectName("mainSubheader")

        layout.addWidget(header)
        layout.addWidget(subheader)

        form_groupbox = QGroupBox("إضافة مشروع جديد")
        form_layout = QVBoxLayout(form_groupbox)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit(placeholderText="اسم المشروع")
        self.cost_input = QLineEdit(placeholderText="تكلفة المشروع")

        self.type_combobox = QComboBox()
        self.type_combobox.addItems(["تأجير", "بيع", "صناعي"])
        self.type_combobox.currentTextChanged.connect(self.on_project_type_changed)

        self.supplier_combobox = QComboBox()
        self.supplier_combobox.setPlaceholderText("اختر المورد")
        self.supplier_combobox.hide()  # Hidden by default since first item is rent, wait, rent shows it.

        self.contracts_label = QLabel("لم يتم اختيار عقود")
        self.contracts_label.setAlignment(Qt.AlignCenter)
        self.contracts_label.setMinimumHeight(40)

        btn_choose_contracts = QPushButton("اختيار عقود (صور/ملفات)")
        btn_choose_contracts.clicked.connect(self.choose_contracts)

        form_layout.addWidget(QLabel("اسم المشروع:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("نوع المشروع:"))
        form_layout.addWidget(self.type_combobox)
        form_layout.addWidget(QLabel("تكلفة المشروع:"))
        form_layout.addWidget(self.cost_input)

        self.supplier_label = QLabel("المورد:")
        self.supplier_label.hide()
        form_layout.addWidget(self.supplier_label)
        form_layout.addWidget(self.supplier_combobox)

        form_layout.addWidget(self.contracts_label)
        form_layout.addWidget(btn_choose_contracts)

        self.btn_add_project = QPushButton("إضافة المشروع")
        self.btn_add_project.setObjectName("primaryButton")
        self.btn_add_project.clicked.connect(self.handle_add_project)
        form_layout.addWidget(self.btn_add_project)

        layout.addWidget(form_groupbox)

        # Initial call to setup visibility
        self.on_project_type_changed(self.type_combobox.currentText())

        return container

    def create_table_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="ابحث باسم المشروع...")
        self.search_button = QPushButton("بحث")
        self.change_status_button = QPushButton("تغير حالة المشروع")
        self.show_project_attachments_button = QPushButton("عرض مرفقات المشروع")
        self.search_button.clicked.connect(self.handle_search)
        self.change_status_button.clicked.connect(self.handle_change_status)
        self.show_project_attachments_button.clicked.connect(
            self.handle_show_attachments
        )

        actions_layout.addWidget(self.search_input, 1)
        actions_layout.addWidget(self.search_button)
        actions_layout.addWidget(self.change_status_button)
        actions_layout.addWidget(self.show_project_attachments_button)

        self.view_all_button = QPushButton("عرض الكل")
        self.view_all_button.clicked.connect(self.handle_view_all)
        actions_layout.addWidget(self.view_all_button)

        layout.addLayout(actions_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        headers = [
            "كود",
            "اسم المشروع",
            "النوع",
            "الحالة",
            "تاريخ الإنشاء",
        ]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)

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

    def on_project_type_changed(self, text):
        if text in ["تأجير", "بيع"]:
            self.supplier_label.show()
            self.supplier_combobox.show()
        else:
            self.supplier_label.hide()
            self.supplier_combobox.hide()

    def choose_contracts(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "اختر العقود", "", "All Files (*)"
        )
        if file_paths:
            self.contract_files_paths = file_paths
            self.contracts_label.setText(
                f"تم اختيار {len(self.contract_files_paths)} ملفات/صور"
            )

    def load_suppliers(self):
        url = f"{BACKEND_BASE_URL}/suppliers/suppliers/"
        self.supplier_thread = QThread()
        self.supplier_worker = ProjectApiWorker("GET", url)
        self.supplier_worker.moveToThread(self.supplier_thread)
        self.supplier_thread.started.connect(self.supplier_worker.run)
        self.supplier_worker.success.connect(self.on_suppliers_loaded)
        self.supplier_worker.finished.connect(self.supplier_thread.quit)
        self.supplier_thread.start()

    def on_suppliers_loaded(self, response_data):
        self.suppliers_list = response_data.get("data", {}).get("results", [])
        self.supplier_combobox.clear()
        for supplier in self.suppliers_list:
            self.supplier_combobox.addItem(supplier.get("name"), supplier.get("id"))

    def handle_add_project(self):
        name = self.name_input.text().strip()
        pt_text = self.type_combobox.currentText()
        project_type = (
            "rent"
            if pt_text == "تأجير"
            else "selling" if pt_text == "بيع" else "industrial"
        )
        cost = float(self.cost_input.text().strip())
        project_status = "active"

        if not name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم المشروع.")
            return

        payload = {
            "name": name,
            "project_type": project_type,
            "project_status": project_status,
            "cost": cost,
        }

        if project_type in ["rent", "selling"]:
            supplier_id = self.supplier_combobox.currentData()
            if not supplier_id:
                QMessageBox.warning(self, "خطأ", "الرجاء اختيار المورد.")
                return
            payload["supplier"] = str(supplier_id)

        username = self.settings.value("user_name", "unknown_user")
        payload["username"] = username

        url = f"{BACKEND_BASE_URL}/projects/"
        self._set_loading(True)
        self.btn_add_project.setText("جاري التحميل...")

        self.post_thread = QThread()
        self.post_worker = ProjectApiWorker("POST", url, payload, None)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)

        self.post_worker.success.connect(self.on_project_added)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_thread.start()

    def on_project_added(self, response_data):
        p_id = response_data.get("id")

        if not p_id:
            self.show_error_message("حدث خطأ غير متوقع: لم يتم إرجاع كود المشروع.")
            return

        if self.contract_files_paths:
            self._upload_contracts(p_id)
        else:
            self.finalize_add_project()

    def _upload_contracts(self, p_id):
        payload = {"project_id": str(p_id)}
        files = []
        for path in self.contract_files_paths:
            files.append(("attachments", open(path, "rb")))

        url = f"{BACKEND_BASE_URL}/projects/contracts/"

        self.att_thread = QThread()
        self.att_worker = ProjectApiWorker("POST", url, payload, files)
        self.att_worker.moveToThread(self.att_thread)
        self.att_thread.started.connect(self.att_worker.run)

        self.att_worker.success.connect(lambda _: self.finalize_add_project())
        self.att_worker.error.connect(self.show_error_message)
        self.att_worker.finished.connect(self.att_thread.quit)
        self.att_thread.start()

    def finalize_add_project(self):
        self._set_loading(False)
        self.btn_add_project.setText("إضافة المشروع")
        QMessageBox.information(self, "نجاح", "تمت إضافة المشروع بنجاح.")
        self.name_input.clear()
        self.cost_input.clear()
        self.contract_files_paths = []
        self.contracts_label.setText("لم يتم اختيار عقود")
        self.handle_view_all()

    def handle_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.handle_view_all()
            return

        params = urlencode({"q": query})
        url = f"{BACKEND_BASE_URL}/projects/?{params}"
        self._start_fetch_request(url)

    def handle_show_attachments(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")
            return

        selected_row = selected_rows[0].row()
        p_id_item = self.table.item(selected_row, 0)

        if p_id_item:
            p_id = p_id_item.text().strip()
            from .project_attachments_dialog import ProjectAttachmentsDialog

            dialog = ProjectAttachmentsDialog(p_id, parent=self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على كود المشروع المختار.")

    def handle_change_status(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")
            return

        selected_row = selected_rows[0].row()
        p_id_item = self.table.item(selected_row, 0)

        if p_id_item:
            p_id = p_id_item.text().strip()

            # Optional confirmation alert
            reply = QMessageBox.question(
                self,
                "تأكيد",
                "هل أنت متأكد من تغيير حالة هذا المشروع؟",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

            url = f"{BACKEND_BASE_URL}/projects/"
            payload = {"project_id": p_id}
            self._set_loading(True)

            self.patch_thread = QThread()
            self.patch_worker = ProjectApiWorker("PATCH", url, payload=payload)
            self.patch_worker.moveToThread(self.patch_thread)
            self.patch_thread.started.connect(self.patch_worker.run)

            self.patch_worker.success.connect(self.on_status_changed)
            self.patch_worker.error.connect(self.show_error_message)
            self.patch_worker.finished.connect(self.patch_thread.quit)
            self.patch_thread.start()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على كود المشروع المختار.")

    def on_status_changed(self, response_data):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تم تغيير حالة المشروع بنجاح.")
        self.handle_view_all()

    def on_add_success(self):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تمت إضافة المشروع بنجاح.")
        self.name_input.clear()
        self.contract_files_paths = []
        self.contracts_label.setText("لم يتم اختيار عقود")
        self.handle_view_all()

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/projects/"
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
        self.worker = ProjectApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        success_handler = on_success if on_success else self.handle_api_response
        self.worker.success.connect(success_handler)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def _start_post_request(self, url, payload, files):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = ProjectApiWorker("POST", url, payload, files)
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

    def populate_table(self, projects):
        self.table.setRowCount(0)
        for project in projects:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            status = project.get("project_status", "")
            status_text = (
                "نشط"
                if status == "active"
                else "غير نشط" if status == "inactive" else status
            )

            status_item = QTableWidgetItem(status_text)
            if status == "active":
                status_item.setForeground(QBrush(QColor("#10b981")))
            elif status == "inactive":
                status_item.setForeground(QBrush(QColor("#ef4444")))

            items = [
                QTableWidgetItem(str(project.get("id", ""))),
                QTableWidgetItem(project.get("name", "")),
                QTableWidgetItem(project.get("project_type", "")),
                status_item,
                QTableWidgetItem(project.get("created_date", "")),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي المشاريع: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد نتائج")

    def _set_loading(self, is_loading):
        self.view_all_button.setEnabled(not is_loading)
        self.search_button.setEnabled(not is_loading)
        self.next_button.setEnabled(not is_loading)
        self.prev_button.setEnabled(not is_loading)
        self.btn_add_project.setEnabled(not is_loading)
        if is_loading:
            self.page_info_label.setText("جاري التحميل...")

    def show_error_message(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

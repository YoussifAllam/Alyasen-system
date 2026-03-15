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
    QStackedWidget,
    QDialog,
    QMessageBox,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
from urllib.parse import urlencode
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL

# Import the UI components
from .inventory_log import MaterialsLogUI
from .edit_material_dialog import EditMaterialDialog
from .update_material_dialog import UpdateMaterialDialog
from .fill_material_dialog import FillMaterialDialog


class MaterialApiWorker(QObject):
    """Generic worker for handling GET, POST, DELETE requests for materials."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method: str, url: str, payload: dict = None):
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
            elif self.method == "DELETE" and response.status_code == 204:
                self.success.emit({"status": "success"})
            else:
                try:
                    error_data = response.json()
                    if "non_field_errors" in error_data:
                        detail = ", ".join(error_data["non_field_errors"])
                    else:
                        # Attempt to extract error detail
                        detail = next(iter(error_data.values()), f"رمز الحالة: {response.status_code}")
                        if isinstance(detail, list):
                            detail = detail[0]
                    self.error.emit(str(detail))
                except Exception:
                    self.error.emit(f"خطأ من الخادم: {response.status_code}")

        except exceptions.RequestException as e:  # noqa
            self.error.emit("فشل الاتصال بالخادم. يرجى التحقق من اتصالك بالإنترنت.")
        finally:
            self.finished.emit()


class MaterialsInventoryUI(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        self.inventory_page = self.create_inventory_page()
        self.log_page = MaterialsLogUI()
        self.stacked_widget.addWidget(self.inventory_page)
        self.stacked_widget.addWidget(self.log_page)
        self.log_page.back_to_inventory_requested.connect(self.show_inventory_page)

    def create_inventory_page(self):
        """Creates and returns the main inventory management widget."""
        inventory_widget = QWidget()
        inventory_widget.setObjectName("mainContent")
        layout = QVBoxLayout(inventory_widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        header = QLabel("مخزن الخامات")
        header.setObjectName("mainHeader")
        subheader = QLabel("إدارة مخزون الخامات والمواد الأولية.")
        subheader.setObjectName("mainSubheader")
        layout.addWidget(header)
        layout.addWidget(subheader)
        top_layout = QHBoxLayout()
        form_groupbox = QGroupBox("بيانات الخامة")
        form_layout = QHBoxLayout(form_groupbox)
        form_layout.setSpacing(20)

        self.name_input = QLineEdit(placeholderText="اسم الخامة")
        self.quantity_input = QLineEdit(placeholderText="كمية بالوحدة")  # Updated placeholder
        self.unit_input = QLineEdit(placeholderText="الوحدة (مثال: كيلو، كرتونة)")  # New unit input
        self.buy_price_per_unit = QLineEdit(placeholderText=" سعر شراء الوحدة ")

        # Removed price inputs as requested
        # self.price_input = QLineEdit(placeholderText="سعر شراء الكيلو")
        # self.sell_price_input = QLineEdit(placeholderText="سعر بيع الكيلو")

        form_layout.addWidget(self.name_input, 1)
        form_layout.addWidget(self.quantity_input)
        form_layout.addWidget(self.buy_price_per_unit)
        form_layout.addWidget(self.unit_input)  # Added unit input

        top_layout.addWidget(form_groupbox)
        layout.addLayout(top_layout)

        actions_layout = QHBoxLayout()
        self.btn_add = QPushButton("اضافة خامة جديدة")
        self.btn_add.setObjectName("primaryButton")
        self.btn_edit = QPushButton("أضافة كمية للخامة")
        self.btn_edit.hide()
        self.btn_fill = QPushButton("تعبئة")
        self.btn_delete = QPushButton("حذف")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_search = QPushButton("بحث")
        self.btn_view_all = QPushButton("عرض الكل")
        self.btn_update = QPushButton("تعديل البيانات")
        btn_show_log = QPushButton("عرض سجل المخزن")
        btn_show_log.clicked.connect(self.show_log_page)

        actions_layout.addWidget(self.btn_add)
        actions_layout.addWidget(self.btn_edit)
        actions_layout.addWidget(self.btn_fill)
        actions_layout.addWidget(self.btn_update)
        actions_layout.addWidget(self.btn_search)
        actions_layout.addWidget(self.btn_view_all)
        actions_layout.addWidget(btn_show_log)
        actions_layout.addWidget(self.btn_delete)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            [
                "رقم الصنف",
                "اسم الصنف",
                "الكمية بالوحدة",
                "الوحدة",
                "سعر الشراء بالوحدة",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        layout.addWidget(self.table)
        layout.addLayout(pagination_layout)

        self.btn_add.clicked.connect(self.handle_add)
        self.btn_view_all.clicked.connect(self.handle_view_all)
        self.btn_delete.clicked.connect(self.handle_delete)
        self.btn_search.clicked.connect(self.handle_search)
        self.btn_edit.clicked.connect(self.open_edit_dialog)
        self.btn_fill.clicked.connect(self.open_fill_dialog)
        self.btn_update.clicked.connect(self.open_update_dialog)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

        return inventory_widget

    def open_fill_dialog(self):
        """Creates and shows the fill material dialog."""
        dialog = FillMaterialDialog(self)
        dialog.exec_()

    def open_edit_dialog(self):
        """Creates and shows the edit material dialog."""
        dialog = EditMaterialDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            material = dialog.material_combo.currentText()
            quantity = dialog.quantity_input.text()
            driver = dialog.driver_name_input.text()
            car_plate = dialog.car_plate_input.text()
            print(
                f"Submitting edit for: {material}, Quantity: {quantity}, Driver: {driver}, Car: {car_plate}"
            )

    def open_update_dialog(self):
        """Opens the dialog to update a material's name."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد الخامة التي تريد تعديلها.")
            return
        selected_row = selected_rows[0].row()
        old_name = self.table.item(selected_row, 1).text()
        # Old prices are not used in the dialog, passing 0
        old_price = "0"
        old_buy_price = self.table.item(selected_row, 4).text()
        dialog = UpdateMaterialDialog(old_name, old_price, old_buy_price, self)
        if dialog.exec_() == QDialog.Accepted:
            # The dialog handles the update internally.
            # We just need to refresh the table to show changes.
            self.handle_view_all()

    def show_inventory_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_log_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def _start_update_request(self, url, payload):
        """Starts a worker thread to send a PUT request."""
        self._set_loading(True)
        self.update_thread = QThread()
        self.update_worker = MaterialApiWorker("PATCH", url, payload)
        self.update_worker.moveToThread(self.update_thread)
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.success.connect(self.on_update_success)
        self.update_worker.error.connect(self.show_error_message)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_thread.start()

    def on_update_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم تعديل بيانات الخامة بنجاح.")
        self.handle_view_all()

    def handle_add(self):
        material_name = self.name_input.text().strip()
        quantity_str = self.quantity_input.text().strip()
        unit_str = self.unit_input.text().strip()  # Get unit
        buy_price_per_unit_str = self.buy_price_per_unit.text().strip()

        if not all([material_name, quantity_str, unit_str]):
            QMessageBox.warning(self, "خطأ", "الرجاء ملء جميع الحقول (الاسم، الكمية، الوحدة).")
            return

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                QMessageBox.warning(self, "خطأ في الإدخال", "يجب أن تكون الكمية رقمًا موجبًا وأكبر من صفر.")
                return
        except ValueError:
            QMessageBox.warning(self, "خطأ في الإدخال", "الرجاء إدخال رقم صالح للكمية.")
            return

        try:
            buy_price_per_unit = float(buy_price_per_unit_str)
            if buy_price_per_unit <= 0:
                QMessageBox.warning(self, "خطأ في الإدخال", "يجب أن يكون السعر رقمًا موجبًا وأكبر من صفر.")
                return
        except ValueError:
            QMessageBox.warning(self, "خطأ في الإدخال", "الرجاء إدخال رقم صالح للسعر.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {
            "material_name": material_name,
            "quantity_in_unit": quantity,  # Changed from quantity_in_kilo
            "unit": unit_str,
            "username": username,
            "buy_price_per_unit": buy_price_per_unit_str,
        }

        url = f"{BACKEND_BASE_URL}/material-warehouse/materials/"
        self._start_post_request(url, payload)

    def handle_delete(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد الخامة التي تريد حذفها.")
            return
        selected_row = selected_rows[0].row()
        material_name = self.table.item(selected_row, 1).text()
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من أنك تريد حذف '{material_name}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")
            url = f"{BACKEND_BASE_URL}/material-warehouse/materials/"
            payload = {"material_name": material_name, "username": username}
            self._start_delete_request(url, payload)

    def handle_search(self):
        material_name = self.name_input.text().strip()
        if not material_name:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم الخامة للبحث.")
            return
        base_url = f"{BACKEND_BASE_URL}/material-warehouse/filter/"
        params = {"material_name": material_name}
        url = f"{base_url}?{urlencode(params)}"
        self._start_fetch_request(url)

    def handle_view_all(self):
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials/"
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
        self.fetch_worker = MaterialApiWorker("GET", url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.success.connect(self.handle_fetch_success)
        self.fetch_worker.error.connect(self.show_error_message)
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.start()

    def _start_post_request(self, url, payload):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = MaterialApiWorker("POST", url, payload)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_add_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_worker.finished.connect(self.post_worker.deleteLater)
        self.post_thread.finished.connect(self.post_thread.deleteLater)
        self.post_thread.start()

    def _start_delete_request(self, url, payload):
        self._set_loading(True)
        self.delete_thread = QThread()
        self.delete_worker = MaterialApiWorker("DELETE", url, payload)
        self.delete_worker.moveToThread(self.delete_thread)
        self.delete_thread.started.connect(self.delete_worker.run)
        self.delete_worker.success.connect(self.on_delete_success)
        self.delete_worker.error.connect(self.show_error_message)
        self.delete_worker.finished.connect(self.delete_thread.quit)
        self.delete_worker.finished.connect(self.delete_worker.deleteLater)
        self.delete_thread.finished.connect(self.delete_thread.deleteLater)
        self.delete_thread.start()

    def handle_fetch_success(self, response_data):
        outer_data = response_data.get("data")
        results = []
        if isinstance(outer_data, dict):
            inner_data = outer_data.get("data")
            if isinstance(inner_data, dict):
                results = inner_data.get("results", [])
                self.next_page_url = inner_data.get("next")
                self.prev_page_url = inner_data.get("previous")
                self.total_count = inner_data.get("count", 0)
            elif isinstance(inner_data, list):
                results = inner_data
                self.next_page_url = None
                self.prev_page_url = None
                self.total_count = len(results)
            else:
                results = outer_data.get("results", [])
                self.next_page_url = outer_data.get("next")
                self.prev_page_url = outer_data.get("previous")
                self.total_count = outer_data.get("count", 0)
        elif isinstance(outer_data, list):
            results = outer_data
            self.next_page_url = None
            self.prev_page_url = None
            self.total_count = len(results)

        self.populate_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def on_add_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تمت إضافة الخامة بنجاح.")
        self.name_input.clear()
        self.quantity_input.clear()
        self.unit_input.clear()
        self.handle_view_all()

    def on_delete_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم حذف الخامة بنجاح.")
        self.handle_view_all()

    def populate_table(self, materials):
        self.table.setRowCount(0)
        for material in materials:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(str(material.get("id", ""))),
                QTableWidgetItem(str(material.get("material_name", ""))),
                QTableWidgetItem(str(material.get("quantity_in_unit", ""))),
                QTableWidgetItem(str(material.get("unit", ""))),
                QTableWidgetItem(str(material.get("buy_price_per_unit", ""))),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            if self.next_page_url or self.prev_page_url:
                try:
                    page_size = self.table.rowCount()
                    current_page = self.get_current_page()
                    start_item = (current_page - 1) * page_size + 1
                    end_item = start_item + self.table.rowCount() - 1
                    if end_item > self.total_count:
                        end_item = self.total_count
                    self.page_info_label.setText(f"عرض {start_item}-{end_item} من {self.total_count} سجل")
                except:  # noqa
                    self.page_info_label.setText(f"إجمالي السجلات: {self.total_count}")
            else:
                self.page_info_label.setText(f"تم العثور على {self.total_count} نتيجة")
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

    def _set_loading(self, is_loading):
        self.btn_add.setDisabled(is_loading)
        self.btn_edit.setDisabled(is_loading)
        self.btn_delete.setDisabled(is_loading)
        self.btn_search.setDisabled(is_loading)
        self.btn_view_all.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)

    def show_error_message(self, message):
        self._set_loading(False)
        self.update_pagination_controls()
        QMessageBox.critical(self, "خطأ", message)

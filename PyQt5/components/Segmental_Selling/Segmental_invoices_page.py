from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QTableWidget,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, pyqtSlot
from requests import request, get, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .create_invoice_dialog import CreateSegmentalInvoiceDialog
from .add_mixture_dialog import AddMixtureDialog
from .show_invoice_mixs_dialog import ClientInvoiceMaterialsDialog


class ApiWorker(QObject):
    """Worker for handling API requests."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
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
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                if self.response_type == "json":
                    self.success.emit(response.json())

            else:
                self.error.emit(f"{response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class SegmentalInvoicesUI(QWidget):
    back_to_list_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.client_id = None
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        header_layout = QHBoxLayout()
        self.name_label = QLabel("ملف العميل")
        self.name_label.setObjectName("mainHeader")
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        actions_card = self.create_actions_card()
        top_layout.addWidget(actions_card)
        main_layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        headers = ["رقم الفاتورة", "التاريخ", "الإجمالي", "ملاحظات"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل الفواتير")
        self.prev_button.clicked.connect(self.handle_prev_page)
        self.next_button.clicked.connect(self.handle_next_page)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        main_layout.addWidget(self.table, 1)
        main_layout.addLayout(pagination_layout)

    def create_picture_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        self.profile_pic = QLabel("Loading...")
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.profile_pic.setFixedSize(200, 200)
        layout.addWidget(self.profile_pic)
        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        self.btn_create_invoices = QPushButton("أضافة فاتورة")
        self.btn_create_invoices.setObjectName("primaryButton")
        self.btn_create_invoices.clicked.connect(self.handle_create_invoice_step1)
        self.btn_show_invoices = QPushButton("عرض الفواتير")
        self.btn_show_invoices.clicked.connect(self.handle_show_invoices)
        self.btn_show_invoice_materials_details = QPushButton("عرض تفاصيل منتجات الفاتورة")
        self.btn_show_invoice_materials_details.clicked.connect(self.handle_show_materials_details)
        self.btn_show_invoice_materials_details.setEnabled(False)
        layout.addWidget(self.btn_create_invoices)
        layout.addWidget(self.btn_show_invoices)
        layout.addWidget(self.btn_show_invoice_materials_details)
        layout.addStretch()
        return card

    def handle_create_invoice_step1(self):
        dialog = CreateSegmentalInvoiceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            invoice_num = dialog.get_invoice_number()
            self.handle_create_invoice_step2(invoice_num)

    def handle_create_invoice_step2(self, invoice_num):
        """Step 2: Open the dialog to add mixtures."""
        dialog = AddMixtureDialog(invoice_num, self)
        if dialog.exec_() == QDialog.Accepted:
            pass

    def on_invoice_creation_success(self, updated_client_data):
        """Called after the entire invoice process is complete."""
        QMessageBox.information(self, "نجاح", "تم إنشاء الفاتورة وتسجيل الدفعة بنجاح.")
        self.update_data(updated_client_data, fetch_pic=False)
        self.handle_show_invoices()

    def update_data(self, client_data, fetch_pic=True):
        data = client_data.get("data", {})
        self.client_id = data.get("id")
        self.name_label.setText(f"ملف العميل: {data.get('name', '')}")

        self.table.setRowCount(0)
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.update_pagination_controls()

    def handle_show_invoices(self):
        url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/invoices/"
        self._start_invoice_fetch(url)

    def handle_show_materials_details(self):
        """Opens a dialog to show material details for the selected invoice."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        invoice_num = self.table.item(selected_rows[0].row(), 0).text()
        dialog = ClientInvoiceMaterialsDialog(invoice_num, self)
        dialog.exec_()

    def _start_post_request(self, url, payload):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = ApiWorker("POST", url, payload=payload)
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_payment_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_thread.start()

    def on_payment_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم تسجيل الدفعة بنجاح.")
        if self.client_id:
            url = f"{BACKEND_BASE_URL}/clients/info/?id={self.client_id}"
            self._start_info_fetch_request(url)

    def on_client_info_update(self, client_data):
        self.update_data(client_data, fetch_pic=False)
        self.handle_show_invoices()

    def handle_next_page(self):
        if self.next_page_url:
            self._start_invoice_fetch(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_invoice_fetch(self.prev_page_url)

    def _start_info_fetch_request(self, url):
        self.info_fetch_thread = QThread()
        self.info_fetch_worker = ApiWorker("GET", url, response_type="json")
        self.info_fetch_worker.moveToThread(self.info_fetch_thread)
        self.info_fetch_thread.started.connect(self.info_fetch_worker.run)
        self.info_fetch_worker.success.connect(self.on_client_info_update)
        self.info_fetch_worker.error.connect(self.show_error_message)
        self.info_fetch_worker.finished.connect(self.info_fetch_thread.quit)
        self.info_fetch_thread.start()

    def _start_invoice_fetch(self, url):
        self._set_loading(True)
        self.invoice_thread = QThread()
        self.invoice_worker = ApiWorker("GET", url, response_type="json")
        self.invoice_worker.moveToThread(self.invoice_thread)
        self.invoice_thread.started.connect(self.invoice_worker.run)
        self.invoice_worker.success.connect(self.handle_invoice_response)
        self.invoice_worker.error.connect(self.show_error_message)
        self.invoice_worker.finished.connect(self.invoice_thread.quit)
        self.invoice_thread.start()

    def handle_invoice_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_invoice_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_invoice_table(self, invoices):
        self.table.setRowCount(0)
        for invoice in invoices:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            items = [
                QTableWidgetItem(str(invoice.get("invoice_number", ""))),
                QTableWidgetItem(invoice.get("invoice_date", "")),
                QTableWidgetItem(f"{invoice.get('invoice_total_amount', 0):,.2f}"),
                QTableWidgetItem(f"{invoice.get('notes')}"),
            ]
            for i, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, i, item)

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي الفواتير: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد فواتير")

    def on_selection_changed(self):
        is_selected = bool(self.table.selectionModel().selectedRows())
        self.btn_show_invoice_materials_details.setEnabled(is_selected)

    def _set_loading(self, is_loading):
        self.btn_show_invoices.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

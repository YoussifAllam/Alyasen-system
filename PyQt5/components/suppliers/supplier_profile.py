from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QGridLayout,
    QLineEdit,
    QMessageBox,
    QDialog,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, pyqtSlot, QSettings
from requests import request, get, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .payment_dialog import PaymentDialog
from .invoice_payment_details_dialog import InvoicePaymentDetailsDialog


class ApiWorker(QObject):
    """Generic worker for all API requests on this page."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    text_success = pyqtSignal(str)
    image_success = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(
        self, method, url, payload=None, data=None, files=None, response_type="json"
    ):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.data = data
        self.files = files
        self.response_type = response_type

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                if self.files or self.data:
                    opened_files = {}
                    if self.files:
                        for key, filepath in self.files.items():
                            if filepath:
                                opened_files[key] = open(filepath, "rb")
                    try:
                        response = request(
                            self.method,
                            self.url,
                            data=self.data,
                            files=opened_files if opened_files else None,
                            timeout=15,
                        )

                    finally:
                        for f in opened_files.values():
                            f.close()
                else:
                    response = request(
                        self.method, self.url, json=self.payload, timeout=15
                    )

            if response.status_code in [200, 201]:
                if self.response_type == "json":
                    self.success.emit(response.json())
                elif self.response_type == "text":
                    self.text_success.emit(response.text)
                else:  # Image
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
            else:
                self.error.emit(f"خطأ من الخادم: {response.json()}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class SupplierProfileUI(QWidget):
    back_to_list_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.supplier_id = None
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        header_layout = QHBoxLayout()
        self.name_label = QLabel("ملف المورد")
        self.name_label.setObjectName("mainHeader")
        back_button = QPushButton("العودة للقائمة")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        main_layout.addLayout(header_layout)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        pic_card = self.create_picture_card()
        top_layout.addWidget(pic_card)
        summary_card = self.create_summary_card()
        top_layout.addWidget(summary_card, 1)
        actions_card = self.create_actions_card()
        top_layout.addWidget(actions_card)
        main_layout.addLayout(top_layout)

        # --- Table Setup (11 Columns) ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        headers = ["كود", "اسم المشروع", "الاجمالي", "المدفوع", "المتبقي للمورد"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل المشاريع")
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
        self.profile_pic_label = QLabel("Loading...")
        self.profile_pic_label.setObjectName("profilePicture")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setFixedSize(200, 200)
        layout.addWidget(self.profile_pic_label)
        return card

    def create_summary_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.setSpacing(15)
        self.due_display = QLineEdit(readOnly=True)
        self.payable_display = QLineEdit(readOnly=True)
        self.paid_display = QLineEdit(readOnly=True)
        layout.addWidget(QLabel("اجمالي المستحق:"), 0, 0)
        layout.addWidget(self.due_display, 0, 1)
        layout.addWidget(QLabel("اجمالي المطلوب:"), 1, 0)
        layout.addWidget(self.payable_display, 1, 1)
        layout.addWidget(QLabel("اجمالي المدفوع:"), 2, 0)
        layout.addWidget(self.paid_display, 2, 1)
        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        self.btn_show_invoices = QPushButton("عرض مشاريع المورد")
        self.btn_show_invoices.clicked.connect(self.handle_show_invoices)
        self.btn_show_invoice_payment_details = QPushButton("عرض تفاصيل الدفعات")
        self.btn_show_invoice_payment_details.clicked.connect(
            self.handle_show_payment_details
        )
        self.btn_pay_invoice = QPushButton("تسديد دفعه")
        self.btn_pay_invoice.clicked.connect(self.handle_pay_invoice)
        self.btn_show_contracts = QPushButton("عرض عقود المشروع")
        self.btn_show_contracts.clicked.connect(self.handle_show_attachments)
        self.send_email = QPushButton("ارسال كشف حساب للمورد")
        self.send_email.clicked.connect(self.handle_send_email)
        layout.addWidget(self.btn_show_invoices)
        layout.addWidget(self.btn_show_invoice_payment_details)
        layout.addWidget(self.btn_show_contracts)
        layout.addWidget(self.btn_pay_invoice)
        layout.addWidget(self.send_email)
        layout.addStretch()
        return card

    # ---------------------------------

    def update_data(self, supplier_data, fetch_pic=True):
        data = supplier_data.get("data", {})
        self.supplier_id = data.get("id")
        self.name_label.setText(f"ملف المورد: {data.get('name', '')}")
        self.due_display.setText(f"{data.get('total_amount_due', 0):,.2f} ج.م")
        self.payable_display.setText(f"{data.get('total_amount_payable', 0):,.2f} ج.م")
        self.paid_display.setText(f"{data.get('total_paid_amount', 0):,.2f} ج.م")
        if fetch_pic:
            pic_url = data.get("profile_picture")
            if pic_url:
                self.fetch_image(pic_url)
            else:
                self.profile_pic_label.setText("No Image")
        self.table.setRowCount(0)
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self.update_pagination_controls()

    def fetch_image(self, url):
        self.image_thread = QThread()
        self.image_worker = ApiWorker("GET", url, response_type="image")
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_worker.image_success.connect(self.set_image)
        self.image_worker.error.connect(lambda msg: self.profile_pic_label.setText(msg))
        self.image_worker.finished.connect(self.image_thread.quit)
        self.image_thread.start()

    def set_image(self, pixmap):
        self.profile_pic_label.setPixmap(
            pixmap.scaled(
                self.profile_pic_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

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

    def handle_show_invoices(self):
        if self.supplier_id:
            url = (
                f"{BACKEND_BASE_URL}/suppliers/projects/?supplier_id={self.supplier_id}"
            )
            self._start_invoice_fetch_request(url)

    def handle_show_payment_details(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")
            return

        selected_row = selected_rows[0].row()
        p_id_item = self.table.item(selected_row, 0)

        if p_id_item:
            p_id = p_id_item.text().strip()
            dialog = InvoicePaymentDetailsDialog(self.supplier_id, p_id, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على كود المشروع المختار.")

    def handle_pay_invoice(self):

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")
            return

        selected_row = selected_rows[0].row()
        p_id_item = self.table.item(selected_row, 0)
        if p_id_item:
            p_id = p_id_item.text().strip()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على كود المشروع المختار.")
            return
        dialog = PaymentDialog(p_id, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            amount_str = data.get("payment_amount")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    QMessageBox.warning(
                        self, "خطأ", "يجب أن يكون المبلغ المدفوع رقمًا موجبًا."
                    )
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "خطأ", "الرجاء إدخال مبلغ صحيح.")
                return
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "system")
            form_data = {
                "supplier_id": str(self.supplier_id) if self.supplier_id else "",
                "project_id": str(p_id),
                "payment_amount": amount_str,
                "note": data.get("notes", ""),
                "payment_date": data.get("payment_date", ""),
                "portal_invoice_number": data.get("portal_invoice_number", ""),
                "username": username,
            }
            files = {}
            if data.get("portal_invoice_file"):
                files["portal_invoice_file"] = data.get("portal_invoice_file")
            url = f"{BACKEND_BASE_URL}/suppliers/projects/payment/"
            self._start_post_request(url, data=form_data, files=files)

    def _start_post_request(self, url, payload=None, data=None, files=None):
        self._set_loading(True)
        self.post_thread = QThread()
        self.post_worker = ApiWorker(
            "POST", url, payload=payload, data=data, files=files
        )
        self.post_worker.moveToThread(self.post_thread)
        self.post_thread.started.connect(self.post_worker.run)
        self.post_worker.success.connect(self.on_payment_success)
        self.post_worker.error.connect(self.show_error_message)
        self.post_worker.finished.connect(self.post_thread.quit)
        self.post_thread.start()

    def on_payment_success(self, response_data):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", "تم تسجيل الدفعة بنجاح.")
        if self.supplier_id:
            url = f"{BACKEND_BASE_URL}/suppliers/info/?id={self.supplier_id}"
            self._start_info_fetch_request(url)

    def on_supplier_info_update(self, supplier_data):
        self.update_data(supplier_data, fetch_pic=False)
        self.handle_show_invoices()

    def handle_send_email(self):
        if not self.supplier_id:
            QMessageBox.warning(self, "خطأ", "لا يوجد مورد محدد.")
            return

        url = f"{BACKEND_BASE_URL}/suppliers/send-report/{self.supplier_id}/"
        self._set_loading(True)
        self.email_thread = QThread()
        self.email_worker = ApiWorker("GET", url, response_type="text")
        self.email_worker.moveToThread(self.email_thread)
        self.email_thread.started.connect(self.email_worker.run)
        self.email_worker.text_success.connect(self.on_email_success)
        self.email_worker.error.connect(self.show_error_message)
        self.email_worker.finished.connect(self.email_thread.quit)
        self.email_thread.start()

    def on_email_success(self, message):
        self._set_loading(False)
        QMessageBox.information(self, "نجاح", message)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_invoice_fetch_request(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_invoice_fetch_request(self.prev_page_url)

    def _start_info_fetch_request(self, url):
        self._set_loading(True)
        self.info_fetch_thread = QThread()
        self.info_fetch_worker = ApiWorker("GET", url, response_type="json")
        self.info_fetch_worker.moveToThread(self.info_fetch_thread)
        self.info_fetch_thread.started.connect(self.info_fetch_worker.run)
        self.info_fetch_worker.success.connect(self.on_supplier_info_update)
        self.info_fetch_worker.error.connect(self.show_error_message)
        self.info_fetch_worker.finished.connect(self.info_fetch_thread.quit)
        self.info_fetch_thread.start()

    def _start_invoice_fetch_request(self, url):
        self._set_loading(True)
        self.invoice_fetch_thread = QThread()
        self.invoice_fetch_worker = ApiWorker("GET", url, response_type="json")
        self.invoice_fetch_worker.moveToThread(self.invoice_fetch_thread)
        self.invoice_fetch_thread.started.connect(self.invoice_fetch_worker.run)
        self.invoice_fetch_worker.success.connect(self.handle_invoice_response)
        self.invoice_fetch_worker.error.connect(self.show_error_message)
        self.invoice_fetch_worker.finished.connect(self.invoice_fetch_thread.quit)
        self.invoice_fetch_thread.start()

    def handle_invoice_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_invoice_table(results)
        self.update_pagination_controls()
        self._set_loading(False)

    def populate_invoice_table(self, projects):
        self.table.setRowCount(0)
        for project in projects:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            project_id = project.get("project_id") or "---"
            project_name = project.get("project_name") or "---"
            total = project.get("total") or 0
            paid = project.get("paid") or 0
            remining = project.get("remining") or 0

            items = [
                QTableWidgetItem(str(project_id)),
                QTableWidgetItem(str(project_name)),
                QTableWidgetItem(str(total)),
                QTableWidgetItem(str(paid)),
                QTableWidgetItem(str(remining)),
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
        self.btn_show_invoice_payment_details.setEnabled(is_selected)
        self.btn_pay_invoice.setEnabled(is_selected)

    def _set_loading(self, is_loading):
        self.btn_show_invoices.setDisabled(is_loading)
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

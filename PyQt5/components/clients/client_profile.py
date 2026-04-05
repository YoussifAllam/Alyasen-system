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
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QDialog,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QSettings, pyqtSlot
from requests import request, get, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .update_client_data_dialog import UpdateClientDataDialog
from .select_project_dialog import ProjectSelectionDialog
from .invoice_payment_details_dialog import InvoicePaymentDetailsDialog
from .payment_dialog import PaymentDialog


class ApiWorker(QObject):
    """Worker for handling API requests."""

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
            if self.method == "GET":
                response = get(self.url, timeout=15)
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                if self.response_type == "json":
                    self.success.emit(response.json())
                else:
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
            else:
                self.error.emit(f"{response.text}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class ClientProfileUI(QWidget):
    back_to_list_requested = pyqtSignal()
    show_rent_project_requested = pyqtSignal(int)
    show_industrial_project_requested = pyqtSignal(int)
    show_selling_project_requested = pyqtSignal(int)

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
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        headers = ["كود ", "اسم ", "نوع ", "تكلفة ", "حالة ", ""]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(70)

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )  # or Qt.ScrollBarAlwaysOn
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
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
        self.profile_pic = QLabel("Loading...")
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.profile_pic.setFixedSize(200, 200)
        layout.addWidget(self.profile_pic)
        return card

    def create_summary_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.setSpacing(15)
        self.due_display = QLineEdit(readOnly=True)
        self.payable_display = QLineEdit(readOnly=True)
        self.paid_display = QLineEdit(readOnly=True)
        layout.addWidget(QLabel("اجمالي المستحق لنا:"), 0, 0)
        layout.addWidget(self.due_display, 0, 1)
        layout.addWidget(QLabel("اجمالي المطلوب من العميل:"), 1, 0)
        layout.addWidget(self.payable_display, 1, 1)
        layout.addWidget(QLabel("اجمالي المدفوع:"), 2, 0)
        layout.addWidget(self.paid_display, 2, 1)
        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        self.add_project_button = QPushButton("اختيار مشروع للعمل عليه")
        self.add_project_button.setObjectName("primaryButton")
        self.add_project_button.clicked.connect(self.handle_add_project)
        self.btn_show_client_projects = QPushButton("عرض مشاريع العميل")
        self.btn_show_client_projects.clicked.connect(self.handle_show_client_projects)
        self.btn_show_invoice_payment_details = QPushButton("عرض تفاصيل الدفعات")
        self.btn_show_invoice_payment_details.clicked.connect(
            self.handle_show_payment_details
        )
        self.btn_pay_invoice = QPushButton("تسديد دفعه")
        self.btn_pay_invoice.clicked.connect(self.handle_pay_invoice)
        self.btn_edit_profile = QPushButton("تعديل البيانات الشخصية")
        self.btn_edit_profile.clicked.connect(self.handle_edit_profile)
        self.send_email = QPushButton("ارسال كشف حساب للعميل")
        layout.addWidget(self.add_project_button)
        layout.addWidget(self.btn_show_client_projects)
        layout.addWidget(self.btn_show_invoice_payment_details)
        layout.addWidget(self.btn_pay_invoice)
        layout.addWidget(self.btn_edit_profile)
        layout.addWidget(self.send_email)
        layout.addStretch()
        return card

    def handle_show_payment_details(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")
            return

        selected_row = selected_rows[0].row()
        p_id_item = self.table.item(selected_row, 0)
        p_type = self.table.item(selected_row, 2).text().strip()
        p_type = "campaine" if p_type == "حملة" else "project"

        if p_id_item:
            p_id = p_id_item.text().strip()
            dialog = InvoicePaymentDetailsDialog(self.client_id, p_id, p_type, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على كود المشروع المختار.")

    def handle_add_project(self):
        dialog = ProjectSelectionDialog(self)
        dialog.project_selected.connect(self.on_project_selected)
        dialog.exec_()

    def on_project_selected(self, project_data):
        project_type = project_data.get("project_type")
        project_id = project_data.get("id")

        if project_type == "rent":
            self.show_rent_project_requested.emit(project_id)

        elif project_type == "industrial":
            self.show_industrial_project_requested.emit(project_id)

        elif project_type == "selling":
            self.show_selling_project_requested.emit(project_id)
        else:
            QMessageBox.information(
                self,
                "ملاحظة",
                f"مشروع '{project_data.get('name')}' من النوع {project_type}. صفحة عرض هذا النوع غير متوفرة حالياً.",
            )

    def handle_edit_profile(self):
        if not self.client_id or not hasattr(self, "current_client_data"):

            return

        dialog = UpdateClientDataDialog(self.current_client_data, self)
        if dialog.exec_() == QDialog.Accepted:
            url = f"{BACKEND_BASE_URL}/clients/info/?id={self.client_id}"
            self._start_info_fetch_request(url)

    def update_data(self, client_data, fetch_pic=True):
        data = client_data.get("data", {})
        self.current_client_data = data
        self.client_id = data.get("id")
        self.name_label.setText(f"ملف العميل: {data.get('name', '')}")
        self.due_display.setText(f"{data.get('total_balance_owed_to_us', 0):,.2f} ج.م")
        self.payable_display.setText(
            f"{data.get('total_remaining_balance_owed_to_us', 0):,.2f} ج.م"
        )
        self.paid_display.setText(f"{data.get('total_paid_amount', 0):,.2f} ج.م")
        if fetch_pic:
            pic_url = data.get("profile_picture")
            if pic_url:
                self.fetch_image(pic_url)
            else:
                self.profile_pic.setText("No Image")
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
        self.image_worker.error.connect(lambda msg: self.profile_pic.setText(msg))
        self.image_worker.finished.connect(self.image_thread.quit)
        self.image_thread.start()

    def set_image(self, pixmap):
        self.profile_pic.setPixmap(
            pixmap.scaled(
                self.profile_pic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    def handle_show_client_projects(self):
        if not self.client_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على بيانات العميل.")
            return

        url = f"{BACKEND_BASE_URL}/clients/projects/?client_id={self.client_id}"
        self._start_projects_fetch(url)

    def _start_projects_fetch(self, url):
        self._set_loading(True)
        self.projects_fetch_thread = QThread()
        self.projects_fetch_worker = ApiWorker("GET", url, response_type="json")
        self.projects_fetch_worker.moveToThread(self.projects_fetch_thread)
        self.projects_fetch_thread.started.connect(self.projects_fetch_worker.run)
        self.projects_fetch_worker.success.connect(self.on_projects_fetch_success)
        self.projects_fetch_worker.error.connect(self.show_error_message)
        self.projects_fetch_worker.finished.connect(self.projects_fetch_thread.quit)
        self.projects_fetch_thread.start()

    def on_projects_fetch_success(self, response_data):
        self._set_loading(False)
        self.populate_projects_table(response_data)

    def populate_projects_table(self, data):
        campaigns = data.get("campaigns", [])
        projects = data.get("projects", [])

        all_items = campaigns + projects
        all_items.sort(key=lambda x: x.get("created_date", ""), reverse=True)

        self.table.setRowCount(0)
        self.total_count = len(all_items)

        self.next_page_url = data.get("next")
        self.prev_page_url = data.get("previous")

        for row_idx, item in enumerate(all_items):
            self.table.insertRow(row_idx)
            is_campaign = "total_cost" in item

            item_id = str(item.get("id", ""))
            name = str(item.get("name", ""))
            item_type = str(item.get("project_type", ""))
            cost = item.get("total_cost") if is_campaign else item.get("cost")
            status = str(item.get("project_status", ""))

            idx_item = QTableWidgetItem(str(row_idx + 1))
            idx_item.setTextAlignment(Qt.AlignCenter)

            id_item = QTableWidgetItem(item_id)
            id_item.setTextAlignment(Qt.AlignCenter)

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)

            type_item = QTableWidgetItem(item_type)
            type_item.setTextAlignment(Qt.AlignCenter)

            cost_value = "0.00"
            if cost is not None:
                try:
                    cost_value = f"{float(cost):,.2f}"
                except (ValueError, TypeError):
                    cost_value = str(cost)
            cost_item = QTableWidgetItem(cost_value)
            cost_item.setTextAlignment(Qt.AlignCenter)

            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)

            btn_details = QPushButton("عرض التفاصيل")
            btn_details.setObjectName("detailsButton")
            btn_details.clicked.connect(
                lambda checked, p={
                    "id": item.get("id"),
                    "project_type": item.get("project_type"),
                    "name": item.get("name"),
                }: self.on_project_selected(p)
            )

            self.table.setItem(row_idx, 0, id_item)
            self.table.setItem(row_idx, 1, name_item)
            self.table.setItem(row_idx, 2, type_item)
            self.table.setItem(row_idx, 3, cost_item)
            self.table.setItem(row_idx, 4, status_item)
            self.table.setCellWidget(row_idx, 5, btn_details)

        self.update_pagination_controls()

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
                "client_id": str(self.client_id) if self.client_id else "",
                "project_id": str(p_id),
                "payment_amount": amount_str,
                "note": data.get("notes", ""),
                "payment_date": data.get("payment_date", ""),
                "payment_type": data.get("payment_type", ""),
                "portal_invoice_number": data.get("portal_invoice_number", ""),
                "username": username,
            }
            files = {}
            if data.get("portal_invoice_file"):
                files["portal_invoice_file"] = data.get("portal_invoice_file")
            url = f"{BACKEND_BASE_URL}/clients/projects/payments/"
            self._start_post_request(url, data=form_data, files=files)

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
        if self.client_id:
            url = f"{BACKEND_BASE_URL}/clients/projects/?client_id={self.client_id}"
            self._start_projects_fetch(url)

    def handle_next_page(self):
        if self.next_page_url:
            self._start_projects_fetch(self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._start_projects_fetch(self.prev_page_url)

    def _start_info_fetch_request(self, url):
        self.info_fetch_thread = QThread()
        self.info_fetch_worker = ApiWorker("GET", url, response_type="json")
        self.info_fetch_worker.moveToThread(self.info_fetch_thread)
        self.info_fetch_thread.started.connect(self.info_fetch_worker.run)
        self.info_fetch_worker.success.connect(self.on_client_info_update)
        self.info_fetch_worker.error.connect(self.show_error_message)
        self.info_fetch_worker.finished.connect(self.info_fetch_thread.quit)
        self.info_fetch_thread.start()

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي المشاريع: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد مشاريع")

    def _set_loading(self, is_loading):
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

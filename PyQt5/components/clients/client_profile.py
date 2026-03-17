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
from .client_payment_details_dialog import ClientPaymentDetailsDialog
from .client_payment_dialog import ClientPaymentDialog
from .update_client_data_dialog import UpdateClientDataDialog
from .client_projects_dialog import ClientProjectsDialog


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
        self.table.setColumnCount(4)
        headers = ["رقم المشروع", "نوع المشروع", "الإجمالي", "الحالة"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
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
        self.btn_show_client_projects = QPushButton("عرض مشارع العميل")
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
        layout.addWidget(self.btn_show_client_projects)
        layout.addWidget(self.btn_show_invoice_payment_details)
        layout.addWidget(self.btn_pay_invoice)
        layout.addWidget(self.btn_edit_profile)
        layout.addWidget(self.send_email)
        layout.addStretch()
        return card

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
            
        dialog = ClientProjectsDialog(self.client_id, self)
        dialog.exec_()

    def handle_show_payment_details(self):
        dialog = ClientPaymentDetailsDialog(self.client_id, self)
        dialog.exec_()

    def handle_pay_invoice(self):
        dialog = ClientPaymentDialog(self.client_id, self)
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
            username = settings.value("user_name", "unknown_user")
            payload = {
                "client_id": self.client_id,
                "payment_amount": amount_str,
                "username": username,
                "notes": data.get("notes"),
            }
            url = f"{BACKEND_BASE_URL}/clients/invoice/payment/"
            self._start_post_request(url, payload)

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
            url = f"{BACKEND_BASE_URL}/clients/invoice/invoices/?client_id={self.client_id}"
            self._start_invoice_fetch(url)

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

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0:
            self.page_info_label.setText(f"إجمالي الفواتير: {self.total_count}")
        else:
            self.page_info_label.setText("لا توجد فواتير")

    def _set_loading(self, is_loading):
        self.next_button.setDisabled(is_loading)
        self.prev_button.setDisabled(is_loading)
        self.page_info_label.setText("جاري التحميل..." if is_loading else "")

    def show_error_message(self, message):
        self._set_loading(False)
        self.page_info_label.setText("فشل تحميل البيانات")
        QMessageBox.critical(self, "خطأ في الاتصال", message)

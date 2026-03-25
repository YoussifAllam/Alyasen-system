from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGridLayout,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .ui_projects import ProjectApiWorker  # Reusing API worker


class RentProjectPage(QWidget):
    back_to_profile_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.project_id = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Header
        header_layout = QHBoxLayout()
        self.header_label = QLabel("تفاصيل مشروع إيجار")
        self.header_label.setObjectName("mainHeader")

        back_btn = QPushButton("رجوع لملف العميل")
        back_btn.clicked.connect(self.back_to_profile_requested.emit)

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)

        # Upper Layout: Info and Taxes
        info_taxes_layout = QHBoxLayout()
        info_taxes_layout.setSpacing(20)

        self.info_card = self.create_info_card()
        info_taxes_layout.addWidget(self.info_card, 1)

        self.taxes_card = self.create_taxes_card()
        info_taxes_layout.addWidget(self.taxes_card, 1)

        main_layout.addLayout(info_taxes_layout)

        # Lower Layout: Contracts and Buttons
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(20)

        self.contracts_card = self.create_contracts_card()
        lower_layout.addWidget(self.contracts_card, 2)

        self.actions_card = self.create_actions_card()
        lower_layout.addWidget(self.actions_card, 1)

        main_layout.addLayout(lower_layout)

    def create_info_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.setSpacing(15)

        title = QLabel("بيانات المشروع")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title, 0, 0, 1, 2)

        self.lbl_id = QLabel("-")
        self.lbl_name = QLabel("-")
        self.lbl_operating_cost = QLabel("-")
        self.lbl_profit = QLabel("-")
        self.lbl_total_cost = QLabel("-")
        self.lbl_status = QLabel("-")

        layout.addWidget(QLabel("الكود:"), 1, 0)
        layout.addWidget(self.lbl_id, 1, 1)

        layout.addWidget(QLabel("الاسم:"), 2, 0)
        layout.addWidget(self.lbl_name, 2, 1)

        layout.addWidget(QLabel("تكلفة التشغيل:"), 3, 0)
        layout.addWidget(self.lbl_operating_cost, 3, 1)

        layout.addWidget(QLabel("الربح:"), 4, 0)
        layout.addWidget(self.lbl_profit, 4, 1)

        layout.addWidget(QLabel("إجمالي التكلفة:"), 5, 0)
        layout.addWidget(self.lbl_total_cost, 5, 1)

        layout.addWidget(QLabel("الحالة:"), 6, 0)
        layout.addWidget(self.lbl_status, 6, 1)

        return card

    def create_taxes_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.setSpacing(15)

        title = QLabel("الضرائب والتأمينات")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title, 0, 0, 1, 2)

        self.lbl_vat = QLabel("-")
        self.lbl_insurance_tax = QLabel("-")
        self.lbl_insurance_date = QLabel("-")
        self.lbl_profits_tax = QLabel("-")

        layout.addWidget(QLabel("ضريبة القيمة المضافة:"), 1, 0)
        layout.addWidget(self.lbl_vat, 1, 1)

        layout.addWidget(QLabel("تأمينات:"), 2, 0)
        layout.addWidget(self.lbl_insurance_tax, 2, 1)

        layout.addWidget(QLabel("تاريخ التأمينات:"), 3, 0)
        layout.addWidget(self.lbl_insurance_date, 3, 1)

        layout.addWidget(QLabel("ضريبة الأرباح:"), 4, 0)
        layout.addWidget(self.lbl_profits_tax, 4, 1)

        layout.setAlignment(Qt.AlignTop)
        return card

    def create_contracts_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        title = QLabel("العقود")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.contracts_table = QTableWidget()
        self.contracts_table.setColumnCount(2)
        self.contracts_table.setHorizontalHeaderLabels(["م", "رابط العقد"])
        self.contracts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        layout.addWidget(self.contracts_table)

        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        title = QLabel("إجراءات المشروع")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.btn_ads = QPushButton("إعلانات المشروع")
        self.btn_op_cost = QPushButton("تكاليف التشغيل")
        self.btn_cheques = QPushButton("شيكات الضمان")
        self.update_project_data = QPushButton("تحديث بيانات المشروع")
        self.btn_show_payments = QPushButton("عرض دفعات المشروع")
        self.btn_pay = QPushButton("تسديد دفعة للمشروع")

        # Connect buttons to placeholder handlers
        self.btn_ads.clicked.connect(lambda: self.show_placeholder("إعلانات المشروع"))
        self.btn_op_cost.clicked.connect(
            lambda: self.show_placeholder("تكاليف التشغيل")
        )
        self.btn_cheques.clicked.connect(lambda: self.show_placeholder("شيكات الضمان"))
        self.btn_show_payments.clicked.connect(
            lambda: self.show_placeholder("عرض الدفعات")
        )
        self.btn_pay.clicked.connect(lambda: self.show_placeholder("تسديد دفعة"))

        layout.addWidget(self.update_project_data)
        layout.addWidget(self.btn_ads)
        layout.addWidget(self.btn_op_cost)
        layout.addWidget(self.btn_cheques)
        layout.addWidget(self.btn_show_payments)
        layout.addWidget(self.btn_pay)
        layout.addStretch()
        return card

    def show_placeholder(self, title):
        QMessageBox.information(self, "تحت الإنشاء", f"نافذة {title} قيد التطوير.")

    def load_project_data(self, project_id):
        self.project_id = project_id
        payload = {"project_id": project_id}
        url = f"{BACKEND_BASE_URL}/projects/rent/info/"  # Assuming this endpoint exists based on instructions

        self.thread = QThread()
        self.worker = ProjectApiWorker("GET", url, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_data_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_data_loaded(self, response_data):
        # We try to extract data as flexibly as possible
        # since endpoint response structure might wrap it in "data" or return directly
        data = response_data.get("data", response_data)

        # Project base info
        project_details = data.get("project", {})
        if not project_details and "name" in data:
            project_details = data  # In case the backend flattens the response

        self.lbl_id.setText(str(data.get("id", project_details.get("id", "-"))))
        self.lbl_name.setText(str(project_details.get("name", data.get("name", "-"))))
        self.lbl_operating_cost.setText(str(data.get("operating_costs", "-")))
        self.lbl_profit.setText(str(data.get("profit", "-")))

        # total_cost might be in base project or sent separate, handle gracefully
        self.lbl_total_cost.setText(
            str(data.get("total_cost", project_details.get("total_cost", "-")))
        )
        self.lbl_status.setText(str(data.get("project_status", "-")))

        # Taxes
        self.lbl_vat.setText(str(data.get("value_added_tax", "-")))
        self.lbl_insurance_tax.setText(str(data.get("insurance_tax", "-")))
        self.lbl_insurance_date.setText(str(data.get("insurance_tax_date", "-")))
        self.lbl_profits_tax.setText(str(data.get("profits_tax", "-")))

        # Contracts table
        contracts = data.get("contracts", [])
        self.contracts_table.setRowCount(0)
        for idx, contract in enumerate(contracts):
            row = self.contracts_table.rowCount()
            self.contracts_table.insertRow(row)
            self.contracts_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            contract_file = contract.get("contract", "")
            self.contracts_table.setItem(row, 1, QTableWidgetItem(contract_file))

    def on_error(self, message):
        QMessageBox.warning(self, "خطأ", f"فشل تحميل بيانات المشروع:\n{message}")

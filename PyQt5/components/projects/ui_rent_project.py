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
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QIcon
import qtawesome as qta
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
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # Header Section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        self.header_label = QLabel("تفاصيل مشروع إيجار")
        self.header_label.setObjectName("mainHeader")

        back_btn = QPushButton("رجوع")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setIcon(qta.icon("fa5s.arrow-right", color="#ffffff"))
        back_btn.setLayoutDirection(
            Qt.LeftToRight
        )  # Keep icon to the right (start of text in RTL)
        back_btn.setMinimumHeight(45)
        back_btn.clicked.connect(self.back_to_profile_requested.emit)

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)
        main_layout.addWidget(header_widget)

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

    def create_card_title(self, text, icon_name):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color="#00bc88").pixmap(QSize(24, 24)))

        title_label = QLabel(text)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("font-weight: bold; font-size: 18px;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()
        return container

    def create_info_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        layout.addWidget(
            self.create_card_title("بيانات المشروع", "fa5s.project-diagram")
        )

        grid = QGridLayout()
        grid.setSpacing(15)

        self.lbl_id = self.create_value_label()
        self.lbl_name = self.create_value_label()
        self.lbl_operating_cost = self.create_value_label()
        self.lbl_supplier_cost = self.create_value_label()
        self.lbl_sell_cost = self.create_value_label()
        self.lbl_profit = self.create_value_label()
        self.lbl_total_cost = self.create_value_label()

        rows = [
            ("الكود:", self.lbl_id),
            ("الاسم:", self.lbl_name),
            ("تكلفة التشغيل:", self.lbl_operating_cost),
            ("تكلفة الشراء:", self.lbl_supplier_cost),
            ("اجمالي التكلفة:", self.lbl_total_cost),
            ("مبلغ البيع:", self.lbl_sell_cost),
            ("الربح المتوقع:", self.lbl_profit),
        ]

        for i, (label_text, value_widget) in enumerate(rows):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #9ca3af; font-size: 15px;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(value_widget, i, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return card

    def create_value_label(self, text="-"):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 16px;")
        return label

    def create_taxes_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        layout.addWidget(
            self.create_card_title("الضرائب والتأمينات", "fa5s.percentage")
        )

        grid = QGridLayout()
        grid.setSpacing(15)

        self.lbl_vat = self.create_value_label()
        self.lbl_insurance_tax = self.create_value_label()
        self.lbl_insurance_date = self.create_value_label()
        self.lbl_profits_tax = self.create_value_label()

        rows = [
            ("ضريبة القيمة المضافة:", self.lbl_vat),
            ("تأمينات:", self.lbl_insurance_tax),
            ("تاريخ استرداد التأمينات:", self.lbl_insurance_date),
            ("ضريبة الأرباح التاجرية:", self.lbl_profits_tax),
        ]

        for i, (label_text, value_widget) in enumerate(rows):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #9ca3af; font-size: 15px;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(value_widget, i, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return card

    def create_contracts_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        layout.addWidget(self.create_card_title("العقود المرفقة", "fa5s.file-contract"))

        self.contracts_table = QTableWidget()
        self.contracts_table.setColumnCount(3)
        self.contracts_table.setHorizontalHeaderLabels(["م", "رابط العقد", "إجراءات"])
        self.contracts_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.contracts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.contracts_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )

        layout.addWidget(self.contracts_table)
        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        layout.addWidget(self.create_card_title("إجراءات المشروع", "fa5s.tasks"))

        self.update_project_data = QPushButton("تحديث بيانات المشروع")
        self.update_project_data.setObjectName("primaryButton")
        self.btn_ads = QPushButton("إعلانات المأجرة")
        self.btn_op_cost = QPushButton("تكاليف التشغيل")
        self.btn_cheques = QPushButton("شيك الضمان")

        # Connect buttons
        self.update_project_data.clicked.connect(
            lambda: self.load_project_data(self.project_id)
        )
        self.btn_ads.clicked.connect(lambda: self.show_placeholder("إعلانات المشروع"))
        self.btn_op_cost.clicked.connect(
            lambda: self.show_placeholder("تكاليف التشغيل")
        )
        self.btn_cheques.clicked.connect(lambda: self.show_placeholder("شيكات الضمان"))

        layout.addWidget(self.update_project_data)
        layout.addWidget(self.btn_ads)
        layout.addWidget(self.btn_op_cost)
        layout.addWidget(self.btn_cheques)
        layout.addStretch()
        return card

    def show_placeholder(self, title):
        QMessageBox.information(self, "تحت الإنشاء", f"نافذة {title} قيد التطوير.")

    def load_project_data(self, project_id):
        self.header_label.setText(
            f"تفاصيل مشروع إيجار رقم : {project_id} (جاري التحميل...)"
        )
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
        self.header_label.setText(f"تفاصيل مشروع إيجار رقم : {self.project_id}")
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

            # Index
            self.contracts_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))

            # File name
            contract_file = contract.get("contract", "")
            file_name = contract_file.split("/")[-1] if contract_file else "بدون ملف"
            self.contracts_table.setItem(row, 1, QTableWidgetItem(file_name))

            # Actions cell (Download/View button)
            view_btn = QPushButton("عرض")
            view_btn.setIcon(qta.icon("fa5s.eye", color="#ffffff"))
            view_btn.setStyleSheet("background-color: #374151; padding: 5px;")
            view_btn.clicked.connect(
                lambda checked, url=contract_file: self.open_contract(url)
            )

            self.contracts_table.setCellWidget(row, 2, view_btn)

    def open_contract(self, url):
        """Placeholder for opening a contract file."""
        if url:
            import webbrowser

            webbrowser.open(url)
        else:
            QMessageBox.warning(self, "تنبيه", "لا يوجد رابط لهذا العقد.")

    def on_error(self, message):
        self.header_label.setText(f"تفاصيل مشروع إيجار رقم : {self.project_id}")
        QMessageBox.warning(self, "خطأ", f"فشل تحميل بيانات المشروع:\n{message}")

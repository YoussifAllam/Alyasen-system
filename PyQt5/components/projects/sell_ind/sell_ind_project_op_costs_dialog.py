from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QFrame,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QWidget,
)
from PyQt5.QtCore import Qt, QThread, QPoint, QSize
import qtawesome as qta
from ..ui_projects import ProjectApiWorker
from ...Main_Ui_Components.constant import BACKEND_BASE_URL
from ...validation import attach_number_formatter, clean_number


class AddOpCostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة تكلفة تشغيل جديدة")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("dialogContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel("إضافة تكلفة تشغيل")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        layout.addWidget(self.title_bar)

        # Form
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.name_input = QLineEdit()
        self.amount_input = QLineEdit()
        attach_number_formatter(self.amount_input)

        form_layout.addRow("الوصف/الاسم:", self.name_input)
        form_layout.addRow("المبلغ:", self.amount_input)

        content_layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.handle_add)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        content_layout.addLayout(btn_layout)

        layout.addLayout(content_layout)
        main_layout.addWidget(container)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (
            hasattr(self, "old_pos")
            and self.old_pos
            and event.buttons() == Qt.LeftButton
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def handle_add(self):
        name = self.name_input.text().strip()
        amount = clean_number(self.amount_input.text())
        if not name or not amount:
            QMessageBox.warning(self, "تنبيه", "يرجى ملء جميع الحقول.")
            return
        self.cost_data = {"name": name, "amount": amount}
        self.accept()


class RentProjectOpCostsDialog(QDialog):
    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("تكاليف التشغيل")
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None
        self.data_changed = False

        self.setup_ui()
        self.load_costs()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("dialogContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel("تكاليف التشغيل للمشروع")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.close_dialog)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        layout.addWidget(self.title_bar)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(15)

        # Add Button
        self.add_btn = QPushButton("إضافة تكلفة جديدة")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setIcon(qta.icon("fa5s.plus", color="#ffffff"))
        self.add_btn.clicked.connect(self.handle_add_cost)
        content_layout.addWidget(self.add_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "الوصف", "المبلغ", "إجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(50)
        content_layout.addWidget(self.table)

        layout.addLayout(content_layout)
        main_layout.addWidget(container)

    def close_dialog(self):
        if self.data_changed:
            self.accept()
        else:
            self.reject()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (
            hasattr(self, "old_pos")
            and self.old_pos
            and event.buttons() == Qt.LeftButton
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def load_costs(self):
        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/operating-costs/?CBP_id={self.project_id}"
        self.thread = QThread()
        self.worker = ProjectApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def show_error(self, message):
        self.add_btn.setEnabled(True)
        QMessageBox.warning(self, "خطأ", message)

    def populate_table(self, response):
        data = response.get("data", [])
        self.table.setRowCount(0)
        for cost in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(cost.get("id"))))
            self.table.setItem(row, 1, QTableWidgetItem(str(cost.get("name"))))
            try:
                amt = float(cost.get("amount", 0))
            except (ValueError, TypeError):
                amt = 0.0
            self.table.setItem(row, 2, QTableWidgetItem(f"{amt:,.2f}"))

            # Delete Button
            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#ffffff"))
            del_btn.setStyleSheet(
                "background-color: #dc3545; border: none; border-radius: 4px; padding: 5px;"
            )
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(
                lambda checked, cid=cost.get("id"): self.delete_cost(cid)
            )

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 3, actions_widget)

    def handle_add_cost(self):
        dialog = AddOpCostDialog(self)
        if dialog.exec_():
            cost_data = dialog.cost_data
            cost_data["CBP_id"] = str(self.project_id)

            self.add_btn.setEnabled(False)
            url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/operating-costs/"
            self.add_thread = QThread()
            self.add_worker = ProjectApiWorker("POST", url, cost_data, files=None)
            self.add_worker.moveToThread(self.add_thread)
            self.add_thread.started.connect(self.add_worker.run)
            self.add_worker.success.connect(self.on_op_success)
            self.add_worker.error.connect(self.show_error)
            self.add_worker.finished.connect(self.add_thread.quit)
            self.add_worker.finished.connect(self.add_worker.deleteLater)
            self.add_thread.finished.connect(self.add_thread.deleteLater)
            self.add_thread.start()

    def on_op_success(self, _):
        self.add_btn.setEnabled(True)
        self.data_changed = True
        self.load_costs()

    def delete_cost(self, cost_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه التكلفة؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/operating-costs/"
        payload = {"cost_id": str(cost_id)}

        self.del_thread = QThread()
        self.del_worker = ProjectApiWorker("DELETE", url, payload, files=None)
        self.del_worker.moveToThread(self.del_thread)
        self.del_thread.started.connect(self.del_worker.run)
        self.del_worker.success.connect(self.on_op_success)
        self.del_worker.error.connect(self.show_error)
        self.del_worker.finished.connect(self.del_thread.quit)
        self.del_worker.finished.connect(self.del_worker.deleteLater)
        self.del_thread.finished.connect(self.del_thread.deleteLater)
        self.del_thread.start()

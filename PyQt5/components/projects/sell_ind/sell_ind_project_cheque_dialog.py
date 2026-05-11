from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QDateEdit,
    QFormLayout,
    QMessageBox,
    QFrame,
    QWidget,
)
from PyQt5.QtCore import Qt, QThread, QPoint, QDate
import qtawesome as qta
from ..ui_projects import ProjectApiWorker
from ...Main_Ui_Components.constant import BACKEND_BASE_URL
from ...validation import attach_number_formatter, clean_number


class RentProjectChequeDialog(QDialog):
    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("شيك الضمان")
        self.setMinimumWidth(450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None
        self.cheque_data = None

        self.setup_ui()
        self.load_cheque_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel("شيك الضمان للمشروع")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.close)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        self.layout.addWidget(self.title_bar)

        # Content Area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 20, 25, 25)
        self.content_layout.setSpacing(20)

        self.loading_label = QLabel("جاري التحميل...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.loading_label)

        self.layout.addWidget(self.content_widget)
        main_layout.addWidget(self.container)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (
            hasattr(self, "old_pos")
            and self.old_pos  # noqa
            and event.buttons() == Qt.LeftButton  # noqa
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def load_cheque_data(self):
        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/guarantee-cheque/?CBP_id={self.project_id}"
        self.thread = QThread()
        self.worker = ProjectApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_data_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_data_loaded(self, response):
        self.cheque_data = response.get("data")
        self.show_cheque_view()

    def on_error(self, message):
        # If it's a 404, it means no cheque found
        if "Guarantee cheque not found" in message or "404" in message:
            self.cheque_data = None
            self.show_add_form()
        else:
            QMessageBox.warning(self, "خطأ", message)
            self.close()

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def show_cheque_view(self):
        self.clear_content()
        data = self.cheque_data

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        rows = [
            ("رقم الشيك:", str(data.get("cheque_number"))),
            ("تاريخ الشيك:", str(data.get("cheque_date"))),
            ("مبلغ الشيك:", f"{data.get('cheque_amount', 0):,.2f}"),
        ]

        for lbl_text, val_text in rows:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("color: #9ca3af; font-size: 15px;")
            val = QLabel(val_text)
            val.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff;")
            form_layout.addRow(lbl, val)

        self.content_layout.addLayout(form_layout)

        self.del_btn = QPushButton("حذف الشيك")
        self.del_btn.setStyleSheet(
            "background-color: #dc3545; color: white; min-height: 40px;"
        )
        self.del_btn.clicked.connect(self.handle_delete)
        self.content_layout.addWidget(self.del_btn)

    def show_add_form(self):
        self.clear_content()

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.num_input = QLineEdit()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        self.amount_input = QLineEdit()
        attach_number_formatter(self.amount_input)

        form_layout.addRow("رقم الشيك:", self.num_input)
        form_layout.addRow("تاريخ الشيك:", self.date_input)
        form_layout.addRow("مبلغ الشيك:", self.amount_input)

        self.content_layout.addLayout(form_layout)

        self.add_btn = QPushButton("إضافة الشيك")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.handle_add)
        self.content_layout.addWidget(self.add_btn)

    def handle_add(self):
        num = self.num_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")
        amount = clean_number(self.amount_input.text())

        if not num or not amount:
            QMessageBox.warning(self, "تنبيه", "يرجى ملء جميع الحقول.")
            return

        payload = {
            "CBP_id": str(self.project_id),
            "cheque_number": num,
            "cheque_date": date,
            "cheque_amount": amount,
        }

        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/guarantee-cheque/"
        self.add_thread = QThread()
        self.add_worker = ProjectApiWorker("POST", url, payload, files={})
        self.add_worker.moveToThread(self.add_thread)
        self.add_thread.started.connect(self.add_worker.run)
        self.add_worker.success.connect(self.load_cheque_data)  # Reload to show view
        self.add_worker.error.connect(lambda msg: QMessageBox.warning(self, "خطأ", msg))
        self.add_worker.finished.connect(self.add_thread.quit)
        self.add_thread.start()

    def handle_delete(self):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف شيك الضمان؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        url = f"{BACKEND_BASE_URL}/projects/selling_ind_p/guarantee-cheque/"
        payload = {"CBP_id": str(self.project_id)}

        self.del_thread = QThread()
        self.del_worker = ProjectApiWorker("DELETE", url, payload, files={})
        self.del_worker.moveToThread(self.del_thread)
        self.del_thread.started.connect(self.del_worker.run)
        self.del_worker.success.connect(
            self.load_cheque_data
        )  # Reload to show add form
        self.del_worker.error.connect(lambda msg: QMessageBox.warning(self, "خطأ", msg))
        self.del_worker.finished.connect(self.del_thread.quit)
        self.del_thread.start()

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


class AddAdDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة إعلان جديد")
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

        title_text = QLabel("إضافة إعلان جديد")
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

        self.ad_type_input = QLineEdit()
        self.number_input = QLineEdit()
        self.size_input = QLineEdit()
        self.address_input = QLineEdit()
        self.notes_input = QLineEdit()

        form_layout.addRow("نوع الإعلان:", self.ad_type_input)
        form_layout.addRow("العدد:", self.number_input)
        form_layout.addRow("الحجم:", self.size_input)
        form_layout.addRow("العنوان:", self.address_input)
        form_layout.addRow("ملاحظات:", self.notes_input)

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
            and self.old_pos  # noqa
            and event.buttons() == Qt.LeftButton  # noqa
        ):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def handle_add(self):
        data = {
            "ad_type": self.ad_type_input.text().strip(),
            "number": self.number_input.text().strip(),
            "size": self.size_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.text().strip(),
        }
        if not data["ad_type"] or not data["number"]:
            QMessageBox.warning(
                self, "تنبيه", "يرجى ملء الحقول الأساسية (النوع والعدد)."
            )
            return
        self.ad_data = data
        self.accept()


class RentProjectAdsDialog(QDialog):
    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("إعلانات المشروع")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        self.setup_ui()
        self.load_ads()

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

        title_text = QLabel(f"إعلانات المشروع (CBP ID: {self.project_id})")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.close)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        layout.addWidget(self.title_bar)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(15)

        # Add Ad Button
        self.add_ad_btn = QPushButton("إضافة إعلان جديد")
        self.add_ad_btn.setObjectName("primaryButton")
        self.add_ad_btn.setMinimumHeight(40)
        self.add_ad_btn.setIcon(qta.icon("fa5s.plus", color="#ffffff"))
        self.add_ad_btn.clicked.connect(self.handle_add_ad)
        content_layout.addWidget(self.add_ad_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "النوع", "العدد", "الحجم", "العنوان", "ملاحظات", "إجراءات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(50)

        content_layout.addWidget(self.table)

        layout.addLayout(content_layout)
        main_layout.addWidget(container)

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

    def load_ads(self):
        url = f"{BACKEND_BASE_URL}/projects/rent/ads/?CBP_id={self.project_id}"
        self.thread = QThread()
        self.worker = ProjectApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.populate_table)
        self.worker.error.connect(lambda msg: QMessageBox.warning(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_table(self, response):
        data = response.get("data", [])
        self.table.setRowCount(0)
        for ad in data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(ad.get("id"))))
            self.table.setItem(row, 1, QTableWidgetItem(str(ad.get("ad_type"))))
            self.table.setItem(row, 2, QTableWidgetItem(str(ad.get("number"))))
            self.table.setItem(row, 3, QTableWidgetItem(str(ad.get("size"))))
            self.table.setItem(row, 4, QTableWidgetItem(str(ad.get("address"))))
            self.table.setItem(row, 5, QTableWidgetItem(str(ad.get("notes"))))

            # Delete Button
            del_btn = QPushButton()
            del_btn.setIcon(qta.icon("fa5s.trash-alt", color="#ffffff"))
            del_btn.setStyleSheet(
                "background-color: #dc3545; border: none; border-radius: 4px; padding: 5px;"
            )
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(
                lambda checked, aid=ad.get("id"): self.delete_ad(aid)
            )

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 6, actions_widget)

    def handle_add_ad(self):
        dialog = AddAdDialog(self)
        if dialog.exec_():
            ad_data = dialog.ad_data
            ad_data["CBP_id"] = str(self.project_id)

            url = f"{BACKEND_BASE_URL}/projects/rent/ads/"
            self.add_thread = QThread()
            # Passing files={} to ensure multipart/form-data as per --form requirement
            self.add_worker = ProjectApiWorker("POST", url, ad_data, files={})
            self.add_worker.moveToThread(self.add_thread)
            self.add_thread.started.connect(self.add_worker.run)
            self.add_worker.success.connect(self.load_ads)
            self.add_worker.error.connect(
                lambda msg: QMessageBox.warning(self, "خطأ", msg)
            )
            self.add_worker.finished.connect(self.add_thread.quit)
            self.add_thread.start()

    def delete_ad(self, ads_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الإعلان؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        url = f"{BACKEND_BASE_URL}/projects/rent/ads/"
        payload = {"ads_id": str(ads_id)}

        self.del_thread = QThread()
        # Passing files={} to trigger form-data
        self.del_worker = ProjectApiWorker("DELETE", url, payload, files={})
        self.del_worker.moveToThread(self.del_thread)
        self.del_thread.started.connect(self.del_worker.run)
        self.del_worker.success.connect(self.load_ads)
        self.del_worker.error.connect(lambda msg: QMessageBox.warning(self, "خطأ", msg))
        self.del_worker.finished.connect(self.del_thread.quit)
        self.del_thread.start()

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QScrollArea,
    QWidget,
    QFrame,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot, QSettings, QPoint
from requests import request, exceptions
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..validation import (
    validate_not_empty,
    validate_combo_selected,
    run_validations,
    _clear_errors,
)


class ApiWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None):
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
            else:
                error_data = response.json()
                msg = error_data.get("message", f"خطأ: {response.status_code}")
                self.error.emit(msg)
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class CampaignItemRow(QFrame):
    removed = pyqtSignal(object)
    value_changed = pyqtSignal()

    def __init__(self, suppliers):
        super().__init__()
        self.suppliers = suppliers
        self.setObjectName("formRow")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("اختر المورد", None)
        for s in suppliers:
            self.supplier_combo.addItem(s["name"], s["id"])

        self.project_combo = QComboBox()
        self.project_combo.addItem("اختر المشروع", None)
        self.project_combo.setEnabled(False)
        self.project_combo.currentIndexChanged.connect(
            lambda: self.value_changed.emit()
        )

        self.remove_btn = QPushButton("حذف")
        self.remove_btn.setObjectName("dangerButton")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(QLabel("المورد:"))
        layout.addWidget(self.supplier_combo, 1)
        layout.addWidget(QLabel("المشروع:"))
        layout.addWidget(self.project_combo, 1)
        layout.addWidget(self.remove_btn)

        self.supplier_combo.currentIndexChanged.connect(self.on_supplier_changed)

    def on_supplier_changed(self, index):
        supplier_id = self.supplier_combo.currentData()
        self.project_combo.clear()
        self.project_combo.addItem("اختر المشروع", None)
        self.project_combo.setEnabled(False)

        if supplier_id:
            url = f"{BACKEND_BASE_URL}/suppliers/projects/?supplier_id={supplier_id}"
            self.thread = QThread()
            self.worker = ApiWorker("GET", url)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.success.connect(self.on_projects_fetched)
            self.worker.finished.connect(self.thread.quit)
            self.thread.start()

            # Keep a reference to prevent garbage collection
            self._fetch_thread = self.thread
            self._fetch_worker = self.worker
        else:
            self.value_changed.emit()

    def on_projects_fetched(self, data_response):
        results = data_response.get("data", {}).get("results", [])
        for p in results:
            project_id = p.get("project_id")
            project_name = p.get("project_name", f"مشروع {project_id}")
            total_cost = p.get("total", 0)
            self.project_combo.addItem(project_name, (project_id, total_cost))

        self.project_combo.setEnabled(True)
        self.value_changed.emit()

    def get_data(self):
        proj_data = self.project_combo.currentData()
        proj_id = proj_data[0] if isinstance(proj_data, tuple) else None
        amount = proj_data[1] if isinstance(proj_data, tuple) else 0
        return {
            "supplier_id": self.supplier_combo.currentData(),
            "project_id": proj_id,
            "amount": amount,
        }


class AddCampaignDialog(QDialog):
    campaign_added = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة حملة جديدة")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.suppliers = []
        self.clients = []
        self.rows = []

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("dialogContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)

        title_text = QLabel("إضافة حملة جديدة")
        title_text.setObjectName("titleBarText")

        close_button = QPushButton("✕")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.reject)

        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)

        layout.addWidget(self.title_bar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 0, 15, 15)
        content_layout.setSpacing(15)

        # Campaign Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("اسم الحملة:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        content_layout.addLayout(name_layout)

        # Client Selection
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel("العميل:"))
        self.client_combo = QComboBox()
        self.client_combo.addItem("اختر العميل", None)
        client_layout.addWidget(self.client_combo)
        content_layout.addLayout(client_layout)

        # Items Section
        items_group = QFrame()
        items_layout = QVBoxLayout(items_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.items_container = QWidget()
        self.items_vbox = QVBoxLayout(self.items_container)
        self.items_vbox.addStretch()
        scroll.setWidget(self.items_container)

        items_layout.addWidget(QLabel("الموردين والمشاريع:"))
        items_layout.addWidget(scroll)

        add_item_btn = QPushButton("+ إضافة مورد")
        add_item_btn.clicked.connect(self.add_row)
        items_layout.addWidget(add_item_btn)

        content_layout.addWidget(items_group, 1)

        # Footer
        footer_layout = QHBoxLayout()
        self.total_label = QLabel("إجمالي التكلفة: 0.00")
        self.total_label.setObjectName("totalLabel")
        footer_layout.addWidget(self.total_label)
        footer_layout.addStretch()

        self.save_btn = QPushButton("حفظ الحملة")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.handle_save)
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.reject)

        footer_layout.addWidget(self.cancel_btn)
        footer_layout.addWidget(self.save_btn)
        content_layout.addLayout(footer_layout)

        layout.addLayout(content_layout)
        main_layout.addWidget(container)

        self.fetch_initial_data()

    def fetch_initial_data(self):
        self._start_get_request(f"{BACKEND_BASE_URL}/clients/clients/", "clients")
        self._start_get_request(f"{BACKEND_BASE_URL}/suppliers/suppliers/", "suppliers")

    def _start_get_request(self, url, target):
        thread = QThread()
        worker = ApiWorker("GET", url)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.success.connect(lambda data: self.handle_fetch_success(data, target))
        worker.finished.connect(thread.quit)
        thread.start()
        # Keep references
        if not hasattr(self, "threads"):
            self.threads = []
        self.threads.append((thread, worker))

    def handle_fetch_success(self, data, target):
        results = data.get("data", {}).get("results", [])
        if target == "clients":
            self.clients = results
            for c in results:
                self.client_combo.addItem(c["name"], c["id"])
        elif target == "suppliers":
            self.suppliers = results

    def add_row(self):
        row = CampaignItemRow(self.suppliers)
        row.removed.connect(self.remove_row)
        row.value_changed.connect(self.update_total)
        self.items_vbox.insertWidget(len(self.rows), row)
        self.rows.append(row)
        self.update_total()

    def remove_row(self, row):
        self.items_vbox.removeWidget(row)
        self.rows.remove(row)
        row.deleteLater()
        self.update_total()

    def update_total(self):
        total = sum(row.get_data().get("amount", 0) for row in self.rows)
        self.total_label.setText(f"إجمالي التكلفة: {total:,.2f} ")

    def handle_save(self):
        _clear_errors([self.name_input, self.client_combo])

        validations = [
            validate_not_empty(self.name_input, "اسم الحملة"),
            validate_combo_selected(self.client_combo, "العميل"),
        ]
        if not run_validations(self, validations):
            return

        if not self.rows:
            QMessageBox.warning(self, "خطأ", "يرجى إضافة مورد واحد على الأقل.")
            return

        name = self.name_input.text().strip()
        client_id = self.client_combo.currentData()
        items_data = []
        for row in self.rows:
            data = row.get_data()
            if not data["supplier_id"] or not data["project_id"]:
                QMessageBox.warning(
                    self, "خطأ", "يرجى التحقق من بيانات الموردين والمشاريع."
                )
                return
            items_data.append(
                {"supplier_id": data["supplier_id"], "project_id": data["project_id"]}
            )

        payload = {"name": name, "client": client_id, "items": items_data}

        url = f"{BACKEND_BASE_URL}/campaine/"
        self._start_post_request(url, payload)

    def _start_post_request(self, url, payload):
        self.save_btn.setEnabled(False)
        self._post_thread = QThread()
        self._post_worker = ApiWorker("POST", url, payload)
        self._post_worker.moveToThread(self._post_thread)
        self._post_thread.started.connect(self._post_worker.run)
        self._post_worker.success.connect(self.on_save_success)
        self._post_worker.error.connect(
            lambda msg: QMessageBox.critical(self, "خطأ", msg)
        )
        self._post_worker.finished.connect(lambda: self.save_btn.setEnabled(True))
        self._post_worker.finished.connect(self._post_thread.quit)
        self._post_thread.start()

    def on_save_success(self, data):
        QMessageBox.information(self, "نجاح", "تمت إضافة الحملة بنجاح.")
        self.campaign_added.emit()
        self.accept()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and hasattr(self, "title_bar")  # noqa
            and self.title_bar.underMouse()  # noqa
        ):
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

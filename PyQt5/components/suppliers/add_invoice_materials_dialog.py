from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QFrame,
    QWidget,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QMessageBox,
    QGroupBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot, QSettings
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class ApiWorker(QObject):
    """Generic worker for handling various API requests in this dialog."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    list_success = pyqtSignal(list)
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
                json_data = response.json()
                if self.method == "GET":
                    self.list_success.emit(json_data.get("data", []))
                else:
                    self.success.emit(json_data)
            elif response.status_code == 204 and self.method == "DELETE":
                self.success.emit({"status": "deleted"})
            else:
                try:
                    error_data = response.json()
                    error_msg = next(iter(error_data.values()), [f"HTTP {response.status_code}"])[0]
                    self.error.emit(error_msg)
                except Exception:
                    self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class AddInvoiceMaterialsDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.setWindowTitle(f"إضافة خامات للفاتورة: {invoice_num}")
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(f"إضافة خامات للفاتورة رقم: {invoice_num}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.handle_cancel)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        form_group = QGroupBox("إضافة خامة")
        form_layout = QHBoxLayout(form_group)
        self.material_combo = QComboBox()
        self.material_combo.setEditable(True)
        self.quantity_input = QLineEdit(placeholderText="الكمية بالوحدة")
        self.buy_price_input = QLineEdit(placeholderText="سعر الشراء للوحده")
        self.unit_input = QLineEdit(placeholderText="الوحده")
        self.add_material_button = QPushButton("إضافة")
        self.add_material_button.setObjectName("primaryButton")
        self.add_material_button.clicked.connect(self.handle_add_material)
        form_layout.addWidget(self.material_combo, 2)
        form_layout.addWidget(self.quantity_input, 1)
        form_layout.addWidget(self.buy_price_input, 1)
        form_layout.addWidget(self.unit_input, 1)
        form_layout.addWidget(self.add_material_button)
        content_layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["اسم الخامة", "الكمية", "سعر الشراء", "الوحده", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(5, 120)
        self.table.verticalHeader().setDefaultSectionSize(55)

        content_layout.addWidget(self.table, 1)

        bottom_layout = QHBoxLayout()
        self.save_button = QPushButton("حفظ ومتابعة")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save_and_continue)
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.handle_cancel)
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(cancel_button)
        content_layout.addLayout(bottom_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.fetch_material_names()

    def handle_save_and_continue(self):
        """Validates and starts the API request to finalize the materials list."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "خطأ", "لا يمكن حفظ فاتورة فارغة. الرجاء إضافة خامة واحدة على الأقل.")
            return

        settings = QSettings("FactorySystem")
        username = settings.value("user_name", "unknown_user")

        payload = {"invoice_number": self.invoice_num, "username": username}
        url = f"{BACKEND_BASE_URL}/suppliers/invoice/move-to-warehouse/"
        self._start_api_request("POST", url, payload=payload, on_success=self.on_save_continue_success)

    def on_save_continue_success(self, response_data):
        """Closes the dialog with an accept signal after the API call succeeds."""
        # We removed the internal call to InvoiceDetailsDialog here.
        # The parent (SupplierProfileUI) will handle the next step.
        self.accept()

    def handle_cancel(self):
        reply = QMessageBox.question(
            self,
            "تأكيد الإلغاء",
            "هل أنت متأكد؟ سيتم حذف الفاتورة الحالية.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.reject()

    def fetch_material_names(self):
        self.material_combo.setEnabled(False)
        self.material_combo.addItem("جاري التحميل...")
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials-names/"
        self._start_api_request("GET", url, on_list_success=self.populate_material_combo)

    def populate_material_combo(self, material_names):
        self.material_combo.clear()
        if material_names:
            self.material_combo.addItems(material_names)
        self.material_combo.setEnabled(True)

    def handle_add_material(self):
        material = self.material_combo.currentText().strip()
        qty_str = self.quantity_input.text().strip()
        buy_price_str = self.buy_price_input.text().strip()
        unit = self.unit_input.text()

        if not all([material, qty_str, buy_price_str, unit]):
            QMessageBox.warning(self, "خطأ", "الرجاء ملء جميع حقول الخامة.")
            return
        try:
            qty = float(qty_str)
            buy_price = float(buy_price_str)
            if qty <= 0 or buy_price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال أرقام موجبة وصالحة.")
            return

        payload = {
            "material_name": material,
            "quantity_in_unit": qty,
            "buy_price_per_unit": buy_price,
            "unit": unit,
            "invoice_num": self.invoice_num,
        }
        url = f"{BACKEND_BASE_URL}/suppliers/invoice/materials/"
        self._start_api_request("POST", url, payload=payload, on_success=self.on_add_material_success)

    def on_add_material_success(self, response_data):
        data = response_data.get("data", {})
        material_id = data.get("id")
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        name_item = QTableWidgetItem(data.get("material_name", ""))
        name_item.setData(Qt.UserRole, material_id)
        self.table.setItem(row_pos, 0, name_item)
        self.table.setItem(row_pos, 1, QTableWidgetItem(f"{data.get('quantity_in_unit', 0):,.2f}"))
        self.table.setItem(row_pos, 2, QTableWidgetItem(f"{data.get('buy_price_per_unit', 0):,.2f}"))
        self.table.setItem(row_pos, 3, QTableWidgetItem(f"{data.get('unit', 0)}"))
        delete_button_widget = self.create_delete_button_widget(row_pos)
        self.table.setCellWidget(row_pos, 4, delete_button_widget)
        self.table.resizeRowToContents(row_pos)

        self.clear_form_inputs()

    def create_delete_button_widget(self, row):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        delete_button = QPushButton("حذف")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(lambda ch, r=row: self.handle_delete_row(r))
        layout.addWidget(delete_button)
        return container

    def handle_delete_row(self, row):
        item = self.table.item(row, 0)
        if not item:
            return
        material_id = item.data(Qt.UserRole)
        if material_id is None:
            QMessageBox.critical(self, "خطأ", "لا يمكن العثور على معرف الخامة.")
            return
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه الخامة من الفاتورة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            payload = {"material_id": material_id, "invoice_num": self.invoice_num}
            url = f"{BACKEND_BASE_URL}/suppliers/invoice/materials/"
            self._start_api_request(
                "DELETE",
                url,
                payload=payload,
                on_success=lambda d, r=row: self.on_delete_material_success(d, r),
            )

    def on_delete_material_success(self, response_data, row):
        self.table.removeRow(row)

        QMessageBox.information(self, "نجاح", "تم حذف الخامة من الفاتورة.")



    def clear_form_inputs(self):
        self.material_combo.setCurrentIndex(-1)
        self.material_combo.lineEdit().clear()
        self.quantity_input.clear()
        self.buy_price_input.clear()
        self.unit_input.clear()

    def _start_api_request(self, method, url, payload=None, on_success=None, on_list_success=None):
        thread = QThread()
        worker = ApiWorker(method, url, payload)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        if on_success:
            worker.success.connect(on_success)
        if on_list_success:
            worker.list_success.connect(on_list_success)
        worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        worker.finished.connect(thread.quit)
        setattr(self, f"{method.lower()}_thread", thread)
        setattr(self, f"{method.lower()}_worker", worker)
        thread.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "old_pos") and self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

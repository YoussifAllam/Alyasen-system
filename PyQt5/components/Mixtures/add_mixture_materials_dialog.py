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
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
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
                    if isinstance(json_data.get("data"), list):
                        self.list_success.emit(json_data.get("data", []))
                    else:
                        self.success.emit(json_data)
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


class AddMixtureMaterialsDialog(QDialog):
    def __init__(self, mixture_id, mixture_name, parent=None):
        super().__init__(parent)
        self.mixture_id = mixture_id
        self.mixture_name = mixture_name
        self.setWindowTitle(f"إضافة خامات للخلطة: {mixture_name}")
        self.setMinimumSize(1100, 800)
        self.setModal(True)

        # Thread and worker management
        self.fetch_thread = None
        self.add_thread = None
        self.delete_thread = None

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
        title_text = QLabel(f"إضافة خامات للخلطة: {mixture_name}")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
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
        self.quantity_input = QLineEdit(placeholderText="الوزن بالكيلو")
        self.add_material_button = QPushButton("إضافة")
        self.add_material_button.setObjectName("primaryButton")
        self.add_material_button.clicked.connect(self.handle_add_material)

        self.show_all_button = QPushButton("عرض الكل")
        self.show_all_button.clicked.connect(self.fetch_mixture_materials)

        form_layout.addWidget(self.material_combo, 3)
        form_layout.addWidget(self.quantity_input, 1)
        form_layout.addWidget(self.add_material_button)
        form_layout.addWidget(self.show_all_button)
        content_layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "اسم الخامة",
                "الكمية المستخدمة",
                "سعر الشراء",
                "سعر البيع",
                "إجمالي سعر الشراء",
                "إجمالي الربح",
                "",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setDefaultSectionSize(55)
        content_layout.addWidget(self.table, 1)

        bottom_layout = QHBoxLayout()
        self.total_cost_display = QLineEdit("0.00", readOnly=True)
        self.total_profit_display = QLineEdit("0.00", readOnly=True)
        bottom_layout.addWidget(QLabel("إجمالي تكلفة الخامات:"))
        bottom_layout.addWidget(self.total_cost_display)
        bottom_layout.addWidget(QLabel("إجمالي الربح:"))
        bottom_layout.addWidget(self.total_profit_display)
        bottom_layout.addStretch()
        self.continue_button = QPushButton("متابعة")
        self.continue_button.setObjectName("primaryButton")
        self.continue_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        bottom_layout.addWidget(self.continue_button)
        bottom_layout.addWidget(self.cancel_button)
        content_layout.addLayout(bottom_layout)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.fetch_material_names()
        self.fetch_mixture_materials()

    def fetch_material_names(self):
        self._set_loading(True)
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials-names/"

        self.fetch_thread = QThread()
        self.fetch_worker = ApiWorker("GET", url)
        self.fetch_worker.moveToThread(self.fetch_thread)
        self.fetch_thread.started.connect(self.fetch_worker.run)
        self.fetch_worker.list_success.connect(self.populate_material_combo)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.finished.connect(self.fetch_thread.quit)
        self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.finished.connect(lambda: self._set_loading(False))
        self.fetch_thread.start()

    def fetch_mixture_materials(self):
        self._set_loading(True)
        url = f"{BACKEND_BASE_URL}/mixtures/materials/?mixture_id={self.mixture_id}"
        self.mix_fetch_thread = QThread()
        self.mix_fetch_worker = ApiWorker("GET", url)
        self.mix_fetch_worker.moveToThread(self.mix_fetch_thread)
        self.mix_fetch_thread.started.connect(self.mix_fetch_worker.run)
        self.mix_fetch_worker.success.connect(self.populate_materials_table)
        self.mix_fetch_worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.mix_fetch_worker.finished.connect(self.mix_fetch_thread.quit)
        self.mix_fetch_worker.finished.connect(self.mix_fetch_worker.deleteLater)
        self.mix_fetch_thread.finished.connect(self.mix_fetch_thread.deleteLater)
        self.mix_fetch_thread.finished.connect(lambda: self._set_loading(False))
        self.mix_fetch_thread.start()

    def populate_material_combo(self, material_names):
        self.material_combo.clear()
        if material_names:
            self.material_combo.addItems(material_names)
        self.material_combo.lineEdit().clear()

    def populate_materials_table(self, response_data):
        self.table.setRowCount(0)
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        for material_data in results:
            self.add_material_row_to_table(material_data)
        self.update_totals()

    def handle_add_material(self):
        material_name = self.material_combo.currentText().strip()
        quantity_str = self.quantity_input.text().strip()
        if not material_name or not quantity_str:
            QMessageBox.warning(self, "خطأ", "الرجاء اختيار خامة وإدخال الكمية.")
            return
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال كمية موجبة وصالحة.")
            return

        payload = {"material_name": material_name, "mixture_id": self.mixture_id, "quantity_used": quantity}
        url = f"{BACKEND_BASE_URL}/mixtures/materials/"

        self._set_loading(True)
        self.add_thread = QThread()
        self.add_worker = ApiWorker("POST", url, payload)
        self.add_worker.moveToThread(self.add_thread)
        self.add_worker.success.connect(self.on_add_material_success)
        self.add_worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        self.add_worker.finished.connect(self.add_thread.quit)
        self.add_worker.finished.connect(self.add_worker.deleteLater)
        self.add_thread.finished.connect(self.add_thread.deleteLater)
        self.add_worker.finished.connect(lambda: self._set_loading(False))
        self.add_thread.started.connect(self.add_worker.run)
        self.add_thread.start()

    def on_add_material_success(self, response_data):
        self.add_material_row_to_table(response_data.get("data", {}))
        self.update_totals()
        self.clear_form_inputs()

    def add_material_row_to_table(self, data):
        material_id = data.get("id")
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        name_item = QTableWidgetItem(data.get("material_name", ""))
        name_item.setData(Qt.UserRole, material_id)
        self.table.setItem(row_pos, 0, name_item)
        self.table.setItem(row_pos, 1, QTableWidgetItem(f"{data.get('quantity_used', 0):,.2f}"))
        self.table.setItem(row_pos, 2, QTableWidgetItem(f"{data.get('material_buy_price_per_kilo', 0):,.2f}"))
        self.table.setItem(
            row_pos, 3, QTableWidgetItem(f"{data.get('material_sell_price_per_kilo', 0):,.2f}")
        )
        self.table.setItem(row_pos, 4, QTableWidgetItem(f"{data.get('total_price', 0):,.2f}"))
        self.table.setItem(row_pos, 5, QTableWidgetItem(f"{data.get('total_profit', 0):,.2f}"))
        delete_button_widget = self.create_delete_button_widget(row_pos)
        self.table.setCellWidget(row_pos, 6, delete_button_widget)

    def create_delete_button_widget(self, row):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        delete_button = QPushButton("حذف")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(lambda: self.handle_delete_row(row))
        layout.addWidget(delete_button)
        return container

    def handle_delete_row(self, row):
        """Handles deleting a material from the invoice."""
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
            payload = {"id": material_id}
            url = f"{BACKEND_BASE_URL}/mixtures/materials/"
            self._start_delete_request(url, payload, row)

    def _start_delete_request(self, url, payload, row):
        self._set_loading(True)
        self.delete_thread = QThread()
        self.delete_worker = ApiWorker("DELETE", url, payload)
        self.delete_worker.moveToThread(self.delete_thread)

        self.delete_worker.success.connect(
            lambda response, r=row: self.on_delete_material_success(response, r)
        )
        self.delete_worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))

        self.delete_worker.finished.connect(self.delete_thread.quit)
        self.delete_worker.finished.connect(self.delete_worker.deleteLater)
        self.delete_thread.finished.connect(self.delete_thread.deleteLater)
        self.delete_worker.finished.connect(lambda: self._set_loading(False))
        self.delete_thread.started.connect(self.delete_worker.run)
        self.delete_thread.start()

    def on_delete_material_success(self, response_data, row):
        """Removes the row from the table and updates totals after successful API call."""
        self.table.removeRow(row)
        self.update_totals()
        QMessageBox.information(self, "نجاح", "تم حذف الخامة من الفاتورة.")

    def update_totals(self):
        total_cost, total_profit = 0.0, 0.0
        for row in range(self.table.rowCount()):
            try:
                total_cost += float(self.table.item(row, 4).text().replace(",", ""))
                total_profit += float(self.table.item(row, 5).text().replace(",", ""))
            except (ValueError, AttributeError):
                continue
        self.total_cost_display.setText(f"{total_cost:,.2f}")
        self.total_profit_display.setText(f"{total_profit:,.2f}")

    def clear_form_inputs(self):
        self.material_combo.setCurrentIndex(-1)
        self.material_combo.lineEdit().clear()
        self.quantity_input.clear()

    def get_materials_data(self):
        """Returns the data currently in the table and the total cost."""
        # This method is called by the parent (MixesUI) to get the final data.
        materials = []
        for row in range(self.table.rowCount()):
            materials.append(
                {
                    "material_name": self.table.item(row, 0).text(),
                    "quantity_used": self.table.item(row, 1).text(),
                    # Add other data if needed by the final step
                }
            )
        total_cost = float(self.total_cost_display.text().replace(",", ""))
        return materials, total_cost

    def _set_loading(self, is_loading):
        self.material_combo.setEnabled(not is_loading)
        self.quantity_input.setDisabled(is_loading)
        self.add_material_button.setDisabled(is_loading)
        self.continue_button.setDisabled(is_loading)
        self.cancel_button.setDisabled(is_loading)
        self.show_all_button.setDisabled(is_loading)
        self.add_material_button.setText("جاري..." if is_loading else "إضافة")

    def on_fetch_error(self, message):
        self.material_combo.clear()
        self.material_combo.addItem("فشل التحميل")
        QMessageBox.warning(self, "خطأ", f"فشل في جلب قائمة الخامات:\n{message}")

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

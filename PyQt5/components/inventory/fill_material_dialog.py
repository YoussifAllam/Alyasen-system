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
    QMessageBox,
)
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import qtawesome as qta
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL


class MaterialInfoWorker(QObject):
    """Worker to fetch material names and details."""

    finished = pyqtSignal()
    success_names = pyqtSignal(list)
    success_details = pyqtSignal(dict)  # For fetching qty/unit
    error = pyqtSignal(str)

    def __init__(self, url, fetch_type="names"):
        super().__init__()
        self.url = url
        self.fetch_type = fetch_type

    @pyqtSlot()
    def run(self):
        try:
            response = request("GET", self.url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if self.fetch_type == "names":
                    self.success_names.emit(data.get("data", []))
                else:
                    self.success_details.emit(data.get("data", {}))
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException:
            self.error.emit("فشل الاتصال بالخادم.")
        finally:
            self.finished.emit()


class FillTransferWorker(QObject):
    """Worker to handle the Transfer and Payment API calls sequentially."""

    finished = pyqtSignal()
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, fill_payload, payment_payload):
        super().__init__()
        self.fill_payload = fill_payload
        self.payment_payload = payment_payload
        self.fill_url = f"{BACKEND_BASE_URL}/material-warehouse/fill-materials/"
        self.payment_url = f"{BACKEND_BASE_URL}/segmental-salling/SegmentalPayment/"

    @pyqtSlot()
    def run(self):
        try:
            # 1. Execute Fill Material Request
            response_fill = request("PATCH", self.fill_url, json=self.fill_payload, timeout=15)
            if response_fill.status_code not in [200, 201]:
                self.error.emit(f"فشل في عملية التعبئة: {response_fill.text}")
                return

            # 2. Execute Payment Request (Only if amount is valid and not zero)
            amount_str = self.payment_payload.get("amount", "0")
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0.0

            if amount != 0:
                response_pay = request("POST", self.payment_url, json=self.payment_payload, timeout=15)
                if response_pay.status_code not in [200, 201]:
                    self.error.emit(f"تمت التعبئة ولكن فشل تسجيل الدفع: {response_pay.text}")
                    return

            self.success.emit()

        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class FillMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تعبئة خامات")
        self.setMinimumSize(500, 600)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel("تعبئة (نقل كمية)")
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        self.main_layout.addWidget(self.title_bar)

        # Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(15)

        # --- Source Material ---
        content_layout.addWidget(QLabel("من (المصدر):"))
        source_layout = QHBoxLayout()
        self.source_combo = QComboBox()
        self.source_combo.setEditable(False)  # Changed to False
        self.source_info_display = QLineEdit()
        self.source_info_display.setPlaceholderText("الكمية الحالية والوحدة")
        self.source_info_display.setReadOnly(True)
        source_layout.addWidget(self.source_combo, 2)
        source_layout.addWidget(self.source_info_display, 1)
        content_layout.addLayout(source_layout)

        # --- Transfer Quantity & Source Price ---
        content_layout.addWidget(QLabel("الكمية المراد نقلها وسعر الوحدة:"))
        transfer_layout = QHBoxLayout()
        self.transfer_qty_input = QLineEdit()
        self.transfer_qty_input.setPlaceholderText("الكمية")
        self.source_price_input = QLineEdit()
        self.source_price_input.setPlaceholderText("سعر الوحدة (المصدر)")

        transfer_layout.addWidget(self.transfer_qty_input)
        transfer_layout.addWidget(self.source_price_input)
        content_layout.addLayout(transfer_layout)

        # --- Arrow ---
        arrow_label = QLabel("⬇")
        arrow_label.setAlignment(Qt.AlignCenter)
        arrow_label.setStyleSheet("font-size: 24px; color: #819A91; font-weight: bold;")
        content_layout.addWidget(arrow_label)

        # --- Destination Material ---
        content_layout.addWidget(QLabel("إلى (الوجهة):"))
        dest_layout = QHBoxLayout()
        self.dest_combo = QComboBox()
        self.dest_combo.setEditable(False)  # Changed to False
        self.dest_info_display = QLineEdit()
        self.dest_info_display.setPlaceholderText("الكمية الحالية")
        self.dest_info_display.setReadOnly(True)
        dest_layout.addWidget(self.dest_combo, 2)
        dest_layout.addWidget(self.dest_info_display, 1)
        content_layout.addLayout(dest_layout)

        # --- New Quantity (Calculated) & Dest Price ---
        content_layout.addWidget(QLabel("الكمية المراد اضافتها وسعر الوحدة (الوجهة):"))  # Changed label text
        new_qty_layout = QHBoxLayout()
        self.new_qty_display = QLineEdit()
        self.new_qty_display.setPlaceholderText("الكمية الجديدة")

        self.dest_price_input = QLineEdit()
        self.dest_price_input.setPlaceholderText("سعر الوحدة (الوجهة)")

        new_qty_layout.addWidget(self.new_qty_display)
        new_qty_layout.addWidget(self.dest_price_input)
        content_layout.addLayout(new_qty_layout)

        # --- Price Difference ---
        content_layout.addWidget(QLabel("فرق السعر الإجمالي:"))
        self.price_diff_input = QLineEdit()
        self.price_diff_input.setPlaceholderText("سيتم الحساب تلقائياً")
        self.price_diff_input.setReadOnly(True)
        content_layout.addWidget(self.price_diff_input)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("تأكيد النقل")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save)  # Connected
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        content_layout.addLayout(button_layout)

        self.main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        # Data Loading
        self.materials_data = {}  # To store name -> {id, qty, unit} map if possible, or fetch on change
        self.source_id = None
        self.dest_id = None

        self.fetch_materials()

        # Connect signals
        self.source_combo.currentIndexChanged.connect(self.update_source_info)
        self.dest_combo.currentIndexChanged.connect(self.update_dest_info)

        # Connect calculation signals
        self.transfer_qty_input.textChanged.connect(self.calculate_all)
        self.source_price_input.textChanged.connect(self.calculate_all)
        self.dest_price_input.textChanged.connect(self.calculate_all)

    def fetch_materials(self):
        """Fetches material names to populate combos."""
        url = f"{BACKEND_BASE_URL}/material-warehouse/materials-names/"
        self.thread = QThread()
        self.worker = MaterialInfoWorker(url, fetch_type="names")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success_names.connect(self.populate_combos)
        self.worker.error.connect(lambda msg: QMessageBox.warning(self, "خطأ", msg))
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def populate_combos(self, names):
        self.source_combo.clear()
        self.dest_combo.clear()
        self.source_combo.addItems(names)
        self.dest_combo.addItems(names)
        self.source_combo.setCurrentIndex(-1)
        self.dest_combo.setCurrentIndex(-1)

    def update_source_info(self):
        name = self.source_combo.currentText()
        if not name:
            return
        self.fetch_material_details(name, is_source=True)

    def update_dest_info(self):
        name = self.dest_combo.currentText()
        if not name:
            return
        self.fetch_material_details(name, is_source=False)

    def fetch_material_details(self, name, is_source):
        # We need an endpoint to get details by name.
        # Using filter endpoint based on previous files:
        url = f"{BACKEND_BASE_URL}/material-warehouse/filter/?material_name={name}"

        # We need a new thread/worker to avoid blocking
        thread = QThread()
        worker = MaterialInfoWorker(url, fetch_type="details")
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        # Define a closure or use lambda to pass is_source
        worker.success_details.connect(lambda data: self.on_details_fetched(data, is_source))
        worker.finished.connect(thread.quit)

        # Keep reference to avoid GC
        if is_source:
            self.source_thread = thread
            self.source_worker = worker
        else:
            self.dest_thread = thread
            self.dest_worker = worker

        thread.start()

    def on_details_fetched(self, data, is_source):
        # API response structure based on provided example:
        # { "status": "success", "data": { "status": "success", "data": { "count": X, "results": [...] } } }

        # Parse nested structure
        inner_data = data.get("data", {})
        results = inner_data.get("results", [])

        if not results and isinstance(data, list):
            results = data  # Fallback

        if results:
            material = results[0]
            # Extract fields
            material_id = material.get("id")
            qty = material.get("quantity_in_unit") or material.get("quantity_in_kilo", 0)
            unit = material.get("unit", "")

            if is_source:
                self.source_id = material_id
                self.source_qty = float(qty)
                self.source_info_display.setText(f"{qty} {unit}")
            else:
                self.dest_id = material_id
                self.dest_qty = float(qty)
                self.dest_info_display.setText(f"{qty} {unit}")
                self.calculate_all()  # Recalculate if dest changes

    def calculate_all(self):
        """Calculates new quantity and price difference."""
        try:
            qty_text = self.transfer_qty_input.text()
            transfer_qty = float(qty_text) if qty_text else 0.0

            # Calculate Price Difference
            # (Price1 * Qty) - (Price2 * Qty)
            p1_text = self.source_price_input.text()
            p2_text = self.dest_price_input.text()

            price1 = float(p1_text) if p1_text else 0.0
            price2 = float(p2_text) if p2_text else 0.0

            total_val_source = transfer_qty * price1
            total_val_dest = transfer_qty * price2

            diff = total_val_source - total_val_dest
            self.price_diff_input.setText(f"{diff:.2f}")

        except ValueError:
            # Handle invalid input (e.g. non-numeric) gracefully
            if not self.transfer_qty_input.text():
                self.new_qty_display.setText(str(getattr(self, "dest_qty", 0)))
            # self.price_diff_input.setText("ERROR") # Optional

    def handle_save(self):
        """Prepares data and starts the save worker."""
        source_name = self.source_combo.currentText()
        dest_name = self.dest_combo.currentText()
        source_qty = self.transfer_qty_input.text().strip()

        # NOTE: Using the value from new_qty_display as requested ("target_added_qty = new_qty_layout")
        # Assuming the API logic on backend handles this value logic.
        target_added_qty = self.new_qty_display.text().strip()

        price_diff = self.price_diff_input.text().strip()

        if not source_name or not dest_name or not source_qty:
            QMessageBox.warning(self, "خطأ", "الرجاء تعبئة جميع الحقول المطلوبة.")
            return

        fill_payload = {
            "source_material_name": source_name,
            "target_material_name": dest_name,
            "source_qty": source_qty,
            "target_added_qty": target_added_qty,
        }

        payment_payload = {"amount": price_diff}

        self.save_button.setDisabled(True)
        self.save_thread = QThread()
        self.save_worker = FillTransferWorker(fill_payload, payment_payload)
        self.save_worker.moveToThread(self.save_thread)
        self.save_thread.started.connect(self.save_worker.run)
        self.save_worker.success.connect(self.on_save_success)
        self.save_worker.error.connect(self.on_save_error)
        self.save_worker.finished.connect(self.save_thread.quit)
        self.save_worker.finished.connect(self.save_worker.deleteLater)
        self.save_worker.finished.connect(lambda: self.save_button.setEnabled(True))
        self.save_thread.start()

    def on_save_success(self):
        QMessageBox.information(self, "نجاح", "تمت العملية بنجاح.")
        self.accept()

    def on_save_error(self, msg):
        QMessageBox.critical(self, "خطأ", msg)

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

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
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
from .choose_mixture_dialog import ChooseMixtureDialog
from .final_invoice_dialog import SaveInvoiceDialog


class ApiWorker(QObject):
    """Generic worker for single API requests in this dialog."""

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
            elif response.status_code == 204 and self.method == "DELETE":
                self.success.emit({"status": "deleted"})
            else:
                self.error.emit(f"خطأ من الخادم: {response.text}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class MoveFromWarehouseWorker(QObject):
    """Worker to sequentially move items from warehouse via API."""

    finished = pyqtSignal()
    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, payload):
        super().__init__()
        self.payload = payload
        self.url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/move-from-warehouse/"

    @pyqtSlot()
    def run(self):
        try:
            response = request("POST", self.url, json=self.payload, timeout=15)
            if response.status_code not in [200, 201]:
                try:
                    error_data = response.json()
                    if "خطأ" in error_data:
                        self.error.emit(error_data["خطأ"])
                        return
                    else:
                        self.error.emit(response.text)
                        return
                except Exception:
                    self.error.emit(response.text)
                    return
            self.success.emit()
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class AddMixtureDialog(QDialog):
    def __init__(self, invoice_num, parent=None):
        super().__init__(parent)
        self.invoice_num = invoice_num
        self.selected_mixture_id = None

        self.setWindowTitle(f"إضافة منتجات للفاتورة: {invoice_num}")

        # Increase size here
        self.setMinimumSize(1000, 800)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Applying stylesheet for bigger fonts
        self.setStyleSheet(
            """
            QLabel { font-size: 16px; font-weight: bold; }
            QLineEdit { font-size: 16px; padding: 5px; }
            QPushButton { font-size: 16px; padding: 8px; }
            QTableWidget { font-size: 18px; }
            QHeaderView::section { font-size: 18px; font-weight: bold; }
            QGroupBox { font-size: 16px; font-weight: bold; }
        """
        )

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 10, 0)
        title_text = QLabel(f"إضافة منتجات للفاتورة رقم: {invoice_num}")
        title_text.setObjectName("titleBarText")
        # Ensure title bar text is also styled if not covered by global
        title_text.setStyleSheet("font-size: 18px; font-weight: bold;")

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

        # Form Group
        form_group = QGroupBox("إضافة منتج")
        form_layout = QHBoxLayout(form_group)

        self.mixture_name_input = QLineEdit(placeholderText="اسم المنتج")
        self.mixture_name_input.setReadOnly(True)

        self.choose_mixture_button = QPushButton("اختر منتج")
        self.choose_mixture_button.clicked.connect(self.open_choose_mixture_dialog)

        self.quantity_input = QLineEdit(placeholderText="الكمية")

        # New Label for Unit
        self.unit_label = QLabel("")
        self.unit_label.setStyleSheet("color: #666; font-size: 18px; margin-left: 5px; font-weight: bold;")

        self.add_button = QPushButton("إضافة")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.handle_add_mixture)

        form_layout.addWidget(self.mixture_name_input, 2)
        form_layout.addWidget(self.choose_mixture_button)
        form_layout.addWidget(self.quantity_input, 1)
        form_layout.addWidget(self.unit_label)  # Add unit label to layout
        form_layout.addWidget(self.add_button)
        content_layout.addWidget(form_group)

        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Changed column count
        self.table.setHorizontalHeaderLabels(["الاسم", "الوحدة", "الكمية", ""])  # Changed headers
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(60)
        content_layout.addWidget(self.table, 1)

        bottom_layout = QHBoxLayout()
        # Removed total displays
        bottom_layout.addStretch()
        self.save_button = QPushButton("متابعة")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.handle_save_and_continue)
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.handle_cancel)
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.cancel_button)
        content_layout.addLayout(bottom_layout)
        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        # Initial Fetch
        self.fetch_invoice_mixtures()

    def handle_save_and_continue(self):
        """Validates table, gathers payload, and starts the move-from-warehouse process."""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "خطأ", "لا يمكن المتابعة بفاتورة فارغة.")
            return

        payload = {
            "invoice_num": self.invoice_num,
        }

        self._start_move_request(payload)

    def _start_move_request(self, payload):
        self._set_loading(True, "جاري النقل من المخزن...")
        self.move_thread = QThread()
        self.move_worker = MoveFromWarehouseWorker(payload)
        self.move_worker.moveToThread(self.move_thread)

        self.move_thread.started.connect(self.move_worker.run)
        self.move_worker.success.connect(self.on_move_success)  # Changed to specific handler
        self.move_worker.error.connect(self.on_api_error)

        self.move_worker.finished.connect(self.move_thread.quit)
        self.move_worker.finished.connect(lambda: self._set_loading(False))
        self.move_thread.start()

    def on_move_success(self):
        """Called when items are successfully moved from warehouse."""
        # Open the SaveInvoiceDialog
        dialog = SaveInvoiceDialog(self.invoice_num, self)
        if dialog.exec_() == QDialog.Accepted:
            self.accept()  # Close this dialog if save was successful

    def handle_cancel(self):
        """Asks for confirmation and deletes the invoice if the user agrees."""
        reply = QMessageBox.question(
            self,
            "تأكيد الإلغاء",
            "هل أنت متأكد من أنك تريد إلغاء هذه الفاتورة؟ سيتم حذفها نهائياً.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")

            payload = {"invoice_num": self.invoice_num, "username": username}
            url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/invoices/"
            self._start_api_request("DELETE", url, payload=payload, on_success=self.on_cancel_success)

    def on_cancel_success(self, response_data):
        """Handles the successful deletion of the invoice."""
        QMessageBox.information(self, "نجاح", "تم إلغاء الفاتورة بنجاح.")
        self.reject()  # Close the dialog with a reject signal

    def open_choose_mixture_dialog(self):
        dialog = ChooseMixtureDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Unpack 3 values: id, name, unit
            mixture_id, mixture_name, mixture_unit = dialog.get_selected_mixture()
            self.selected_mixture_id = mixture_id
            self.mixture_name_input.setText(mixture_name)
            self.unit_label.setText(mixture_unit if mixture_unit else "")

    def fetch_invoice_mixtures(self):
        url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/materials/?invoice_num={self.invoice_num}"
        self._start_api_request("GET", url, on_success=self.populate_table, thread_name="fetch_mixtures")

    def populate_table(self, response_data):
        data_obj = response_data.get("data", {}).get("data", {})
        results = data_obj.get("results", [])
        self.table.setRowCount(0)
        for mixture in results:
            self.add_row_to_table(mixture)
        # self.update_totals() # No longer needed

    def handle_add_mixture(self):
        if self.selected_mixture_id is None:
            QMessageBox.warning(self, "خطأ", "الرجاء اختيار منتج أولاً.")
            return
        quantity_str = self.quantity_input.text().strip()
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال كمية موجبة وصالحة.")
            return

        payload = {
            "material_id": self.selected_mixture_id,
            "invoice_num": self.invoice_num,
            "quantity_in_unit": quantity,  # Changed from quantity_in_kilo
        }

        url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/materials/"

        self._start_api_request(
            "POST", url, payload=payload, on_success=self.on_add_mixture_success, thread_name="add_mixture"
        )

    def on_add_mixture_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تمت إضافة المنتج للفاتورة.")
        self.fetch_invoice_mixtures()
        self.clear_form()

    def add_row_to_table(self, mixture_data):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        item_id = mixture_data.get("id")

        # Get name from 'material_name' or 'mixture_name' to be safe
        name = mixture_data.get("material_name") or mixture_data.get("mixture_name", "")
        # Get unit - ensure we check both potential keys or default
        unit = mixture_data.get("unit") or mixture_data.get("material_unit", "")

        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, item_id)

        items = [
            name_item,
            QTableWidgetItem(str(unit)),
            QTableWidgetItem(f"{mixture_data.get('quantity_in_unit', 0):,.2f}"),
        ]
        for i, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_pos, i, item)

        del_btn = self.create_delete_button(item_id)
        self.table.setCellWidget(row_pos, 3, del_btn)

    def create_delete_button(self, mixture_id):
        btn = QPushButton("حذف")
        btn.setObjectName("dangerButton")
        btn.setMinimumHeight(30)
        btn.setMaximumHeight(40)
        btn.clicked.connect(lambda: self.handle_delete_mixture(mixture_id))
        return btn

    def handle_delete_mixture(self, mixture_id):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا المنتج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        payload = {"invoice_num": self.invoice_num, "material_id": mixture_id}
        if reply == QMessageBox.Yes:
            url = f"{BACKEND_BASE_URL}/segmental-salling/invoice/materials/"
            self._start_api_request(
                "DELETE",
                url,
                on_success=self.on_delete_success,
                thread_name="delete_mixture",
                payload=payload,
            )

    def on_delete_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم حذف المنتج بنجاح.")
        self.fetch_invoice_mixtures()

    def handle_delete_row(self, row):
        self.table.removeRow(row)
        # self.update_totals() # Removed

    # Removed update_totals function

    def clear_form(self):
        self.mixture_name_input.clear()
        self.quantity_input.clear()
        self.unit_label.clear()  # Clear unit label
        self.selected_mixture_id = None

    def _start_api_request(self, method, url, payload=None, on_success=None, thread_name="api"):
        self._set_loading(True)
        thread = QThread()
        worker = ApiWorker(method, url, payload)
        worker.moveToThread(thread)
        setattr(self, f"{thread_name}_thread", thread)
        setattr(self, f"{thread_name}_worker", worker)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(lambda: self._set_loading(False))
        if on_success:
            worker.success.connect(on_success)
        worker.error.connect(self.on_api_error)
        thread.started.connect(worker.run)
        thread.start()

    def _set_loading(self, is_loading, message="جاري..."):
        self.choose_mixture_button.setDisabled(is_loading)
        self.quantity_input.setDisabled(is_loading)
        self.add_button.setDisabled(is_loading)
        self.save_button.setDisabled(is_loading)
        self.cancel_button.setDisabled(is_loading)
        self.save_button.setText(message if is_loading else "متابعة")

    def on_api_error(self, message):
        self._set_loading(False)
        QMessageBox.critical(self, "خطأ", message)

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

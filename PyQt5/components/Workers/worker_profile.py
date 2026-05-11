from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGridLayout,
    QLineEdit,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, pyqtSlot, QSettings
from requests import request, get, exceptions
import os

from ..Main_Ui_Components.constant import BACKEND_BASE_URL, BASE_DIR
from .update_info_dialog import UpdateWorkerDialog
from .absence_dialog import AbsenceDialog
from .deduction_dialog import DeductionDialog
from .advance_dialog import AdvanceDialog
from .attendance_log_dialog import AttendanceLogDialog
from .alternative_dialog import AlternativesDialog

from ..worker_report_generator.report_generator import ArabicSalaryReport


class ApiWorker(QObject):
    """Worker for handling API requests for the profile page."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    image_success = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, files=None, response_type="json"):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.files = files
        self.response_type = response_type

    @pyqtSlot()
    def run(self):
        try:
            if self.method == "GET" and self.response_type == "image":
                response = get(self.url, timeout=10)
            elif self.method in ["PATCH", "DELETE"] and self.files:
                response = request(
                    self.method,
                    self.url,
                    data=self.payload,
                    files=self.files,
                    timeout=15,
                )
            else:
                response = request(self.method, self.url, json=self.payload, timeout=15)

            if response.status_code in [200, 201]:
                if self.response_type == "json":
                    self.success.emit(response.json())
                else:
                    image = QImage()
                    image.loadFromData(response.content)
                    self.image_success.emit(QPixmap.fromImage(image))
            elif response.status_code == 204 and self.method == "DELETE":
                self.success.emit({"status": "deleted"})
            else:
                self.error.emit(f"خطأ من الخادم: {response.text}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class WorkerProfileUI(QWidget):
    back_to_list_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.worker_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Header ---
        header_layout = QHBoxLayout()
        self.name_label = QLabel("ملف العامل")
        self.name_label.setObjectName("mainHeader")
        back_button = QPushButton("العودة للقائمة")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        main_layout.addLayout(header_layout)

        # --- Top Section: Picture, Basic Info, and Actions ---
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(20)
        self.profile_pic_card = self.create_picture_card()
        top_section_layout.addWidget(self.profile_pic_card)
        basic_info_card = self.create_basic_info_card()
        top_section_layout.addWidget(basic_info_card, 1)
        actions_card = self.create_actions_card()
        top_section_layout.addWidget(actions_card)
        main_layout.addLayout(top_section_layout)

        # --- Bottom Section: Financial and Attendance Stats ---
        stats_grid_layout = QGridLayout()
        stats_grid_layout.setSpacing(20)
        attendance_card = self.create_attendance_card()
        financial_card = self.create_financial_card()
        stats_grid_layout.addWidget(attendance_card, 0, 0)
        stats_grid_layout.addWidget(financial_card, 0, 1)
        main_layout.addLayout(stats_grid_layout)

    def create_picture_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        self.profile_pic_label = QLabel("Loading...")
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setFixedSize(300, 300)
        layout.addWidget(self.profile_pic_label)
        return card

    def create_basic_info_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        layout.setSpacing(15)
        self.id_display = QLineEdit(readOnly=True)
        self.name_display = QLineEdit(readOnly=True)
        self.phone_display = QLineEdit(readOnly=True)
        self.job_display = QLineEdit(readOnly=True)
        self.start_date_display = QLineEdit(readOnly=True)
        layout.addWidget(QLabel("الرمز التعريفي :"), 0, 0)
        layout.addWidget(self.id_display, 0, 1)
        layout.addWidget(QLabel("الاسم:"), 1, 0)
        layout.addWidget(self.name_display, 1, 1)
        layout.addWidget(QLabel("رقم الهاتف:"), 2, 0)
        layout.addWidget(self.phone_display, 2, 1)
        layout.addWidget(QLabel("الوظيفة:"), 3, 0)
        layout.addWidget(self.job_display, 3, 1)
        layout.addWidget(QLabel("تاريخ بدء العمل:"), 4, 0)
        layout.addWidget(self.start_date_display, 4, 1)
        return card

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        # Existing Buttons
        update_btn = QPushButton("تعديل البيانات")
        update_btn.setObjectName("primaryButton")
        update_btn.clicked.connect(self.handle_update_worker)
        layout.addWidget(update_btn)

        absence_btn = QPushButton("الغياب")
        absence_btn.clicked.connect(self.handle_absence)
        layout.addWidget(absence_btn)

        advance_btn = QPushButton("السلفيات")
        advance_btn.clicked.connect(self.handle_advance)
        layout.addWidget(advance_btn)

        deduction_btn = QPushButton("الخصم")
        deduction_btn.clicked.connect(self.handle_deduction)
        layout.addWidget(deduction_btn)

        alternatives_btn = QPushButton("مبالغ البدائل")
        alternatives_btn.clicked.connect(self.handle_alternatives)
        layout.addWidget(alternatives_btn)

        attendance_log_btn = QPushButton("سجل الحضور والأنصراف")
        attendance_log_btn.clicked.connect(self.handle_show_attendance_log)
        layout.addWidget(attendance_log_btn)

        layout.addStretch()

        finalize_button = QPushButton("تصفية حساب العامل")
        finalize_button.setObjectName("dangerButton")
        finalize_button.clicked.connect(self.handle_finalize_shift)

        delete_button = QPushButton("حذف العامل")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.handle_delete_worker)

        self.btn_print_report = QPushButton("طباعة تقرير العامل")
        self.btn_print_report.clicked.connect(self.handle_print_report)
        layout.addWidget(self.btn_print_report)

        layout.addWidget(finalize_button)
        layout.addWidget(delete_button)

        layout.addStretch()
        return card

    def handle_print_report(self):
        """Fetches salary report data and generates a PDF."""
        if not self.worker_id:
            QMessageBox.warning(self, "خطأ", "لا يوجد عامل محدد لطباعة التقرير.")
            return

        url = f"{BACKEND_BASE_URL}/workers/salary-report/?worker_id={self.worker_id}"
        self._start_api_request("GET", url, on_success=self.on_report_fetch_success)

    def on_report_fetch_success(self, api_response):
        """Generates the PDF report using the fetched data."""
        try:
            filename = f"{BASE_DIR}/invoices/worker_salary_report_{self.worker_id}.pdf"
            report = ArabicSalaryReport()
            report.generate_report_from_api(api_response, filename)
            QMessageBox.information(self, "نجاح", f"تم إنشاء التقرير بنجاح: {filename}")
            # open the file automatically:
            os.startfile(filename)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء التقرير: {str(e)}")

    def handle_print_attendance_report(self):
        """Placeholder handler for printing the worker report."""
        if not self.worker_id:
            QMessageBox.warning(self, "خطأ", "لا يوجد عامل محدد لطباعة التقرير.")
            return

        QMessageBox.information(
            self, "طباعة", f"سيتم طباعة تقرير للعامل ID: {self.worker_id}"
        )

    def handle_alternatives(self):
        """Opens the dialog for managing worker alternatives (payments)."""
        if not self.worker_id:
            return
        worker_name = self.name_display.text()

        # Use the newly created dialog
        dialog = AlternativesDialog(worker_name, self.worker_id, self)

        # Connect to refresh data when a change is made
        dialog.data_changed.connect(self.refresh_worker_data)
        dialog.exec_()

    def handle_finalize_shift(self):
        """Asks for confirmation and starts the finalize shift API call."""
        if not self.worker_id:
            return
        reply = QMessageBox.question(
            self,
            "تأكيد تصفية الحساب",
            f"هل أنت متأكد من تصفية حساب العامل '{self.name_display.text()}'؟ هذا الإجراء لا يمكن التراجع عنه.",  # noqa
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            payload = {"worker_id": self.worker_id}
            url = f"{BACKEND_BASE_URL}/workers/finish-shift/"
            self._start_api_request(
                "POST", url, payload=payload, on_success=self.on_finalize_success
            )

    def on_finalize_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تمت تصفية حساب العامل بنجاح.")
        self.refresh_worker_data()  # Refresh data to show zeroed out values

    def handle_advance(self):
        if not self.worker_id:
            return
        worker_name = self.name_display.text()
        dialog = AdvanceDialog(worker_name, self.worker_id, self)
        dialog.data_changed.connect(self.refresh_worker_data)
        dialog.exec_()

    def handle_absence(self):
        """Opens the absence dialog and connects its data_changed signal."""
        if not self.worker_id:
            return
        worker_name = self.name_display.text()
        dialog = AbsenceDialog(worker_name, self.worker_id, self)
        dialog.data_changed.connect(self.refresh_worker_data)
        dialog.exec_()

    def handle_deduction(self):
        """Opens the dialog for managing worker deductions."""
        if not self.worker_id:
            return
        worker_name = self.name_display.text()
        dialog = DeductionDialog(worker_name, self.worker_id, self)
        dialog.data_changed.connect(self.refresh_worker_data)
        dialog.exec_()

    def handle_update_worker(self):
        if not self.worker_id:
            return
        current_data = {
            "name": self.name_display.text(),
            "phone": self.phone_display.text(),
            "job": self.job_display.text(),
            "work_start_date": self.start_date_display.text(),
            "daily_salary": self.daily_salary_display.text().replace(",", ""),
        }
        dialog = UpdateWorkerDialog(self.worker_id, current_data, self)
        dialog.update_successful.connect(self.on_update_success)
        dialog.exec_()

    def refresh_worker_data(self):
        """Fetches the latest worker info from the API."""
        if not self.worker_id:
            return
        url = f"{BACKEND_BASE_URL}/workers/info/?worker_id={self.worker_id}"
        self._start_api_request("GET", url, on_success=self.update_data)

    def create_attendance_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)
        self.attendance_display = QLineEdit(readOnly=True)
        self.absence_display = QLineEdit(readOnly=True)
        self.on_vacation_checkbox = QCheckBox("هل العامل في أجازة ؟")
        self.on_vacation_checkbox.setObjectName("vacationcheckbox")
        self.on_vacation_checkbox.toggled.connect(self.handle_vacation_status_change)
        layout.addWidget(QLabel("أيام الحضور:"), 0, 0)
        layout.addWidget(self.attendance_display, 0, 1)
        layout.addWidget(QLabel("أيام الغياب:"), 1, 0)
        layout.addWidget(self.absence_display, 1, 1)
        layout.addWidget(self.on_vacation_checkbox, 2, 0, 1, 2)
        return card

    def handle_vacation_status_change(self, is_checked):
        """Sends an API request to update the worker's vacation status."""
        if not self.worker_id:
            return

        payload = {"worker_id": self.worker_id, "is_in_vacation": is_checked}
        url = f"{BACKEND_BASE_URL}/workers/absence/"
        self._start_api_request(
            "PATCH", url, payload=payload, on_success=self.on_vacation_status_updated
        )

    def on_vacation_status_updated(self, response_data):
        QMessageBox.information(self, "نجاح", "تم تحديث حالة الأجازة للعامل.")
        self.refresh_worker_data()

    def create_financial_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QGridLayout(card)

        # Existing Line Edits
        self.daily_salary_display = QLineEdit(readOnly=True)
        self.advances_display = QLineEdit(readOnly=True)
        self.deductions_display = QLineEdit(readOnly=True)
        self.alternatives_display = QLineEdit(readOnly=True)
        self.final_salary_display = QLineEdit(readOnly=True)
        self.final_salary_display.setObjectName("netProfitResult")
        layout.addWidget(QLabel("الراتب اليومي:"), 0, 0)
        layout.addWidget(self.daily_salary_display, 0, 1)
        layout.addWidget(QLabel("إجمالي السلفيات:"), 1, 0)
        layout.addWidget(self.advances_display, 1, 1)
        layout.addWidget(QLabel("إجمالي الخصومات:"), 2, 0)
        layout.addWidget(self.deductions_display, 2, 1)
        layout.addWidget(QLabel("اجمالي مبلغ البدائل:"), 3, 0)
        layout.addWidget(self.alternatives_display, 3, 1)
        layout.addWidget(QLabel("الراتب بعد الخصم و السلف:"), 4, 0)
        layout.addWidget(self.final_salary_display, 4, 1)
        return card

    def handle_delete_worker(self):
        """Asks for confirmation and starts the delete API call."""
        if not self.worker_id:
            return

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من أنك تريد حذف '{self.name_display.text()}'؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "unknown_user")

            payload = {"worker_id": self.worker_id, "username": username}
            url = f"{BACKEND_BASE_URL}/workers/workers/"
            self._start_api_request(
                "DELETE", url, payload=payload, on_success=self.on_delete_success
            )

    def on_update_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم تحديث بيانات العامل بنجاح.")
        # self.update_data(response_data)
        self.refresh_worker_data()

    def on_delete_success(self, response_data):
        QMessageBox.information(self, "نجاح", "تم حذف العامل بنجاح.")
        self.back_to_list_requested.emit()

    def update_data(self, worker_data):
        data = worker_data.get("data", {})

        if "worker_id" in data:
            self.worker_id = data.get("worker_id")
            self.id_display.setText(str(self.worker_id))

        self.name_label.setText(f"ملف العامل: {data.get('name', 'N/A')}")
        self.name_display.setText(data.get("name", "N/A"))
        self.phone_display.setText(data.get("phone", "N/A"))
        self.job_display.setText(data.get("job", "N/A"))
        self.start_date_display.setText(data.get("work_start_date", "N/A"))
        self.daily_salary_display.setText(f"{data.get('daily_salary', 0):,.2f}")
        self.advances_display.setText(f"{data.get('total_advance', 0):,.2f}")
        self.deductions_display.setText(f"{data.get('total_deduction', 0):,.2f}")
        self.alternatives_display.setText(
            f"{data.get('total_alternatives_amount', 0):,.2f}"
        )
        self.final_salary_display.setText(f"{data.get('remaining_salary', 0):,.2f}")
        self.attendance_display.setText(str(data.get("total_days_of_work", 0)))
        self.absence_display.setText(str(data.get("total_days_of_absence", 0)))
        self.on_vacation_checkbox.setChecked(data.get("is_in_vacation", False))
        self.on_vacation_checkbox.blockSignals(True)
        self.on_vacation_checkbox.setChecked(data.get("is_in_vacation", False))
        self.on_vacation_checkbox.blockSignals(False)
        pic_url = data.get("profile_picture")
        if pic_url:
            self.fetch_image(pic_url)
        else:
            self.profile_pic_label.setText("No Image")

    def fetch_image(self, url):
        self.image_thread = QThread()
        self.image_worker = ApiWorker("GET", url, response_type="image")
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_worker.image_success.connect(self.set_image)
        self.image_worker.error.connect(lambda msg: self.profile_pic_label.setText(msg))
        self.image_worker.finished.connect(self.image_thread.quit)
        self.image_thread.start()

    def set_image(self, pixmap):
        self.profile_pic_label.setPixmap(
            pixmap.scaled(
                self.profile_pic_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _start_api_request(
        self, method, url, payload=None, files=None, on_success=None
    ):
        thread = QThread()
        worker = ApiWorker(method, url, payload, files)
        worker.moveToThread(thread)
        setattr(self, f"{method}_thread", thread)
        setattr(self, f"{method}_worker", worker)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        if on_success:
            worker.success.connect(on_success)
        worker.error.connect(lambda msg: QMessageBox.critical(self, "خطأ", msg))
        thread.started.connect(worker.run)
        thread.start()

    def handle_show_attendance_log(self):
        """Opens the dialog to show the worker's full attendance history."""
        if not self.worker_id:
            return
        worker_name = self.name_display.text()
        dialog = AttendanceLogDialog(worker_name, self.worker_id, self)
        dialog.exec_()

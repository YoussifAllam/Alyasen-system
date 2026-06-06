from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QMessageBox,
    QFrame,
    QWidget,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QObject, pyqtSlot, QSettings
from requests import get, exceptions, request
from PyQt5.QtGui import QPixmap, QImage
import qtawesome as qta

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..utils.api_errors import (
    format_request_exception,
    is_http_success,
    parse_api_error_response,
    parse_api_response,
)


class ApiWorker(QObject):
    """Worker for handling API requests."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    image_success = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, method, url, payload=None, data=None, response_type="json"):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload
        self.data = data
        self.response_type = response_type

    @pyqtSlot()
    def run(self):
        try:
            kwargs = {"timeout": 15}
            if self.payload:
                kwargs["json"] = self.payload
            if self.data:
                kwargs["data"] = self.data

            response = request(self.method, self.url, **kwargs)

            if self.response_type == "json":
                ok, result = parse_api_response(response)
                if ok:
                    self.success.emit(result)
                else:
                    self.error.emit(result)
            elif is_http_success(response.status_code):
                image = QImage()
                image.loadFromData(response.content)
                self.image_success.emit(QPixmap.fromImage(image))
            else:
                self.error.emit(parse_api_error_response(response))
        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        finally:
            self.finished.emit()


class ProjectSelectionDialog(QDialog):
    project_selected = pyqtSignal(dict)  # Emits full project dictionary

    def __init__(self, client_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle("اختيار مشروع")
        self.setMinimumSize(800, 600)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.all_projects = []
        self.filtered_projects = []
        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        # Main Container
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

        title_text = QLabel("اختيار مشروع")
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
        layout = QVBoxLayout(content_area)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        header_label = QLabel("برجاء اختيار المشروع الذي ترغب في العمل عليه:")
        header_label.setObjectName("dialogHeader")
        layout.addWidget(header_label)

        # Search and Filter Area
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث باسم المشروع أو المورد...")
        self.search_input.textChanged.connect(self.filter_projects)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "تأجير", "صناعي", "بيع", "حملة"])
        self.type_filter.currentTextChanged.connect(self.filter_projects)
        self.type_filter.setFixedWidth(150)

        filter_layout.addWidget(self.search_input, 1)
        filter_layout.addWidget(self.type_filter)
        layout.addLayout(filter_layout)

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["اسم المشروع", "اسم المورد"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.handle_next)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        self.next_button = QPushButton("اختيار")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.handle_next)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.next_button)

        layout.addLayout(btn_layout)

        self.main_layout.addWidget(content_area)
        self.main_layout.addStretch()

        # Set the main layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(container)
        self.old_pos = None

    def load_projects(self):
        url = f"{BACKEND_BASE_URL}/clients/projects/get-all-projects/"
        self.thread = QThread()
        self.worker = ApiWorker("GET", url)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_projects_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_projects_loaded(self, response_data):
        # Handle cases where data might be wrapped in a 'data' key or at root
        if "campaigns" in response_data or "projects" in response_data:
            data = response_data
        else:
            data = response_data.get("data", {})

        campaigns_data = data.get("campaigns", [])
        projects_data = data.get("projects", [])

        # If projects is empty but results exists, use results (legacy support)
        if not projects_data and "results" in data:
            projects_data = data.get("results", [])

        # Normalize campaigns to match project structure
        normalized_campaigns = []
        for campaign in campaigns_data:
            # Join suppliers list into a single string for display
            suppliers = campaign.get("suppliers", [])
            supplier_name = (
                ", ".join(suppliers) if isinstance(suppliers, list) else str(suppliers)
            )

            normalized_campaigns.append(
                {
                    "id": campaign.get("id"),
                    "name": campaign.get("name") or campaign.get("project_name", ""),
                    "supplier_name": supplier_name,
                    "project_type": "campaine",  # Aligns with UI type_map filter
                }
            )

        # Normalize projects - and handle project_type if it's missing but can be inferred
        normalized_projects = []
        for project in projects_data:
            p_copy = project.copy()
            # Ensure name field exists
            if not p_copy.get("name"):
                p_copy["name"] = p_copy.get("project_name", "")

            # If project_type is missing, try to infer it from the name for the filter to work
            if not p_copy.get("project_type"):
                name_lower = p_copy.get("name", "").lower()
                if "rent" in name_lower:
                    p_copy["project_type"] = "rent"
                elif "industrial" in name_lower:
                    p_copy["project_type"] = "industrial"
                elif "selling" in name_lower or "seeling" in name_lower:
                    p_copy["project_type"] = "selling"
            normalized_projects.append(p_copy)

        self.all_projects = normalized_projects + normalized_campaigns

        if not self.all_projects:
            QMessageBox.information(self, "تنبيه", "لا توجد مشاريع متاحة حالياً.")
            return

        self.filter_projects()
        self.next_button.setEnabled(True)

    def filter_projects(self):
        search_text = self.search_input.text().strip().lower()
        type_text = self.type_filter.currentText()

        # Mapping UI type to API type
        type_map = {
            "تأجير": "rent",
            "صناعي": "industrial",
            "بيع": "selling",
            "حملة": "campaine",
        }

        self.filtered_projects = []
        for project in self.all_projects:
            name = project.get("name", "").lower()

            # Robust supplier name lookup
            supplier_obj = project.get("supplier")
            if isinstance(supplier_obj, dict):
                supplier_name = supplier_obj.get("name", "").lower()
            else:
                supplier_name = project.get("supplier_name", "").lower()

            project_type = project.get("project_type", "")

            # Search Filter
            search_match = search_text in name or search_text in supplier_name

            # Type Filter
            type_match = True
            if type_text != "الكل":
                expected_type = type_map.get(type_text)
                type_match = project_type == expected_type

            if search_match and type_match:
                self.filtered_projects.append(project)

        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)
        for project in self.filtered_projects:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            name = project.get("name", "")

            # Robust supplier name lookup
            supplier_obj = project.get("supplier")
            if isinstance(supplier_obj, dict):
                supplier_name = supplier_obj.get("name", "غير محدد")
            else:
                supplier_name = project.get("supplier_name") or "غير محدد"

            name_item = QTableWidgetItem(name)
            supplier_item = QTableWidgetItem(supplier_name)

            name_item.setTextAlignment(Qt.AlignCenter)
            supplier_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, supplier_item)

    def on_error(self, message):
        QMessageBox.warning(self, "خطأ", f"فشل تحميل المشاريع:\n{message}")

    def handle_next(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0 and selected_row < len(self.filtered_projects):
            selected_project = self.filtered_projects[selected_row]

            # Prepare API call to link project to client
            url = f"{BACKEND_BASE_URL}/clients/projects/"

            settings = QSettings("FactorySystem")
            username = settings.value("user_name", "system")

            p_type = selected_project.get("project_type", "")
            # Ensure p_type is 'project' if it's not a campaign (legacy/general projects)
            if p_type != "campaine" and p_type not in ["rent", "industrial", "selling"]:
                p_type = "project"

            form_data = {
                "project_type": p_type,
                "project_id": str(selected_project.get("id", "")),
                "client_id": str(self.client_id) if self.client_id else "",
                "username": username,
            }

            self.next_button.setEnabled(False)
            self.thread = QThread()
            self.worker = ApiWorker("POST", url, data=form_data)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.success.connect(
                lambda response: self.on_link_success(response, selected_project)
            )
            self.worker.error.connect(self.on_link_error)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
        else:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مشروع من الجدول أولاً.")

    def _resolve_nav_project_type(self, cbp_id):
        """Ask server for canonical type so industrial/selling don't open the rent page (would 404)."""
        try:
            url = f"{BACKEND_BASE_URL}/clients/projects/resolve/?cbp_id={cbp_id}"
            r = get(url, timeout=15)
            if r.status_code == 200:
                body = r.json()
                return (body.get("data") or {}).get("project_type")
        except (exceptions.RequestException, ValueError, TypeError):
            pass
        return None

    def on_link_success(self, response_data, selected_project):
        # Link API creates ClientProjectBalance; detail URLs expect CBP id, not BaseProject/Campaine id.
        payload = dict(selected_project)
        data = (response_data or {}).get("data") or {}
        cbp_id = data.get("cbp_id")
        api_project_type = data.get("project_type")
        if cbp_id is not None:
            payload["id"] = cbp_id

        resolved = (
            self._resolve_nav_project_type(cbp_id) if cbp_id is not None else None
        )
        nav_type = resolved or api_project_type or payload.get("project_type")
        if nav_type:
            payload["project_type"] = nav_type

        self.project_selected.emit(payload)
        self.accept()

    def on_link_error(self, message):
        self.next_button.setEnabled(True)
        QMessageBox.warning(self, "خطأ", f"فشل ربط المشروع بالعميل:\n{message}")

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

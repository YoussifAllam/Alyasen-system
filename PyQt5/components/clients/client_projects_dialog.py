from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QLabel,
    QWidget,
)
from PyQt5.QtCore import Qt, QThread, pyqtSlot, QPoint
import qtawesome as qta


class ClientProjectsDialog(QDialog):
    def __init__(self, client_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle("مشاريع العميل")
        self.setMinimumSize(900, 500)
        self.setModal(True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel("مشاريع العميل")
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

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        headers = [
            "",
            "كود ",
            "اسم ",
            "نوع ",
            "تكلفة ",
            "حالة ",
            "تفاصيل ",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )  # or Qt.ScrollBarAlwaysOn
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        content_layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        content_layout.addLayout(button_layout)

        main_layout.addWidget(content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

        self.load_projects()

    def load_projects(self):
        try:
            from .client_profile import ApiWorker
            from ..Main_Ui_Components.constant import BACKEND_BASE_URL

            url = f"{BACKEND_BASE_URL}/projects/?client_id={self.client_id}"

            self.fetch_thread = QThread()
            self.fetch_worker = ApiWorker("GET", url, response_type="json")
            self.fetch_worker.moveToThread(self.fetch_thread)

            self.fetch_thread.started.connect(self.fetch_worker.run)
            self.fetch_worker.success.connect(self.populate_table)
            self.fetch_worker.error.connect(self.handle_error)
            self.fetch_worker.finished.connect(self.fetch_thread.quit)

            self.fetch_thread.start()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error initializing project fetch: {e}",
                QMessageBox.Ok,
            )

    @pyqtSlot(dict)
    def populate_table(self, data):
        # We handle pagination format or list format
        projects = (
            data.get("results", data.get("data", []))
            if isinstance(data, dict)
            else data
        )
        if not isinstance(projects, list):
            projects = []

        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            # cols: "", "id", "name", "type", "total cost", "status", "show_project_details btn"
            self.table.setItem(row, 0, QTableWidgetItem(""))

            id_item = QTableWidgetItem(str(project.get("id", "")))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, id_item)

            name_item = QTableWidgetItem(str(project.get("name", "")))
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, name_item)

            type_item = QTableWidgetItem(
                str(project.get("project_type", project.get("type", "")))
            )
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, type_item)

            cost_item = QTableWidgetItem(
                str(project.get("project_total_cost", project.get("total_cost", "")))
            )
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, cost_item)

            status_item = QTableWidgetItem(
                str(project.get("project_status", project.get("status", "")))
            )
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, status_item)

            btn = QPushButton("show_project_details")
            btn.clicked.connect(
                lambda checked, p_id=project.get("id"): self.show_project_details(p_id)
            )
            self.table.setCellWidget(row, 6, btn)

    def handle_error(self, message):
        # Could be silent or display an error if the endpoint does not exist yet
        # print(f"Failed to fetch projects: {message}")
        QMessageBox.critical(
            self,
            "Error",
            f"Error initializing project fetch: {message}",
            QMessageBox.Ok,
        )

    def show_project_details(self, project_id):
        QMessageBox.information(
            self, "Project Details", f"Show details for project id: {project_id}"
        )

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

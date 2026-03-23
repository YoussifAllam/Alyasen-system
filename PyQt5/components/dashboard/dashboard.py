from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QFrame,
    QScrollArea,
    QProgressBar,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from requests import request, exceptions

# Import the custom chart and dialog widgets
from .donut_chart import DonutChartWidget
from .user_management_dialog import UserManagementDialog
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .line_graph_widget import LineGraphWidget


class ApiFetcherWorker(QObject):
    """Generic worker for fetching dashboard data."""

    finished = pyqtSignal()
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        # return  # todo  remove
        try:
            response = request("GET", self.url, timeout=15)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"خطأ من الخادم: {response.status_code}")
        except exceptions.RequestException as e:
            self.error.emit(f"فشل الاتصال بالخادم: {e}")
        finally:
            self.finished.emit()


class DashboardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.is_first_load = True

        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """
        )

        # Create content widget that will go inside scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 40)  # Increased bottom margin
        content_layout.setSpacing(20)

        # --- Header ---
        header_layout = QHBoxLayout()
        header = QLabel("لوحة التحكم الرئيسية")
        header.setObjectName("mainHeader")
        subheader = QLabel("نظرة عامة حية على أداء وعمليات المصنع.")
        subheader.setObjectName("mainSubheader")
        header_text_layout = QVBoxLayout()
        header_text_layout.addWidget(header)
        header_text_layout.addWidget(subheader)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        content_layout.addLayout(header_layout)

        # --- Main Content Grid ---
        content_grid = QGridLayout()
        content_grid.setSpacing(20)
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        left_column.addWidget(self.create_performance_chart_card())
        left_column.addWidget(self.create_guarantee_checks_card())
        top_lists_layout = QHBoxLayout()
        top_lists_layout.setSpacing(20)
        top_clients_card, self.top_clients_layout = self.create_top_list_card(
            "أفضل العملاء"
        )
        top_products_card, self.top_products_layout = self.create_top_list_card(
            "المشاريع النشطة الأن"
        )
        top_lists_layout.addWidget(top_clients_card)
        top_lists_layout.addWidget(top_products_card)
        left_column.addLayout(top_lists_layout)

        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        right_column.addWidget(self.create_expense_chart_card(), 1)
        right_column.addWidget(self.create_user_management_card())
        content_grid.addLayout(left_column, 0, 0, 1, 2)
        content_grid.addLayout(right_column, 0, 2, 1, 1)
        content_layout.addLayout(content_grid, 1)

        # Add bottom spacing to ensure all content is visible when scrolled
        content_layout.addSpacing(40)

        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)

    def showEvent(self, event):
        """Fetches all initial data concurrently when the widget is first shown."""
        super().showEvent(event)
        if self.is_first_load:
            self.handle_fetch_expense_graph()
            # self.handle_fetch_top_lists()
            # self.handle_fetch_guarantee_checks()
            # self.handle_fetch_performance_graph()
            self.handle_fetch_users_status()
            self.is_first_load = False

    def _start_api_request(self, url, success_slot, thread_name, worker_name):
        """A generic helper to start an API worker."""
        thread = QThread()
        worker = ApiFetcherWorker(url)

        # Keep a reference to the thread and worker to prevent them from being garbage collected
        setattr(self, thread_name, thread)
        setattr(self, worker_name, worker)

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.success.connect(success_slot)
        worker.error.connect(
            lambda msg: QMessageBox.critical(self, "خطأ في تحميل البيانات", msg)
        )
        worker.finished.connect(thread.quit)
        thread.start()

    def handle_fetch_top_lists(self):
        url = f"{BACKEND_BASE_URL}/dashboard/top-lists-data/"
        self._start_api_request(
            url, self.update_top_lists, "top_lists_thread", "top_lists_worker"
        )

    def handle_fetch_expense_graph(self):
        url = f"{BACKEND_BASE_URL}/dashboard/expenses-graph-data/"
        self._start_api_request(
            url, self.update_expense_chart, "graph_thread", "graph_worker"
        )

    def handle_fetch_guarantee_checks(self):
        url = f"{BACKEND_BASE_URL}/dashboard/guarantee-checks/"
        self._start_api_request(
            url, self.update_guarantee_checks, "checks_thread", "checks_worker"
        )

    def handle_fetch_performance_graph(self):
        url = f"{BACKEND_BASE_URL}/dashboard/performance-graph/"
        self._start_api_request(
            url, self.update_performance_graph, "perf_graph_thread", "perf_graph_worker"
        )

    def handle_fetch_users_status(self):
        url = f"{BACKEND_BASE_URL}/dashboard/users-status/"
        self._start_api_request(
            url, self.update_users_status_card, "users_thread", "users_worker"
        )

    def update_expense_chart(self, response_data):
        data = response_data.get("data", {})
        top_expenses = data.get("top_expenses", [])
        others = data.get("others", {})
        total_amount = data.get("total_amount", 0)
        chart_data = []
        legend_data = []
        colors = ["#00bc88", "#ef4444", "#3b82f6", "#a78bfa", "#f59e0b"]
        for i, expense in enumerate(top_expenses):
            color = colors[i % len(colors)]
            chart_data.append({"value": expense.get("percentage", 0), "color": color})
            legend_data.append(
                {
                    "name": expense.get("name", ""),
                    "amount": expense.get("amount", 0),
                    "percentage": expense.get("percentage", 0),
                    "color": color,
                }
            )
        if others and others.get("amount", 0) > 0:
            color = colors[len(top_expenses) % len(colors)]
            chart_data.append({"value": others.get("percentage", 0), "color": color})
            legend_data.append(
                {
                    "name": "أخرى",
                    "amount": others.get("amount", 0),
                    "percentage": others.get("percentage", 0),
                    "color": color,
                }
            )
        center_text = f"{total_amount:,.2f}"
        self.expense_chart.setData(chart_data, center_text)
        for i, (widget, name_label, value_label) in enumerate(
            self.expense_legend_items
        ):
            if i < len(legend_data):
                item = legend_data[i]
                widget.show()
                name_label.setText(item["name"])
                value_label.setText(
                    f"{item['amount']:,.2f} ج.م ({item['percentage']:.1f}%)"
                )
                widget.findChild(QFrame).setStyleSheet(
                    f"background-color: {item['color']}; border-radius: 6px;"
                )
            else:
                widget.hide()

    def update_top_lists(self, response_data):
        data = response_data.get("data", {})
        top_clients = data.get("top_client_list", [])
        self.populate_list_card(
            self.top_clients_layout, top_clients, "name", "amount", "ج.م"
        )
        top_products = data.get("top_materials_list", [])
        self.populate_list_card(
            self.top_products_layout, top_products, "name", "total_quantity", "كجم"
        )

    def populate_list_card(self, layout, items, name_key, value_key, unit):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, item in enumerate(items):
            item_layout = QHBoxLayout()
            name_label = QLabel(f"{i + 1}. {item.get(name_key, '')}")
            value_label = QLabel(f"{item.get(value_key, 0):,.2f} {unit}")

            if i == 0:
                value_label.setStyleSheet("color: #00bc88; font-weight: bold;")

            item_layout.addWidget(name_label)
            item_layout.addStretch()
            item_layout.addWidget(value_label)
            layout.addLayout(item_layout)

    def update_guarantee_checks(self, response_data):
        checks_data = response_data.get("data", [])
        while self.guarantee_checks_layout.count():
            child = self.guarantee_checks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    nested_child = child.layout().takeAt(0)
                    if nested_child.widget():
                        nested_child.widget().deleteLater()

        for item in checks_data:
            client_name = item.get("client_name", "غير محدد")
            project_name = item.get("project_name", "غير محدد")
            check_date = item.get("date", "غير محدد")
            amount = item.get("amount", 0)

            check_item_widget = self.create_guarantee_check_item(
                client_name, project_name, check_date, amount
            )
            self.guarantee_checks_layout.addWidget(check_item_widget)

        self.guarantee_checks_layout.addStretch()

    def update_performance_graph(self, response_data):
        data = response_data.get("data", {}).get("data", {})
        labels = data.get("labels", [])
        sales = data.get("sales", [])
        expenses = data.get("expenses", [])
        self.performance_chart.setData(labels, sales, expenses)

    def create_performance_chart_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        title = QLabel(
            "                                  ملخص الأداء الشهري المبيعات والمصروفات"
        )
        title.setObjectName("cardTitle")
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(20)
        legend_layout.addWidget(self.create_chart_legend_item("المبيعات", "#00bc88"))
        legend_layout.addWidget(self.create_chart_legend_item("المصروفات", "#ef4444"))
        header_layout.addLayout(legend_layout)
        header_layout.addStretch()
        header_layout.addWidget(title)
        layout.addLayout(header_layout)
        self.performance_chart = LineGraphWidget()
        layout.addWidget(self.performance_chart)
        return card

    def create_chart_legend_item(self, text, color):
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label = QLabel(text)
        label.setObjectName("legendLabel")
        color_swatch = QFrame()
        color_swatch.setFixedSize(14, 14)
        color_swatch.setStyleSheet(f"background-color: {color}; border-radius: 7px;")
        layout.addWidget(label)
        layout.addWidget(color_swatch)
        return item_widget

    def create_guarantee_checks_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        title = QLabel("تذكير بشيكات الضمان")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        # Add headers
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("تاريخ الشيك"), 2)
        header_layout.addWidget(QLabel("اسم المشروع"), 3)
        header_layout.addWidget(QLabel("اسم العميل"), 3)
        header_layout.addWidget(QLabel("القيمة"), 2)

        # Style headers
        for i in range(header_layout.count()):
            widget = header_layout.itemAt(i).widget()
            widget.setStyleSheet("color: #9ca3af; font-weight: bold; font-size: 14px;")

        layout.addLayout(header_layout)

        self.guarantee_checks_layout = QVBoxLayout()
        layout.addLayout(self.guarantee_checks_layout)
        return card

    def create_top_list_card(self, title):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        layout.addLayout(content_layout)
        return card, content_layout

    def create_guarantee_check_item(
        self, client_name, project_name, check_date, amount
    ):
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 5, 0, 5)

        date_lbl = QLabel(str(check_date))
        date_lbl.setStyleSheet("color: #e5e7eb; font-weight: bold; font-size: 14px;")

        project_lbl = QLabel(str(project_name))
        project_lbl.setStyleSheet("font-size: 14px;")

        client_lbl = QLabel(str(client_name))
        client_lbl.setStyleSheet("font-size: 14px;")

        amount_lbl = QLabel(f"{amount:,.2f} ج.م")
        amount_lbl.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")

        layout.addWidget(date_lbl, 2)
        layout.addWidget(project_lbl, 3)
        layout.addWidget(client_lbl, 3)
        layout.addWidget(amount_lbl, 2)

        return item

    def create_expense_chart_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        title = QLabel("توزيع المصروفات")
        title.setObjectName("cardTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.expense_chart = DonutChartWidget()
        self.expense_chart.setMinimumSize(350, 350)
        chart_container_layout = QHBoxLayout()
        chart_container_layout.addStretch()
        chart_container_layout.addWidget(self.expense_chart)
        chart_container_layout.addStretch()
        self.expense_legend_items = []
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(10)
        for _ in range(3):
            widget, name_label, value_label = self.create_legend_item(
                "-", "-", "#374151"
            )
            legend_layout.addWidget(widget)
            self.expense_legend_items.append((widget, name_label, value_label))
            widget.hide()
        layout.addLayout(chart_container_layout, 1)
        layout.addLayout(legend_layout)
        return card

    def create_legend_item(self, name, value, color_hex):
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        color_swatch = QFrame()
        color_swatch.setFixedSize(12, 12)
        color_swatch.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 6px;"
        )
        name_label = QLabel(name)
        value_label = QLabel(value)
        name_label.setStyleSheet("font-size: 16px;")
        value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(color_swatch)
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(value_label)
        return item, name_label, value_label

    def update_users_status_card(self, response_data):
        data = response_data.get("data", {})
        approved_count = data.get("approved_count", 0)
        unapproved_count = data.get("unapproved_count", 0)

        self.approved_users_label.setText(str(approved_count))
        self.pending_requests_label.setText(str(unapproved_count))

    def create_user_management_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        title = QLabel("إدارة المستخدمين")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 10, 0, 10)
        users_layout = QVBoxLayout()
        self.approved_users_label = QLabel("٠")
        self.approved_users_label.setObjectName("userStatValue")
        users_label = QLabel("مستخدم حالي")
        users_label.setObjectName("userStatLabel")
        users_layout.addWidget(self.approved_users_label)
        users_layout.addWidget(users_label)
        users_layout.setAlignment(Qt.AlignCenter)
        requests_layout = QVBoxLayout()
        self.pending_requests_label = QLabel("٠")
        self.pending_requests_label.setObjectName("userStatValue")
        requests_label = QLabel("طلب جديد")
        requests_label.setObjectName("userStatLabel")
        requests_layout.addWidget(self.pending_requests_label)
        requests_layout.addWidget(requests_label)
        requests_layout.setAlignment(Qt.AlignCenter)
        stats_layout.addLayout(users_layout)
        stats_layout.addLayout(requests_layout)
        layout.addWidget(stats_widget)
        manage_button = QPushButton("فتح لوحة الإدارة")
        manage_button.setObjectName("primaryButton")
        manage_button.clicked.connect(self.open_user_management_dialog)
        layout.addWidget(manage_button)
        return card

    def open_user_management_dialog(self):
        dialog = UserManagementDialog(self)
        dialog.exec_()

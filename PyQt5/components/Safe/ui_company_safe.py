from urllib.parse import urlencode

import qtawesome as qta
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QFrame,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QStackedWidget,
    QGridLayout,
    QDialog,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QDate,
    Qt,
    QSettings,
    QTimer,
)
from PyQt5.QtGui import QColor
from requests import request, exceptions

from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from ..Main_Ui_Components.date_edit import configure_date_edit, format_date
from ..utils.api_errors import format_request_exception, parse_api_response
from .safe_transaction_dialog import SafeTransactionDialog

DEPOSIT_COLOR = QColor("#10b981")
WITHDRAWAL_COLOR = QColor("#ef4444")
ADJUSTMENT_COLOR = QColor("#fbbf24")
MUTED_COLOR = QColor("#9ca3af")


class SafeApiWorker(QObject):
    finished = pyqtSignal()
    balance_success = pyqtSignal(dict)
    logs_success = pyqtSignal(dict)
    mutation_success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        *,
        fetch_balance=False,
        logs_url=None,
        put_payload=None,
    ):
        super().__init__()
        self.fetch_balance = fetch_balance
        self.logs_url = logs_url
        self.put_payload = put_payload

    @pyqtSlot()
    def run(self):
        try:
            if self.put_payload is not None:
                balance_url = f"{BACKEND_BASE_URL}/safe/safe/"
                resp = request("PUT", balance_url, json=self.put_payload, timeout=8)
                ok, result = parse_api_response(resp)
                if ok:
                    payload = result.get("data", {}) if isinstance(result, dict) else {}
                    self.mutation_success.emit(payload)
                else:
                    self.error.emit(result)
                return

            if self.fetch_balance:
                balance_url = f"{BACKEND_BASE_URL}/safe/safe/"
                resp = request("GET", balance_url, timeout=8)
                ok, result = parse_api_response(resp)
                if ok:
                    payload = result.get("data", {}) if isinstance(result, dict) else {}
                    if isinstance(payload, (int, float)):
                        payload = {"balance": float(payload)}
                    self.balance_success.emit(payload)
                else:
                    self.error.emit(result)

            if self.logs_url:
                resp = request("GET", self.logs_url, timeout=8)
                ok, result = parse_api_response(resp)
                if ok:
                    if isinstance(result, dict) and "data" in result and isinstance(
                        result["data"], dict
                    ):
                        self.logs_success.emit(result["data"])
                    elif isinstance(result, dict) and "results" in result:
                        self.logs_success.emit(result)
                    else:
                        self.logs_success.emit(result if isinstance(result, dict) else {})
                else:
                    self.error.emit(result)

        except exceptions.RequestException as e:
            self.error.emit(format_request_exception(e))
        except Exception as e:
            self.error.emit(f"حدث خطأ غير متوقع: {e}")
        finally:
            self.finished.emit()


class CompanySafeUI(QWidget):
    OPERATION_FILTER_ALL = ""
    OPERATION_LABELS = {
        "deposit": "إيداع",
        "withdrawal": "سحب",
        "adjustment": "تسوية",
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")

        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self._balance_loaded = False
        self._initial_load_done = False
        self._safe_pending_load = False
        self._last_request_was_mutation = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        header_row = QHBoxLayout()
        titles = QVBoxLayout()
        header = QLabel("خزنة الشركة")
        header.setObjectName("mainHeader")
        subheader = QLabel("رصيد الخزنة وسجل الإيداعات والسحوبات.")
        subheader.setObjectName("mainSubheader")
        titles.addWidget(header)
        titles.addWidget(subheader)
        header_row.addLayout(titles)
        header_row.addStretch()

        self.btn_deposit = QPushButton("  إيداع")
        self.btn_deposit.setIcon(qta.icon("fa5s.plus-circle", color="#111827"))
        self.btn_deposit.setObjectName("primaryButton")
        # self.btn_withdraw = QPushButton("  سحب")
        # self.btn_withdraw.setIcon(qta.icon("fa5s.minus-circle", color="#ffffff"))
        # self.btn_withdraw.setObjectName("dangerButton")
        header_row.addWidget(self.btn_deposit)
        # header_row.addWidget(self.btn_withdraw)
        main_layout.addLayout(header_row)

        self.balance_stack = QStackedWidget()
        self.balance_stack.addWidget(self._build_balance_card())
        self.balance_stack.addWidget(self._build_balance_skeleton())
        main_layout.addWidget(self.balance_stack)

        main_layout.addWidget(self._build_filter_bar())

        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self._build_table())
        self.table_stack.addWidget(self._build_table_skeleton())
        self.table_stack.addWidget(self._build_empty_state())
        main_layout.addWidget(self.table_stack, 1)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("لم يتم تحميل بيانات")
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        main_layout.addLayout(pagination_layout)

        self.btn_deposit.clicked.connect(lambda: self._open_transaction_dialog("add"))
        # self.btn_withdraw.clicked.connect(
        #     lambda: self._open_transaction_dialog("subtract")
        # )
        self.search_input.returnPressed.connect(self.apply_filters)
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        self.show_all_button.clicked.connect(self.reset_filters)
        self.show_today_button.clicked.connect(self.handle_show_today)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

    def _build_balance_card(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("safeBalanceCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(20)

        accent = QFrame()
        accent.setObjectName("safeBalanceCardAccent")
        card_layout.addWidget(accent)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        title = QLabel("رصيد الخزنة")
        title.setObjectName("safeBalanceTitle")
        amount_row = QHBoxLayout()
        amount_row.setSpacing(8)
        self.balance_amount_label = QLabel("—")
        self.balance_amount_label.setObjectName("safeBalanceAmount")
        self.balance_currency_label = QLabel("جنيه")
        self.balance_currency_label.setObjectName("safeBalanceCurrency")
        amount_row.addWidget(self.balance_amount_label)
        amount_row.addWidget(self.balance_currency_label)
        amount_row.addStretch()
        text_col.addWidget(title)
        text_col.addLayout(amount_row)
        card_layout.addLayout(text_col, 1)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(8)
        meta_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.trend_label = QLabel("")
        self.trend_label.setObjectName("safeTrendNeutral")
        self.last_updated_label = QLabel("")
        self.last_updated_label.setObjectName("safeBalanceMeta")
        self.today_flow_label = QLabel("")
        self.today_flow_label.setObjectName("safeBalanceMeta")
        meta_col.addWidget(self.trend_label)
        meta_col.addWidget(self.today_flow_label)
        meta_col.addWidget(self.last_updated_label)
        card_layout.addLayout(meta_col)

        layout.addWidget(card)
        return page

    def _build_balance_skeleton(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        for width in (180, 320, 140):
            bar = QFrame()
            bar.setObjectName("safeSkeletonBar")
            bar.setFixedWidth(width)
            layout.addWidget(bar)
        return page

    def _build_filter_bar(self):
        bar = QFrame()
        bar.setObjectName("safeFilterBar")
        grid = QGridLayout(bar)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        def _lbl(text):
            label = QLabel(text)
            label.setObjectName("safeFilterLabel")
            return label

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث في وصف العملية...")
        self.type_filter = QComboBox()
        self.type_filter.addItem("كل الأنواع", "")
        self.type_filter.addItem("إيداع", "deposit")
        self.type_filter.addItem("سحب", "withdrawal")
        self.type_filter.addItem("تسوية", "adjustment")

        self.date_from_input = QDateEdit(date=QDate.currentDate().addMonths(-1))
        configure_date_edit(self.date_from_input)
        self.date_to_input = QDateEdit(date=QDate.currentDate())
        configure_date_edit(self.date_to_input)

        self.show_today_button = QPushButton("سجلات اليوم")
        self.show_all_button = QPushButton("عرض الكل")
        self.btn_apply_filters = QPushButton("تطبيق")
        self.btn_apply_filters.setObjectName("primaryButton")
        self.btn_reset_filters = QPushButton("مسح الفلاتر")

        grid.addWidget(_lbl("بحث"), 0, 0)
        grid.addWidget(self.search_input, 0, 1)
        grid.addWidget(_lbl("نوع العملية"), 0, 2)
        grid.addWidget(self.type_filter, 0, 3)
        grid.addWidget(_lbl("من تاريخ"), 1, 0)
        grid.addWidget(self.date_from_input, 1, 1)
        grid.addWidget(_lbl("إلى تاريخ"), 1, 2)
        grid.addWidget(self.date_to_input, 1, 3)

        actions = QHBoxLayout()
        actions.addWidget(self.show_today_button)
        actions.addSpacing(15)
        actions.addWidget(self.show_all_button)
        actions.addSpacing(15)
        actions.addWidget(self.btn_reset_filters)
        actions.addStretch()
        actions.addWidget(self.btn_apply_filters)
        grid.addLayout(actions, 2, 0, 1, 4)
        return bar

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        headers = [
            "نوع العملية",
            "المبلغ",
            "الرصيد بعد العملية",
            "العملية",
            "التاريخ",
            "الوقت",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        return self.table

    def _build_table_skeleton(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 12, 0, 0)
        for _ in range(6):
            bar = QFrame()
            bar.setObjectName("safeSkeletonBar")
            layout.addWidget(bar)
        layout.addStretch()
        return page

    def _build_empty_state(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("لا توجد عمليات مطابقة للفلاتر الحالية")
        label.setObjectName("emptyStateLabel")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def refresh_data(self):
        if self._safe_pending_load:
            return
        self._safe_pending_load = True
        self._show_balance_skeleton(True)
        self._show_table_skeleton(True)
        self._start_fetch_request(fetch_balance=True, logs_url=self._build_logs_url())

    def _build_logs_url(self, page_url=None):
        if page_url:
            return page_url
        params = {}
        search = self.search_input.text().strip()
        if search:
            params["search"] = search
        op_type = self.type_filter.currentData()
        if op_type:
            params["operation_type"] = op_type
        params["date_from"] = format_date(self.date_from_input.date())
        params["date_to"] = format_date(self.date_to_input.date())
        query = urlencode(params)
        return f"{BACKEND_BASE_URL}/safe/logs/?{query}"

    def apply_filters(self):
        self._show_table_skeleton(True)
        self._start_fetch_request(fetch_balance=False, logs_url=self._build_logs_url())

    def reset_filters(self):
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_input.setDate(QDate.currentDate())
        self.apply_filters()

    def handle_show_today(self):
        today = QDate.currentDate()
        self.date_from_input.setDate(today)
        self.date_to_input.setDate(today)
        self.apply_filters()

    def handle_next_page(self):
        if self.next_page_url:
            self._show_table_skeleton(True)
            self._start_fetch_request(fetch_balance=False, logs_url=self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._show_table_skeleton(True)
            self._start_fetch_request(fetch_balance=False, logs_url=self.prev_page_url)

    def _open_transaction_dialog(self, process: str):
        dialog = SafeTransactionDialog(process, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        payload = dialog.get_payload()
        settings = QSettings("FactorySystem")
        payload["username"] = settings.value("user_name", "")
        self._start_fetch_request(put_payload=payload)

    def _start_fetch_request(
        self,
        *,
        fetch_balance=False,
        logs_url=None,
        put_payload=None,
    ):
        try:
            if (
                hasattr(self, "_api_thread")
                and getattr(self, "_api_thread", None) is not None
            ):
                if self._api_thread.isRunning():
                    return
        except RuntimeError:
            pass

        self._last_request_was_mutation = put_payload is not None
        self._set_controls_enabled(False)
        if logs_url and put_payload is None:
            self.page_info_label.setText("جاري التحميل...")

        self._api_thread = QThread()
        self.worker = SafeApiWorker(
            fetch_balance=fetch_balance,
            logs_url=logs_url,
            put_payload=put_payload,
        )
        self.worker.moveToThread(self._api_thread)
        self._api_thread.started.connect(self.worker.run)
        self.worker.balance_success.connect(self.update_balance_summary)
        self.worker.logs_success.connect(self.handle_logs_response)
        self.worker.mutation_success.connect(self._on_mutation_success)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self._api_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._api_thread.finished.connect(self._api_thread.deleteLater)
        self._api_thread.start()

    def _reload_logs_after_mutation(self):
        try:
            if (
                hasattr(self, "_api_thread")
                and self._api_thread is not None
                and self._api_thread.isRunning()
            ):
                QTimer.singleShot(50, self._reload_logs_after_mutation)
                return
        except RuntimeError:
            pass
        self._last_request_was_mutation = False
        self._start_fetch_request(fetch_balance=False, logs_url=self._build_logs_url())

    def update_balance_summary(self, data: dict):
        balance = float(data.get("balance", 0))
        self.balance_amount_label.setText(f"{balance:,.2f}")
        currency = data.get("currency", "جنيه")
        self.balance_currency_label.setText(currency)

        change = data.get("change_vs_yesterday")
        if change is not None:
            if change > 0:
                self.trend_label.setObjectName("safeTrendUp")
                self.trend_label.setText(f"▲ +{change:,.2f} عن أمس")
            elif change < 0:
                self.trend_label.setObjectName("safeTrendDown")
                self.trend_label.setText(f"▼ {change:,.2f} عن أمس")
            else:
                self.trend_label.setObjectName("safeTrendNeutral")
                self.trend_label.setText("بدون تغيير عن أمس")
        else:
            self.trend_label.setObjectName("safeTrendNeutral")
            self.trend_label.setText("لا توجد بيانات مقارنة بأمس")

        deposits = float(data.get("today_deposits", 0))
        withdrawals = float(data.get("today_withdrawals", 0))
        self.today_flow_label.setText(
            f"حركة اليوم: إيداع {deposits:,.2f}  |  سحب {withdrawals:,.2f}"
        )

        last_updated = data.get("last_updated") or ""
        if last_updated:
            display = self._format_datetime_display(last_updated)
            self.last_updated_label.setText(f"آخر تحديث: {display}")
        else:
            self.last_updated_label.setText("آخر تحديث: —")

        self._refresh_widget_style(self.trend_label)
        self._balance_loaded = True
        self._show_balance_skeleton(False)

    def _on_mutation_success(self, data: dict):
        self.update_balance_summary(data)
        self._show_table_skeleton(True)
        QTimer.singleShot(0, self._reload_logs_after_mutation)

    def handle_logs_response(self, data_obj):
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        self.populate_table(results)
        self._set_controls_enabled(True)
        self._safe_pending_load = False
        self._initial_load_done = True
        if results:
            self.table_stack.setCurrentIndex(0)
        else:
            self.table_stack.setCurrentIndex(2)

    def populate_table(self, logs):
        self.table.setRowCount(0)
        for log_entry in logs:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            op_type = log_entry.get("operation_type", "")
            op_label = log_entry.get(
                "operation_type_display"
            ) or self.OPERATION_LABELS.get(op_type, "—")
            amount = log_entry.get("amount")
            balance_after = log_entry.get("balance_after")

            transaction_val = log_entry.get("transaction") or log_entry.get(
                "trnasaction", ""
            )
            date_val = log_entry.get("date", "")
            time_val = log_entry.get("time", "")
            if not time_val and date_val:
                time_val = self._extract_time(date_val)

            date_disp, _time_from_date = self._split_datetime(date_val)
            if not time_val:
                time_val = _time_from_date

            type_item = QTableWidgetItem(op_label)
            type_item.setTextAlignment(Qt.AlignCenter)
            self._color_operation_type(type_item, op_type)

            amount_item = QTableWidgetItem(self._format_amount(amount, op_type))
            amount_item.setTextAlignment(Qt.AlignCenter)
            self._color_operation_type(amount_item, op_type)

            balance_item = QTableWidgetItem(
                f"{balance_after:,.2f}" if balance_after is not None else "—"
            )
            balance_item.setTextAlignment(Qt.AlignCenter)

            desc_item = QTableWidgetItem(transaction_val)
            desc_item.setTextAlignment(Qt.AlignCenter)
            date_item = QTableWidgetItem(date_disp)
            date_item.setTextAlignment(Qt.AlignCenter)
            time_item = QTableWidgetItem(time_val)
            time_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_position, 0, type_item)
            self.table.setItem(row_position, 1, amount_item)
            self.table.setItem(row_position, 2, balance_item)
            self.table.setItem(row_position, 3, desc_item)
            self.table.setItem(row_position, 4, date_item)
            self.table.setItem(row_position, 5, time_item)

    def _format_amount(self, amount, op_type):
        if amount is None:
            return "—"
        prefix = "+" if op_type == "deposit" else "-" if op_type == "withdrawal" else ""
        return f"{prefix}{float(amount):,.2f}"

    def _color_operation_type(self, item, op_type):
        if op_type == "deposit":
            item.setForeground(DEPOSIT_COLOR)
        elif op_type == "withdrawal":
            item.setForeground(WITHDRAWAL_COLOR)
        elif op_type == "adjustment":
            item.setForeground(ADJUSTMENT_COLOR)
        else:
            item.setForeground(MUTED_COLOR)

    @staticmethod
    def _style_pagination_button(button: QPushButton, enabled: bool) -> None:
        button.setEnabled(enabled)
        if enabled:
            button.setGraphicsEffect(None)
            return
        effect = button.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(button)
            button.setGraphicsEffect(effect)
        effect.setOpacity(0.4)

    def update_pagination_controls(self):
        self._style_pagination_button(
            self.next_button, self.next_page_url is not None
        )
        self._style_pagination_button(
            self.prev_button, self.prev_page_url is not None
        )

        page = self.get_current_page()
        page_size = self.table.rowCount() or 20
        start_item = (page - 1) * page_size + 1 if self.table.rowCount() else 0
        end_item = (
            start_item + self.table.rowCount() - 1 if self.table.rowCount() else 0
        )

        if self.total_count > 0 and self.table.rowCount():
            self.page_info_label.setText(
                f"عرض {start_item}-{end_item} من {self.total_count} سجل"
            )
        elif self.total_count == 0:
            self.page_info_label.setText("لا توجد نتائج")
        else:
            self.page_info_label.setText(f"إجمالي {self.total_count} سجل")

    def get_current_page(self):
        if not self.prev_page_url:
            return 1
        try:
            if self.next_page_url:
                page_str = self.next_page_url.split("page=")[1].split("&")[0]
                return int(page_str) - 1
            if self.prev_page_url:
                page_str = self.prev_page_url.split("page=")[-1].split("&")[0]
                return int(page_str) + 1
        except (IndexError, ValueError):
            return 1
        return 1

    def show_error_message(self, message):
        self._set_controls_enabled(True)
        self._safe_pending_load = False
        self._show_balance_skeleton(False)
        if not self._balance_loaded:
            self.balance_amount_label.setText("—")
        self.table_stack.setCurrentIndex(2 if self.table.rowCount() == 0 else 0)
        self.page_info_label.setText("تعذر تحميل البيانات")
        if self._last_request_was_mutation:
            QMessageBox.critical(self, "خطأ", message)

    def _set_controls_enabled(self, enabled: bool):
        for widget in (
            self.show_all_button,
            self.show_today_button,
            self.btn_apply_filters,
            self.btn_reset_filters,
            self.search_input,
            self.type_filter,
            self.date_from_input,
            self.date_to_input,
            self.btn_deposit,
            # self.btn_withdraw,
        ):
            widget.setEnabled(enabled)
        if enabled:
            self.update_pagination_controls()
        else:
            self._style_pagination_button(self.next_button, False)
            self._style_pagination_button(self.prev_button, False)

    def _show_balance_skeleton(self, show: bool):
        self.balance_stack.setCurrentIndex(1 if show else 0)

    def _show_table_skeleton(self, show: bool):
        if show:
            self.table_stack.setCurrentIndex(1)

    @staticmethod
    def _split_datetime(date_val):
        if not date_val:
            return "", ""
        if "T" in str(date_val):
            dt_parts = str(date_val).split("T")
            date_str = dt_parts[0]
            time_str = dt_parts[1].split(".")[0].split("+")[0]
            return date_str, time_str
        return str(date_val), ""

    @staticmethod
    def _extract_time(date_val):
        _, time_str = CompanySafeUI._split_datetime(date_val)
        return time_str

    @staticmethod
    def _format_datetime_display(iso_value):
        date_part, time_part = CompanySafeUI._split_datetime(iso_value)
        if date_part and time_part:
            return f"{date_part} {time_part}"
        return iso_value

    @staticmethod
    def _refresh_widget_style(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

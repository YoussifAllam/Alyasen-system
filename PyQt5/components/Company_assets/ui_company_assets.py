import os
from urllib.parse import urlencode

import qtawesome as qta
from PyQt5.QtCore import QSettings, QThread, Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from ..Main_Ui_Components.constant import BACKEND_BASE_URL
from .asset_attachments_dialog import AssetAttachmentsDialog
from .asset_form_dialog import ASSET_CATEGORIES, ASSET_STATUSES, AssetFormDialog
from .company_assets_api_worker import MachineApiWorker

CATEGORY_COLORS = {
    "equipment": QColor("#60a5fa"),
    "vehicle": QColor("#a78bfa"),
    "furniture": QColor("#f59e0b"),
    "electronics": QColor("#22d3ee"),
    "other": QColor("#9ca3af"),
}
STATUS_COLORS = {
    "working": QColor("#10b981"),
    "maintenance": QColor("#fbbf24"),
    "retired": QColor("#ef4444"),
}
MUTED_COLOR = QColor("#9ca3af")

CATEGORY_LABELS = dict(ASSET_CATEGORIES)
STATUS_LABELS = dict(ASSET_STATUSES)


def _create_stat_card(title: str, variant: str):
    card = QFrame()
    card.setObjectName(f"assetStatCard{variant}")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("assetStatTitle")
    value_label = QLabel("—")
    value_label.setObjectName(f"assetStatValue{variant}")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return card, value_label


class CompanyAssetsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainContent")
        self.next_page_url = None
        self.prev_page_url = None
        self.total_count = 0
        self._initial_load_done = False
        self._pending_load = False
        self._last_request_was_mutation = False
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._hide_feedback)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        header_row = QHBoxLayout()
        titles = QVBoxLayout()
        header = QLabel("أصول الشركة")
        header.setObjectName("mainHeader")
        subheader = QLabel(
            "سجل الأصول الثابتة: المعدات، المركبات، الأثاث، والإلكترونيات."
        )
        subheader.setObjectName("mainSubheader")
        titles.addWidget(header)
        titles.addWidget(subheader)
        header_row.addLayout(titles)
        header_row.addStretch()

        self.btn_add_asset = QPushButton("  إضافة أصل")
        self.btn_add_asset.setIcon(qta.icon("fa5s.plus", color="#111827"))
        self.btn_add_asset.setObjectName("primaryButton")
        header_row.addWidget(self.btn_add_asset)
        main_layout.addLayout(header_row)

        self.feedback_banner = self._build_feedback_banner()
        main_layout.addWidget(self.feedback_banner)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        count_card, self.count_display = _create_stat_card("عدد الأصول", "Count")
        value_card, self.value_display = _create_stat_card(
            "إجمالي قيمة الأصول", "Value"
        )
        summary_row.addWidget(count_card)
        summary_row.addWidget(value_card)
        summary_row.addStretch()
        main_layout.addLayout(summary_row)

        main_layout.addWidget(self._build_filter_bar())

        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self._build_table())
        self.table_stack.addWidget(self._build_table_skeleton())
        self.table_stack.addWidget(self._build_empty_state())
        main_layout.addWidget(self.table_stack, 1)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("السابق")
        self.next_button = QPushButton("التالي")
        self.page_info_label = QLabel("")
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        main_layout.addLayout(pagination_layout)

        self.btn_add_asset.clicked.connect(self._open_add_dialog)
        self.search_input.returnPressed.connect(self.apply_filters)
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        self.show_all_button.clicked.connect(self.reset_filters)
        self.next_button.clicked.connect(self.handle_next_page)
        self.prev_button.clicked.connect(self.handle_prev_page)

    def _build_feedback_banner(self):
        frame = QFrame()
        frame.setObjectName("assetFeedbackBanner")
        frame.hide()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        self.feedback_icon = QLabel()
        self.feedback_icon.setFixedSize(22, 22)
        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setObjectName("assetFeedbackText")
        layout.addWidget(self.feedback_icon)
        layout.addWidget(self.feedback_label, 1)
        return frame

    @staticmethod
    def _refresh_widget_style(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _hide_feedback(self):
        self.feedback_banner.hide()

    def _show_feedback(
        self, message: str, *, variant: str = "success", auto_hide_ms=6000
    ):
        icons = {
            "success": ("fa5s.check-circle", "#10b981"),
            "error": ("fa5s.exclamation-circle", "#ef4444"),
            "info": ("fa5s.sync", "#60a5fa"),
        }
        icon_name, color = icons.get(variant, icons["info"])
        self.feedback_banner.setProperty("variant", variant)
        self.feedback_label.setText(message)
        self.feedback_icon.setPixmap(qta.icon(icon_name, color=color).pixmap(22, 22))
        self.feedback_banner.show()
        self._refresh_widget_style(self.feedback_banner)
        self._feedback_timer.stop()
        if auto_hide_ms and variant != "info":
            self._feedback_timer.start(auto_hide_ms)

    def _build_filter_bar(self):
        bar = QFrame()
        bar.setObjectName("safeFilterBar")
        grid = QGridLayout(bar)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        def _lbl(text):
            label = QLabel(text)
            label.setObjectName("safeFilterLabel")
            return label

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم، الموقع، المسؤول...")

        self.category_filter = QComboBox()
        self.category_filter.addItem("كل الفئات", "")
        for value, label in ASSET_CATEGORIES:
            self.category_filter.addItem(label, value)

        self.status_filter = QComboBox()
        self.status_filter.addItem("كل الحالات", "")
        for value, label in ASSET_STATUSES:
            self.status_filter.addItem(label, value)

        self.show_all_button = QPushButton("عرض الكل")
        self.btn_apply_filters = QPushButton("تطبيق")
        self.btn_apply_filters.setObjectName("primaryButton")
        self.btn_reset_filters = QPushButton("مسح الفلاتر")

        grid.addWidget(_lbl("بحث"), 0, 0)
        grid.addWidget(self.search_input, 0, 1)
        grid.setSpacing(10)
        grid.addWidget(_lbl("فئة الأصل"), 0, 2)
        grid.addWidget(self.category_filter, 0, 3)
        grid.setSpacing(10)
        grid.addWidget(_lbl("حالة الأصل"), 1, 0)
        grid.addWidget(self.status_filter, 1, 1)
        grid.setSpacing(10)

        actions = QHBoxLayout()
        actions.addWidget(self.show_all_button)
        actions.addWidget(self.btn_reset_filters)
        actions.addStretch()
        actions.addWidget(self.btn_apply_filters)
        grid.addLayout(actions, 1, 2, 1, 2)
        return bar

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        headers = [
            "الاسم",
            "الفئة",
            "السعر",
            "تاريخ الشراء",
            "الحالة",
            "القيمة الدفترية",
            "الموقع",
            "المسؤول",
            "تفاصيل",
            "إجراءات",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            9, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
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
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.box-open", color="#6b7280").pixmap(48, 48))
        icon.setAlignment(Qt.AlignCenter)
        label = QLabel("لا توجد أصول مطابقة\nأضف أصلًا جديدًا أو غيّر معايير البحث")
        label.setObjectName("emptyStateLabel")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(label)
        return page

    def refresh_data(self):
        if self._pending_load:
            return
        self._pending_load = True
        self._show_table_skeleton(True)
        self._start_api_request("GET", self._build_list_url())

    def _build_list_url(self, page_url=None):
        if page_url:
            return page_url
        params = {}
        search = self.search_input.text().strip()
        if search:
            params["q"] = search
        category = self.category_filter.currentData()
        if category:
            params["category"] = category
        status = self.status_filter.currentData()
        if status:
            params["status"] = status
        query = urlencode(params)
        base = f"{BACKEND_BASE_URL}/company_assets/"
        return f"{base}?{query}" if query else base

    def apply_filters(self):
        self._show_table_skeleton(True)
        self._start_api_request("GET", self._build_list_url())

    def reset_filters(self):
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.apply_filters()

    def handle_next_page(self):
        if self.next_page_url:
            self._show_table_skeleton(True)
            self._start_api_request("GET", self.next_page_url)

    def handle_prev_page(self):
        if self.prev_page_url:
            self._show_table_skeleton(True)
            self._start_api_request("GET", self.prev_page_url)

    def _open_add_dialog(self):
        dialog = AssetFormDialog(parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        payload = dialog.get_payload()
        settings = QSettings("FactorySystem")
        payload["username"] = settings.value("user_name", "unknown_user")
        self._set_controls_enabled(False)
        self._show_feedback("جاري إضافة الأصل...", variant="info", auto_hide_ms=0)
        has_attachments = bool(dialog.attachments_paths)
        self._start_api_request(
            "POST",
            f"{BACKEND_BASE_URL}/company_assets/",
            payload=payload,
            reenable_on_finish=not has_attachments,
            on_success=lambda data: self._on_asset_created(
                data, dialog.attachments_paths
            ),
        )

    def _on_asset_created(self, response_data, attachment_paths):
        asset_id = response_data.get("id")
        if not asset_id:
            self._show_feedback("لم يتم إرجاع معرّف الأصل من الخادم.", variant="error")
            self._set_controls_enabled(True)
            return
        if attachment_paths:
            self._show_feedback("جاري رفع المرفقات...", variant="info", auto_hide_ms=0)
            QTimer.singleShot(
                0, lambda: self._upload_attachments(asset_id, attachment_paths)
            )
        else:
            self._finalize_mutation("تمت إضافة الأصل بنجاح.")

    def _upload_attachments(self, asset_id, paths):
        payload = {"asset_id": str(asset_id)}
        files = [
            ("attachments", (os.path.basename(path), open(path, "rb")))
            for path in paths
        ]
        url = f"{BACKEND_BASE_URL}/company_assets/attachments/"
        self._start_api_request(
            "POST",
            url,
            payload=payload,
            files=files,
            on_success=lambda _: self._finalize_mutation(
                "تمت إضافة الأصل والمرفقات بنجاح."
            ),
        )

    def _open_edit_dialog(self, asset_data):
        dialog = AssetFormDialog(asset_data=asset_data, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        payload = dialog.get_payload()
        self._set_controls_enabled(False)
        self._show_feedback("جاري حفظ التعديلات...", variant="info", auto_hide_ms=0)
        self._start_api_request(
            "PATCH",
            f"{BACKEND_BASE_URL}/company_assets/",
            payload=payload,
            on_success=lambda _: self._finalize_mutation("تم تحديث الأصل بنجاح."),
        )

    def _open_attachments_dialog(self, asset_id, asset_name):
        dialog = AssetAttachmentsDialog(asset_id, asset_name=asset_name, parent=self)
        dialog.exec_()

    def _confirm_delete(self, asset_id, asset_name):
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف الأصل «{asset_name}»؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._set_controls_enabled(False)
        self._show_feedback("جاري حذف الأصل...", variant="info", auto_hide_ms=0)
        self._start_api_request(
            "DELETE",
            f"{BACKEND_BASE_URL}/company_assets/",
            payload={"id": asset_id},
            on_success=lambda _: self._finalize_mutation("تم حذف الأصل."),
        )

    def _finalize_mutation(self, message):
        self._set_controls_enabled(True)
        self._show_feedback(message, variant="success")
        QTimer.singleShot(0, self.apply_filters)

    def _start_api_request(
        self,
        method,
        url,
        payload=None,
        files=None,
        on_success=None,
        reenable_on_finish=True,
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

        self._last_request_was_mutation = method in ("POST", "PATCH", "DELETE")
        if method == "GET":
            self.page_info_label.setText("جاري التحميل...")

        self._api_thread = QThread()
        self.worker = MachineApiWorker(method, url, payload, files)
        self.worker.moveToThread(self._api_thread)
        self._api_thread.started.connect(self.worker.run)
        if on_success:
            self.worker.success.connect(on_success)
        else:
            self.worker.success.connect(self.handle_api_response)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self._api_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._api_thread.finished.connect(self._api_thread.deleteLater)
        if method != "GET" and reenable_on_finish:
            self.worker.finished.connect(lambda: self._set_controls_enabled(True))
        self._api_thread.start()

    def handle_api_response(self, response_data):
        data_obj = response_data.get("data", {})
        results = data_obj.get("results", [])
        self.next_page_url = data_obj.get("next")
        self.prev_page_url = data_obj.get("previous")
        self.total_count = data_obj.get("count", 0)
        summary = data_obj.get("summary", {})
        self._update_summary(summary)
        self.populate_table(results)
        self.update_pagination_controls()
        self._set_controls_enabled(True)
        self._initial_load_done = True
        self._pending_load = False
        self._show_table_skeleton(False)

    def _update_summary(self, summary):
        count = summary.get("count", self.total_count)
        total_value = summary.get("total_value", 0)
        self.count_display.setText(str(count))
        self.value_display.setText(f"{float(total_value):,.2f} جنيه")

    def populate_table(self, assets):
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        for asset in assets:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            asset_id = asset.get("id")

            category = asset.get("category", "other")
            status = asset.get("status", "working")
            category_label = asset.get("category_display") or CATEGORY_LABELS.get(
                category, "—"
            )
            status_label = asset.get("status_display") or STATUS_LABELS.get(status, "—")

            name_item = QTableWidgetItem(asset.get("name", ""))
            name_item.setData(Qt.UserRole, asset_id)

            category_item = QTableWidgetItem(category_label)
            self._color_category(category_item, category)

            price = asset.get("price")
            price_item = QTableWidgetItem(
                f"{float(price):,.2f}" if price is not None else "—"
            )

            purchase_date = asset.get("purchase_date")
            date_text = str(purchase_date)[:10] if purchase_date else "—"
            date_item = QTableWidgetItem(date_text)

            status_item = QTableWidgetItem(status_label)
            self._color_status(status_item, status)

            dep = asset.get("depreciation_value")
            dep_item = QTableWidgetItem(
                f"{float(dep):,.2f}" if dep is not None else "—"
            )

            location_item = QTableWidgetItem(asset.get("location") or "—")
            responsible_item = QTableWidgetItem(asset.get("responsible_person") or "—")
            details = (asset.get("details") or "").strip()
            details_item = QTableWidgetItem(
                details[:60] + "…" if len(details) > 60 else (details or "—")
            )
            details_item.setToolTip(details if details else "")

            for col, item in enumerate(
                (
                    name_item,
                    category_item,
                    price_item,
                    date_item,
                    status_item,
                    dep_item,
                    location_item,
                    responsible_item,
                    details_item,
                )
            ):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_pos, col, item)

            self.table.setCellWidget(row_pos, 9, self._build_actions_widget(asset))
        self.table.setUpdatesEnabled(True)

    def _build_actions_widget(self, asset):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        asset_id = asset.get("id")
        asset_name = asset.get("name", "")

        edit_btn = QPushButton()
        edit_btn.setIcon(qta.icon("fa5s.edit", color="#60a5fa"))
        edit_btn.setToolTip("تعديل")
        edit_btn.setFlat(True)
        edit_btn.clicked.connect(lambda: self._open_edit_dialog(asset))

        att_btn = QPushButton()
        att_btn.setIcon(qta.icon("fa5s.paperclip", color="#9ca3af"))
        att_btn.setToolTip("المرفقات")
        att_btn.setFlat(True)
        att_btn.clicked.connect(
            lambda: self._open_attachments_dialog(asset_id, asset_name)
        )

        del_btn = QPushButton()
        del_btn.setIcon(qta.icon("fa5s.trash", color="#ef4444"))
        del_btn.setToolTip("حذف")
        del_btn.setFlat(True)
        del_btn.clicked.connect(lambda: self._confirm_delete(asset_id, asset_name))

        layout.addWidget(edit_btn)
        layout.addWidget(att_btn)
        layout.addWidget(del_btn)
        return widget

    @staticmethod
    def _color_category(item, category):
        item.setForeground(CATEGORY_COLORS.get(category, MUTED_COLOR))

    @staticmethod
    def _color_status(item, status):
        item.setForeground(STATUS_COLORS.get(status, MUTED_COLOR))

    def update_pagination_controls(self):
        self.next_button.setEnabled(self.next_page_url is not None)
        self.prev_button.setEnabled(self.prev_page_url is not None)
        if self.total_count > 0 and self.table.rowCount():
            self.page_info_label.setText(f"إجمالي {self.total_count} أصل")
        elif self.total_count == 0:
            self.page_info_label.setText("لا توجد أصول")
        else:
            self.page_info_label.setText(f"إجمالي {self.total_count} أصل")

    def show_error_message(self, message):
        self._set_controls_enabled(True)
        self._initial_load_done = True
        self._pending_load = False
        self._show_table_skeleton(False)
        if self.table.rowCount() == 0:
            self.table_stack.setCurrentIndex(2)
        self.page_info_label.setText("تعذر تحميل البيانات")
        if self._last_request_was_mutation:
            self._show_feedback(str(message), variant="error")
        else:
            self._show_feedback(f"تعذر تحميل البيانات: {message}", variant="error")

    def _set_controls_enabled(self, enabled):
        for widget in (
            self.btn_add_asset,
            self.show_all_button,
            self.btn_apply_filters,
            self.btn_reset_filters,
            self.search_input,
            self.category_filter,
            self.status_filter,
            self.next_button,
            self.prev_button,
        ):
            widget.setEnabled(enabled)

    def _show_table_skeleton(self, show):
        if show:
            self.table_stack.setCurrentIndex(1)
        elif self.table.rowCount():
            self.table_stack.setCurrentIndex(0)
        else:
            self.table_stack.setCurrentIndex(2)

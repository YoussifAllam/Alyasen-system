import os

import qtawesome as qta
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from ..Main_Ui_Components.date_edit import configure_date_edit, format_date
from ..Main_Ui_Components.ui_scale import apply_form_dialog_geometry, scale_int
from ..validation import (
    _clear_errors,
    attach_number_formatter,
    clean_number,
    validate_not_empty,
    validate_optional_number,
)

ASSET_CATEGORIES = [
    ("equipment", "معدات"),
    ("vehicle", "مركبة"),
    ("furniture", "أثاث"),
    ("electronics", "إلكترونيات"),
    ("other", "أخرى"),
]

ASSET_STATUSES = [
    ("working", "يعمل"),
    ("maintenance", "تحت الصيانة"),
    ("retired", "متقاعد"),
]

ATTACHMENT_FILTER = (
    "فواتير وضمان وصور (*.pdf *.png *.jpg *.jpeg);;مستندات PDF (*.pdf);;"
    "صور (*.png *.jpg *.jpeg);;كل الملفات (*)"
)
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024

# Baseline sizes at 1920×1080 — scaled via ui_scale.
_FORM_FIELD_HEIGHT = 38
_FORM_TEXT_HEIGHT = 72
_FORM_ROW_GAP = 10
_FORM_LABEL_WIDTH = 150


def _form_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("assetFormLabel")
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    label.setMinimumWidth(scale_int(_FORM_LABEL_WIDTH))
    label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    return label


def _configure_form_field(widget, *, multiline=False):
    """Sized inputs that stay readable with theme padding."""
    widget.setObjectName("dialogField")
    if multiline:
        h = scale_int(_FORM_TEXT_HEIGHT)
        widget.setMinimumHeight(h)
        widget.setMaximumHeight(h)
    else:
        h = scale_int(_FORM_FIELD_HEIGHT)
        widget.setFixedHeight(h)
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class AssetFormDialog(QDialog):
    """Add or edit a company asset with structured fields and optional attachments."""

    def __init__(self, *, asset_data=None, parent=None):
        super().__init__(parent)
        self.asset_data = asset_data or {}
        self.is_edit = bool(self.asset_data.get("id"))
        self.attachments_paths = []

        title = "تعديل أصل" if self.is_edit else "إضافة أصل جديد"
        self.setWindowTitle(title)
        apply_form_dialog_geometry(self)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("dialogContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setObjectName("dialogTitleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 0, 5, 0)
        title_text = QLabel(title)
        title_text.setObjectName("titleBarText")
        close_button = QPushButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(qta.icon("fa5s.times", color="#9ca3af"))
        close_button.clicked.connect(self.reject)
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        form_body = QWidget()
        form_body.setMinimumWidth(scale_int(520))
        form_body_layout = QVBoxLayout(form_body)
        form_body_layout.setContentsMargins(0, 0, 4, 0)
        form_body_layout.setSpacing(scale_int(12))

        form_grid = QGridLayout()
        form_grid.setVerticalSpacing(scale_int(_FORM_ROW_GAP))
        form_grid.setHorizontalSpacing(scale_int(14))
        form_grid.setColumnStretch(1, 1)
        form_grid.setColumnMinimumWidth(0, scale_int(_FORM_LABEL_WIDTH))

        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        for value, label in ASSET_CATEGORIES:
            self.category_input.addItem(label, value)
        self.price_input = QLineEdit()
        attach_number_formatter(self.price_input)
        self.purchase_date_input = QDateEdit(date=QDate.currentDate())
        configure_date_edit(self.purchase_date_input)
        self.status_input = QComboBox()
        for value, label in ASSET_STATUSES:
            self.status_input.addItem(label, value)
        self.useful_life_input = QLineEdit()
        self.useful_life_input.setPlaceholderText("مثال: 5")
        attach_number_formatter(self.useful_life_input)
        self.depreciation_input = QLineEdit()
        attach_number_formatter(self.depreciation_input)
        self.location_input = QLineEdit()
        self.responsible_input = QLineEdit()
        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText("وصف مختصر، رقم تسلسلي، ملاحظات...")

        for field in (
            self.name_input,
            self.category_input,
            self.price_input,
            self.purchase_date_input,
            self.status_input,
            self.useful_life_input,
            self.depreciation_input,
            self.location_input,
            self.responsible_input,
        ):
            _configure_form_field(field)
        _configure_form_field(self.details_input, multiline=True)

        rows = [
            ("اسم الأصل *", self.name_input),
            ("فئة الأصل *", self.category_input),
            ("سعر الشراء", self.price_input),
            ("تاريخ الشراء", self.purchase_date_input),
            ("حالة الأصل *", self.status_input),
            ("العمر الافتراضي (سنوات)", self.useful_life_input),
            ("القيمة الدفترية الحالية", self.depreciation_input),
            ("الموقع", self.location_input),
            ("المسؤول عنه", self.responsible_input),
            ("تفاصيل", self.details_input),
        ]
        for row_index, (label_text, field) in enumerate(rows):
            form_grid.addWidget(_form_label(label_text), row_index, 0)
            form_grid.addWidget(field, row_index, 1)

        form_body_layout.addLayout(form_grid)

        if not self.is_edit:
            att_hint = QLabel(
                "المرفقات: فاتورة شراء، ضمان، صور الأصل — PDF أو PNG/JPG، "
                f"بحد أقصى {MAX_ATTACHMENT_BYTES // (1024 * 1024)} ميجابايت لكل ملف"
            )
            att_hint.setWordWrap(True)
            att_hint.setObjectName("assetAttachmentHint")
            form_body_layout.addWidget(att_hint)

            self.attachments_label = QLabel("لم يتم اختيار مرفقات")
            self.attachments_label.setAlignment(Qt.AlignCenter)
            self.attachments_label.setObjectName("assetAttachmentStatus")
            btn_choose = QPushButton("  اختيار مرفقات")
            btn_choose.setIcon(qta.icon("fa5s.paperclip", color="#9ca3af"))
            btn_choose.clicked.connect(self._choose_attachments)
            form_body_layout.addWidget(self.attachments_label)
            form_body_layout.addWidget(btn_choose)

        form_body_layout.addStretch()
        scroll.setWidget(form_body)
        content_layout.addWidget(scroll, 1)

        self.form_feedback = QLabel()
        self.form_feedback.setObjectName("assetFormFeedback")
        self.form_feedback.setWordWrap(True)
        self.form_feedback.hide()
        content_layout.addWidget(self.form_feedback)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        self.save_button = QPushButton(
            "حفظ التعديلات" if self.is_edit else "إضافة الأصل"
        )
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._validate_and_accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self.save_button)
        content_layout.addLayout(buttons)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        if self.is_edit:
            self._prefill()

    @staticmethod
    def _refresh_widget_style(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _set_form_feedback(self, message: str, *, error: bool = True):
        variant = "error" if error else "success"
        self.form_feedback.setProperty("variant", variant)
        self.form_feedback.setText(message)
        self.form_feedback.show()
        self._refresh_widget_style(self.form_feedback)

    def _clear_form_feedback(self):
        self.form_feedback.hide()

    def _prefill(self):
        self.name_input.setText(self.asset_data.get("name", ""))
        category = self.asset_data.get("category", "other")
        idx = self.category_input.findData(category)
        if idx >= 0:
            self.category_input.setCurrentIndex(idx)
        price = self.asset_data.get("price")
        if price is not None:
            self.price_input.setText(str(price))
        purchase_date = self.asset_data.get("purchase_date")
        if purchase_date:
            parsed = QDate.fromString(str(purchase_date)[:10], "yyyy-MM-dd")
            if parsed.isValid():
                self.purchase_date_input.setDate(parsed)
        status = self.asset_data.get("status", "working")
        idx = self.status_input.findData(status)
        if idx >= 0:
            self.status_input.setCurrentIndex(idx)
        life = self.asset_data.get("useful_life_years")
        if life is not None:
            self.useful_life_input.setText(str(life))
        dep = self.asset_data.get("depreciation_value")
        if dep is not None:
            self.depreciation_input.setText(str(dep))
        self.location_input.setText(self.asset_data.get("location", "") or "")
        self.responsible_input.setText(
            self.asset_data.get("responsible_person", "") or ""
        )
        self.details_input.setPlainText(self.asset_data.get("details", "") or "")

    def _choose_attachments(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "اختر مرفقات الأصل", "", ATTACHMENT_FILTER
        )
        if not file_paths:
            return
        valid_paths = []
        for path in file_paths:
            size = os.path.getsize(path)
            if size > MAX_ATTACHMENT_BYTES:
                QMessageBox.warning(
                    self,
                    "حجم الملف",
                    f"الملف {os.path.basename(path)} يتجاوز الحد المسموح (10 ميجابايت).",
                )
                continue
            valid_paths.append(path)
        if valid_paths:
            self.attachments_paths = valid_paths
            names = ", ".join(os.path.basename(p) for p in valid_paths[:3])
            if len(valid_paths) > 3:
                names += f" (+{len(valid_paths) - 3})"
            self.attachments_label.setText(f"تم اختيار {len(valid_paths)} ملف: {names}")
            self._set_form_feedback(
                f"تم اختيار {len(valid_paths)} مرفق/مرفقات بنجاح.",
                error=False,
            )

    def _validate_and_accept(self):
        fields = [
            self.name_input,
            self.price_input,
            self.useful_life_input,
            self.depreciation_input,
        ]
        _clear_errors(fields)
        self._clear_form_feedback()
        validations = [
            validate_not_empty(self.name_input, "اسم الأصل"),
            validate_optional_number(self.price_input, "سعر الشراء"),
            validate_optional_number(self.useful_life_input, "العمر الافتراضي"),
            validate_optional_number(self.depreciation_input, "القيمة الدفترية"),
        ]
        errors = [msg for is_valid, msg in validations if not is_valid]
        if errors:
            self._set_form_feedback(
                "يرجى تصحيح الحقول التالية:\n" + "\n".join(f"• {e}" for e in errors)
            )
            return
        self.accept()

    def get_payload(self) -> dict:
        payload = {
            "name": self.name_input.text().strip(),
            "category": self.category_input.currentData(),
            "status": self.status_input.currentData(),
            "location": self.location_input.text().strip(),
            "responsible_person": self.responsible_input.text().strip(),
            "details": self.details_input.toPlainText().strip(),
            "purchase_date": format_date(self.purchase_date_input.date()),
        }
        price = clean_number(self.price_input.text())
        if price:
            payload["price"] = float(price)
        life = clean_number(self.useful_life_input.text())
        if life:
            payload["useful_life_years"] = int(float(life))
        dep = clean_number(self.depreciation_input.text())
        if dep:
            payload["depreciation_value"] = float(dep)
        if self.is_edit:
            payload["id"] = self.asset_data["id"]
        return payload

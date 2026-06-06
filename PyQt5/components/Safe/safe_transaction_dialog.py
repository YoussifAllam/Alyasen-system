from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QFormLayout,
    QWidget,
    QTextEdit,
)
from PyQt5.QtCore import Qt
import qtawesome as qta

from ..Main_Ui_Components.ui_scale import apply_form_dialog_geometry
from ..validation import (
    validate_positive_number,
    run_validations,
    _clear_errors,
    attach_number_formatter,
    clean_number,
)


class SafeTransactionDialog(QDialog):
    """Quick deposit or withdrawal against the company safe."""

    def __init__(self, process: str, parent=None):
        super().__init__(parent)
        self.process = process
        is_deposit = process == "add"
        title = "إيداع في الخزنة" if is_deposit else "سحب من الخزنة"

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
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.amount_input = QLineEdit()
        attach_number_formatter(self.amount_input)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظة اختيارية...")

        form_layout.addRow("المبلغ *", self.amount_input)
        form_layout.addRow("ملاحظات", self.notes_input)
        content_layout.addLayout(form_layout)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        self.save_button = QPushButton("إيداع" if is_deposit else "سحب")
        self.save_button.setObjectName(
            "primaryButton" if is_deposit else "dangerButton"
        )
        self.save_button.clicked.connect(self._validate_and_accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self.save_button)
        content_layout.addLayout(buttons)

        main_layout.addWidget(content_area)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

    def _validate_and_accept(self):
        fields = [self.amount_input]
        _clear_errors(fields)
        if not run_validations(
            self,
            [
                validate_positive_number(self.amount_input, field_name="المبلغ"),
            ],
        ):
            return
        self.accept()

    def get_payload(self) -> dict:
        return {
            "process": self.process,
            "amount": float(clean_number(self.amount_input.text())),
            "note": self.notes_input.toPlainText().strip(),
        }

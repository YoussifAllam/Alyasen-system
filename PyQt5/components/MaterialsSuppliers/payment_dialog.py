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
from PyQt5.QtCore import Qt, QPoint
import qtawesome as qta


class PaymentDialog(QDialog):
    def __init__(self, supplier_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسديد مبلغ للفاتورة")
        self.setMinimumSize(450, 350)
        self.setModal(True)

        # Frameless Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

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

        title_text = QLabel(f"تسديد دفعة للمورد رقم: {supplier_id}")
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
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.amount_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        form_layout.addRow("المبلغ المدفوع:", self.amount_input)
        form_layout.addRow("ملاحظات:", self.notes_input)

        content_layout.addLayout(form_layout)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("حفظ")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.accept)

        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        content_layout.addLayout(button_layout)

        self.main_layout.addWidget(content_area)

        # Set the main layout for the dialog
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        self.old_pos = None

    def get_data(self):
        """Returns the data entered in the dialog."""
        return {
            "payment_amount": self.amount_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

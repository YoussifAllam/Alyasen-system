from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QRectF


class DonutChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(160, 160)
        self.data = []
        self.center_text = ""

    def setData(self, data, center_text):
        """Sets the chart data and center text, then triggers a repaint."""
        self.data = data
        self.center_text = center_text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        side = min(rect.width(), rect.height())

        painter.setViewport((rect.width() - side) // 2, (rect.height() - side) // 2, side, side)
        painter.setWindow(-55, -55, 110, 110)

        # Draw the background circle
        pen = QPen(QColor("#374151"), 18)
        painter.setPen(pen)
        painter.drawEllipse(-45, -45, 90, 90)

        # Draw the data segments
        pen.setWidth(18)
        pen.setCapStyle(Qt.FlatCap)

        total_value = sum(item["value"] for item in self.data)
        if total_value == 0:
            return

        start_angle = 90 * 16

        for item in self.data:
            angle = (item["value"] / total_value) * 360 * 16
            pen.setColor(QColor(item["color"]))
            painter.setPen(pen)
            painter.drawArc(-45, -45, 90, 90, start_angle, -int(angle))
            start_angle -= int(angle)

        # Draw the center text
        font = QFont("Cairo", 6, QFont.Black)  # Increased font size
        painter.setFont(font)
        pen.setColor(QColor("#ffffff"))
        painter.setPen(pen)
        painter.drawText(QRectF(-45, -45, 90, 90), Qt.AlignCenter, self.center_text)

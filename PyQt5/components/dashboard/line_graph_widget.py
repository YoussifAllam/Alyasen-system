from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF
from PyQt5.QtCore import Qt, QPointF


class LineGraphWidget(QWidget):
    """A custom widget to draw a simple line graph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.sales_data = []
        self.expenses_data = []
        self.labels = []

    def setData(self, labels, sales, expenses):
        """Sets the data for the graph and triggers a repaint."""
        self.labels = labels
        self.sales_data = sales
        self.expenses_data = expenses
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.sales_data or not self.expenses_data:
            return

        # Drawing area dimensions
        padding = 20
        graph_width = self.width() - 2 * padding
        graph_height = self.height() - 2 * padding - 30  # Space for labels

        # Find max value to scale the graph
        max_value = 0
        if self.sales_data:
            max_value = max(max_value, max(self.sales_data))
        if self.expenses_data:
            max_value = max(max_value, max(self.expenses_data))
        if max_value == 0:
            return

        # Draw axis lines (optional, for aesthetics)
        pen = QPen(QColor("#374151"), 2, Qt.SolidLine)
        painter.setPen(pen)
        painter.drawLine(
            padding, padding + graph_height, padding + graph_width, padding + graph_height
        )  # X-axis

        # Prepare points for sales and expenses
        num_points = len(self.labels)
        x_step = graph_width / (num_points - 1) if num_points > 1 else graph_width

        sales_points = QPolygonF()
        expenses_points = QPolygonF()

        for i in range(num_points):
            x = padding + i * x_step

            y_sales = padding + graph_height - (self.sales_data[i] / max_value * graph_height)
            sales_points.append(QPointF(x, y_sales))

            y_expenses = padding + graph_height - (self.expenses_data[i] / max_value * graph_height)
            expenses_points.append(QPointF(x, y_expenses))

            # Draw X-axis labels
            painter.setPen(QColor("#9ca3af"))
            # Fixed LineGraphWidget.paintEvent
            # Allocate more horizontal space (e.g., 70 pixels) for the label text
            label_width = 70
            painter.drawText(
                int(x) - (label_width // 2),
                padding + graph_height + 20,
                label_width,
                30,
                Qt.AlignCenter,
                self.labels[i],
            )

        # Draw the sales line
        pen.setColor(QColor("#00bc88"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPolyline(sales_points)

        # Draw the expenses line
        pen.setColor(QColor("#ef4444"))
        painter.setPen(pen)
        painter.drawPolyline(expenses_points)

        # Draw points on the lines
        painter.setBrush(QColor("#1f2937"))
        for point in sales_points:
            pen.setColor(QColor("#00bc88"))
            painter.setPen(pen)
            painter.drawEllipse(point, 5, 5)

        for point in expenses_points:
            pen.setColor(QColor("#ef4444"))
            painter.setPen(pen)
            painter.drawEllipse(point, 5, 5)

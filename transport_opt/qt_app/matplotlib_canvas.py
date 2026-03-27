from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QFrame, QSizePolicy

from .theme import ThemePalette, get_theme


class ChartCanvas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(360, 280)
        self._theme: ThemePalette = get_theme("light")
        self._mode = "empty"
        self._title = ""
        self._x_label = ""
        self._y_label = ""
        self._color = QColor("#3182CE")
        self._labels: list[str] = []
        self._values: list[float] = []

    def set_theme(self, theme_name: str) -> None:
        self._theme = get_theme(theme_name)
        self.update()

    def plot_line(self, x, y, title: str, x_label: str, y_label: str, color: str) -> None:
        labels, values = self._normalize_pairs(x, y)
        self._mode = "line"
        self._title = title
        self._x_label = x_label
        self._y_label = y_label
        self._color = QColor(color)
        self._labels = labels
        self._values = values
        self.update()

    def plot_bar(self, labels, values, title: str, x_label: str, y_label: str, color: str) -> None:
        normalized_labels, normalized_values = self._normalize_pairs(labels, values)
        self._mode = "bar"
        self._title = title
        self._x_label = x_label
        self._y_label = y_label
        self._color = QColor(color)
        self._labels = normalized_labels
        self._values = normalized_values
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        outer_rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(self._theme.card_border), 1))
        painter.setBrush(QColor(self._theme.chart_bg))
        painter.drawRoundedRect(outer_rect, 16, 16)

        content_rect = QRectF(outer_rect.adjusted(18, 14, -18, -18))
        if content_rect.width() < 200 or content_rect.height() < 160:
            return

        self._draw_title(painter, content_rect)
        plot_rect = QRectF(
            content_rect.left() + 56,
            content_rect.top() + 38,
            content_rect.width() - 78,
            content_rect.height() - 90,
        )
        if plot_rect.width() < 120 or plot_rect.height() < 80:
            return

        self._draw_plot_background(painter, plot_rect)
        self._draw_axes_labels(painter, plot_rect, content_rect)

        if not self._values:
            painter.setPen(QColor(self._theme.chart_muted))
            painter.drawText(plot_rect, Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return

        y_min, y_max = self._value_bounds()
        self._draw_grid(painter, plot_rect, y_min, y_max)
        self._draw_axes(painter, plot_rect)

        if self._mode == "line":
            self._draw_line_series(painter, plot_rect, y_min, y_max)
        else:
            self._draw_bar_series(painter, plot_rect, y_min, y_max)

        self._draw_ticks(painter, plot_rect, y_min, y_max)

    def _draw_title(self, painter: QPainter, content_rect: QRectF) -> None:
        painter.setPen(QColor(self._theme.chart_text))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.drawText(
            QRectF(content_rect.left(), content_rect.top(), content_rect.width(), 24),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._title,
        )

    def _draw_plot_background(self, painter: QPainter, plot_rect: QRectF) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._theme.chart_plot_bg))
        painter.drawRoundedRect(plot_rect, 12, 12)

    def _draw_axes_labels(self, painter: QPainter, plot_rect: QRectF, content_rect: QRectF) -> None:
        painter.setPen(QColor(self._theme.chart_muted))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(plot_rect.left(), plot_rect.bottom() + 8, plot_rect.width(), 18),
            Qt.AlignmentFlag.AlignCenter,
            self._x_label,
        )

        painter.save()
        painter.translate(content_rect.left() + 8, plot_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot_rect.height() / 2, -18, plot_rect.height(), 18),
            Qt.AlignmentFlag.AlignCenter,
            self._y_label,
        )
        painter.restore()

    def _draw_grid(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        steps = 5
        grid_pen = QPen(QColor(self._theme.chart_grid), 1)
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)

        for step in range(steps + 1):
            ratio = step / steps
            y = plot_rect.bottom() - ratio * plot_rect.height()
            painter.drawLine(
                QPointF(plot_rect.left(), y),
                QPointF(plot_rect.right(), y),
            )

    def _draw_axes(self, painter: QPainter, plot_rect: QRectF) -> None:
        painter.setPen(QPen(QColor(self._theme.chart_axis), 1.2))
        painter.drawLine(QPointF(plot_rect.left(), plot_rect.bottom()), QPointF(plot_rect.right(), plot_rect.bottom()))
        painter.drawLine(QPointF(plot_rect.left(), plot_rect.top()), QPointF(plot_rect.left(), plot_rect.bottom()))

    def _draw_line_series(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        points = [self._line_point(index, value, plot_rect, y_min, y_max) for index, value in enumerate(self._values)]
        if not points:
            return

        clip_rect = QRectF(plot_rect.adjusted(0, 0, 0, 0))
        painter.save()
        painter.setClipRect(clip_rect)

        fill_color = QColor(self._color)
        fill_color.setAlpha(48)
        area_path = QPainterPath(QPointF(points[0].x(), plot_rect.bottom()))
        area_path.lineTo(points[0])
        for point in points[1:]:
            area_path.lineTo(point)
        area_path.lineTo(QPointF(points[-1].x(), plot_rect.bottom()))
        area_path.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        painter.drawPath(area_path)

        line_pen = QPen(self._color, 2.8)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        painter.drawPath(path)

        painter.setBrush(self._color)
        painter.setPen(QPen(QColor(self._theme.chart_bg), 2))
        for point in points:
            painter.drawEllipse(point, 4.5, 4.5)
        painter.restore()

    def _draw_bar_series(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        count = len(self._values)
        if count == 0:
            return

        slot_width = plot_rect.width() / max(count, 1)
        bar_width = max(min(slot_width * 0.7, 48.0), 10.0)
        painter.save()
        painter.setClipRect(plot_rect)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)

        for index, value in enumerate(self._values):
            x_center = plot_rect.left() + slot_width * (index + 0.5)
            top = self._value_to_y(value, plot_rect, y_min, y_max)
            bar_rect = QRectF(x_center - bar_width / 2, top, bar_width, plot_rect.bottom() - top)
            painter.drawRoundedRect(bar_rect, 5, 5)

        painter.restore()

        if count <= 8:
            painter.setPen(QColor(self._theme.chart_text))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            for index, value in enumerate(self._values):
                x_center = plot_rect.left() + slot_width * (index + 0.5)
                top = self._value_to_y(value, plot_rect, y_min, y_max)
                text_rect = QRectF(x_center - 26, max(plot_rect.top(), top - 18), 52, 16)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._format_value(value))

    def _draw_ticks(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        painter.setPen(QColor(self._theme.chart_muted))
        painter.setFont(QFont("Segoe UI", 8))

        steps = 5
        for step in range(steps + 1):
            ratio = step / steps
            y = plot_rect.bottom() - ratio * plot_rect.height()
            value = y_min + (y_max - y_min) * ratio
            text_rect = QRectF(plot_rect.left() - 52, y - 8, 44, 16)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._format_value(value))

        if not self._labels:
            return

        tick_count = min(len(self._labels), 6)
        if self._mode == "line" and len(self._labels) == 1:
            positions = [0]
        else:
            positions = [round(index * (len(self._labels) - 1) / max(tick_count - 1, 1)) for index in range(tick_count)]

        seen: set[int] = set()
        for position in positions:
            if position in seen:
                continue
            seen.add(position)
            x = self._x_for_index(position, plot_rect)
            text_rect = QRectF(x - 36, plot_rect.bottom() + 0.5, 72, 18)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._labels[position])

    def _line_point(self, index: int, value: float, plot_rect: QRectF, y_min: float, y_max: float) -> QPointF:
        return QPointF(self._x_for_index(index, plot_rect), self._value_to_y(value, plot_rect, y_min, y_max))

    def _x_for_index(self, index: int, plot_rect: QRectF) -> float:
        count = max(len(self._labels), 1)
        if self._mode == "bar":
            return plot_rect.left() + plot_rect.width() * (index + 0.5) / count
        if count == 1:
            return plot_rect.center().x()
        return plot_rect.left() + plot_rect.width() * index / (count - 1)

    def _value_to_y(self, value: float, plot_rect: QRectF, y_min: float, y_max: float) -> float:
        span = max(y_max - y_min, 1e-6)
        ratio = (value - y_min) / span
        return plot_rect.bottom() - ratio * plot_rect.height()

    def _value_bounds(self) -> tuple[float, float]:
        minimum = min(self._values)
        maximum = max(self._values)
        if minimum >= 0 and maximum <= 100:
            return 0.0, 100.0
        if self._mode == "bar":
            minimum = min(0.0, minimum)
        if minimum == maximum:
            padding = max(abs(maximum) * 0.15, 1.0)
            return minimum - padding, maximum + padding
        padding = (maximum - minimum) * 0.12
        if self._mode == "bar":
            padding = max(padding, maximum * 0.08 if maximum else 1.0)
            minimum = min(0.0, minimum)
        return minimum - padding * 0.2, maximum + padding

    def _normalize_pairs(self, labels: Sequence, values: Sequence) -> tuple[list[str], list[float]]:
        normalized_labels: list[str] = []
        normalized_values: list[float] = []
        for label, value in zip(labels, values):
            normalized_labels.append(str(label))
            normalized_values.append(float(value))
        return normalized_labels, normalized_values

    @staticmethod
    def _format_value(value: float) -> str:
        if abs(value) >= 100 or float(value).is_integer():
            return str(int(round(value)))
        return f"{value:.1f}"

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QDate, QPoint, QTime, QTimer, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QListView,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .data_service import AppDataService
from .map_widget import TransportMapPanel
from .chart_canvas import ChartCanvas
from .theme import get_theme


def _configure_table(table: QTableWidget, headers: list[str]) -> None:
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(False)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.verticalHeader().setVisible(False)
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    header.setStretchLastSection(True)
    header.setHighlightSections(False)
    header.setSortIndicatorShown(True)


def _create_item(value: object) -> QTableWidgetItem:
    item = QTableWidgetItem("" if value is None else str(value))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


def _create_button(text: str, slot, kind: str | None = None) -> QPushButton:
    button = QPushButton(text)
    if kind:
        button.setProperty("kind", kind)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.clicked.connect(slot)
    return button


def _format_percent(value: float) -> str:
    return f"{float(value):.1f}%"


def _configure_combo(combo: QComboBox, minimum_width: int = 220) -> None:
    view = QListView()
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    view.setTextElideMode(Qt.TextElideMode.ElideRight)
    view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    view.setUniformItemSizes(True)
    view.setWordWrap(False)
    view.setAutoScroll(False)

    combo.setView(view)
    combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    combo.setCursor(Qt.CursorShape.PointingHandCursor)
    combo.setMinimumWidth(minimum_width)
    combo.setMaxVisibleItems(10)
    combo.setMinimumContentsLength(16)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

def _configure_date_edit(widget: QDateEdit) -> None:
    calendar = QCalendarWidget()
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
    calendar.setGridVisible(False)
    widget.setCalendarWidget(calendar)
    widget.setCalendarPopup(True)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)


def _configure_list_widget(widget: QListWidget) -> None:
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    widget.setWordWrap(True)


def _configure_plain_text(widget: QPlainTextEdit) -> None:
    widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    widget.setCenterOnScroll(False)


class NumericTableItem(QTableWidgetItem):
    def __init__(self, display: str, numeric_value: float):
        super().__init__(display)
        self.setData(Qt.ItemDataRole.UserRole, float(numeric_value))
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        if left is None or right is None:
            return super().__lt__(other)
        return float(left) < float(right)


class PopupComboBox(QComboBox):
    def showPopup(self) -> None:
        super().showPopup()
        QTimer.singleShot(0, self._position_popup)

    def _position_popup(self) -> None:
        popup = self.view().window()
        view = self.view()
        screen = self.screen()
        if screen is None:
            return

        available = screen.availableGeometry()
        row_height = max(view.sizeHintForRow(0), 34)
        visible_rows = min(max(self.count(), 1), self.maxVisibleItems())
        popup_height = min(row_height * visible_rows + 10, 320)
        popup_width = max(self.width(), min(view.sizeHintForColumn(0) + 42, 460))

        below_left = self.mapToGlobal(QPoint(0, self.height() + 6))
        above_left = self.mapToGlobal(QPoint(0, -popup_height - 6))
        x = min(max(below_left.x(), available.left() + 8), max(available.right() - popup_width - 8, available.left() + 8))
        y = below_left.y()
        if y + popup_height > available.bottom() and above_left.y() >= available.top():
            y = above_left.y()

        popup.setMinimumWidth(popup_width)
        popup.setGeometry(x, y, popup_width, popup_height)
        popup.raise_()

    def wheelEvent(self, event) -> None:
        if not self.view().isVisible():
            event.ignore()
        else:
            super().wheelEvent(event)


class MetricCard(QFrame):
    def __init__(self, title: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.accent = accent
        self.accent_bar = QFrame()
        self.accent_bar.setFixedHeight(6)
        self.accent_bar.setObjectName("metricAccent")
        self.accent_bar.setStyleSheet(f"background: {accent}; border: none; border-radius: 6px;")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("metricValue")
        self.note_label = QLabel("")
        self.note_label.setObjectName("metricNote")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(8)
        layout.addWidget(self.accent_bar)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.note_label)

    def set_value(self, value: str, note: str = "") -> None:
        self.value_label.setText(value)
        self.note_label.setText(note)


class BasePage(QWidget):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.on_data_changed = on_data_changed
        self.search_query = ""
        self.theme_name = "light"

    def reload(self) -> None:
        raise NotImplementedError

    def apply_search(self, query: str) -> None:
        self.search_query = query.strip()
        self.reload()

    def set_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name
        for chart in self.findChildren(ChartCanvas):
            chart.set_theme(theme_name)

    def _notify_change(self, message: str) -> None:
        if self.on_data_changed is not None:
            self.on_data_changed(message)
        else:
            self.reload()


class DashboardPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.total_card = MetricCard("Автобусов в парке", "#C2410C")
        self.active_card = MetricCard("В рейсе за день", "#0F766E")
        self.avg_card = MetricCard("Средняя загрузка", "#1D4ED8")
        self.critical_card = MetricCard("Критические маршруты", "#B91C1C")
        self.top_chart = ChartCanvas(self)
        self.top_table = QTableWidget()
        self.recommendations_list = QListWidget()
        self.recommendations_list.setObjectName("recommendationList")
        _configure_list_widget(self.recommendations_list)
        self.report_label = QLabel()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        for card in (self.total_card, self.active_card, self.avg_card, self.critical_card):
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        left_card = QFrame()
        left_card.setObjectName("contentCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)
        title = QLabel("Топ-5 маршрутов по загрузке")
        title.setObjectName("sectionTitle")
        left_layout.addWidget(title)
        left_layout.addWidget(self.top_chart, stretch=1)
        _configure_table(self.top_table, ["Маршрут", "Направление", "Загрузка"])
        self.top_table.setMinimumHeight(220)
        left_layout.addWidget(self.top_table)
        content_row.addWidget(left_card, stretch=3)

        right_card = QFrame()
        right_card.setObjectName("contentCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        rec_title = QLabel("Рекомендации системы")
        rec_title.setObjectName("sectionTitle")
        right_layout.addWidget(rec_title)
        self.report_label.setObjectName("pageHint")
        self.report_label.setWordWrap(True)
        right_layout.addWidget(self.report_label)
        self.recommendations_list.setMinimumWidth(320)
        right_layout.addWidget(self.recommendations_list, stretch=1)
        content_row.addWidget(right_card, stretch=2)

        root.addLayout(content_row, stretch=1)

    def reload(self) -> None:
        palette = get_theme(self.theme_name)
        metrics = self.service.dashboard_metrics()
        self.total_card.set_value(str(metrics.total_buses), "Все автобусы в базе")
        self.active_card.set_value(str(metrics.active_buses), f"Отчетная дата: {metrics.reference_date}")
        self.avg_card.set_value(f"{metrics.avg_load:.1f}%", "Среднее за последние 7 дней")
        self.critical_card.set_value(str(metrics.critical_routes), "Загрузка выше 85%")

        top_routes = self.service.top_routes(5, self.search_query)
        if top_routes.empty:
            self.top_chart.plot_bar([], [], "Топ маршрутов", "Маршрут", "Загрузка", "#C2410C")
        else:
            self.top_chart.plot_bar(
                top_routes["route_number"],
                top_routes["avg_load"],
                title="Загрузка маршрутов",
                x_label="Маршрут",
                y_label="Средняя загрузка, %",
                color="#C2410C",
            )

        self.top_table.setRowCount(len(top_routes))
        for row_index, row in enumerate(top_routes.itertuples(index=False)):
            values = [row.route_number, row.route_name, _format_percent(row.avg_load)]
            for column_index, value in enumerate(values):
                self.top_table.setItem(row_index, column_index, _create_item(value))

        recommendations = self.service.recommendations(self.search_query)
        self.recommendations_list.clear()
        if not recommendations and self.search_query:
            self.recommendations_list.addItem("По текущему запросу совпадений не найдено.")
        else:
            for item in recommendations[:8]:
                list_item = QListWidgetItem(item)
                if item.startswith("[Критично]"):
                    list_item.setForeground(QColor(palette.recommendation_critical))
                elif item.startswith("[Высокая загрузка]"):
                    list_item.setForeground(QColor(palette.recommendation_warning))
                elif item.startswith("[Низкая загрузка]"):
                    list_item.setForeground(QColor(palette.recommendation_low))
                self.recommendations_list.addItem(list_item)

        if self.search_query:
            self.report_label.setText(f"Результаты по запросу «{self.search_query}».")
        else:
            self.report_label.setText(
                f"Сводка по автопарку и ключевые маршруты. Данные обновлены на {metrics.reference_date}."
            )


class AnalyticsPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.hourly_chart = ChartCanvas(self)
        self.routes_chart = ChartCanvas(self)
        self.analysis_table = QTableWidget()
        self.report_text = QPlainTextEdit()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        hourly_card = QFrame()
        hourly_card.setObjectName("contentCard")
        hourly_layout = QVBoxLayout(hourly_card)
        hourly_layout.setContentsMargins(18, 18, 18, 18)
        hourly_layout.setSpacing(12)
        hourly_title = QLabel("Средняя загрузка по часам")
        hourly_title.setObjectName("sectionTitle")
        hourly_layout.addWidget(hourly_title)
        hourly_layout.addWidget(self.hourly_chart, stretch=1)
        charts_row.addWidget(hourly_card, stretch=1)

        routes_card = QFrame()
        routes_card.setObjectName("contentCard")
        routes_layout = QVBoxLayout(routes_card)
        routes_layout.setContentsMargins(18, 18, 18, 18)
        routes_layout.setSpacing(12)
        routes_title = QLabel("Средняя загрузка по маршрутам")
        routes_title.setObjectName("sectionTitle")
        routes_layout.addWidget(routes_title)
        routes_layout.addWidget(self.routes_chart, stretch=1)
        charts_row.addWidget(routes_card, stretch=1)

        root.addLayout(charts_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        table_card = QFrame()
        table_card.setObjectName("contentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)
        table_title = QLabel("Детализация по маршрутам")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        _configure_table(
            self.analysis_table,
            ["Маршрут", "Название", "Утро", "Вечер", "Среднее", "Рейсов"],
        )
        table_layout.addWidget(self.analysis_table)
        bottom_row.addWidget(table_card, stretch=3)

        report_card = QFrame()
        report_card.setObjectName("contentCard")
        report_layout = QVBoxLayout(report_card)
        report_layout.setContentsMargins(18, 18, 18, 18)
        report_layout.setSpacing(12)
        report_title = QLabel("Текстовый аналитический отчет")
        report_title.setObjectName("sectionTitle")
        report_layout.addWidget(report_title)
        self.report_text.setReadOnly(True)
        self.report_text.setObjectName("reportText")
        _configure_plain_text(self.report_text)
        report_layout.addWidget(self.report_text)
        bottom_row.addWidget(report_card, stretch=2)

        root.addLayout(bottom_row, stretch=1)

    def reload(self) -> None:
        hourly = self.service.hourly_analysis()
        self.hourly_chart.plot_line(
            hourly["hour"] if not hourly.empty else [],
            hourly["avg_load"] if not hourly.empty else [],
            title="Пиковые и спокойные часы",
            x_label="Час дня",
            y_label="Средняя загрузка, %",
            color="#0F766E",
        )

        route_analysis = self.service.route_load_analysis(self.search_query)
        self.routes_chart.plot_bar(
            route_analysis["route_number"] if not route_analysis.empty else [],
            route_analysis["avg_load"] if not route_analysis.empty else [],
            title="Маршруты по средней загрузке",
            x_label="Маршрут",
            y_label="Средняя загрузка, %",
            color="#1D4ED8",
        )

        self.analysis_table.setRowCount(len(route_analysis))
        for row_index, row in enumerate(route_analysis.itertuples(index=False)):
            values = [
                row.route_number,
                row.route_name,
                _format_percent(row.morning_load),
                _format_percent(row.evening_load),
                _format_percent(row.avg_load),
                int(row.trip_count),
            ]
            for column_index, value in enumerate(values):
                self.analysis_table.setItem(row_index, column_index, _create_item(value))

        if self.search_query:
            if route_analysis.empty:
                self.report_text.setPlainText(f"По запросу «{self.search_query}» совпадений не найдено.")
            else:
                lines = [f"Результаты по запросу: {self.search_query}", "=" * 60, ""]
                for row in route_analysis.itertuples(index=False):
                    lines.extend(
                        [
                            f"Маршрут {row.route_number}: {row.route_name}",
                            f"  Утро: {row.morning_load:.1f}%",
                            f"  Вечер: {row.evening_load:.1f}%",
                            f"  Среднее: {row.avg_load:.1f}%",
                            f"  Рейсов: {int(row.trip_count)}",
                            "-" * 48,
                        ]
                    )
                self.report_text.setPlainText("\n".join(lines))
        else:
            self.report_text.setPlainText(self.service.analytics_report())


class BusesPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.gov_input = QLineEdit()
        self.model_input = QLineEdit()
        self.capacity_input = QSpinBox()
        self.table = QTableWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        form_card = QFrame()
        form_card.setObjectName("contentCard")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        title = QLabel("Добавление автобуса")
        title.setObjectName("sectionTitle")
        form_layout.addWidget(title, 0, 0, 1, 6)

        self.gov_input.setPlaceholderText("Госномер")
        self.model_input.setPlaceholderText("Модель")
        self.capacity_input.setRange(1, 300)
        self.capacity_input.setValue(100)

        form_layout.addWidget(QLabel("Госномер"), 1, 0)
        form_layout.addWidget(self.gov_input, 1, 1)
        form_layout.addWidget(QLabel("Модель"), 1, 2)
        form_layout.addWidget(self.model_input, 1, 3)
        form_layout.addWidget(QLabel("Вместимость"), 1, 4)
        form_layout.addWidget(self.capacity_input, 1, 5)

        form_layout.addWidget(_create_button("Добавить автобус", self._add_bus, kind="primary"), 2, 5)
        root.addWidget(form_card)

        table_card = QFrame()
        table_card.setObjectName("contentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)
        table_title = QLabel("Справочник автобусов")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        _configure_table(self.table, ["ID", "Госномер", "Модель", "Вместимость"])
        table_layout.addWidget(self.table)
        root.addWidget(table_card, stretch=1)

    def reload(self) -> None:
        buses = self.service.buses(self.search_query)
        self.table.setRowCount(len(buses))
        for row_index, row in enumerate(buses.itertuples(index=False)):
            values = [row.id, row.gov_number, row.model, row.capacity]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, _create_item(value))

    def _add_bus(self) -> None:
        try:
            self.service.add_bus(
                self.gov_input.text(),
                self.model_input.text(),
                int(self.capacity_input.value()),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Автобусы", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Автобусы", str(error))
            return

        self.gov_input.clear()
        self.model_input.clear()
        self.capacity_input.setValue(100)
        self._notify_change("Автобус добавлен.")


class RoutesPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.number_input = QLineEdit()
        self.name_input = QLineEdit()
        self.table = QTableWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        form_card = QFrame()
        form_card.setObjectName("contentCard")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        title = QLabel("Добавление маршрута")
        title.setObjectName("sectionTitle")
        form_layout.addWidget(title, 0, 0, 1, 5)

        self.number_input.setPlaceholderText("Номер маршрута")
        self.name_input.setPlaceholderText("Название маршрута")

        form_layout.addWidget(QLabel("Номер"), 1, 0)
        form_layout.addWidget(self.number_input, 1, 1)
        form_layout.addWidget(QLabel("Название"), 1, 2)
        form_layout.addWidget(self.name_input, 1, 3)

        form_layout.addWidget(_create_button("Добавить маршрут", self._add_route, kind="primary"), 1, 4)
        root.addWidget(form_card)

        table_card = QFrame()
        table_card.setObjectName("contentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)
        table_title = QLabel("Справочник маршрутов")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        _configure_table(self.table, ["ID", "Номер", "Название"])
        table_layout.addWidget(self.table)
        root.addWidget(table_card, stretch=1)

    def reload(self) -> None:
        routes = self.service.routes(self.search_query)
        self.table.setRowCount(len(routes))
        for row_index, row in enumerate(routes.itertuples(index=False)):
            values = [row.id, row.route_number, row.route_name]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, _create_item(value))

    def _add_route(self) -> None:
        try:
            self.service.add_route(self.number_input.text(), self.name_input.text())
        except ValueError as error:
            QMessageBox.warning(self, "Маршруты", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Маршруты", str(error))
            return

        self.number_input.clear()
        self.name_input.clear()
        self._notify_change("Маршрут добавлен.")


class DriversPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.name_input = QLineEdit()
        self.license_input = QLineEdit()
        self.table = QTableWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        form_card = QFrame()
        form_card.setObjectName("contentCard")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        title = QLabel("Добавление водителя")
        title.setObjectName("sectionTitle")
        form_layout.addWidget(title, 0, 0, 1, 5)

        self.name_input.setPlaceholderText("ФИО")
        self.license_input.setPlaceholderText("Номер прав")

        form_layout.addWidget(QLabel("ФИО"), 1, 0)
        form_layout.addWidget(self.name_input, 1, 1)
        form_layout.addWidget(QLabel("Номер прав"), 1, 2)
        form_layout.addWidget(self.license_input, 1, 3)

        form_layout.addWidget(_create_button("Добавить водителя", self._add_driver, kind="primary"), 1, 4)
        root.addWidget(form_card)

        table_card = QFrame()
        table_card.setObjectName("contentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)
        table_title = QLabel("Справочник водителей")
        table_title.setObjectName("sectionTitle")
        table_layout.addWidget(table_title)
        _configure_table(self.table, ["ID", "ФИО", "Номер прав"])
        table_layout.addWidget(self.table)
        root.addWidget(table_card, stretch=1)

    def reload(self) -> None:
        drivers = self.service.drivers(self.search_query)
        self.table.setRowCount(len(drivers))
        for row_index, row in enumerate(drivers.itertuples(index=False)):
            values = [row.id, row.full_name, row.license_number]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, _create_item(value))

    def _add_driver(self) -> None:
        try:
            self.service.add_driver(self.name_input.text(), self.license_input.text())
        except ValueError as error:
            QMessageBox.warning(self, "Водители", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Водители", str(error))
            return

        self.name_input.clear()
        self.license_input.clear()
        self._notify_change("Водитель добавлен.")


class TripsPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.route_combo = PopupComboBox()
        self.bus_combo = PopupComboBox()
        self.driver_combo = PopupComboBox()
        self.date_edit = QDateEdit()
        self.time_edit = QTimeEdit()
        self.passenger_input = QSpinBox()
        self.load_preview = QLabel("Загрузка: 0%")
        self.table = QTableWidget()
        self.sort_order: Qt.SortOrder | None = None
        self._bus_capacities: dict[int, int] = {}
        self._form_initialized = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        form_card = QFrame()
        form_card.setObjectName("contentCard")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        title = QLabel("Регистрация рейса")
        title.setObjectName("sectionTitle")
        form_layout.addWidget(title, 0, 0, 1, 8)

        _configure_date_edit(self.date_edit)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.time_edit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
        self.time_edit.setCursor(Qt.CursorShape.IBeamCursor)
        
        self.passenger_input.setRange(0, 500)
        self.passenger_input.setValue(60)
        self.passenger_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.passenger_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        _configure_combo(self.route_combo)
        _configure_combo(self.bus_combo)
        _configure_combo(self.driver_combo)

        self.passenger_input.valueChanged.connect(self._update_load_preview)
        self.bus_combo.currentIndexChanged.connect(self._update_load_preview)

        form_layout.addWidget(QLabel("Маршрут"), 1, 0)
        form_layout.addWidget(self.route_combo, 1, 1)
        form_layout.addWidget(QLabel("Автобус"), 1, 2)
        form_layout.addWidget(self.bus_combo, 1, 3)
        form_layout.addWidget(QLabel("Водитель"), 1, 4)
        form_layout.addWidget(self.driver_combo, 1, 5)

        form_layout.addWidget(QLabel("Дата"), 2, 0)
        form_layout.addWidget(self.date_edit, 2, 1)
        form_layout.addWidget(QLabel("Время"), 2, 2)
        form_layout.addWidget(self.time_edit, 2, 3)
        form_layout.addWidget(QLabel("Пассажиров"), 2, 4)
        form_layout.addWidget(self.passenger_input, 2, 5)
        self.load_preview.setObjectName("pageHint")
        form_layout.addWidget(self.load_preview, 2, 6)

        form_layout.addWidget(_create_button("Добавить рейс", self._add_trip, kind="primary"), 2, 7)
        root.addWidget(form_card)

        table_card = QFrame()
        table_card.setObjectName("contentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)
        table_title = QLabel("Журнал рейсов")
        table_title.setObjectName("sectionTitle")
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(table_title)
        title_row.addStretch(1)
        title_row.addWidget(_create_button("Загрузка ↓", lambda: self._sort_by_load(Qt.SortOrder.DescendingOrder)))
        title_row.addWidget(_create_button("Загрузка ↑", lambda: self._sort_by_load(Qt.SortOrder.AscendingOrder)))
        table_layout.addLayout(title_row)
        _configure_table(
            self.table,
            ["ID", "Маршрут", "Направление", "Автобус", "Водитель", "Дата", "Время", "Пассажиры", "Загрузка"],
        )
        self.table.setSortingEnabled(True)
        table_layout.addWidget(self.table)
        root.addWidget(table_card, stretch=1)

    def set_theme(self, theme_name: str) -> None:
        super().set_theme(theme_name)
        self._restyle_trip_rows()

    def reload(self) -> None:
        current_date = self.date_edit.date()
        current_time = self.time_edit.time()
        current_passengers = int(self.passenger_input.value())

        self._populate_selectors()

        if not self._form_initialized:
            reference_date = self.service.reference_date()
            if reference_date:
                self.date_edit.setDate(QDate.fromString(reference_date, "yyyy-MM-dd"))
            else:
                self.date_edit.setDate(QDate.currentDate())
            self.time_edit.setTime(QTime.currentTime())
            self._form_initialized = True
        else:
            self.date_edit.setDate(current_date)
            self.time_edit.setTime(current_time)
            self.passenger_input.setValue(current_passengers)

        self._update_load_preview()

        trips = self.service.trips(self.search_query)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(trips))
        for row_index, row in enumerate(trips.itertuples(index=False)):
            self.table.setItem(row_index, 0, NumericTableItem(str(row.id), float(row.id)))
            self.table.setItem(row_index, 1, _create_item(row.route_number))
            self.table.setItem(row_index, 2, _create_item(row.route_name))
            self.table.setItem(row_index, 3, _create_item(f"{row.gov_number} ({row.model})"))
            self.table.setItem(row_index, 4, _create_item(row.full_name))
            self.table.setItem(row_index, 5, _create_item(row.trip_date))
            self.table.setItem(row_index, 6, _create_item(row.trip_time))
            self.table.setItem(row_index, 7, NumericTableItem(str(row.passenger_count), float(row.passenger_count)))
            self.table.setItem(row_index, 8, NumericTableItem(f"{row.load_percent}%", float(row.load_percent)))
            self._apply_trip_row_style(row_index, float(row.load_percent))
        self.table.setSortingEnabled(True)
        if self.sort_order is not None:
            self._sort_by_load(self.sort_order)

    def _populate_selectors(self) -> None:
        current_route_id = self.route_combo.currentData()
        current_bus_id = self.bus_combo.currentData()
        current_driver_id = self.driver_combo.currentData()

        routes = self.service.route_options()
        buses = self.service.bus_options()
        drivers = self.service.driver_options()
        self._bus_capacities = {int(row.id): int(row.capacity) for row in self.service.buses().itertuples(index=False)}

        self.route_combo.clear()
        for row in routes.itertuples(index=False):
            self.route_combo.addItem(row.display, int(row.id))

        self.bus_combo.clear()
        for row in buses.itertuples(index=False):
            self.bus_combo.addItem(row.display, int(row.id))

        self.driver_combo.clear()
        for row in drivers.itertuples(index=False):
            self.driver_combo.addItem(row.display, int(row.id))

        self._restore_combo(self.route_combo, current_route_id)
        self._restore_combo(self.bus_combo, current_bus_id)
        self._restore_combo(self.driver_combo, current_driver_id)

    def _restore_combo(self, combo: QComboBox, current_id: int | None) -> None:
        if current_id is None:
            if combo.count() > 0:
                combo.setCurrentIndex(0)
            return

        for index in range(combo.count()):
            if combo.itemData(index) == current_id:
                combo.setCurrentIndex(index)
                return
        if combo.count() > 0:
            combo.setCurrentIndex(0)

    def _update_load_preview(self) -> None:
        bus_id = self.bus_combo.currentData()
        capacity = self._bus_capacities.get(int(bus_id), 0) if bus_id is not None else 0
        passengers = int(self.passenger_input.value())
        load = round((passengers / capacity) * 100) if capacity else 0
        self.load_preview.setText(f"Загрузка: {load}%")

    def _trip_colors(self, load_percent: float) -> tuple[QColor, QColor] | None:
        if load_percent > 85:
            if self.theme_name == "dark":
                return QColor("#472629"), QColor("#FEE2E2")
            return QColor("#FDE7E9"), QColor("#7F1D1D")
        if load_percent < 40:
            if self.theme_name == "dark":
                return QColor("#12362E"), QColor("#D1FAE5")
            return QColor("#DCFCE7"), QColor("#065F46")
        return None

    def _apply_trip_row_style(self, row_index: int, load_percent: float) -> None:
        default_foreground = QColor(get_theme(self.theme_name).input_text)
        colors = self._trip_colors(load_percent)
        for column_index in range(self.table.columnCount()):
            item = self.table.item(row_index, column_index)
            if item is None:
                continue
            if colors is None:
                item.setBackground(QColor(0, 0, 0, 0))
                item.setForeground(default_foreground)
            else:
                background, foreground = colors
                item.setBackground(background)
                item.setForeground(foreground)

    def _restyle_trip_rows(self) -> None:
        for row_index in range(self.table.rowCount()):
            item = self.table.item(row_index, self.table.columnCount() - 1)
            if item is None:
                continue
            load_percent = float(item.text().replace("%", "").strip() or 0)
            self._apply_trip_row_style(row_index, load_percent)

    def _sort_by_load(self, order: Qt.SortOrder) -> None:
        self.sort_order = order
        self.table.horizontalHeader().setSortIndicator(8, order)
        self.table.sortItems(8, order)

    def _add_trip(self) -> None:
        route_id = self.route_combo.currentData()
        bus_id = self.bus_combo.currentData()
        driver_id = self.driver_combo.currentData()
        if route_id is None or bus_id is None or driver_id is None:
            QMessageBox.warning(self, "Рейсы", "Сначала заполните справочники автобусов, маршрутов и водителей.")
            return

        try:
            load_percent = self.service.add_trip(
                int(route_id),
                int(bus_id),
                int(driver_id),
                self.date_edit.date().toString("yyyy-MM-dd"),
                self.time_edit.time().toString("HH:mm"),
                int(self.passenger_input.value()),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Рейсы", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Рейсы", str(error))
            return

        self.time_edit.setTime(QTime.currentTime())
        self._notify_change(f"Рейс зарегистрирован. Загрузка автобуса: {load_percent}%.")


class MapPage(BasePage):
    def __init__(self, service: AppDataService, on_data_changed: Callable[[str], None] | None = None, parent=None):
        super().__init__(service, on_data_changed, parent)
        self.map_panel = TransportMapPanel(service, self)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        header_card = QFrame()
        header_card.setObjectName("contentCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(6)

        title = QLabel("Карта маршрутов")
        title.setObjectName("sectionTitle")
        hint = QLabel("Карта автобусной сети, остановок и движения автобусов по маршрутам.")
        hint.setObjectName("pageHint")
        hint.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(hint)
        root.addWidget(header_card)
        root.addWidget(self.map_panel, stretch=1)

    def reload(self) -> None:
        self.map_panel.reload()

    def apply_search(self, query: str) -> None:
        self.search_query = query.strip()
        self.map_panel.set_search(self.search_query)
        self.reload()

    def set_theme(self, theme_name: str) -> None:
        super().set_theme(theme_name)
        self.map_panel.set_theme(theme_name)

    def set_active(self, active: bool) -> None:
        self.map_panel.set_active(active)

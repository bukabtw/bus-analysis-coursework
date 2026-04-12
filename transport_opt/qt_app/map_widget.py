from __future__ import annotations

from math import hypot

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from transport_opt.map_data import BusMarker, DistrictShape, MapStaticData, RoadShape, RouteShape, StopShape

from .data_service import AppDataService
from .theme import ThemePalette, get_theme


SIMULATION_SPEED_SCALE = 10
SIMULATION_BASE_HOURS_PER_SECOND = 0.12
SIMULATION_MIN_SPEED = 0.1
SIMULATION_MAX_SPEED = 20.0


class TransportMapCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.static_data: MapStaticData | None = None
        self.buses: list[BusMarker] = []
        self.show_districts = True
        self.show_roads = True
        self.show_routes = True
        self.show_stops = True
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._drag_active = False
        self._drag_moved = False
        self._last_mouse_pos: QPoint | None = None
        self._theme: ThemePalette = get_theme("light")
        self.setMouseTracking(True)
        self.setMinimumHeight(520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_theme(self, theme_name: str) -> None:
        self._theme = get_theme(theme_name)
        self.update()

    def set_static_data(self, static_data: MapStaticData) -> None:
        self.static_data = static_data
        self.reset_view()
        self.update()

    def set_buses(self, buses: list[BusMarker]) -> None:
        self.buses = buses
        self.update()

    def set_layers(self, *, districts: bool, roads: bool, routes: bool, stops: bool) -> None:
        self.show_districts = districts
        self.show_roads = roads
        self.show_routes = routes
        self.show_stops = stops
        self.update()

    def reset_view(self) -> None:
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self._draw_background(painter)

        if self.static_data is None:
            painter.setPen(QColor(self._theme.text))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Карта загружается...")
            return

        rect = self.rect().adjusted(20, 20, -20, -20)
        if rect.width() < 80 or rect.height() < 80:
            painter.setPen(QColor(self._theme.muted_text))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Подготовка карты...")
            return

        if self.show_districts:
            for district in self.static_data.districts:
                self._draw_district(painter, rect, district)
        if self.show_roads:
            for road in self.static_data.roads:
                self._draw_road(painter, rect, road)
        if self.show_routes:
            for route in self.static_data.routes:
                self._draw_route(painter, rect, route)
        if self.show_stops:
            for stop in self.static_data.stops:
                self._draw_stop(painter, rect, stop)
        for bus in self.buses:
            self._draw_bus(painter, rect, bus)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_moved = False
            self._last_mouse_pos = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        current_pos = event.position().toPoint()
        if self._drag_active and self._last_mouse_pos is not None:
            delta = current_pos - self._last_mouse_pos
            if delta.manhattanLength() > 0:
                self._drag_moved = True
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self._last_mouse_pos = current_pos
            self.update()
            return

        hovered_stop = self._find_stop(current_pos)
        self.setCursor(Qt.CursorShape.PointingHandCursor if hovered_stop else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._drag_moved:
            stop = self._find_stop(event.position().toPoint())
            if stop is not None:
                tooltip = (
                    f"{stop.name}\n"
                    f"Район: {stop.district}\n"
                    f"Маршрут: {stop.route_name}\n"
                    f"Спрос: {stop.demand}"
                )
                QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
        self._drag_active = False
        self._last_mouse_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.reset_view()
        self.update()

    def wheelEvent(self, event) -> None:
        if event.angleDelta().y() > 0:
            self.zoom = min(self.zoom * 1.15, 8.0)
        else:
            self.zoom = max(self.zoom / 1.15, 0.65)
        self.update()

    def _draw_background(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor(self._theme.chart_plot_bg))
        painter.setPen(QPen(QColor(self._theme.card_border), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 16, 16)
        grid_color = QColor(self._theme.chart_grid)
        grid_color.setAlpha(90)
        painter.setPen(QPen(grid_color, 1))
        for x in range(0, self.width(), 48):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 48):
            painter.drawLine(0, y, self.width(), y)

    def _draw_district(self, painter: QPainter, rect, district: DistrictShape) -> None:
        fill = QColor(district.fill_color)
        fill.setAlpha(118)
        left, top, width, height = self._district_rect(rect, district)
        painter.fillRect(left, top, width, height, fill)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        border = QColor(district.border_color)
        border.setAlpha(180)
        painter.setPen(QPen(border, 1.3))
        painter.drawRect(left, top, width, height)

        if width >= 36 and height >= 16:
            painter.setPen(QColor(self._theme.chart_text))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            painter.drawText(left, top, width, height, int(Qt.AlignmentFlag.AlignCenter), district.name)

    def _draw_road(self, painter: QPainter, rect, road: RoadShape) -> None:
        if len(road.path) < 2:
            return
        p1 = self._to_screen(rect, road.path[0])
        p2 = self._to_screen(rect, road.path[1])
        road_color = QColor(road.color)
        road_color.setAlpha(165)
        painter.setPen(QPen(road_color, 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(p1, p2)

    def _draw_route(self, painter: QPainter, rect, route: RouteShape) -> None:
        if len(route.path) < 2:
            return
        pen = QPen(QColor(route.color), 4.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for start, end in zip(route.path, route.path[1:]):
            painter.drawLine(self._to_screen(rect, start), self._to_screen(rect, end))

    def _draw_stop(self, painter: QPainter, rect, stop: StopShape) -> None:
        point = self._to_screen(rect, stop.coord)
        painter.setPen(QPen(QColor("#F8FAFC"), 1.5))
        painter.setBrush(QColor("#7DD3FC"))
        painter.drawEllipse(point, 5, 5)

    def _draw_bus(self, painter: QPainter, rect, bus: BusMarker) -> None:
        point = self._to_screen(rect, bus.coord)
        painter.setPen(QPen(QColor("#FFFFFF"), 1.4))
        painter.setBrush(QColor(bus.color))
        painter.drawEllipse(point, 7, 7)

    def _district_rect(self, rect, district: DistrictShape) -> tuple[int, int, int, int]:
        points = [self._to_screen(rect, coord) for coord in district.polygon]
        xs = [point.x() for point in points]
        ys = [point.y() for point in points]
        left = min(xs)
        right = max(xs)
        top = min(ys)
        bottom = max(ys)
        return left, top, max(right - left, 1), max(bottom - top, 1)

    def _to_screen(self, rect, coord):
        if self.static_data is None:
            return rect.center()
        if rect.width() <= 1 or rect.height() <= 1:
            return rect.center()

        bounds = self.static_data.bounds
        center_lon = (bounds.min_lon + bounds.max_lon) / 2
        center_lat = (bounds.min_lat + bounds.max_lat) / 2
        width = max(bounds.max_lon - bounds.min_lon, 1e-6)
        height = max(bounds.max_lat - bounds.min_lat, 1e-6)
        scale = min(rect.width() / width, rect.height() / height) * self.zoom

        lat, lon = coord
        x = rect.center().x() + (lon - center_lon) * scale + self.pan_x
        y = rect.center().y() - (lat - center_lat) * scale + self.pan_y
        return QPoint(int(x), int(y))

    def _find_stop(self, pos: QPoint) -> StopShape | None:
        if self.static_data is None or not self.show_stops:
            return None

        rect = self.rect().adjusted(20, 20, -20, -20)
        nearest_stop = None
        nearest_distance = float("inf")
        for stop in self.static_data.stops:
            point = self._to_screen(rect, stop.coord)
            distance = hypot(point.x() - pos.x(), point.y() - pos.y())
            if distance <= 12 and distance < nearest_distance:
                nearest_distance = distance
                nearest_stop = stop
        return nearest_stop


class TransportMapPanel(QWidget):
    def __init__(self, service: AppDataService, parent=None):
        super().__init__(parent)
        self.service = service
        self.is_playing = False
        self.page_active = True
        self.theme_name = "light"
        self.search_query = ""
        self.current_hour = 8.0
        self.setMinimumHeight(560)
        self.legend_scroll = None

        self.map_canvas = TransportMapCanvas(self)
        self.active_buses_label = QLabel("Активных автобусов: 0")
        self.time_label = QLabel()
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_label = QLabel("Скорость симуляции: 1.0x")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.play_button = QPushButton("Старт")
        self.districts_checkbox = QCheckBox("Районы")
        self.roads_checkbox = QCheckBox("Дороги")
        self.routes_checkbox = QCheckBox("Маршруты")
        self.stops_checkbox = QCheckBox("Остановки")
        self.legend_layout = QVBoxLayout()

        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)

        self._build_ui()
        self.reload()
        self._sync_timer()

    def set_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name
        self.map_canvas.set_theme(theme_name)
        self._update_legend_style()

    def _update_legend_style(self) -> None:
        if not hasattr(self, "legend_scroll") or self.legend_scroll is None:
            return
        theme = get_theme(self.theme_name)
        self.legend_scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {theme.card_bg};
                border: none;
            }}
            QWidget {{
                background: {theme.card_bg};
                color: {theme.text};
            }}
            QLabel {{
                color: {theme.text};
            }}
        """
        )

    def set_search(self, query: str) -> None:
        self.search_query = query.strip()

    def reload(self) -> None:
        static_data = self.service.map_static_data(self.search_query)
        self.map_canvas.set_static_data(static_data)
        self._rebuild_legend(static_data)
        self._refresh_bus_overlay()

    def set_active(self, active: bool) -> None:
        self.page_active = active
        self._sync_timer()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)
        root_layout.addWidget(self.map_canvas, stretch=3)

        controls_card = QFrame(self)
        controls_card.setObjectName("contentCard")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(18, 18, 18, 18)
        controls_layout.setSpacing(12)

        title = QLabel("Управление симуляцией")
        title.setObjectName("sectionTitle")
        controls_layout.addWidget(title)
        controls_layout.addWidget(self.active_buses_label)
        controls_layout.addWidget(self.time_label)

        self.time_slider.setRange(0, 240)
        self.time_slider.setSingleStep(1)
        self.time_slider.setValue(int(round(self.current_hour * 10)))
        self.time_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.time_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.time_slider.valueChanged.connect(self._time_changed)
        controls_layout.addWidget(self.time_slider)

        self.speed_slider.setRange(
            int(SIMULATION_MIN_SPEED * SIMULATION_SPEED_SCALE),
            int(SIMULATION_MAX_SPEED * SIMULATION_SPEED_SCALE),
        )
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setPageStep(5)
        self.speed_slider.setValue(int(1.0 * SIMULATION_SPEED_SCALE))
        self.speed_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.speed_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speed_slider.valueChanged.connect(self._speed_changed)
        controls_layout.addWidget(self.speed_label)
        controls_layout.addWidget(self.speed_slider)

        self.play_button.setProperty("kind", "primary")
        self.play_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_button)

        layers_title = QLabel("Слои")
        layers_title.setObjectName("sectionTitle")
        controls_layout.addWidget(layers_title)

        for checkbox in (
            self.districts_checkbox,
            self.roads_checkbox,
            self.routes_checkbox,
            self.stops_checkbox,
        ):
            checkbox.setChecked(True)
            checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.stateChanged.connect(self._update_layers)
            controls_layout.addWidget(checkbox)

        legend_title = QLabel("Легенда")
        legend_title.setObjectName("sectionTitle")
        controls_layout.addWidget(legend_title)

        legend_container = QWidget()
        legend_container.setLayout(self.legend_layout)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(8)

        self.legend_scroll = QScrollArea()
        self.legend_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.legend_scroll.setWidgetResizable(True)
        self.legend_scroll.setWidget(legend_container)
        self.legend_scroll.setMinimumHeight(160)
        self.legend_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.legend_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.legend_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._update_legend_style()
        controls_layout.addWidget(self.legend_scroll, stretch=1)

        root_layout.addWidget(controls_card, stretch=1)
        self._speed_changed(self.speed_slider.value())
        self._time_changed(self.time_slider.value())
        self._update_layers()

    def _rebuild_legend(self, static_data: MapStaticData) -> None:
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not static_data.routes:
            empty = QLabel("Нет маршрутов для отображения.")
            empty.setWordWrap(True)
            self.legend_layout.addWidget(empty)
            self.legend_layout.addStretch(1)
            return

        for route in static_data.routes:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            color_dot = QLabel()
            color_dot.setFixedSize(14, 14)
            color_dot.setStyleSheet(
                f"background: {route.color}; border-radius: 7px; border: 1px solid #FFFFFF;"
            )
            row_layout.addWidget(color_dot)

            text = QLabel(route.name)
            text.setWordWrap(True)
            row_layout.addWidget(text, stretch=1)
            self.legend_layout.addWidget(row)

        self.legend_layout.addStretch(1)

    def _toggle_playback(self) -> None:
        self.is_playing = not self.is_playing
        self.play_button.setText("Пауза" if self.is_playing else "Старт")
        self._sync_timer()

    def _sync_timer(self) -> None:
        if self.is_playing and self.page_active:
            self.timer.start()
        else:
            self.timer.stop()

    def _tick(self) -> None:
        increment = (
            SIMULATION_BASE_HOURS_PER_SECOND
            * self._speed_multiplier()
            * (self.timer.interval() / 1000.0)
        )
        self._apply_simulation_hour(self.current_hour + increment)

    def _apply_simulation_hour(self, hour: float) -> None:
        self.current_hour = hour % 24.0
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(int(round(self.current_hour * 10)) % (self.time_slider.maximum() + 1))
        self.time_slider.blockSignals(False)
        self._update_time_label()
        self._refresh_bus_overlay()

    def _time_changed(self, value: int) -> None:
        self.current_hour = (value / 10.0) % 24.0
        self._update_time_label()
        self._refresh_bus_overlay()

    def _update_time_label(self) -> None:
        total_seconds = int(round(self.current_hour * 3600)) % (24 * 3600)
        whole_hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.time_label.setText(f"Время суток: {whole_hours:02d}:{minutes:02d}:{seconds:02d}")

    def _speed_changed(self, value: int) -> None:
        self.speed_label.setText(f"Скорость симуляции: {self._speed_multiplier():.1f}x")

    def _speed_multiplier(self) -> float:
        return self.speed_slider.value() / SIMULATION_SPEED_SCALE

    def _refresh_bus_overlay(self) -> None:
        buses = self.service.bus_positions(self.current_hour, self.search_query)
        self.map_canvas.set_buses(buses)
        self.active_buses_label.setText(f"Активных автобусов: {len(buses)}")

    def _update_layers(self) -> None:
        self.map_canvas.set_layers(
            districts=self.districts_checkbox.isChecked(),
            roads=self.roads_checkbox.isChecked(),
            routes=self.routes_checkbox.isChecked(),
            stops=self.stops_checkbox.isChecked(),
        )

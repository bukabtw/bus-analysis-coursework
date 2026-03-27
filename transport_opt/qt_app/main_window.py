from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PyQt6.QtCore import QSettings, QTimer, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .data_service import AppDataService
from .pages import AnalyticsPage, BusesPage, DashboardPage, DriversPage, MapPage, RoutesPage, TripsPage
from .theme import build_stylesheet, get_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1240, 820)

        self.service = AppDataService()
        self.settings = QSettings("BAC", "BAC")
        self.current_theme = self.settings.value("theme", "light", type=str)
        if self.current_theme not in {"light", "dark"}:
            self.current_theme = "light"

        self.pages: dict[str, QWidget] = {}
        self.page_factories: dict[str, Callable[[], QWidget]] = {
            "Дашборд": lambda: DashboardPage(self.service, self._handle_data_changed),
            "Аналитика": lambda: AnalyticsPage(self.service, self._handle_data_changed),
            "Автобусы": lambda: BusesPage(self.service, self._handle_data_changed),
            "Маршруты": lambda: RoutesPage(self.service, self._handle_data_changed),
            "Водители": lambda: DriversPage(self.service, self._handle_data_changed),
            "Рейсы": lambda: TripsPage(self.service, self._handle_data_changed),
            "Карта": lambda: MapPage(self.service, self._handle_data_changed),
        }

        self.stack = QStackedWidget()
        self.nav_list = QListWidget()
        self.clock_label = QLabel()
        self.reference_label = QLabel()
        self.search_input = QLineEdit()
        self.theme_button = self._build_button("", self._toggle_theme)

        self._build_ui()
        self._create_initial_page()
        self._apply_theme(self.current_theme)
        self._update_clock()
        self._update_reference_label()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _build_ui(self) -> None:
        self.setWindowTitle("BAC Автопарк")
        self.resize(1540, 960)

        shell = QWidget()
        shell.setObjectName("shell")
        shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(shell)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(14)

        header_card = QFrame()
        header_card.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(22, 20, 22, 20)
        header_layout.setSpacing(18)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)
        title = QLabel("BAC Автопарк")
        title.setObjectName("appTitle")
        subtitle = QLabel("Учет автобусного парка, пассажиропотока и регистрация рейсов в едином рабочем приложении")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        header_layout.addLayout(title_column, stretch=1)

        meta_column = QVBoxLayout()
        meta_column.setSpacing(4)
        self.reference_label.setObjectName("metaLabel")
        self.clock_label.setObjectName("clockLabel")
        meta_column.addWidget(self.reference_label)
        meta_column.addWidget(self.clock_label)
        header_layout.addLayout(meta_column)
        root.addWidget(header_card)

        toolbar_card = QFrame()
        toolbar_card.setObjectName("toolbarCard")
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(18, 14, 18, 14)
        toolbar_layout.setSpacing(10)

        toolbar_layout.addWidget(self._build_button("Загрузить базовые данные", self._load_base_data, kind="primary"))
        toolbar_layout.addWidget(self._build_button("Экспорт отчета", self._export_report, kind="accent"))
        toolbar_layout.addWidget(self._build_button("Обновить все", self._refresh_loaded_pages))
        toolbar_layout.addStretch(1)

        self.search_input.setPlaceholderText("Поиск по автобусам, маршрутам, водителям и рейсам")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_search)
        self.search_input.setMinimumWidth(340)
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addWidget(self.theme_button)
        root.addWidget(toolbar_card)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarCard")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(12)

        brand = QLabel("Навигация")
        brand.setObjectName("sidebarBrand")
        caption = QLabel("Рабочие разделы системы")
        caption.setObjectName("sidebarCaption")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(caption)

        self.nav_list.setObjectName("navList")
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        for page_name in self.page_factories:
            self.nav_list.addItem(QListWidgetItem(page_name))
        self.nav_list.currentTextChanged.connect(self._open_page)
        sidebar_layout.addWidget(self.nav_list, stretch=1)
        body_layout.addWidget(sidebar)

        self.stack.setObjectName("pageStack")
        body_layout.addWidget(self.stack, stretch=1)
        root.addLayout(body_layout, stretch=1)

        self.setCentralWidget(shell)
        self.statusBar().showMessage("Система готова к работе.")

    def _build_button(self, text: str, slot, kind: str | None = None) -> QPushButton:
        button = QPushButton(text)
        if kind:
            button.setProperty("kind", kind)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(slot)
        return button

    def _create_initial_page(self) -> None:
        dashboard = self.page_factories["Дашборд"]()
        if hasattr(dashboard, "set_theme"):
            dashboard.set_theme(self.current_theme)
        self.pages["Дашборд"] = dashboard
        self.stack.addWidget(dashboard)
        self.stack.setCurrentWidget(dashboard)
        if hasattr(dashboard, "reload"):
            dashboard.reload()
        self.nav_list.setCurrentRow(0)

    def _open_page(self, page_name: str) -> None:
        if not page_name:
            return

        previous_page = self.stack.currentWidget()
        if page_name not in self.pages:
            page = self.page_factories[page_name]()
            if hasattr(page, "set_theme"):
                page.set_theme(self.current_theme)
            self.pages[page_name] = page
            self.stack.addWidget(page)

        current_page = self.pages[page_name]
        if previous_page is not None and previous_page is not current_page and hasattr(previous_page, "set_active"):
            previous_page.set_active(False)
        self.stack.setCurrentWidget(current_page)
        if hasattr(current_page, "set_active"):
            current_page.set_active(True)

        if hasattr(current_page, "apply_search"):
            current_page.apply_search(self.search_input.text())
        elif hasattr(current_page, "reload"):
            current_page.reload()

        self.statusBar().showMessage(f"Открыт раздел: {page_name}")

    def _refresh_loaded_pages(self) -> None:
        self.service.refresh()
        for page in self.pages.values():
            if hasattr(page, "reload"):
                page.reload()
        self._update_reference_label()
        self.statusBar().showMessage("Данные обновлены.")

    def _load_base_data(self) -> None:
        answer = QMessageBox.question(
            self,
            "Базовые данные",
            "Текущая база будет пересоздана. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.service.load_base_data()
        self.search_input.clear()
        self._refresh_loaded_pages()
        self.statusBar().showMessage("Базовые данные успешно загружены.")

    def _export_report(self) -> None:
        try:
            report_path = self.service.export_report()
        except Exception as error:
            QMessageBox.critical(self, "Экспорт отчета", str(error))
            return

        self.statusBar().showMessage(f"Отчет сохранен: {report_path.name}")
        QMessageBox.information(self, "Экспорт отчета", f"Отчет сохранен:\n{report_path}")

    def _apply_search(self, query: str) -> None:
        for page in self.pages.values():
            if hasattr(page, "apply_search"):
                page.apply_search(query)

        if query.strip():
            summary = self.service.search_summary(query)
            self.statusBar().showMessage(
                f"Поиск: автобусы {summary['buses']}, маршруты {summary['routes']}, "
                f"водители {summary['drivers']}, рейсы {summary['trips']}."
            )
        else:
            self.statusBar().showMessage("Поиск очищен.")

    def _toggle_theme(self) -> None:
        next_theme = "dark" if self.current_theme == "light" else "light"
        self._apply_theme(next_theme)
        title = "тёмная" if next_theme == "dark" else "светлая"
        self.statusBar().showMessage(f"Тема переключена: {title}.")

    def _handle_data_changed(self, message: str) -> None:
        self._refresh_loaded_pages()
        self.statusBar().showMessage(message)

    def _update_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

    def _update_reference_label(self) -> None:
        reference_date = self.service.dashboard_metrics().reference_date
        self.reference_label.setText(f"Отчетная дата: {reference_date}")

    def _apply_theme(self, theme_name: str) -> None:
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        palette = get_theme(theme_name)
        self.setStyleSheet(build_stylesheet(palette))
        self.theme_button.setText(f"Тема: {'тёмная' if theme_name == 'dark' else 'светлая'}")
        for page in self.pages.values():
            if hasattr(page, "set_theme"):
                page.set_theme(theme_name)

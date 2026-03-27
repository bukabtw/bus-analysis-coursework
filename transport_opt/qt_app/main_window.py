from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QFrame
)

from .data_service import AppDataService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.service = AppDataService()
        
        self.setWindowTitle("BAC Автопарк")
        self.resize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        
        self.nav_list = QListWidget()
        self.nav_list.addItems(["Дашборд", "Аналитика", "Автобусы", "Маршруты", "Водители", "Рейсы", "Карта"])
        sidebar_layout.addWidget(self.nav_list)
        
        self.stack = QStackedWidget()
        
        for name in ["Дашборд", "Аналитика", "Автобусы", "Маршруты", "Водители", "Рейсы", "Карта"]:
            if name == "Дашборд":
                stats = self.service.dashboard_metrics()
                text = f"""
                Всего автобусов: {stats.total_buses}
                В рейсе сегодня: {stats.active_buses}
                Средняя загрузка: {stats.avg_load}%
                Критические маршруты: {stats.critical_routes}
                Отчетная дата: {stats.reference_date}
                """
                page = QLabel(text)
            else:
                page = QLabel(f"Страница: {name}\n(будет реализована позже)")
            page.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stack.addWidget(page)
        
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, stretch=1)
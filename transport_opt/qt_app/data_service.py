from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class DashboardMetrics:
    """Метрики для дашборда"""
    total_buses: int
    active_buses: int
    avg_load: float
    critical_routes: int
    reference_date: str


class AppDataService:
    """Сервис данных для всего приложения"""
    
    BASE_BUSES = [
        ("А777АА", "ЛиАЗ-5292", 115),
        ("В888ВВ", "ЛиАЗ-6213", 150),
        ("С999СС", "МАЗ-203", 105),
        ("О111ОО", "НефАЗ-5299", 110),
        ("Т222ТТ", "ЛиАЗ-4292", 90),
        ("У333УУ", "ПАЗ-3204", 75),
        ("К444КК", "МАЗ-206", 85),
        ("Н555НН", "ЛиАЗ-5292", 115),
        ("Р666РР", "ЛиАЗ-6213", 150),
        ("С777СС", "НефАЗ-5299", 110),
        ("М888ММ", "МАЗ-203", 105),
        ("А999АА", "ПАЗ-3204", 75),
    ]
    
    BASE_ROUTES = [
        ("м1", "Китай-город - Силикатный завод"),
        ("м2", "Фили - ВДНХ"),
        ("т4", "Новогиреево - Таганская"),
        ("716", "Выхино - Кожухово"),
        ("204", "Беляево - Черемушки"),
        ("144", "Теплый Стан - Метро Парк Победы"),
        ("Т47", "Нагатино - Павелецкая"),
        ("с13", "Ясенево - Битцевский парк"),
        ("835", "Южное Бутово - Щербинка"),
        ("877", "Некрасовка - Люблино"),
        ("951", "Жулебино - Кузьминки"),
        ("309", "Котельники - Выхино"),
    ]
    
    BASE_DRIVERS = [
        ("Петров А.С.", "77УР456789"),
        ("Иванов В.П.", "77МР123456"),
        ("Сидоров К.Н.", "77АА654321"),
        ("Козлов Д.В.", "77ТТ789012"),
        ("Морозов С.И.", "77ВС345678"),
        ("Волков Н.Ф.", "77КЕ901234"),
        ("Лебедев П.Р.", "77МН567890"),
        ("Соколов А.Г.", "77ОХ789123"),
        ("Михайлов И.К.", "77НТ456123"),
        ("Новиков В.С.", "77РР789456"),
    ]
    
    def __init__(self, db_path: str | Path = "data/bus_company.db"):
        self.db_path = Path(db_path)
        self._ensure_database()
    
    
    def buses(self):
        """Получить все автобусы"""
        with self._connect() as conn:
            return conn.execute(
                "SELECT id, gov_number, model, capacity FROM buses ORDER BY id"
            ).fetchall()
    
    def routes(self):
        """Получить все маршруты"""
        with self._connect() as conn:
            return conn.execute(
                "SELECT id, route_number, route_name FROM routes ORDER BY id"
            ).fetchall()
    
    def drivers(self):
        """Получить всех водителей"""
        with self._connect() as conn:
            return conn.execute(
                "SELECT id, full_name, license_number FROM drivers ORDER BY id"
            ).fetchall()
    
    def trips(self):
        """Получить все рейсы с расширенной информацией"""
        with self._connect() as conn:
            return conn.execute("""
                SELECT 
                    trips.id,
                    routes.route_number,
                    buses.gov_number,
                    drivers.full_name,
                    trips.trip_date,
                    trips.trip_time,
                    trips.passenger_count,
                    trips.load_percent
                FROM trips
                JOIN routes ON trips.route_id = routes.id
                JOIN buses ON trips.bus_id = buses.id
                JOIN drivers ON trips.driver_id = drivers.id
                ORDER BY trips.trip_date DESC, trips.trip_time DESC, trips.id DESC
            """).fetchall()
    
    def route_options(self):
        """Получить маршруты для выпадающего списка (отображение + значение)"""
        routes = self.routes()
        return [(r["id"], f"{r['route_number']} - {r['route_name']}") for r in routes]
    
    def bus_options(self):
        """Получить автобусы для выпадающего списка"""
        buses = self.buses()
        return [(b["id"], f"{b['gov_number']} ({b['model']})") for b in buses]
    
    def driver_options(self):
        """Получить водителей для выпадающего списка"""
        drivers = self.drivers()
        return [(d["id"], d["full_name"]) for d in drivers]
    
    def add_bus(self, gov_number: str, model: str, capacity: int) -> None:
        """Добавить новый автобус"""
        gov_number = gov_number.strip().upper()
        model = model.strip()
        if not gov_number or not model or capacity <= 0:
            raise ValueError("Заполните данные автобуса корректно.")
        
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO buses (gov_number, model, capacity) VALUES (?, ?, ?)",
                (gov_number, model, capacity)
            )
            conn.commit()
    
    def add_route(self, route_number: str, route_name: str) -> None:
        """Добавить новый маршрут"""
        route_number = route_number.strip()
        route_name = route_name.strip()
        if not route_number or not route_name:
            raise ValueError("Заполните номер и название маршрута.")
        
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO routes (route_number, route_name) VALUES (?, ?)",
                (route_number, route_name)
            )
            conn.commit()
    
    def add_driver(self, full_name: str, license_number: str) -> None:
        """Добавить нового водителя"""
        full_name = full_name.strip()
        license_number = license_number.strip().upper()
        if not full_name or not license_number:
            raise ValueError("Заполните данные водителя.")
        
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO drivers (full_name, license_number) VALUES (?, ?)",
                (full_name, license_number)
            )
            conn.commit()
    
    def add_trip(
        self,
        route_id: int,
        bus_id: int,
        driver_id: int,
        trip_date: str,
        trip_time: str,
        passenger_count: int,
    ) -> int:
        """Добавить новый рейс. Возвращает процент загрузки"""
        if passenger_count < 0:
            raise ValueError("Количество пассажиров не может быть отрицательным.")
        
        with self._connect() as conn:
            if not self._record_exists(conn, "routes", route_id):
                raise ValueError("Не найден выбранный маршрут.")
            if not self._record_exists(conn, "drivers", driver_id):
                raise ValueError("Не найден выбранный водитель.")
            
            row = conn.execute("SELECT capacity FROM buses WHERE id = ?", (bus_id,)).fetchone()
            if row is None:
                raise ValueError("Не найден выбранный автобус.")
            
            capacity = row["capacity"]
            load_percent = round((passenger_count / capacity) * 100) if capacity else 0
            
            conn.execute("""
                INSERT INTO trips (
                    bus_id, route_id, driver_id, trip_date, trip_time,
                    passenger_count, load_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (bus_id, route_id, driver_id, trip_date, trip_time, passenger_count, load_percent))
            conn.commit()
        
        return load_percent
    
    def dashboard_metrics(self) -> DashboardMetrics:
        """Получить метрики для дашборда"""
        total_buses = len(self.buses())
        
        reference_date = self._reference_date()
        if reference_date is None:
            return DashboardMetrics(0, 0, 0.0, 0, "нет данных")
        
        end_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        start_date = (end_date - timedelta(days=6)).isoformat()
        
        with self._connect() as conn:
            active = conn.execute(
                "SELECT COUNT(DISTINCT bus_id) AS active FROM trips WHERE trip_date = ?",
                (reference_date,)
            ).fetchone()["active"] or 0
            
            avg = conn.execute(
                "SELECT AVG(load_percent) AS avg FROM trips WHERE trip_date BETWEEN ? AND ?",
                (start_date, reference_date)
            ).fetchone()["avg"] or 0.0
            
            critical = conn.execute("""
                SELECT COUNT(DISTINCT route_id) AS critical
                FROM trips
                WHERE trip_date BETWEEN ? AND ? AND load_percent > 85
            """, (start_date, reference_date)).fetchone()["critical"] or 0
        
        return DashboardMetrics(
            total_buses=total_buses,
            active_buses=active,
            avg_load=round(avg, 1),
            critical_routes=critical,
            reference_date=end_date.strftime("%d.%m.%Y"),
        )
    
    def load_base_data(self) -> None:
        """Перезагрузить базовые данные (очистить и заполнить заново)"""
        self._seed_base_data()
    
    def _connect(self) -> sqlite3.Connection:
        """Создать подключение к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _record_exists(self, conn: sqlite3.Connection, table: str, record_id: int) -> bool:
        """Проверить существование записи по ID"""
        result = conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return result is not None
    
    def _table_count(self, table: str) -> int:
        """Получить количество записей в таблице"""
        with self._connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    
    def _reference_date(self) -> str | None:
        """Получить последнюю дату с рейсами"""
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(trip_date) AS ref FROM trips").fetchone()
            return row["ref"] if row and row["ref"] else None
    
    def _ensure_database(self) -> None:
        """Создать БД и таблицы, если их нет"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS buses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gov_number TEXT NOT NULL,
                    model TEXT NOT NULL,
                    capacity INTEGER NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_number TEXT NOT NULL,
                    route_name TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    license_number TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bus_id INTEGER NOT NULL,
                    route_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    trip_date TEXT NOT NULL,
                    trip_time TEXT NOT NULL,
                    passenger_count INTEGER NOT NULL,
                    load_percent INTEGER NOT NULL,
                    FOREIGN KEY (bus_id) REFERENCES buses (id),
                    FOREIGN KEY (route_id) REFERENCES routes (id),
                    FOREIGN KEY (driver_id) REFERENCES drivers (id)
                );
            """)
            conn.commit()
        
        if self._table_count("buses") == 0:
            self._seed_base_data()
    
    def _seed_base_data(self) -> None:
        """Заполнить БД тестовыми данными"""
        rng = random.Random(20260315)
        
        with self._connect() as conn:
            conn.execute("DELETE FROM trips")
            conn.execute("DELETE FROM buses")
            conn.execute("DELETE FROM routes")
            conn.execute("DELETE FROM drivers")
            try:
                conn.execute("DELETE FROM sqlite_sequence")
            except sqlite3.OperationalError:
                pass
            
            conn.executemany(
                "INSERT INTO buses (gov_number, model, capacity) VALUES (?, ?, ?)",
                self.BASE_BUSES
            )
            conn.executemany(
                "INSERT INTO routes (route_number, route_name) VALUES (?, ?)",
                self.BASE_ROUTES
            )
            conn.executemany(
                "INSERT INTO drivers (full_name, license_number) VALUES (?, ?)",
                self.BASE_DRIVERS
            )
            
            capacities = {
                i: bus[2] for i, bus in enumerate(self.BASE_BUSES, start=1)
            }
            
            start_date = datetime(2026, 3, 15)
            for day_offset in range(7):
                current_date = start_date + timedelta(days=day_offset)
                date_str = current_date.strftime("%Y-%m-%d")
                is_weekend = current_date.weekday() >= 5
                
                for route_id in range(1, len(self.BASE_ROUTES) + 1):
                    buses_on_route = rng.randint(3, 6)
                    for _ in range(buses_on_route):
                        bus_id = rng.randint(1, len(self.BASE_BUSES))
                        for _ in range(rng.randint(4, 8)):
                            hour = rng.randint(5, 23)
                            
                            if 7 <= hour <= 10:
                                load = rng.randint(60, 85) if is_weekend else rng.randint(85, 100)
                            elif 17 <= hour <= 20:
                                load = rng.randint(65, 90) if is_weekend else rng.randint(85, 100)
                            elif 11 <= hour <= 16:
                                load = rng.randint(40, 75)
                            elif 21 <= hour <= 23:
                                load = rng.randint(20, 45)
                            else:
                                load = rng.randint(5, 25)
                            
                            passenger_count = int(capacities[bus_id] * load / 100)
                            driver_id = rng.randint(1, len(self.BASE_DRIVERS))
                            trip_time = f"{hour:02d}:{rng.randint(0, 59):02d}"
                            
                            conn.execute("""
                                INSERT INTO trips (
                                    bus_id, route_id, driver_id, trip_date, trip_time,
                                    passenger_count, load_percent
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (bus_id, route_id, driver_id, date_str, trip_time, passenger_count, load))
            
            conn.commit()
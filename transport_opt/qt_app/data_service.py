from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from transport_opt.map_data import BusMarker, MapStaticData, build_map_static, simulate_bus_positions


@dataclass(frozen=True)
class DashboardMetrics:
    total_buses: int
    active_buses: int
    avg_load: float
    critical_routes: int
    reference_date: str


class AppDataService:
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

    def __init__(self, db_path: Path | str = "data/bus_company.db"):
        self.db_path = Path(db_path)
        self.reports_dir = Path("reports")
        self._map_static_cache: dict[str, MapStaticData] = {}
        self._ensure_database()

    def refresh(self) -> None:
        self._ensure_database()
        self._map_static_cache.clear()

    def load_base_data(self) -> None:
        self._ensure_database(force_seed=True)
        self._map_static_cache.clear()

    def buses(self, query: str = "") -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT id, gov_number, model, capacity
            FROM buses
            ORDER BY id
            """
        )
        return self._apply_search(frame, query)

    def routes(self, query: str = "") -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT id, route_number, route_name
            FROM routes
            ORDER BY id
            """
        )
        return self._apply_search(frame, query)

    def drivers(self, query: str = "") -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT id, full_name, license_number
            FROM drivers
            ORDER BY id
            """
        )
        return self._apply_search(frame, query)

    def trips(self, query: str = "") -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT
                trips.id,
                trips.route_id,
                trips.bus_id,
                trips.driver_id,
                routes.route_number,
                routes.route_name,
                buses.gov_number,
                buses.model,
                drivers.full_name,
                trips.trip_date,
                trips.trip_time,
                trips.passenger_count,
                trips.load_percent
            FROM trips
            JOIN routes ON routes.id = trips.route_id
            JOIN buses ON buses.id = trips.bus_id
            JOIN drivers ON drivers.id = trips.driver_id
            ORDER BY trips.trip_date DESC, trips.trip_time DESC, trips.id DESC
            """
        )
        return self._apply_search(frame, query)

    def search_summary(self, query: str) -> dict[str, int]:
        return {
            "buses": len(self.buses(query)),
            "routes": len(self.routes(query)),
            "drivers": len(self.drivers(query)),
            "trips": len(self.trips(query)),
        }

    def route_options(self) -> pd.DataFrame:
        frame = self.routes()
        frame["display"] = frame["route_number"] + " - " + frame["route_name"]
        return frame

    def bus_options(self) -> pd.DataFrame:
        frame = self.buses()
        frame["display"] = frame["gov_number"] + " (" + frame["model"] + ")"
        return frame

    def driver_options(self) -> pd.DataFrame:
        frame = self.drivers()
        frame["display"] = frame["full_name"]
        return frame

    def add_bus(self, gov_number: str, model: str, capacity: int) -> None:
        gov_number = gov_number.strip().upper()
        model = model.strip()
        if not gov_number or not model or capacity <= 0:
            raise ValueError("Заполните данные автобуса корректно.")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO buses (gov_number, model, capacity)
                VALUES (?, ?, ?)
                """,
                (gov_number, model, capacity),
            )
            connection.commit()
        self._map_static_cache.clear()

    def add_route(self, route_number: str, route_name: str) -> None:
        route_number = route_number.strip()
        route_name = route_name.strip()
        if not route_number or not route_name:
            raise ValueError("Заполните номер и название маршрута.")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO routes (route_number, route_name)
                VALUES (?, ?)
                """,
                (route_number, route_name),
            )
            connection.commit()
        self._map_static_cache.clear()

    def add_driver(self, full_name: str, license_number: str) -> None:
        full_name = full_name.strip()
        license_number = license_number.strip().upper()
        if not full_name or not license_number:
            raise ValueError("Заполните данные водителя.")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO drivers (full_name, license_number)
                VALUES (?, ?)
                """,
                (full_name, license_number),
            )
            connection.commit()

    def add_trip(
        self,
        route_id: int,
        bus_id: int,
        driver_id: int,
        trip_date: str,
        trip_time: str,
        passenger_count: int,
    ) -> int:
        if passenger_count < 0:
            raise ValueError("Количество пассажиров не может быть отрицательным.")

        with self._connect() as connection:
            if not self._record_exists(connection, "routes", route_id):
                raise ValueError("Не найден выбранный маршрут.")
            if not self._record_exists(connection, "drivers", driver_id):
                raise ValueError("Не найден выбранный водитель.")

            cursor = connection.execute(
                "SELECT capacity FROM buses WHERE id = ?",
                (bus_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Не найден выбранный автобус.")

            capacity = int(row["capacity"])
            load_percent = round((passenger_count / capacity) * 100) if capacity else 0
            connection.execute(
                """
                INSERT INTO trips (
                    bus_id,
                    route_id,
                    driver_id,
                    trip_date,
                    trip_time,
                    passenger_count,
                    load_percent
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (bus_id, route_id, driver_id, trip_date, trip_time, passenger_count, load_percent),
            )
            connection.commit()
        self._map_static_cache.clear()
        return load_percent

    def dashboard_metrics(self) -> DashboardMetrics:
        total_buses = int(len(self.buses()))
        reference_date = self.reference_date()
        if reference_date is None:
            return DashboardMetrics(0, 0, 0.0, 0, "нет данных")

        end_date = date.fromisoformat(reference_date)
        start_date = (end_date - timedelta(days=6)).isoformat()

        active_buses_frame = self._read_frame(
            """
            SELECT COUNT(DISTINCT bus_id) AS active_buses
            FROM trips
            WHERE trip_date = ?
            """,
            (reference_date,),
        )
        avg_load_frame = self._read_frame(
            """
            SELECT AVG(load_percent) AS avg_load
            FROM trips
            WHERE trip_date BETWEEN ? AND ?
            """,
            (start_date, reference_date),
        )
        critical_routes_frame = self._read_frame(
            """
            SELECT COUNT(DISTINCT route_id) AS critical_routes
            FROM trips
            WHERE trip_date BETWEEN ? AND ?
              AND load_percent > 85
            """,
            (start_date, reference_date),
        )

        active_buses = int(active_buses_frame.iloc[0]["active_buses"] or 0)
        avg_load = float(avg_load_frame.iloc[0]["avg_load"] or 0.0)
        critical_routes = int(critical_routes_frame.iloc[0]["critical_routes"] or 0)
        return DashboardMetrics(
            total_buses=total_buses,
            active_buses=active_buses,
            avg_load=round(avg_load, 1),
            critical_routes=critical_routes,
            reference_date=end_date.strftime("%d.%m.%Y"),
        )

    def hourly_analysis(self) -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT
                CAST(substr(trip_time, 1, 2) AS INTEGER) AS hour,
                AVG(load_percent) AS avg_load,
                COUNT(*) AS trip_count
            FROM trips
            GROUP BY hour
            ORDER BY hour
            """
        )
        if frame.empty:
            return pd.DataFrame(columns=["hour", "avg_load", "trip_count"])
        frame["avg_load"] = frame["avg_load"].round(1)
        return frame

    def route_load_analysis(self, query: str = "") -> pd.DataFrame:
        frame = self._read_frame(
            """
            SELECT
                routes.id AS route_id,
                routes.route_number,
                routes.route_name,
                AVG(CASE WHEN CAST(substr(trips.trip_time, 1, 2) AS INTEGER) BETWEEN 7 AND 10
                    THEN trips.load_percent END) AS morning_load,
                AVG(CASE WHEN CAST(substr(trips.trip_time, 1, 2) AS INTEGER) BETWEEN 17 AND 20
                    THEN trips.load_percent END) AS evening_load,
                AVG(trips.load_percent) AS avg_load,
                COUNT(trips.id) AS trip_count
            FROM trips
            JOIN routes ON routes.id = trips.route_id
            GROUP BY routes.id, routes.route_number, routes.route_name
            ORDER BY avg_load DESC, routes.route_number
            """
        )
        if frame.empty:
            return pd.DataFrame(
                columns=[
                    "route_id",
                    "route_number",
                    "route_name",
                    "morning_load",
                    "evening_load",
                    "avg_load",
                    "trip_count",
                ]
            )

        for column in ("morning_load", "evening_load", "avg_load"):
            frame[column] = frame[column].fillna(0.0).round(1)
        return self._apply_search(frame, query)

    def top_routes(self, limit: int = 5, query: str = "") -> pd.DataFrame:
        frame = self.route_load_analysis(query).head(limit).copy()
        return frame[["route_number", "route_name", "avg_load"]]

    def recommendations(self, query: str = "") -> list[str]:
        recommendations: list[str] = []
        for row in self.route_load_analysis(query).itertuples(index=False):
            peak_load = max(float(row.morning_load or 0), float(row.evening_load or 0))
            avg_load = float(row.avg_load or 0)
            if peak_load > 90:
                recommendations.append(
                    f"[Критично] Маршрут {row.route_number}: пик {peak_load:.0f}%, требуется усиление в часы нагрузки."
                )
            elif avg_load > 75:
                recommendations.append(
                    f"[Высокая загрузка] Маршрут {row.route_number}: средняя загрузка {avg_load:.0f}%, стоит добавить рейсы."
                )
            elif avg_load < 30:
                recommendations.append(
                    f"[Низкая загрузка] Маршрут {row.route_number}: средняя загрузка {avg_load:.0f}%, можно сократить выпуск."
                )
            else:
                recommendations.append(
                    f"[Стабильно] Маршрут {row.route_number}: средняя загрузка {avg_load:.0f}%."
                )
        return recommendations

    def analytics_report(self) -> str:
        sections = [
            self.format_stats(),
            self.format_route_report(),
            self.format_recommendations(),
        ]
        return "\n\n".join(section.strip() for section in sections if section.strip())

    def format_stats(self) -> str:
        stats = self.dashboard_metrics()
        return (
            "СТАТИСТИКА АВТОПАРКА\n"
            + "=" * 60
            + "\n"
            + f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"Отчетная дата: {stats.reference_date}\n"
            + "=" * 60
            + "\n\n"
            + f"Всего автобусов: {stats.total_buses}\n"
            + f"В рейсе за отчетный день: {stats.active_buses}\n"
            + f"Средняя загрузка парка: {stats.avg_load:.1f}%\n"
            + f"Маршрутов с критической загрузкой: {stats.critical_routes}\n"
        )

    def format_route_report(self) -> str:
        data = self.route_load_analysis()
        if data.empty:
            return "АНАЛИЗ МАРШРУТОВ\n" + "=" * 60 + "\nНет данных по рейсам."

        lines = [
            "АНАЛИЗ ЗАГРУЗКИ МАРШРУТОВ",
            "=" * 60,
            "",
            "ТОП-3 ПРОБЛЕМНЫХ МАРШРУТА:",
        ]
        for index, row in enumerate(self.top_routes(3).itertuples(index=False), start=1):
            lines.append(f"  {index}. Маршрут {row.route_number}: {row.avg_load:.1f}% загрузки")
        lines.append("")

        for row in data.itertuples(index=False):
            lines.extend(
                [
                    f"Маршрут {row.route_number}: {row.route_name}",
                    f"  Утро (7-10): {row.morning_load:.1f}%",
                    f"  Вечер (17-20): {row.evening_load:.1f}%",
                    f"  Средняя загрузка: {row.avg_load:.1f}%",
                    f"  Всего рейсов: {int(row.trip_count)}",
                    "-" * 50,
                ]
            )
        return "\n".join(lines)

    def format_recommendations(self) -> str:
        recommendations = self.recommendations()
        critical = [item for item in recommendations if item.startswith("[Критично]")]
        normal = [item for item in recommendations if not item.startswith("[Критично]")]

        lines = ["РЕКОМЕНДАЦИИ ПО РАСПРЕДЕЛЕНИЮ", "=" * 60, ""]
        if critical:
            lines.append("СРОЧНЫЕ МЕРЫ:")
            for item in critical:
                lines.append(f"  {item}")
            lines.append("")

        lines.append("ОБЩИЕ РЕКОМЕНДАЦИИ:")
        for item in normal:
            lines.append(f"  {item}")
        return "\n".join(lines)

    def export_report(self) -> Path:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_path.write_text(self.analytics_report(), encoding="utf-8")
        return output_path

    def map_static_data(self, query: str = "") -> MapStaticData:
        cache_key = query.strip().lower()
        if cache_key not in self._map_static_cache:
            routes_frame = self.routes(query)
            if routes_frame.empty and cache_key:
                routes_frame = self.routes()
            map_routes = routes_frame.rename(columns={"route_name": "name"})[["id", "name"]].copy()
            stops = self._build_map_stops(routes_frame)
            flow = self._build_map_flow(stops, query)
            self._map_static_cache[cache_key] = build_map_static(map_routes, stops, flow)
        return self._map_static_cache[cache_key]

    def bus_positions(self, hour: float, query: str = "") -> list[BusMarker]:
        static_data = self.map_static_data(query)
        buses = self._map_bus_assignments(query)
        return simulate_bus_positions(
            buses=buses,
            route_lookup=static_data.route_lookup,
            route_colors=static_data.route_colors,
            route_names=static_data.route_names,
            hour=hour,
        )

    def reference_date(self) -> str | None:
        frame = self._read_frame("SELECT MAX(trip_date) AS reference_date FROM trips")
        if frame.empty:
            return None
        value = frame.iloc[0]["reference_date"]
        return str(value) if value else None

    def _ensure_database(self, force_seed: bool = False) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
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
                """
            )
            connection.commit()

        if force_seed or self._table_count("buses") == 0:
            self._seed_base_data()

    def _seed_base_data(self) -> None:
        rng = random.Random(20260315)
        with self._connect() as connection:
            connection.execute("DELETE FROM trips")
            connection.execute("DELETE FROM buses")
            connection.execute("DELETE FROM routes")
            connection.execute("DELETE FROM drivers")
            try:
                connection.execute("DELETE FROM sqlite_sequence")
            except sqlite3.OperationalError:
                pass

            connection.executemany(
                "INSERT INTO buses (gov_number, model, capacity) VALUES (?, ?, ?)",
                self.BASE_BUSES,
            )
            connection.executemany(
                "INSERT INTO routes (route_number, route_name) VALUES (?, ?)",
                self.BASE_ROUTES,
            )
            connection.executemany(
                "INSERT INTO drivers (full_name, license_number) VALUES (?, ?)",
                self.BASE_DRIVERS,
            )

            capacities = {index: bus[2] for index, bus in enumerate(self.BASE_BUSES, start=1)}
            start_date = datetime(2026, 3, 15)
            for day_offset in range(7):
                current_date = start_date + timedelta(days=day_offset)
                date_value = current_date.strftime("%Y-%m-%d")
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
                            connection.execute(
                                """
                                INSERT INTO trips (
                                    bus_id,
                                    route_id,
                                    driver_id,
                                    trip_date,
                                    trip_time,
                                    passenger_count,
                                    load_percent
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    bus_id,
                                    route_id,
                                    driver_id,
                                    date_value,
                                    trip_time,
                                    passenger_count,
                                    load,
                                ),
                            )
            connection.commit()

    def _build_map_stops(self, routes_frame: pd.DataFrame) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for row in routes_frame.sort_values("id").itertuples(index=False):
            route_id = int(row.id)
            route_number = str(row.route_number)
            route_name = str(row.route_name)
            stops = self._route_stop_names(route_number, route_name)
            for index, stop_name in enumerate(stops, start=1):
                rows.append(
                    {
                        "id": route_id * 100 + index,
                        "name": stop_name,
                        "route_id": route_id,
                    }
                )
        return pd.DataFrame(rows, columns=["id", "name", "route_id"])

    def _build_map_flow(self, stops_frame: pd.DataFrame, query: str) -> pd.DataFrame:
        if stops_frame.empty:
            return pd.DataFrame(columns=["stop_id", "count"])

        trips = self.trips(query)
        if trips.empty:
            return pd.DataFrame(columns=["stop_id", "count"])

        route_totals = trips.groupby("route_id")["passenger_count"].sum().to_dict()
        weights = [0.28, 0.46, 0.72, 0.94, 0.78, 0.52]
        weight_sum = sum(weights)

        rows: list[dict[str, int]] = []
        for route_id, group in stops_frame.groupby("route_id", sort=True):
            route_total = int(route_totals.get(int(route_id), 0))
            ordered = group.sort_values("id").reset_index(drop=True)
            for index, stop in ordered.iterrows():
                weight = weights[min(index, len(weights) - 1)]
                count = int(round(route_total * weight / weight_sum))
                rows.append({"stop_id": int(stop["id"]), "count": max(count, 0)})
        return pd.DataFrame(rows, columns=["stop_id", "count"])

    def _map_bus_assignments(self, query: str) -> pd.DataFrame:
        buses = self.buses().copy()
        if buses.empty:
            return pd.DataFrame(columns=["id", "route_id"])

        relevant_routes = self.routes(query)
        route_ids = relevant_routes["id"].astype(int).tolist()
        if not route_ids:
            route_ids = self.routes()["id"].astype(int).tolist()
        if not route_ids:
            return pd.DataFrame(columns=["id", "route_id"])

        trips = self.trips(query)
        assignments: dict[int, int] = {}
        if not trips.empty:
            ordered = trips.sort_values(["trip_date", "trip_time", "id"], ascending=[False, False, False])
            latest = ordered.drop_duplicates(subset=["bus_id"], keep="first")
            assignments = {
                int(row.bus_id): int(row.route_id)
                for row in latest.itertuples(index=False)
                if int(row.route_id) in route_ids
            }

        rows: list[dict[str, int]] = []
        for index, row in enumerate(buses.itertuples(index=False)):
            bus_id = int(row.id)
            route_id = assignments.get(bus_id, route_ids[index % len(route_ids)])
            rows.append({"id": bus_id, "route_id": route_id})
        return pd.DataFrame(rows, columns=["id", "route_id"])

    @staticmethod
    def _route_stop_names(route_number: str, route_name: str) -> list[str]:
        parts = [part.strip() for part in route_name.split(" - ") if part.strip()]
        start = parts[0] if parts else route_name
        end = parts[-1] if parts else route_name
        names = [
            start,
            f"{route_number} Пересадка",
            f"{route_number} Центр",
            f"{route_number} Магистраль",
            f"{route_number} Узел",
            end,
        ]
        unique_names: list[str] = []
        for name in names:
            if not unique_names or unique_names[-1] != name:
                unique_names.append(name)
        return unique_names

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _record_exists(connection: sqlite3.Connection, table_name: str, record_id: int) -> bool:
        cursor = connection.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (record_id,))
        return cursor.fetchone() is not None

    def _read_frame(self, query: str, params: tuple | list = ()) -> pd.DataFrame:
        with self._connect() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def _table_count(self, table_name: str) -> int:
        frame = self._read_frame(f"SELECT COUNT(*) AS count FROM {table_name}")
        return int(frame.iloc[0]["count"])

    @staticmethod
    def _apply_search(frame: pd.DataFrame, query: str) -> pd.DataFrame:
        query = query.strip().lower()
        if not query or frame.empty:
            return frame

        comparable = frame.astype(str)
        mask = comparable.apply(lambda column: column.str.lower().str.contains(query, na=False, regex=False))
        return frame.loc[mask.any(axis=1)].reset_index(drop=True)

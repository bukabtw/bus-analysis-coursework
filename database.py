import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_NAME = 'bus_company.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gov_number TEXT NOT NULL,
            model TEXT NOT NULL,
            capacity INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_number TEXT NOT NULL,
            route_name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            license_number TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
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
        )
    ''')
    
    conn.commit()
    conn.close()

def add_bus(gov_number, model, capacity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO buses (gov_number, model, capacity) VALUES (?, ?, ?)',
                  (gov_number, model, capacity))
    conn.commit()
    conn.close()

def get_all_buses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM buses')
    data = cursor.fetchall()
    conn.close()
    return data

def add_route(route_number, route_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO routes (route_number, route_name) VALUES (?, ?)',
                  (route_number, route_name))
    conn.commit()
    conn.close()

def get_all_routes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM routes')
    data = cursor.fetchall()
    conn.close()
    return data

def add_driver(full_name, license_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO drivers (full_name, license_number) VALUES (?, ?)',
                  (full_name, license_number))
    conn.commit()
    conn.close()

def get_all_drivers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM drivers')
    data = cursor.fetchall()
    conn.close()
    return data

def add_trip(bus_id, route_id, driver_id, trip_date, trip_time, passenger_count, load_percent):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trips (bus_id, route_id, driver_id, trip_date, trip_time, passenger_count, load_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (bus_id, route_id, driver_id, trip_date, trip_time, passenger_count, load_percent))
    conn.commit()
    conn.close()

def get_all_trips():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT trips.id, routes.route_number, buses.gov_number, drivers.full_name, 
               trips.trip_date, trips.trip_time, trips.passenger_count, trips.load_percent
        FROM trips
        JOIN routes ON trips.route_id = routes.id
        JOIN buses ON trips.bus_id = buses.id
        JOIN drivers ON trips.driver_id = drivers.id
    ''')
    data = cursor.fetchall()
    conn.close()
    return data

def add_base_data():
    
    buses = [
        ('А777АА', 'ЛиАЗ-5292', 115),
        ('В888ВВ', 'ЛиАЗ-6213', 150),
        ('С999СС', 'МАЗ-203', 105),
        ('О111ОО', 'НефАЗ-5299', 110),
        ('Т222ТТ', 'ЛиАЗ-4292', 90),
        ('У333УУ', 'ПАЗ-3204', 75),
        ('К444КК', 'МАЗ-206', 85),
        ('Н555НН', 'ЛиАЗ-5292', 115),
        ('Р666РР', 'ЛиАЗ-6213', 150),
        ('С777СС', 'НефАЗ-5299', 110),
        ('М888ММ', 'МАЗ-203', 105),
        ('А999АА', 'ПАЗ-3204', 75),
    ]
    
    for bus in buses:
        add_bus(*bus)
    
    routes = [
        ('м1', 'Китай-город - Силикатный завод'),
        ('м2', 'Фили - ВДНХ'),
        ('т4', 'Новогиреево - Таганская'),
        ('716', 'Выхино - Кожухово'),
        ('204', 'Беляево - Черемушки'),
        ('144', 'Теплый Стан - Метро Парк Победы'),
        ('Т47', 'Нагатино - Павелецкая'),
        ('с13', 'Ясенево - Битцевский парк'),
        ('835', 'Южное Бутово - Щербинка'),
        ('877', 'Некрасовка - Люблино'),
        ('951', 'Жулебино - Кузьминки'),
        ('309', 'Котельники - Выхино'),
    ]
    
    for route in routes:
        add_route(*route)
    
    drivers = [
        ('Петров А.С.', '77УР456789'),
        ('Иванов В.П.', '77МР123456'),
        ('Сидоров К.Н.', '77АА654321'),
        ('Козлов Д.В.', '77ТТ789012'),
        ('Морозов С.И.', '77ВС345678'),
        ('Волков Н.Ф.', '77КЕ901234'),
        ('Лебедев П.Р.', '77МН567890'),
        ('Соколов А.Г.', '77ОХ789123'),
        ('Михайлов И.К.', '77НТ456123'),
        ('Новиков В.С.', '77РП789456'),
    ]
    
    for driver in drivers:
        add_driver(*driver)
    
    start_date = datetime(2026, 3, 15)
    
    for day in range(7):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')
        
        is_weekend = current_date.weekday() >= 5
        
        for route_id in range(1, 13):
            num_buses_on_route = random.randint(3, 6)
            for _ in range(num_buses_on_route):
                bus_id = random.randint(1, 12)
                
                for trip_num in range(random.randint(4, 8)):
                    hour = random.randint(5, 23)
                    
                    if 7 <= hour <= 10:
                        if is_weekend:
                            load = random.randint(60, 85)
                        else:
                            load = random.randint(85, 100)
                    elif 17 <= hour <= 20:
                        if is_weekend:
                            load = random.randint(65, 90)
                        else:
                            load = random.randint(85, 100)
                    elif 11 <= hour <= 16:
                        load = random.randint(40, 75)
                    elif 21 <= hour <= 23:
                        load = random.randint(20, 45)
                    else:
                        load = random.randint(5, 25)
                    
                    capacities = [115, 150, 105, 110, 90, 75, 85, 115, 150, 110, 105, 75]
                    capacity = capacities[bus_id-1]
                    passengers = int(capacity * load / 100)
                    
                    driver_id = random.randint(1, 10)
                    minute = random.randint(0, 59)
                    time_str = f"{hour:02d}:{minute:02d}"
                    
                    add_trip(
                        bus_id, route_id, driver_id,
                        date_str, time_str,
                        passengers, load
                    )
    

def ensure_test_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM buses')
    count = cursor.fetchone()[0]
    
    if count == 0:
        add_base_data()
        print("Данные загружены!")
    else:
        print("В базе уже есть данные.")
    
    conn.close()

init_db()
ensure_test_data()
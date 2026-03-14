import tkinter as tk
from tkinter import ttk, messagebox, font
from tkinter.scrolledtext import ScrolledText
import database as db
import reports as rpt
from analytics import get_recommendations, get_parking_stats, get_route_load_analysis, get_top_routes
from datetime import datetime

try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    SV_TTK_AVAILABLE = False
    print("sv_ttk не найден, используется стандартная тема")

class BusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BAC - Анализ пассажиропотока")
        self.root.geometry("1350x800")
        
        if SV_TTK_AVAILABLE:
            try:
                sv_ttk.set_theme("dark")
            except Exception as e:
                print(f"Ошибка применения темы: {e}")
        
        try:
            default_font = font.nametofont("TkDefaultFont")
            default_font.configure(size=10, family="Segoe UI")
        except:
            pass
        
        self.create_header()
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.create_buses_tab()
        self.create_routes_tab()
        self.create_drivers_tab()
        self.create_trips_tab()
        self.create_analytics_tab()
        self.create_dashboard_tab()
        
        self.create_toolbar()
        
        self.status_bar = ttk.Label(root, text="✅ Система готова к работе", relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
        
        self.refresh_all()
    
    def create_header(self):
        header = ttk.Frame(self.root)
        header.pack(fill='x', padx=10, pady=10)
        
        title = ttk.Label(header, 
                         text="🚍 АВТОМАТИЗИРОВАННАЯ СИСТЕМА УПРАВЛЕНИЯ АВТОПАРКОМ",
                         font=("Segoe UI", 16, "bold"))
        title.pack(side='left')
        
        self.time_label = ttk.Label(header, font=("Segoe UI", 12))
        self.time_label.pack(side='right')
        self.update_time()
    
    def update_time(self):
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.time_label.config(text=f"📅 {current_time}")
        self.root.after(1000, self.update_time)
    
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        buttons = [
            ("🧪 Загрузить базовые данные", self.load_base_data),
            ("📤 Экспорт отчета", self.export_report),
            ("🔄 Обновить все", self.refresh_all),
        ]
        
        for text, command in buttons:
            btn = ttk.Button(toolbar, text=text, command=command)
            btn.pack(side='left', padx=2)
        
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side='right')
        
        ttk.Label(search_frame, text="🔍 Поиск:").pack(side='left')
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_data)
    
    def create_buses_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🚌 Автобусы")
        
        form = ttk.LabelFrame(tab, text="➕ Добавить автобус")
        form.pack(fill='x', padx=10, pady=10)
        
        self.bus_gov = ttk.Entry(form, width=15)
        self.bus_gov.grid(row=0, column=1, padx=5, pady=10)
        
        self.bus_model = ttk.Entry(form, width=20)
        self.bus_model.grid(row=0, column=3, padx=5, pady=10)
        
        self.bus_capacity = ttk.Entry(form, width=10)
        self.bus_capacity.grid(row=0, column=5, padx=5, pady=10)
        
        ttk.Label(form, text="Госномер:").grid(row=0, column=0, padx=5)
        ttk.Label(form, text="Модель:").grid(row=0, column=2, padx=5)
        ttk.Label(form, text="Вместимость:").grid(row=0, column=4, padx=5)
        
        ttk.Button(form, text="➕ Добавить", command=self.add_bus).grid(row=0, column=6, padx=10)
        
        columns = ('ID', 'Госномер', 'Модель', 'Вместимость')
        self.bus_tree = ttk.Treeview(tab, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.bus_tree.heading(col, text=col)
            self.bus_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=self.bus_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.bus_tree.configure(yscrollcommand=scrollbar.set)
        self.bus_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_routes_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🛣️ Маршруты")
        
        form = ttk.LabelFrame(tab, text="➕ Добавить маршрут")
        form.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(form, text="Номер маршрута:").grid(row=0, column=0, padx=5, pady=10)
        self.route_number = ttk.Entry(form)
        self.route_number.grid(row=0, column=1, padx=5)
        
        ttk.Label(form, text="Название:").grid(row=0, column=2, padx=5)
        self.route_name = ttk.Entry(form, width=40)
        self.route_name.grid(row=0, column=3, padx=5)
        
        ttk.Button(form, text="➕ Добавить", command=self.add_route).grid(row=0, column=4, padx=10)
        
        columns = ('ID', 'Номер', 'Название')
        self.route_tree = ttk.Treeview(tab, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.route_tree.heading(col, text=col)
            self.route_tree.column(col, width=200)
        
        self.route_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_drivers_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="👨‍✈️ Водители")
        
        form = ttk.LabelFrame(tab, text="➕ Добавить водителя")
        form.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(form, text="ФИО:").grid(row=0, column=0, padx=5, pady=10)
        self.driver_name = ttk.Entry(form, width=40)
        self.driver_name.grid(row=0, column=1, padx=5)
        
        ttk.Label(form, text="Номер прав:").grid(row=0, column=2, padx=5)
        self.driver_license = ttk.Entry(form)
        self.driver_license.grid(row=0, column=3, padx=5)
        
        ttk.Button(form, text="➕ Добавить", command=self.add_driver).grid(row=0, column=4, padx=10)
        
        columns = ('ID', 'ФИО', 'Номер прав')
        self.driver_tree = ttk.Treeview(tab, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.driver_tree.heading(col, text=col)
            self.driver_tree.column(col, width=300)
        
        self.driver_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_trips_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📅 Рейсы")
        
        form = ttk.LabelFrame(tab, text="➕ Зарегистрировать рейс")
        form.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(form, text="Маршрут:").grid(row=0, column=0, padx=5, pady=5)
        self.trip_route = ttk.Combobox(form, state='readonly', width=30)
        self.trip_route.grid(row=0, column=1, padx=5)
        
        ttk.Label(form, text="Автобус:").grid(row=0, column=2, padx=5)
        self.trip_bus = ttk.Combobox(form, state='readonly', width=20)
        self.trip_bus.grid(row=0, column=3, padx=5)
        
        ttk.Label(form, text="Водитель:").grid(row=0, column=4, padx=5)
        self.trip_driver = ttk.Combobox(form, state='readonly', width=25)
        self.trip_driver.grid(row=0, column=5, padx=5)
        
        ttk.Label(form, text="Дата (ГГГГ-ММ-ДД):").grid(row=1, column=0, padx=5, pady=5)
        self.trip_date = ttk.Entry(form)
        self.trip_date.grid(row=1, column=1, padx=5)
        self.trip_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(form, text="Время (ЧЧ:ММ):").grid(row=1, column=2, padx=5)
        self.trip_time = ttk.Entry(form)
        self.trip_time.grid(row=1, column=3, padx=5)
        self.trip_time.insert(0, datetime.now().strftime('%H:%M'))
        
        ttk.Label(form, text="Пассажиров:").grid(row=1, column=4, padx=5)
        self.trip_passengers = ttk.Entry(form, width=10)
        self.trip_passengers.grid(row=1, column=5, padx=5)
        
        ttk.Button(form, text="✅ Добавить рейс", command=self.add_trip).grid(row=1, column=6, padx=10)
        
        columns = ('ID', 'Маршрут', 'Автобус', 'Водитель', 'Дата', 'Время', 'Пассажиры', 'Загрузка %')
        self.trip_tree = ttk.Treeview(tab, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.trip_tree.heading(col, text=col)
            self.trip_tree.column(col, width=110)
        
        v_scroll = ttk.Scrollbar(tab, orient='vertical', command=self.trip_tree.yview)
        v_scroll.pack(side='right', fill='y')
        h_scroll = ttk.Scrollbar(tab, orient='horizontal', command=self.trip_tree.xview)
        h_scroll.pack(side='bottom', fill='x')
        
        self.trip_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.trip_tree.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_analytics_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Аналитика")
        
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="🔄 Обновить аналитику", 
                  command=self.refresh_analytics).pack(side='left')
        
        self.analytics_text = ScrolledText(tab, wrap=tk.WORD, width=100, height=35, 
                                          font=("Consolas", 10))
        self.analytics_text.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_dashboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📈 Дашборд")
        
        cards_frame = ttk.Frame(tab)
        cards_frame.pack(fill='x', padx=20, pady=20)
        
        self.metric_labels = {}
        metrics = [
            ("🚌 Всего автобусов", "total_buses", "#3498db"),
            ("🔄 В рейсе", "active_buses", "#2ecc71"),
            ("📊 Средняя загрузка", "avg_load", "#f1c40f"),
            ("⚠️ Пиковые маршруты", "critical_routes", "#e74c3c"),
        ]
        
        for i, (label, key, color) in enumerate(metrics):
            card = ttk.Frame(cards_frame, relief='raised', borderwidth=2)
            card.grid(row=0, column=i, padx=10, sticky='ew')
            cards_frame.columnconfigure(i, weight=1)
            
            ttk.Label(card, text=label, font=("Segoe UI", 12)).pack(pady=(15,5))
            self.metric_labels[key] = ttk.Label(card, text="0", font=("Segoe UI", 24, "bold"))
            self.metric_labels[key].pack(pady=(0,15))
        
        top_frame = ttk.LabelFrame(tab, text="🔥 Топ-5 загруженных маршрутов")
        top_frame.pack(fill='x', padx=20, pady=10)
        
        columns = ('Маршрут', 'Название', 'Загрузка')
        self.top_tree = ttk.Treeview(top_frame, columns=columns, show='headings', height=5)
        
        for col in columns:
            self.top_tree.heading(col, text=col)
            self.top_tree.column(col, width=200)
        
        self.top_tree.pack(fill='x', padx=5, pady=5)
    
    def add_bus(self):
        gov = self.bus_gov.get()
        model = self.bus_model.get()
        capacity = self.bus_capacity.get()
        
        if gov and model and capacity:
            try:
                db.add_bus(gov, model, int(capacity))
                self.bus_gov.delete(0, tk.END)
                self.bus_model.delete(0, tk.END)
                self.bus_capacity.delete(0, tk.END)
                self.refresh_buses()
                self.status_bar.config(text=f"✅ Автобус {gov} добавлен")
            except:
                messagebox.showerror("Ошибка", "Проверьте данные")
        else:
            messagebox.showwarning("Внимание", "Заполните все поля")
    
    def add_route(self):
        number = self.route_number.get()
        name = self.route_name.get()
        
        if number and name:
            db.add_route(number, name)
            self.route_number.delete(0, tk.END)
            self.route_name.delete(0, tk.END)
            self.refresh_routes()
            self.status_bar.config(text=f"✅ Маршрут {number} добавлен")
        else:
            messagebox.showwarning("Внимание", "Заполните все поля")
    
    def add_driver(self):
        name = self.driver_name.get()
        license_num = self.driver_license.get()
        
        if name and license_num:
            db.add_driver(name, license_num)
            self.driver_name.delete(0, tk.END)
            self.driver_license.delete(0, tk.END)
            self.refresh_drivers()
            self.status_bar.config(text=f"✅ Водитель {name} добавлен")
        else:
            messagebox.showwarning("Внимание", "Заполните все поля")
    
    def add_trip(self):
        try:
            route_idx = self.trip_route.current()
            bus_idx = self.trip_bus.current()
            driver_idx = self.trip_driver.current()
            
            if route_idx == -1 or bus_idx == -1 or driver_idx == -1:
                messagebox.showwarning("Внимание", "Выберите все элементы")
                return
            
            routes = db.get_all_routes()
            buses = db.get_all_buses()
            drivers = db.get_all_drivers()
            
            route_id = routes[route_idx][0]
            bus_id = buses[bus_idx][0]
            driver_id = drivers[driver_idx][0]
            
            date = self.trip_date.get()
            time = self.trip_time.get()
            passengers = int(self.trip_passengers.get())
            
            capacity = buses[bus_idx][3]
            load_percent = round((passengers / capacity) * 100)
            
            db.add_trip(bus_id, route_id, driver_id, date, time, passengers, load_percent)
            
            self.refresh_trips()
            self.status_bar.config(text=f"✅ Рейс на маршрут {routes[route_idx][1]} добавлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def refresh_buses(self):
        for row in self.bus_tree.get_children():
            self.bus_tree.delete(row)
        for bus in db.get_all_buses():
            self.bus_tree.insert('', 'end', values=bus)
    
    def refresh_routes(self):
        for row in self.route_tree.get_children():
            self.route_tree.delete(row)
        for route in db.get_all_routes():
            self.route_tree.insert('', 'end', values=route)
    
    def refresh_drivers(self):
        for row in self.driver_tree.get_children():
            self.driver_tree.delete(row)
        for driver in db.get_all_drivers():
            self.driver_tree.insert('', 'end', values=driver)
    
    def refresh_trips(self):
        for row in self.trip_tree.get_children():
            self.trip_tree.delete(row)
        
        for trip in db.get_all_trips():
            item_id = self.trip_tree.insert('', 'end', values=trip)
            load = trip[7]
            if load > 85:
                self.trip_tree.tag_configure('high', background='#3d1a1a')
                self.trip_tree.item(item_id, tags=('high',))
            elif load < 40:
                self.trip_tree.tag_configure('low', background='#1a3d1a')
                self.trip_tree.item(item_id, tags=('low',))
    
    def refresh_comboboxes(self):
        routes = db.get_all_routes()
        self.trip_route['values'] = [f"{r[1]} - {r[2]}" for r in routes]
        
        buses = db.get_all_buses()
        self.trip_bus['values'] = [f"{b[1]} ({b[2]})" for b in buses]
        
        drivers = db.get_all_drivers()
        self.trip_driver['values'] = [d[1] for d in drivers]
    
    def refresh_analytics(self):
        self.analytics_text.delete(1.0, tk.END)
        self.analytics_text.insert(tk.END, rpt.format_stats())
        self.analytics_text.insert(tk.END, rpt.format_route_report())
        self.analytics_text.insert(tk.END, rpt.format_recommendations())
        self.analytics_text.see(1.0)
    
    def refresh_dashboard(self):
        stats = get_parking_stats()
        self.metric_labels['total_buses'].config(text=str(stats['total_buses']))
        self.metric_labels['active_buses'].config(text=str(stats['active_buses']))
        self.metric_labels['avg_load'].config(text=f"{stats['avg_load']}%")
        self.metric_labels['critical_routes'].config(text=str(stats['critical_routes']))
        
        for row in self.top_tree.get_children():
            self.top_tree.delete(row)
        
        for route in get_top_routes(5):
            self.top_tree.insert('', 'end', values=route)
    
    def refresh_all(self):
        self.refresh_buses()
        self.refresh_routes()
        self.refresh_drivers()
        self.refresh_trips()
        self.refresh_comboboxes()
        self.refresh_analytics()
        self.refresh_dashboard()
        self.status_bar.config(text="✅ Все данные обновлены")
    
    def search_data(self, event=None):
        query = self.search_entry.get().lower()
        
        if not query or len(query) < 2:
            self.refresh_all()
            return
        
        for tree in [self.bus_tree, self.route_tree, self.driver_tree, self.trip_tree]:
            for row in tree.get_children():
                tree.delete(row)
        
        for bus in db.get_all_buses():
            if query in str(bus).lower():
                self.bus_tree.insert('', 'end', values=bus)
        
        for route in db.get_all_routes():
            if query in str(route).lower():
                self.route_tree.insert('', 'end', values=route)
        
        for driver in db.get_all_drivers():
            if query in str(driver).lower():
                self.driver_tree.insert('', 'end', values=driver)
        
        for trip in db.get_all_trips():
            if query in str(trip).lower():
                self.trip_tree.insert('', 'end', values=trip)
        
        self.status_bar.config(text=f"🔍 Найдено результатов по запросу: {query}")
    
    def load_base_data(self):
        if messagebox.askyesno("Подтверждение", "Это удалит все текущие данные. Продолжить?"):
            import os
            if os.path.exists('bus_company.db'):
                os.remove('bus_company.db')
            db.init_db()
            db.add_base_data()
            self.refresh_all()
            self.status_bar.config(text="✅ Базовые данные Москвы загружены!")
    
    def export_report(self):
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ОТЧЕТ ПО РАБОТЕ АВТОПАРКА\n")
            f.write(f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write(rpt.format_stats())
            f.write("\n")
            f.write(rpt.format_route_report())
            f.write("\n")
            f.write(rpt.format_recommendations())
        
        self.status_bar.config(text=f"✅ Отчет сохранен: {filename}")
        messagebox.showinfo("Экспорт", f"Отчет сохранен в файл:\n{filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BusApp(root)
    root.mainloop()
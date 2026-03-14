from analytics import get_route_load_analysis, get_recommendations, get_parking_stats, get_top_routes
from datetime import datetime

def format_stats():
    stats = get_parking_stats()
    
    report = "📊 СТАТИСТИКА АВТОПАРКА\n"
    report += "=" * 60 + "\n"
    report += f"📅 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    report += "=" * 60 + "\n\n"
    report += f"🚌 Всего автобусов: {stats['total_buses']}\n"
    report += f"🔄 В рейсе сегодня: {stats['active_buses']}\n"
    report += f"📈 Средняя загрузка парка: {stats['avg_load']}%\n"
    report += f"⚠️ Маршрутов с критической загрузкой: {stats['critical_routes']}\n"
    
    return report

def format_route_report():
    data = get_route_load_analysis()
    top_routes = get_top_routes(3)
    
    report = "\n📊 АНАЛИЗ ЗАГРУЗКИ МАРШРУТОВ\n"
    report += "=" * 60 + "\n\n"
    
    report += "🔥 ТОП-3 ПРОБЛЕМНЫХ МАРШРУТА:\n"
    for i, route in enumerate(top_routes, 1):
        report += f"  {i}. Маршрут {route[0]}: {route[2]:.1f}% загрузки\n"
    report += "\n"
    
    for row in data:
        route_num, route_name, morning, evening, avg, trips = row
        morning = morning or 0
        evening = evening or 0
        
        if avg > 75:
            icon = "🔴"
        elif avg > 50:
            icon = "🟡"
        else:
            icon = "🟢"
        
        report += f"{icon} Маршрут {route_num}: {route_name}\n"
        report += f"   🌅 Утро (7-10): {morning:.1f}%\n"
        report += f"   🌃 Вечер (17-20): {evening:.1f}%\n"
        report += f"   📊 Среднее: {avg:.1f}%\n"
        report += f"   🚌 Рейсов: {trips}\n"
        report += "-" * 50 + "\n"
    
    return report

def format_recommendations():
    recs = get_recommendations()
    
    report = "\n💡 РЕКОМЕНДАЦИИ ПО РАСПРЕДЕЛЕНИЮ\n"
    report += "=" * 60 + "\n\n"
    
    critical = [r for r in recs if "КРИТИЧЕСКАЯ" in r]
    normal = [r for r in recs if "КРИТИЧЕСКАЯ" not in r]
    
    if critical:
        report += "🚨 СРОЧНЫЕ МЕРЫ:\n"
        for rec in critical:
            report += f"  {rec}\n"
        report += "\n"
    
    report += "📋 РЕКОМЕНДАЦИИ:\n"
    for rec in normal:
        report += f"  {rec}\n"
    
    return report
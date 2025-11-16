import json
import csv
from datetime import datetime, timedelta
from collections import Counter

class ReportGenerator:
    def __init__(self, data):
        self.data = data
    
    def generate_expiry_report(self):
        """Генерация отчета по срокам годности"""
        expired = []
        expiring_soon = []
        valid = []
        
        for item in self.data:
            if item.get('data_type') == 'СИЗ' and item.get('expiry_date') != 'Не указан':
                try:
                    expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    if days_until_expiry < 0:
                        expired.append(item)
                    elif days_until_expiry <= 30:
                        expiring_soon.append(item)
                    else:
                        valid.append(item)
                except:
                    pass
        
        return {
            'expired': expired,
            'expiring_soon': expiring_soon,
            'valid': valid,
            'summary': {
                'total_siz': len(expired) + len(expiring_soon) + len(valid),
                'expired_count': len(expired),
                'expiring_soon_count': len(expiring_soon),
                'valid_count': len(valid)
            }
        }
    
    def generate_type_report(self):
        """Генерация отчета по типам СИЗ"""
        type_counter = Counter()
        manufacturer_counter = Counter()
        
        for item in self.data:
            if item.get('data_type') == 'СИЗ':
                siz_type = item.get('type', 'Не указан')
                manufacturer = item.get('manufacturer', 'Не указан')
                type_counter[siz_type] += 1
                manufacturer_counter[manufacturer] += 1
        
        return {
            'by_type': dict(type_counter.most_common()),
            'by_manufacturer': dict(manufacturer_counter.most_common(10))  # Топ 10 производителей
        }
    
    def generate_timeline_report(self, days=30):
        """Генерация отчета по временной линии"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_counts = {}
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%d.%m.%Y')
            daily_counts[date_str] = 0
        
        for item in self.data:
            try:
                item_date = datetime.strptime(item.get('timestamp', ''), '%d.%m.%Y %H:%M')
                date_str = item_date.strftime('%d.%m.%Y')
                if date_str in daily_counts:
                    daily_counts[date_str] += 1
            except:
                pass
        
        return daily_counts
    
    def generate_comprehensive_report(self):
        """Генерация комплексного отчета"""
        expiry_report = self.generate_expiry_report()
        type_report = self.generate_type_report()
        timeline_report = self.generate_timeline_report(30)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'total_records': len(self.data),
                'siz_count': sum(1 for item in self.data if item.get('data_type') == 'СИЗ'),
                'receipt_count': sum(1 for item in self.data if item.get('data_type') == 'Фискальный чек'),
                'other_count': len(self.data) - sum(1 for item in self.data if item.get('data_type') in ['СИЗ', 'Фискальный чек'])
            },
            'expiry_analysis': expiry_report['summary'],
            'type_analysis': type_report,
            'timeline_analysis': timeline_report,
            'critical_items': expiry_report['expired'][:10]  # Топ 10 просроченных
        }
    
    def export_report_to_json(self, report, filename):
        """Экспорт отчета в JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return True, f"Отчет сохранен в {filename}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"
    
    def export_report_to_csv(self, report, filename):
        """Экспорт отчета в CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Записываем сводку
                writer.writerow(['Сводка отчета'])
                writer.writerow(['Сгенерировано', report['generated_at']])
                writer.writerow([])
                
                # Данные по СИЗ
                writer.writerow(['Статистика по СИЗ'])
                for key, value in report['data_summary'].items():
                    writer.writerow([key, value])
                writer.writerow([])
                
                # Анализ сроков
                writer.writerow(['Анализ сроков годности'])
                for key, value in report['expiry_analysis'].items():
                    writer.writerow([key, value])
                writer.writerow([])
                
                # Критические позиции
                writer.writerow(['Критические позиции (просроченные)'])
                writer.writerow(['Название', 'Тип', 'Срок годности', 'Производитель'])
                for item in report.get('critical_items', []):
                    writer.writerow([
                        item.get('name', ''),
                        item.get('type', ''),
                        item.get('expiry_date', ''),
                        item.get('manufacturer', '')
                    ])
            
            return True, f"Отчет сохранен в {filename}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"

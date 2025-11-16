import json

# Тестовые данные в разных форматах
test_data_sets = {
    "siz_json": {
        "name": "Респиратор Р-2",
        "type": "Фильтрующий полумаска", 
        "protection_class": "FFP2",
        "expiry_date": "2025-12-31",
        "manufacturer": "Завод СИЗ",
        "certificate": "РОСС RU.ПБ01.В00001"
    },
    
    "receipt": "t=20251115T1213&s=150.00&fn=7380440801230307&i=3562&fp=1980160056&n=1",
    
    "simple_text": "Защитные очки;EN166;2026-06-30;Очковый завод",
    
    "custom_siz": {
        "product": "Защитные перчатки",
        "category": "СИЗ",
        "expiration": "2025-06-30",
        "standard": "ГОСТ 12.4.103"
    }
}

def print_test_data():
    """Печать тестовых данных для копирования в QR-генератор"""
    print("=== Тестовые данные для QR-кодов ===\n")
    
    print("1. СИЗ в JSON формате:")
    print(json.dumps(test_data_sets["siz_json"], ensure_ascii=False, indent=2))
    print()
    
    print("2. Фискальный чек:")
    print(test_data_sets["receipt"])
    print()
    
    print("3. Простой текст с разделителями:")
    print(test_data_sets["simple_text"])
    print()
    
    print("4. Кастомные данные СИЗ:")
    print(json.dumps(test_data_sets["custom_siz"], ensure_ascii=False, indent=2))
    print("\n" + "="*50)

if __name__ == "__main__":
    print_test_data()

import os
import json
from datetime import datetime, timedelta

class NotificationManager:
    def __init__(self):
        self.config_file = "notifications_config.json"
        self.load_config()
    
    def load_config(self):
        """Загрузка конфигурации уведомлений"""
        default_config = {
            "enabled": True,
            "check_interval_hours": 24,
            "last_check": None,
            "warning_days": 30
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except:
            self.config = default_config
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def should_check(self):
        """Проверка, нужно ли выполнять проверку"""
        if not self.config.get("enabled", True):
            return False
        
        last_check = self.config.get("last_check")
        if not last_check:
            return True
        
        try:
            last_check_date = datetime.fromisoformat(last_check)
            interval = timedelta(hours=self.config.get("check_interval_hours", 24))
            return datetime.now() - last_check_date >= interval
        except:
            return True
    
    def check_expirations(self, history_data):
        """Проверка просроченных СИЗ"""
        if not self.should_check():
            return None
        
        expired = []
        soon_expired = []
        warning_days = self.config.get("warning_days", 30)
        
        for item in history_data:
            if item.get('data_type') == 'СИЗ' and item.get('expiry_date') != 'Не указан':
                try:
                    expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    if days_until_expiry < 0:
                        expired.append(item)
                    elif days_until_expiry <= warning_days:
                        soon_expired.append(item)
                except:
                    pass
        
        # Обновляем время последней проверки
        self.config["last_check"] = datetime.now().isoformat()
        self.save_config()
        
        return expired, soon_expired
    
    def show_windows_notification(self, title, message):
        """Показать уведомление Windows"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=10,
                threaded=True
            )
            return True
        except ImportError:
            print("Библиотека win10toast не установлена")
            return False
        except Exception as e:
            print(f"Ошибка показа уведомления: {e}")
            return False
    
    def enable_notifications(self):
        """Включить уведомления"""
        self.config["enabled"] = True
        self.save_config()
    
    def disable_notifications(self):
        """Выключить уведомления"""
        self.config["enabled"] = False
        self.save_config()

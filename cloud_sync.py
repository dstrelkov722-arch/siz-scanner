import requests
import json
import os
from datetime import datetime

class CloudSync:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.config_file = "cloud_config.json"
        self.load_config()
    
    def load_config(self):
        """Загрузка конфигурации облака"""
        default_config = {
            "enabled": False,
            "server_url": "http://localhost:8000",
            "sync_interval": 3600,
            "last_sync": None
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
            print(f"Ошибка сохранения конфигурации облака: {e}")
    
    def enable_sync(self, server_url):
        """Включение синхронизации"""
        self.config["enabled"] = True
        self.config["server_url"] = server_url
        self.save_config()
    
    def disable_sync(self):
        """Выключение синхронизации"""
        self.config["enabled"] = False
        self.save_config()
    
    def upload_data(self, data):
        """Загрузка данных на сервер"""
        if not self.config["enabled"]:
            return False, "Синхронизация отключена"
        
        try:
            response = requests.post(
                f"{self.config['server_url']}/api/data",
                json={
                    "user": self.auth_manager.get_current_user(),
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.config["last_sync"] = datetime.now().isoformat()
                self.save_config()
                return True, "Данные успешно загружены"
            else:
                return False, f"Ошибка сервера: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Ошибка соединения: {str(e)}"
    
    def download_data(self):
        """Загрузка данных с сервера"""
        if not self.config["enabled"]:
            return None, "Синхронизация отключена"
        
        try:
            response = requests.get(
                f"{self.config['server_url']}/api/data",
                params={"user": self.auth_manager.get_current_user()},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.config["last_sync"] = datetime.now().isoformat()
                self.save_config()
                return data, "Данные успешно загружены"
            else:
                return None, f"Ошибка сервера: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return None, f"Ошибка соединения: {str(e)}"
    
    def sync_data(self, local_data):
        """Синхронизация данных"""
        if not self.config["enabled"]:
            return local_data, "Синхронизация отключена"
        
        # Загружаем данные с сервера
        server_data, message = self.download_data()
        if server_data is None:
            return local_data, message
        
        # Объединяем данные (простая стратегия - приоритет у более новых записей)
        merged_data = self.merge_data(local_data, server_data)
        
        # Загружаем объединенные данные обратно на сервер
        success, upload_message = self.upload_data(merged_data)
        if success:
            return merged_data, "Синхронизация завершена"
        else:
            return merged_data, f"Синхронизация частично завершена: {upload_message}"
    
    def merge_data(self, local_data, server_data):
        """Объединение локальных и серверных данных"""
        # Простая стратегия слияния - объединяем и убираем дубликаты по timestamp и имени
        merged = {}
        
        for item in local_data + server_data:
            key = f"{item.get('name', '')}_{item.get('timestamp', '')}"
            if key not in merged:
                merged[key] = item
            else:
                # Если запись уже есть, оставляем более новую (по timestamp)
                existing_timestamp = merged[key].get('timestamp', '')
                new_timestamp = item.get('timestamp', '')
                if new_timestamp > existing_timestamp:
                    merged[key] = item
        
        return list(merged.values())

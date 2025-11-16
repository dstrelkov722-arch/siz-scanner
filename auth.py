import json
import os
import hashlib
from datetime import datetime

class AuthManager:
    def __init__(self):
        self.users_file = "users.json"
        self.current_user = None
        self.load_users()
    
    def load_users(self):
        """Загрузка пользователей из файла"""
        default_users = {
            "admin": {
                "password": self.hash_password("admin"),
                "role": "admin",
                "created": datetime.now().isoformat()
            }
        }
        
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = default_users
                self.save_users()
        except:
            self.users = default_users
    
    def save_users(self):
        """Сохранение пользователей"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {e}")
    
    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, role="user"):
        """Регистрация нового пользователя"""
        if username in self.users:
            return False, "Пользователь уже существует"
        
        self.users[username] = {
            "password": self.hash_password(password),
            "role": role,
            "created": datetime.now().isoformat()
        }
        self.save_users()
        return True, "Пользователь зарегистрирован"
    
    def login(self, username, password):
        """Аутентификация пользователя"""
        if username not in self.users:
            return False, "Пользователь не найден"
        
        if self.users[username]["password"] == self.hash_password(password):
            self.current_user = username
            return True, "Успешный вход"
        else:
            return False, "Неверный пароль"
    
    def logout(self):
        """Выход пользователя"""
        self.current_user = None
    
    def get_current_user(self):
        """Получить текущего пользователя"""
        return self.current_user
    
    def get_user_role(self):
        """Получить роль текущего пользователя"""
        if self.current_user and self.current_user in self.users:
            return self.users[self.current_user].get("role", "user")
        return "guest"
    
    def has_permission(self, required_role):
        """Проверка прав доступа"""
        roles = {"guest": 0, "user": 1, "admin": 2}
        user_role = self.get_user_role()
        return roles.get(user_role, 0) >= roles.get(required_role, 0)
    
    def change_password(self, username, new_password):
        """Изменение пароля"""
        if username in self.users:
            self.users[username]["password"] = self.hash_password(new_password)
            self.save_users()
            return True, "Пароль изменен"
        return False, "Пользователь не найден"

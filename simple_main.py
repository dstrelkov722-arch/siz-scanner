from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty
import json
import os
import csv
from datetime import datetime, timedelta

# Импортируем наши модули
try:
    from qr_scanner import QRScanner
    HAS_QR_SCANNER = True
    print("QR-сканер доступен")
except ImportError as e:
    print(f"QR-сканер недоступен: {e}")
    HAS_QR_SCANNER = False

try:
    from auth import AuthManager
    HAS_AUTH = True
except ImportError:
    print("Модуль аутентификации недоступен")
    HAS_AUTH = False

try:
    from cloud_sync import CloudSync
    HAS_CLOUD_SYNC = True
except ImportError:
    print("Модуль облачной синхронизации недоступен")
    HAS_CLOUD_SYNC = False

try:
    from reports import ReportGenerator
    HAS_REPORTS = True
except ImportError:
    print("Модуль отчетов недоступен")
    HAS_REPORTS = False

# Классы экранов
class LoginScreen(Screen):
    pass

class MainScreen(Screen):
    pass

class HistoryScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class SIZScannerApp(App):
    scan_results = ListProperty([])
    history_data = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if HAS_AUTH:
            self.auth_manager = AuthManager()
        if HAS_CLOUD_SYNC and HAS_AUTH:
            self.cloud_sync = CloudSync(self.auth_manager)

    def build(self):
        self.sm = ScreenManager()
        
        # Создаем экраны
        self.login_screen = LoginScreen(name='login')
        self.main_screen = MainScreen(name='main')
        self.history_screen = HistoryScreen(name='history')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.history_screen)
        self.sm.add_widget(self.settings_screen)
        
        # Настраиваем экраны
        self.setup_login_screen()
        self.setup_main_screen()
        self.setup_history_screen()
        self.setup_settings_screen()
        
        self.load_history()
        
        # Если аутентификация отключена, сразу переходим на главный экран
        if not HAS_AUTH:
            self.sm.current = 'main'
        else:
            self.sm.current = 'login'
            
        return self.sm

    def on_start(self):
        """Вызывается при запуске приложения"""
        # Проверяем просроченные СИЗ при запуске
        self.show_expiration_warnings()

    def check_camera_status(self):
        """Проверка статуса камеры"""
        if not HAS_QR_SCANNER:
            return "no_scanner"
        
        try:
            scanner = QRScanner()
            if scanner.available_cameras:
                return "available"
            else:
                return "no_camera"
        except:
            return "error"

    def check_expirations(self):
        """Проверка СИЗ с истекающим сроком годности"""
        soon_expired = []
        expired = []
        
        for item in self.history_data:
            if item.get('data_type') == 'СИЗ' and item.get('expiry_date') != 'Не указан':
                try:
                    expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    if days_until_expiry < 0:
                        expired.append(item)
                    elif days_until_expiry <= 30:  # Меньше 30 дней
                        soon_expired.append(item)
                except:
                    pass
        
        return soon_expired, expired

    def show_expiration_warnings(self):
        """Показать предупреждения о истекающих сроках"""
        soon_expired, expired = self.check_expirations()
        
        if expired:
            message = "ПРОСРОЧЕННЫЕ СИЗ:\n"
            for item in expired[:3]:  # Показываем первые 3
                message += f"• {item['name']} (истек {item['expiry_date']})\n"
            if len(expired) > 3:
                message += f"... и еще {len(expired) - 3}\n"
            self.show_error("ВНИМАНИЕ: Просроченные СИЗ", message)
        
        elif soon_expired:
            message = "Скоро истекают:\n"
            for item in soon_expired[:3]:
                days_left = (datetime.strptime(item['expiry_date'], '%Y-%m-%d') - datetime.now()).days
                message += f"• {item['name']} (осталось {days_left} дней)\n"
            if len(soon_expired) > 3:
                message += f"... и еще {len(soon_expired) - 3}\n"
            self.show_info("Срок годности", message)

    def get_stats_text(self):
        """Получить текст статистики"""
        total = len(self.history_data)
        siz_count = len([x for x in self.history_data if x.get('data_type') == 'СИЗ'])
        receipt_count = len([x for x in self.history_data if x.get('data_type') == 'Фискальный чек'])
        
        soon_expired, expired = self.check_expirations()
        warning_text = ""
        if expired:
            warning_text = f" ⚠ {len(expired)} просрочено"
        elif soon_expired:
            warning_text = f" ⚠ {len(soon_expired)} скоро истекает"
        
        return f"Всего: {total} | СИЗ: {siz_count} | Чеки: {receipt_count}{warning_text}"

    def update_stats(self):
        """Обновить отображение статистики"""
        if hasattr(self, 'stats_label'):
            self.stats_label.text = self.get_stats_text()

    def update_user_display(self):
        """Обновление отображения информации о пользователе"""
        if hasattr(self, 'user_label') and HAS_AUTH:
            current_user = self.auth_manager.get_current_user()
            user_role = self.auth_manager.get_user_role()
            
            if current_user:
                self.user_label.text = f"{current_user} ({user_role})"
            else:
                self.user_label.text = "Гость"

    def setup_login_screen(self):
        """Настройка экрана входа"""
        if not HAS_AUTH:
            return
            
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text='Сканер СИЗ', font_size='24sp')
        layout.add_widget(title)
        
        self.username_input = TextInput(hint_text='Имя пользователя', size_hint_y=0.15)
        self.password_input = TextInput(hint_text='Пароль', password=True, size_hint_y=0.15)
        
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        login_btn = Button(text='Вход')
        register_btn = Button(text='Регистрация')
        
        login_btn.bind(on_release=self.login)
        register_btn.bind(on_release=self.show_registration)
        
        btn_layout.add_widget(login_btn)
        btn_layout.add_widget(register_btn)
        layout.add_widget(btn_layout)
        
        self.login_status = Label(text='', size_hint_y=0.1)
        layout.add_widget(self.login_status)
        
        # Кнопка для пропуска аутентификации (для тестирования)
        skip_btn = Button(text='Продолжить без входа', size_hint_y=0.1)
        skip_btn.bind(on_release=lambda x: setattr(self.sm, 'current', 'main'))
        layout.add_widget(skip_btn)
        
        self.login_screen.add_widget(layout)

    def setup_main_screen(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Верхняя панель с информацией о пользователе
        if HAS_AUTH:
            top_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
            
            user_label = Label(
                text='Гость',
                size_hint_x=0.6,
                text_size=(200, None),
                halign='left'
            )
            self.user_label = user_label
            
            settings_btn = Button(text='⚙️', size_hint_x=0.2)
            settings_btn.bind(on_release=lambda x: setattr(self.sm, 'current', 'settings'))
            
            logout_btn = Button(text='🚪', size_hint_x=0.2)
            logout_btn.bind(on_release=self.logout)
            
            top_layout.add_widget(user_label)
            top_layout.add_widget(settings_btn)
            top_layout.add_widget(logout_btn)
            layout.add_widget(top_layout)
        
        # Заголовок
        title = Label(text='Сканер СИЗ', font_size='20sp', size_hint_y=0.06)
        layout.add_widget(title)
        
        # Статистика
        self.stats_label = Label(
            text=self.get_stats_text(),
            font_size='12sp', 
            size_hint_y=0.06,
            text_size=(400, None),
            halign='center'
        )
        layout.add_widget(self.stats_label)
        
        # Статус камеры
        self.camera_status = self.check_camera_status()
        status_text = self.get_camera_status_text()
        status_label = Label(
            text=status_text, 
            font_size='12sp', 
            size_hint_y=0.05,
            color=(1, 0.5, 0, 1) if self.camera_status != "available" else (0, 0.8, 0, 1)
        )
        layout.add_widget(status_label)
        
        # Основные кнопки действий
        action_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        scan_btn = Button(text='📷\nСканировать')
        scan_btn.bind(on_release=self.scan_qr_code)
        
        history_btn = Button(text='📋\nИстория')
        history_btn.bind(on_release=self.show_history)
        
        stats_btn = Button(text='📊\nСтатистика')
        stats_btn.bind(on_release=self.show_detailed_stats)
        
        action_layout.add_widget(scan_btn)
        action_layout.add_widget(history_btn)
        action_layout.add_widget(stats_btn)
        layout.add_widget(action_layout)
        
        # Дополнительные кнопки
        extra_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        backup_btn = Button(text='💾\nРезервная копия')
        backup_btn.bind(on_release=self.create_backup)
        
        export_btn = Button(text='📤\nЭкспорт')
        export_btn.bind(on_release=self.export_data)
        
        clear_btn = Button(text='🗑️\nОчистить')
        clear_btn.bind(on_release=self.clear_results)
        
        extra_layout.add_widget(backup_btn)
        extra_layout.add_widget(export_btn)
        extra_layout.add_widget(clear_btn)
        
        # Кнопка восстановления только если есть модуль
        if HAS_REPORTS:
            restore_btn = Button(text='🔄\nВосстановить')
            restore_btn.bind(on_release=self.restore_from_backup)
            extra_layout.add_widget(restore_btn)
        
        layout.add_widget(extra_layout)
        
        # Область результатов
        self.results_container = GridLayout(cols=1, size_hint_y=0.5, spacing=10)
        scroll = ScrollView()
        scroll.add_widget(self.results_container)
        layout.add_widget(scroll)
        
        self.main_screen.add_widget(layout)

    def get_camera_status_text(self):
        """Текст статуса камеры"""
        if self.camera_status == "available":
            return "✓ Камера доступна"
        elif self.camera_status == "no_camera":
            return "⚠ Камера не найдена (используется демо-режим)"
        elif self.camera_status == "no_scanner":
            return "⚠ Сканер QR-кодов недоступен"
        else:
            return "❌ Ошибка доступа к камере"

    def get_scan_button_text(self):
        """Текст кнопки сканирования"""
        if self.camera_status == "available":
            return 'Сканировать QR-код с камеры'
        else:
            return 'Добавить тестовый СИЗ (демо-режим)'

    def setup_history_screen(self):
        layout = BoxLayout(orientation='vertical')
        
        # Кнопка назад
        back_btn = Button(text='Назад', size_hint_y=0.08)
        back_btn.bind(on_release=self.back_to_main)
        layout.add_widget(back_btn)
        
        # Поле поиска
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=5)
        self.search_input = TextInput(
            hint_text='Поиск по названию...',
            multiline=False,
            size_hint_x=0.7
        )
        search_btn = Button(text='Найти', size_hint_x=0.2)
        search_btn.bind(on_release=self.search_history)
        clear_search_btn = Button(text='X', size_hint_x=0.1)
        clear_search_btn.bind(on_release=self.clear_search)
        
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(search_btn)
        search_layout.add_widget(clear_search_btn)
        layout.add_widget(search_layout)
        
        # Список истории
        self.history_list = GridLayout(cols=1, size_hint_y=0.84, spacing=5)
        scroll = ScrollView()
        scroll.add_widget(self.history_list)
        layout.add_widget(scroll)
        
        self.history_screen.add_widget(layout)

    def setup_settings_screen(self):
        """Настройка экрана настроек"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title = Label(text='Настройки', font_size='20sp', size_hint_y=0.1)
        layout.add_widget(title)
        
        # Настройки облачной синхронизации (только если модули доступны)
        if HAS_CLOUD_SYNC and HAS_AUTH:
            sync_label = Label(text='Облачная синхронизация:', size_hint_y=0.05)
            layout.add_widget(sync_label)
            
            self.server_url_input = TextInput(
                hint_text='URL сервера',
                text=self.cloud_sync.config.get('server_url', ''),
                size_hint_y=0.08
            )
            layout.add_widget(self.server_url_input)
            
            sync_btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
            enable_sync_btn = Button(text='Включить синхронизацию')
            disable_sync_btn = Button(text='Выключить синхронизацию')
            sync_now_btn = Button(text='Синхронизировать сейчас')
            
            enable_sync_btn.bind(on_release=self.enable_cloud_sync)
            disable_sync_btn.bind(on_release=self.disable_cloud_sync)
            sync_now_btn.bind(on_release=self.sync_data)
            
            sync_btn_layout.add_widget(enable_sync_btn)
            sync_btn_layout.add_widget(disable_sync_btn)
            sync_btn_layout.add_widget(sync_now_btn)
            layout.add_widget(sync_btn_layout)
        
        # Отчеты (только если модуль доступен)
        if HAS_REPORTS:
            reports_label = Label(text='Отчеты:', size_hint_y=0.05)
            layout.add_widget(reports_label)
            
            reports_btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
            gen_report_btn = Button(text='Сгенерировать отчет')
            export_json_btn = Button(text='Экспорт в JSON')
            export_csv_btn = Button(text='Экспорт в CSV')
            
            gen_report_btn.bind(on_release=self.generate_report)
            export_json_btn.bind(on_release=self.export_report_json)
            export_csv_btn.bind(on_release=self.export_report_csv)
            
            reports_btn_layout.add_widget(gen_report_btn)
            reports_btn_layout.add_widget(export_json_btn)
            reports_btn_layout.add_widget(export_csv_btn)
            layout.add_widget(reports_btn_layout)
        
        # Кнопка назад
        back_btn = Button(text='Назад', size_hint_y=0.1)
        back_btn.bind(on_release=lambda x: setattr(self.sm, 'current', 'main'))
        layout.add_widget(back_btn)
        
        self.settings_screen.add_widget(layout)

    # Методы аутентификации
    def login(self, instance):
        """Вход пользователя"""
        if not HAS_AUTH:
            self.sm.current = 'main'
            return
            
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.login_status.text = "Заполните все поля"
            return
        
        success, message = self.auth_manager.login(username, password)
        if success:
            self.login_status.text = "Успешный вход!"
            self.sm.current = 'main'
            # Обновляем облачную синхронизацию для текущего пользователя
            if HAS_CLOUD_SYNC:
                self.cloud_sync = CloudSync(self.auth_manager)
            self.update_user_display()
        else:
            self.login_status.text = message

    def logout(self, instance):
        """Выход пользователя"""
        if HAS_AUTH:
            self.auth_manager.logout()
        self.sm.current = 'login'
        self.update_user_display()
        self.show_info("Выход", "Вы вышли из системы")

    def show_registration(self, instance):
        """Показать диалог регистрации"""
        if not HAS_AUTH:
            self.show_info("Регистрация", "Модуль аутентификации недоступен")
            return
            
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        reg_username = TextInput(hint_text='Имя пользователя')
        reg_password = TextInput(hint_text='Пароль', password=True)
        reg_password_confirm = TextInput(hint_text='Подтверждение пароля', password=True)
        
        content.add_widget(reg_username)
        content.add_widget(reg_password)
        content.add_widget(reg_password_confirm)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
        register_btn = Button(text='Зарегистрировать')
        cancel_btn = Button(text='Отмена')
        
        def do_register(btn):
            if reg_password.text != reg_password_confirm.text:
                self.show_error("Ошибка", "Пароли не совпадают")
                return
            
            success, message = self.auth_manager.register_user(
                reg_username.text, 
                reg_password.text
            )
            if success:
                popup.dismiss()
                self.show_info("Успех", message)
            else:
                self.show_error("Ошибка", message)
        
        register_btn.bind(on_release=do_register)
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        
        btn_layout.add_widget(register_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title="Регистрация", content=content, size_hint=(0.8, 0.6))
        popup.open()

    # Методы облачной синхронизации
    def enable_cloud_sync(self, instance):
        """Включение облачной синхронизации"""
        if not HAS_CLOUD_SYNC:
            self.show_error("Ошибка", "Модуль облачной синхронизации недоступен")
            return
            
        server_url = self.server_url_input.text.strip()
        if not server_url:
            self.show_error("Ошибка", "Введите URL сервера")
            return
        
        self.cloud_sync.enable_sync(server_url)
        self.show_info("Успех", "Облачная синхронизация включена")

    def disable_cloud_sync(self, instance):
        """Выключение облачной синхронизации"""
        if not HAS_CLOUD_SYNC:
            self.show_error("Ошибка", "Модуль облачной синхронизации недоступен")
            return
            
        self.cloud_sync.disable_sync()
        self.show_info("Успех", "Облачная синхронизация выключена")

    def sync_data(self, instance):
        """Синхронизация данных с облаком"""
        if not HAS_CLOUD_SYNC:
            self.show_error("Ошибка", "Модуль облачной синхронизации недоступен")
            return
            
        if HAS_AUTH and not self.auth_manager.get_current_user():
            self.show_error("Ошибка", "Войдите в систему для синхронизации")
            return
        
        self.history_data, message = self.cloud_sync.sync_data(self.history_data)
        self.save_history()
        self.update_display()
        self.update_stats()
        self.show_info("Синхронизация", message)

    # Методы отчетов
    def generate_report(self, instance):
        """Генерация отчета"""
        if not HAS_REPORTS:
            self.show_error("Ошибка", "Модуль отчетов недоступен")
            return
            
        report_generator = ReportGenerator(self.history_data)
        self.current_report = report_generator.generate_comprehensive_report()
        
        # Показываем сводку отчета
        summary = self.current_report['data_summary']
        expiry = self.current_report['expiry_analysis']
        
        report_text = f"""
Отчет сгенерирован: {self.current_report['generated_at']}

Статистика данных:
- Всего записей: {summary['total_records']}
- СИЗ: {summary['siz_count']}
- Чеки: {summary['receipt_count']}
- Прочие: {summary['other_count']}

Анализ сроков:
- Всего СИЗ: {expiry['total_siz']}
- Просрочено: {expiry['expired_count']}
- Скоро истекают: {expiry['expiring_soon_count']}
- Действительны: {expiry['valid_count']}
        """
        
        self.show_info("Отчет сгенерирован", report_text.strip())

    def export_report_json(self, instance):
        """Экспорт отчета в JSON"""
        if not HAS_REPORTS:
            self.show_error("Ошибка", "Модуль отчетов недоступен")
            return
            
        if not hasattr(self, 'current_report'):
            self.show_error("Ошибка", "Сначала сгенерируйте отчет")
            return
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_generator = ReportGenerator(self.history_data)
        success, message = report_generator.export_report_to_json(self.current_report, filename)
        
        if success:
            self.show_info("Успех", message)
        else:
            self.show_error("Ошибка", message)

    def export_report_csv(self, instance):
        """Экспорт отчета в CSV"""
        if not HAS_REPORTS:
            self.show_error("Ошибка", "Модуль отчетов недоступен")
            return
            
        if not hasattr(self, 'current_report'):
            self.show_error("Ошибка", "Сначала сгенерируйте отчет")
            return
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        report_generator = ReportGenerator(self.history_data)
        success, message = report_generator.export_report_to_csv(self.current_report, filename)
        
        if success:
            self.show_info("Успех", message)
        else:
            self.show_error("Ошибка", message)

    # Основные методы приложения (остаются без изменений)
    def scan_qr_code(self, instance):
        '''Запуск сканирования QR-кода с камеры'''
        try:
            if self.camera_status == "available":
                # Реальное сканирование с камеры
                scanner = QRScanner()
                qr_data = scanner.scan_qr_code()
                if qr_data:
                    self.process_siz_data(qr_data)
                    self.show_info("Успех", "QR-код успешно отсканирован!")
                else:
                    self.show_error("QR-код не найден", "Попробуйте еще раз")
            else:
                # Демо-режим
                self.use_demo_data()
        except Exception as e:
            error_msg = str(e)
            self.show_error("Ошибка сканирования", error_msg)
            # Автоматически переходим в демо-режим при ошибке
            self.use_demo_data()

    def scan_qr_from_file(self, instance):
        '''Сканирование QR-кода из файла изображения'''
        # В реальном приложении здесь был бы диалог выбора файла
        self.show_info("Функция в разработке", 
                      "В полной версии здесь будет диалог выбора файла.\n"
                      "Сейчас добавляется демо-СИЗ.")
        
        # Демо: создаем тестовые данные для файлового сканирования
        test_data = {
            "name": "Защитные очки (из файла)",
            "type": "Очки защитные",
            "protection_class": "EN166",
            "expiry_date": "2026-06-30", 
            "manufacturer": "Очковый завод",
            "certificate": "РОСС RU.ПБ03.В00003"
        }
        self.process_siz_data(test_data)

    def use_demo_data(self):
        """Использовать демо-данные"""
        test_data = {
            "name": "Респиратор Р-2 (демо)",
            "type": "Фильтрующий полумаска",
            "protection_class": "FFP2",
            "expiry_date": "2025-12-31",
            "manufacturer": "Завод СИЗ",
            "certificate": "РОСС RU.ПБ01.В00001"
        }
        self.process_siz_data(test_data)

    def process_siz_data(self, data):
        '''Обработка данных СИЗ'''
        original_data = data
        print(f"Получены данные: {data}")
        
        # Если данные в виде строки, пробуем разобрать как JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
                print("Данные распознаны как JSON")
            except:
                # Если не JSON, пробуем разобрать как параметры URL (чеки и т.д.)
                data = self.parse_qr_data(data)
        
        # Определяем тип данных и обрабатываем соответственно
        if isinstance(data, dict) and "name" in data:
            # Это структурированные данные СИЗ в JSON формате
            result = self.create_siz_result(data)
        elif isinstance(data, dict) and any(key in data for key in ['t', 's', 'fn']):
            # Это фискальный чек
            result = self.create_receipt_result(data, original_data)
        elif isinstance(data, dict):
            # Это другие структурированные данные
            result = self.create_generic_result(data, original_data)
        else:
            # Неизвестный формат
            result = self.create_unknown_result(original_data)
        
        self.scan_results.append(result)
        self.history_data.append(result)
        self.save_history()
        self.update_display()
        self.update_stats()
        
        # Показываем информацию о типе распознанных данных
        self.show_data_type_info(result)

    def parse_qr_data(self, data_str):
        """Парсинг различных форматов QR-кодов"""
        # Пробуем разобрать как параметры URL (фискальные чеки)
        if '=' in data_str and '&' in data_str:
            try:
                params = {}
                parts = data_str.split('&')
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        params[key] = value
                print(f"Распознаны параметры URL: {params}")
                return params
            except Exception as e:
                print(f"Ошибка парсинга URL параметров: {e}")
        
        # Пробуем разобрать как простой текст с разделителями
        if any(sep in data_str for sep in [';', ',', '|']):
            try:
                # Пробуем разные разделители
                for sep in [';', ',', '|']:
                    if sep in data_str:
                        parts = data_str.split(sep)
                        if len(parts) >= 2:
                            params = {}
                            for i, part in enumerate(parts):
                                params[f'field_{i}'] = part.strip()
                            print(f"Распознан текст с разделителем '{sep}': {params}")
                            return params
            except Exception as e:
                print(f"Ошибка парсинга текста с разделителями: {e}")
        
        # Если ничего не подошло, возвращаем как сырые данные
        return {"raw_data": data_str}

    def create_siz_result(self, data):
        """Создание результата для данных СИЗ"""
        return {
            "name": data.get("name", "Неизвестно"),
            "type": data.get("type", "Не указан"),
            "expiry_date": data.get("expiry_date", "Не указан"),
            "protection_class": data.get("protection_class", "Не указан"),
            "manufacturer": data.get("manufacturer", "Не указан"),
            "certificate": data.get("certificate", "Не указан"),
            "data_type": "СИЗ",
            "timestamp": self.get_current_timestamp()
        }

    def create_receipt_result(self, data, original_data):
        """Создание результата для фискального чека"""
        # Парсим параметры чека
        date_time = data.get('t', 'Неизвестно')
        amount = data.get('s', 'Неизвестно')
        fiscal_number = data.get('fn', 'Неизвестно')
        fiscal_doc = data.get('i', 'Неизвестно')
        fiscal_sign = data.get('fp', 'Неизвестно')
        
        # Форматируем дату
        try:
            if len(date_time) >= 13:
                date_str = f"{date_time[6:8]}.{date_time[4:6]}.{date_time[0:4]} {date_time[9:11]}:{date_time[11:13]}"
            else:
                date_str = date_time
        except:
            date_str = date_time
        
        return {
            "name": "Фискальный чек",
            "type": "Чек покупки",
            "amount": f"{amount} руб.",
            "date_time": date_str,
            "fiscal_number": fiscal_number,
            "fiscal_doc": fiscal_doc,
            "fiscal_sign": fiscal_sign,
            "data_type": "Фискальный чек",
            "timestamp": self.get_current_timestamp(),
            "raw_data": original_data
        }

    def create_generic_result(self, data, original_data):
        """Создание результата для общих структурированных данных"""
        # Создаем читаемое описание из ключевых полей
        name = "Структурированные данные"
        if 'name' in data:
            name = data['name']
        elif 'title' in data:
            name = data['title']
        elif 'product' in data:
            name = data['product']
        
        return {
            "name": name,
            "type": "Структурированные данные",
            "data_type": "Структурированные данные",
            "fields_count": len(data),
            "timestamp": self.get_current_timestamp(),
            "raw_data": original_data,
            **data  # Включаем все оригинальные поля
        }

    def create_unknown_result(self, original_data):
        """Создание результата для неизвестного формата"""
        return {
            "name": "Неизвестный формат данных",
            "type": "Не распознан",
            "data_type": "Неизвестный формат",
            "raw_data": original_data,
            "timestamp": self.get_current_timestamp()
        }

    def show_data_type_info(self, result):
        """Показать информацию о типе распознанных данных"""
        data_type = result.get("data_type", "Неизвестно")
        if data_type == "СИЗ":
            self.show_info("Успех", f"Данные СИЗ распознаны: {result['name']}")
        elif data_type == "Фискальный чек":
            self.show_info("Фискальный чек", 
                          f"Чек на {result.get('amount', 'Неизвестно')}\n"
                          f"Время: {result.get('date_time', 'Неизвестно')}")
        elif data_type == "Структурированные данные":
            self.show_info("Структурированные данные", 
                          f"Распознано {result.get('fields_count', 0)} полей")
        else:
            self.show_info("Неизвестный формат", 
                          "Данные не распознаны в формате СИЗ")

    def update_display(self):
        '''Обновление отображения результатов'''
        self.results_container.clear_widgets()

        for result in self.scan_results[-5:]:  # Показываем последние 5
            data_type = result.get("data_type", "Неизвестно")
            
            if data_type == "СИЗ":
                card = self.create_siz_card(result)
            elif data_type == "Фискальный чек":
                card = self.create_receipt_card(result)
            elif data_type == "Структурированные данные":
                card = self.create_structured_card(result)
            else:
                card = self.create_unknown_card(result)
                
            self.results_container.add_widget(card)

    def create_siz_card(self, result):
        """Создание карточки для данных СИЗ"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=140, spacing=5, padding=10)
        
        # Заголовок с типом данных
        type_label = Label(
            text="[СИЗ] " + result['name'],
            font_size='16sp',
            size_hint_y=0.25,
            text_size=(400, None),
            halign='left',
            color=(0, 0.6, 0, 1)  # Зеленый для СИЗ
        )
        type_label.bind(size=type_label.setter('text_size'))
        
        # Тип СИЗ
        type_label2 = Label(
            text=result['type'],
            font_size='14sp', 
            size_hint_y=0.2,
            text_size=(400, None),
            halign='left'
        )
        type_label2.bind(size=type_label2.setter('text_size'))
        
        # Срок годности
        expiry_label = Label(
            text=f"Срок: {result['expiry_date']} | Класс: {result['protection_class']}",
            font_size='12sp',
            size_hint_y=0.2,
            text_size=(400, None),
            halign='left'
        )
        expiry_label.bind(size=expiry_label.setter('text_size'))
        
        # Производитель и сертификат
        details_label = Label(
            text=f"Производитель: {result['manufacturer']}",
            font_size='11sp',
            size_hint_y=0.2,
            text_size=(400, None),
            halign='left'
        )
        details_label.bind(size=details_label.setter('text_size'))
        
        # Время добавления
        time_label = Label(
            text=f"Добавлен: {result['timestamp']}",
            font_size='10sp',
            size_hint_y=0.15,
            text_size=(400, None), 
            halign='left'
        )
        time_label.bind(size=time_label.setter('text_size'))
        
        card.add_widget(type_label)
        card.add_widget(type_label2)
        card.add_widget(expiry_label)
        card.add_widget(details_label)
        card.add_widget(time_label)
        
        return card

    def create_receipt_card(self, result):
        """Создание карточки для фискального чека"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=5, padding=10)
        
        type_label = Label(
            text="[ЧЕК] " + result['name'],
            font_size='16sp',
            size_hint_y=0.3,
            text_size=(400, None),
            halign='left',
            color=(0.8, 0.4, 0, 1)  # Оранжевый для чеков
        )
        type_label.bind(size=type_label.setter('text_size'))
        
        amount_label = Label(
            text=f"Сумма: {result['amount']}",
            font_size='14sp', 
            size_hint_y=0.25,
            text_size=(400, None),
            halign='left'
        )
        amount_label.bind(size=amount_label.setter('text_size'))
        
        date_label = Label(
            text=f"Время: {result['date_time']}",
            font_size='12sp',
            size_hint_y=0.25,
            text_size=(400, None),
            halign='left'
        )
        date_label.bind(size=date_label.setter('text_size'))
        
        time_label = Label(
            text=f"Добавлен: {result['timestamp']}",
            font_size='10sp',
            size_hint_y=0.2,
            text_size=(400, None), 
            halign='left'
        )
        time_label.bind(size=time_label.setter('text_size'))
        
        card.add_widget(type_label)
        card.add_widget(amount_label)
        card.add_widget(date_label)
        card.add_widget(time_label)
        
        return card

    def create_structured_card(self, result):
        """Создание карточки для структурированных данных"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=5, padding=10)
        
        type_label = Label(
            text="[ДАННЫЕ] " + result['name'],
            font_size='16sp',
            size_hint_y=0.3,
            text_size=(400, None),
            halign='left',
            color=(0, 0.4, 0.8, 1)  # Синий для данных
        )
        type_label.bind(size=type_label.setter('text_size'))
        
        fields_label = Label(
            text=f"Поля: {result.get('fields_count', 0)}",
            font_size='14sp', 
            size_hint_y=0.3,
            text_size=(400, None),
            halign='left'
        )
        fields_label.bind(size=fields_label.setter('text_size'))
        
        time_label = Label(
            text=f"Добавлен: {result['timestamp']}",
            font_size='10sp',
            size_hint_y=0.2,
            text_size=(400, None), 
            halign='left'
        )
        time_label.bind(size=time_label.setter('text_size'))
        
        card.add_widget(type_label)
        card.add_widget(fields_label)
        card.add_widget(time_label)
        
        return card

    def create_unknown_card(self, result):
        """Создание карточки для неизвестных данных"""
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=5, padding=10)
        
        type_label = Label(
            text="[НЕИЗВЕСТНО] " + result['name'],
            font_size='16sp',
            size_hint_y=0.4,
            text_size=(400, None),
            halign='left',
            color=(0.8, 0, 0, 1)  # Красный для неизвестных
        )
        type_label.bind(size=type_label.setter('text_size'))
        
        time_label = Label(
            text=f"Добавлен: {result['timestamp']}",
            font_size='10sp',
            size_hint_y=0.3,
            text_size=(400, None), 
            halign='left'
        )
        time_label.bind(size=time_label.setter('text_size'))
        
        card.add_widget(type_label)
        card.add_widget(time_label)
        
        return card

    def search_history(self, instance):
        """Поиск по истории"""
        search_term = self.search_input.text.lower().strip()
        if not search_term:
            self.update_history_display()
            return
        
        filtered_data = []
        for item in self.history_data:
            if (search_term in item.get('name', '').lower() or 
                search_term in item.get('type', '').lower() or
                search_term in item.get('manufacturer', '').lower()):
                filtered_data.append(item)
        
        self.update_history_display(filtered_data)
    
    def clear_search(self, instance):
        """Очистить поиск"""
        self.search_input.text = ''
        self.update_history_display()

    def show_history(self, instance):
        '''Показать историю'''
        self.sm.current = 'history'
        self.update_history_display()

    def update_history_display(self, data=None):
        '''Обновление отображения истории'''
        if data is None:
            data = self.history_data
            
        self.history_list.clear_widgets()

        for item in reversed(data):
            history_item = Button(
                text=f"{item['name']} - {item['timestamp']}",
                size_hint_y=None,
                height=40,
                text_size=(350, None),
                halign='left'
            )
            history_item.bind(on_release=lambda btn, data=item: self.show_history_item(data))
            self.history_list.add_widget(history_item)

    def show_history_item(self, data):
        '''Показать детали элемента истории'''
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        for key, value in data.items():
            label = Label(
                text=f"{key}: {value}",
                size_hint_y=None,
                height=30,
                text_size=(350, None),
                halign='left'
            )
            label.bind(size=label.setter('text_size'))
            content.add_widget(label)
        
        popup = Popup(
            title="Информация о СИЗ",
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()

    def back_to_main(self, instance):
        '''Вернуться на главный экран'''
        self.sm.current = 'main'

    def clear_results(self, instance):
        '''Очистить результаты'''
        self.scan_results = []
        self.update_display()
        self.update_stats()
        self.show_info("Успех", "Результаты очищены")

    def create_backup(self, instance):
        """Создать резервную копию данных"""
        try:
            backup_file = f"backup_siz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            backup_data = {
                'metadata': {
                    'version': '1.0',
                    'created': datetime.now().isoformat(),
                    'records_count': len(self.history_data)
                },
                'data': self.history_data
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.show_info("Резервная копия", f"Резервная копия создана:\n{backup_file}")
            
        except Exception as e:
            self.show_error("Ошибка резервного копирования", f"Не удалось создать резервную копию: {str(e)}")

    def restore_from_backup(self, instance):
        """Восстановить данные из резервной копии"""
        # В реальном приложении здесь был бы диалог выбора файла
        self.show_info("Восстановление", 
                      "В полной версии здесь будет диалог выбора файла.\n"
                      "Сейчас демонстрируется функция восстановления.")
        
        # Демо: создаем тестовые данные восстановления
        demo_restore_data = [
            {
                "name": "Восстановленный СИЗ",
                "type": "Перчатки защитные",
                "expiry_date": "2026-03-15",
                "protection_class": "EN388",
                "manufacturer": "Завод СИЗ",
                "certificate": "РОСС RU.ПБ05.В00005",
                "data_type": "СИЗ",
                "timestamp": "01.01.2024 10:00"
            }
        ]
        
        self.history_data.extend(demo_restore_data)
        self.save_history()
        self.update_display()
        self.update_stats()
        self.show_info("Восстановлено", "Демо-данные восстановлены из резервной копии")

    def export_data(self, instance):
        """Экспорт данных в CSV файл"""
        try:
            filename = f"siz_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'type', 'protection_class', 'expiry_date', 
                            'manufacturer', 'certificate', 'data_type', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for item in self.history_data:
                    # Экспортируем только основные поля
                    row = {field: item.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            self.show_info("Экспорт завершен", f"Данные сохранены в файл:\n{filename}")
            
        except Exception as e:
            self.show_error("Ошибка экспорта", f"Не удалось экспортировать данные: {str(e)}")

    def show_detailed_stats(self, instance):
        """Показать детальную статистику"""
        stats = self.get_detailed_stats()
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Общая статистика
        general_label = Label(
            text=f"Всего записей: {stats['total']}\n"
                 f"СИЗ: {stats['siz_count']} | Чеки: {stats['receipt_count']}\n"
                 f"Данные: {stats['data_count']} | Неизвестно: {stats['unknown_count']}\n"
                 f"Просрочено: {stats['expired_count']} | Скоро истекает: {stats['soon_expired_count']}",
            size_hint_y=None,
            height=120,
            text_size=(350, None),
            halign='left'
        )
        general_label.bind(size=general_label.setter('text_size'))
        content.add_widget(general_label)
        
        # Статистика по типам СИЗ
        if stats['by_type']:
            types_label = Label(
                text="Типы СИЗ:\n" + "\n".join([f"{k}: {v}" for k, v in list(stats['by_type'].items())[:5]]),
                size_hint_y=None,
                height=120,
                text_size=(350, None),
                halign='left'
            )
            types_label.bind(size=types_label.setter('text_size'))
            content.add_widget(types_label)
        
        # Статистика по месяцам
        if stats['by_month']:
            months_label = Label(
                text="По месяцам:\n" + "\n".join([f"{k}: {v}" for k, v in list(stats['by_month'].items())[:6]]),
                size_hint_y=None,
                height=120,
                text_size=(350, None),
                halign='left'
            )
            months_label.bind(size=months_label.setter('text_size'))
            content.add_widget(months_label)
        
        popup = Popup(
            title="Детальная статистика",
            content=content,
            size_hint=(0.8, 0.8)
        )
        popup.open()

    def get_detailed_stats(self):
        """Получить детальную статистику"""
        stats = {
            'total': len(self.history_data),
            'siz_count': 0,
            'receipt_count': 0,
            'data_count': 0,
            'unknown_count': 0,
            'expired_count': 0,
            'soon_expired_count': 0,
            'by_month': {},
            'by_type': {}
        }
        
        soon_expired, expired = self.check_expirations()
        stats['expired_count'] = len(expired)
        stats['soon_expired_count'] = len(soon_expired)
        
        for item in self.history_data:
            data_type = item.get('data_type', 'Неизвестно')
            
            if data_type == 'СИЗ':
                stats['siz_count'] += 1
                # Статистика по типам СИЗ
                siz_type = item.get('type', 'Не указан')
                stats['by_type'][siz_type] = stats['by_type'].get(siz_type, 0) + 1
            elif data_type == 'Фискальный чек':
                stats['receipt_count'] += 1
            elif data_type == 'Структурированные данные':
                stats['data_count'] += 1
            else:
                stats['unknown_count'] += 1
            
            # Статистика по месяцам
            try:
                month = item['timestamp'][3:5]  # MM из DD.MM.YYYY
                year = item['timestamp'][6:10]  # YYYY
                month_key = f"{month}/{year}"
                stats['by_month'][month_key] = stats['by_month'].get(month_key, 0) + 1
            except:
                pass
        
        return stats

    def show_error(self, title, message):
        '''Показать сообщение об ошибке'''
        content = Label(text=message, text_size=(350, None))
        content.bind(size=content.setter('text_size'))
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        popup.open()

    def show_info(self, title, message):
        '''Показать информационное сообщение'''
        content = Label(text=message, text_size=(350, None))
        content.bind(size=content.setter('text_size'))
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        popup.open()

    def get_current_timestamp(self):
        '''Получить текущую дату и время'''
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    def save_history(self):
        '''Сохранить историю'''
        try:
            history_file = "siz_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def load_history(self):
        '''Загрузить историю'''
        try:
            history_file = "siz_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")
            self.history_data = []

if __name__ == '__main__':
    SIZScannerApp().run()

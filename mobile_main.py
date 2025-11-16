from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.properties import ListProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import json
import os
from datetime import datetime, timedelta

# Адаптивные импорты для мобильных устройств
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

try:
    from qr_scanner import QRScanner
    HAS_QR_SCANNER = True
except ImportError:
    HAS_QR_SCANNER = False

class MobileMainScreen(Screen):
    pass

class MobileHistoryScreen(Screen):
    pass

class MobileSettingsScreen(Screen):
    pass

class SIZMobileApp(App):
    scan_results = ListProperty([])
    history_data = ListProperty([])
    current_user = StringProperty("Гость")

    def build(self):
        self.sm = ScreenManager()
        
        self.main_screen = MobileMainScreen(name='main')
        self.history_screen = MobileHistoryScreen(name='history')
        self.settings_screen = MobileSettingsScreen(name='settings')
        
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.history_screen)
        self.sm.add_widget(self.settings_screen)
        
        self.setup_main_screen()
        self.setup_history_screen()
        self.setup_settings_screen()
        
        self.load_history()
        return self.sm

    def on_start(self):
        """Запрос разрешений при запуске на Android"""
        if IS_ANDROID:
            request_permissions([
                Permission.CAMERA,
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        
        # Показываем приветственное сообщение
        Clock.schedule_once(lambda dt: self.show_welcome_message(), 1)

    def show_welcome_message(self):
        """Показать приветственное сообщение"""
        self.show_info("Добро пожаловать!", 
                      "Сканер СИЗ для мобильных устройств\n\n"
                      "• Сканируйте QR-коды СИЗ\n"
                      "• Просматривайте историю\n"
                      "• Получайте уведомления о сроках")

    def setup_main_screen(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # Верхняя панель
        header = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        user_label = Label(
            text=f"👤 {self.current_user}",
            size_hint_x=0.6,
            text_size=(200, None),
            halign='left',
            font_size='16sp'
        )
        self.user_label = user_label
        
        settings_btn = Button(text='⚙️', size_hint_x=0.2, font_size='20sp')
        settings_btn.bind(on_release=self.show_settings)
        
        history_btn = Button(text='📋', size_hint_x=0.2, font_size='20sp')
        history_btn.bind(on_release=self.show_history)
        
        header.add_widget(user_label)
        header.add_widget(history_btn)
        header.add_widget(settings_btn)
        layout.add_widget(header)
        
        # Основной контент
        content = BoxLayout(orientation='vertical', spacing=20)
        
        # Заголовок
        title = Label(
            text='📱 Сканер СИЗ',
            font_size='24sp',
            size_hint_y=0.15,
            bold=True
        )
        content.add_widget(title)
        
        # Статистика
        self.stats_label = Label(
            text=self.get_stats_text(),
            font_size='14sp',
            size_hint_y=0.1,
            text_size=(300, None),
            halign='center'
        )
        content.add_widget(self.stats_label)
        
        # Основные кнопки действий (большие для сенсорного управления)
        action_layout = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=15)
        
        scan_btn = Button(
            text='📷 СКАНИРОВАТЬ QR-КОД',
            size_hint_y=0.5,
            font_size='18sp',
            background_color=(0.2, 0.6, 1, 1)
        )
        scan_btn.bind(on_release=self.scan_qr_code)
        
        demo_btn = Button(
            text='➕ ДОБАВИТЬ ТЕСТОВЫЙ СИЗ',
            size_hint_y=0.5,
            font_size='16sp',
            background_color=(0.3, 0.8, 0.3, 1)
        )
        demo_btn.bind(on_release=self.add_demo_siz)
        
        action_layout.add_widget(scan_btn)
        action_layout.add_widget(demo_btn)
        content.add_widget(action_layout)
        
        # Последние сканирования
        recent_label = Label(
            text='Последние сканирования:',
            font_size='16sp',
            size_hint_y=0.08,
            text_size=(300, None),
            halign='left'
        )
        content.add_widget(recent_label)
        
        self.results_container = GridLayout(cols=1, size_hint_y=0.5, spacing=10)
        scroll = ScrollView()
        scroll.add_widget(self.results_container)
        content.add_widget(scroll)
        
        layout.add_widget(content)
        self.main_screen.add_widget(layout)

    def setup_history_screen(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Панель управления
        control_panel = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        back_btn = Button(text='⬅️ НАЗАД', size_hint_x=0.3)
        back_btn.bind(on_release=self.back_to_main)
        
        search_input = TextInput(
            hint_text='🔍 Поиск...',
            multiline=False,
            size_hint_x=0.5
        )
        self.search_input = search_input
        
        search_btn = Button(text='НАЙТИ', size_hint_x=0.2)
        search_btn.bind(on_release=self.search_history)
        
        control_panel.add_widget(back_btn)
        control_panel.add_widget(search_input)
        control_panel.add_widget(search_btn)
        layout.add_widget(control_panel)
        
        # Список истории
        self.history_list = GridLayout(cols=1, size_hint_y=0.9, spacing=5)
        scroll = ScrollView()
        scroll.add_widget(self.history_list)
        layout.add_widget(scroll)
        
        self.history_screen.add_widget(layout)

    def setup_settings_screen(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Заголовок
        title = Label(text='⚙️ НАСТРОЙКИ', font_size='20sp', size_hint_y=0.1)
        layout.add_widget(title)
        
        # Настройки
        settings_content = BoxLayout(orientation='vertical', spacing=15)
        
        # Резервное копирование
        backup_btn = Button(
            text='💾 СОЗДАТЬ РЕЗЕРВНУЮ КОПИЮ',
            size_hint_y=0.15,
            font_size='16sp'
        )
        backup_btn.bind(on_release=self.create_backup)
        
        # Экспорт данных
        export_btn = Button(
            text='📤 ЭКСПОРТИРОВАТЬ ДАННЫЕ',
            size_hint_y=0.15,
            font_size='16sp'
        )
        export_btn.bind(on_release=self.export_data)
        
        # Очистка данных
        clear_btn = Button(
            text='🗑️ ОЧИСТИТЬ ИСТОРИЮ',
            size_hint_y=0.15,
            font_size='16sp',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        clear_btn.bind(on_release=self.clear_history)
        
        # Информация о приложении
        info_btn = Button(
            text='ℹ️ О ПРИЛОЖЕНИИ',
            size_hint_y=0.15,
            font_size='16sp'
        )
        info_btn.bind(on_release=self.show_app_info)
        
        settings_content.add_widget(backup_btn)
        settings_content.add_widget(export_btn)
        settings_content.add_widget(clear_btn)
        settings_content.add_widget(info_btn)
        
        layout.add_widget(settings_content)
        
        # Кнопка назад
        back_btn = Button(text='⬅️ НАЗАД', size_hint_y=0.1)
        back_btn.bind(on_release=self.back_to_main)
        layout.add_widget(back_btn)
        
        self.settings_screen.add_widget(layout)

    def scan_qr_code(self, instance):
        """Сканирование QR-кода"""
        if HAS_QR_SCANNER:
            try:
                scanner = QRScanner()
                qr_data = scanner.scan_qr_code()
                if qr_data:
                    self.process_siz_data(qr_data)
                    self.show_success("QR-код успешно отсканирован!")
                else:
                    self.show_error("QR-код не найден")
            except Exception as e:
                self.show_error(f"Ошибка сканирования: {str(e)}")
                self.add_demo_siz(None)
        else:
            self.show_info("Сканер недоступен", "Добавляется тестовый СИЗ")
            self.add_demo_siz(None)

    def add_demo_siz(self, instance):
        """Добавление демо-СИЗ"""
        demo_data = {
            "name": "Респиратор защитный",
            "type": "Фильтрующий полумаска",
            "protection_class": "FFP2",
            "expiry_date": "2025-12-31",
            "manufacturer": "Завод СИЗ",
            "certificate": "РОСС RU.ПБ01.В00001"
        }
        self.process_siz_data(demo_data)

    def process_siz_data(self, data):
        """Обработка данных СИЗ"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                data = {"raw_data": data}

        result = {
            "name": data.get("name", "Неизвестно"),
            "type": data.get("type", "Не указан"),
            "expiry_date": data.get("expiry_date", "Не указан"),
            "protection_class": data.get("protection_class", "Не указан"),
            "manufacturer": data.get("manufacturer", "Не указан"),
            "certificate": data.get("certificate", "Не указан"),
            "data_type": "СИЗ",
            "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        self.scan_results.append(result)
        self.history_data.append(result)
        self.save_history()
        self.update_display()
        self.update_stats()

    def update_display(self):
        """Обновление отображения"""
        self.results_container.clear_widgets()
        
        for result in self.scan_results[-3:]:  # Показываем последние 3
            card = self.create_result_card(result)
            self.results_container.add_widget(card)

    def create_result_card(self, result):
        """Создание карточки результата"""
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=120,
            spacing=5,
            padding=10
        )
        
        # Заголовок
        title = Label(
            text=result['name'],
            font_size='16sp',
            size_hint_y=0.4,
            text_size=(300, None),
            halign='left',
            bold=True
        )
        
        # Детали
        details = Label(
            text=f"{result['type']} | Срок: {result['expiry_date']}",
            font_size='14sp',
            size_hint_y=0.3,
            text_size=(300, None),
            halign='left'
        )
        
        # Время
        time_label = Label(
            text=f"Добавлен: {result['timestamp']}",
            font_size='12sp',
            size_hint_y=0.3,
            text_size=(300, None),
            halign='left'
        )
        
        card.add_widget(title)
        card.add_widget(details)
        card.add_widget(time_label)
        
        return card

    def search_history(self, instance):
        """Поиск по истории"""
        query = self.search_input.text.lower().strip()
        if not query:
            self.update_history_display()
            return
        
        filtered = [item for item in self.history_data 
                   if query in item.get('name', '').lower() or 
                   query in item.get('type', '').lower()]
        self.update_history_display(filtered)

    def update_history_display(self, data=None):
        """Обновление отображения истории"""
        if data is None:
            data = self.history_data
            
        self.history_list.clear_widgets()
        
        for item in reversed(data):
            history_item = Button(
                text=f"{item['name']} - {item['timestamp']}",
                size_hint_y=None,
                height=60,
                text_size=(350, None),
                halign='left',
                font_size='14sp'
            )
            history_item.bind(on_release=lambda btn, data=item: self.show_item_details(data))
            self.history_list.add_widget(history_item)

    def show_item_details(self, item):
        """Показать детали элемента"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        for key, value in item.items():
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
            key_label = Label(text=f"{key}:", size_hint_x=0.4, font_size='14sp', bold=True)
            value_label = Label(text=str(value), size_hint_x=0.6, font_size='14sp')
            row.add_widget(key_label)
            row.add_widget(value_label)
            content.add_widget(row)
        
        popup = Popup(
            title="Детали СИЗ",
            content=content,
            size_hint=(0.9, 0.7)
        )
        popup.open()

    def create_backup(self, instance):
        """Создание резервной копии"""
        try:
            backup_file = "siz_backup.json"
            backup_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "records": len(self.history_data)
                },
                "data": self.history_data
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.show_success(f"Резервная копия создана: {backup_file}")
            
        except Exception as e:
            self.show_error(f"Ошибка создания резервной копии: {str(e)}")

    def export_data(self, instance):
        """Экспорт данных"""
        try:
            export_file = f"siz_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(export_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Название', 'Тип', 'Класс защиты', 'Срок годности', 'Производитель', 'Сертификат', 'Время добавления'])
                
                for item in self.history_data:
                    if item.get('data_type') == 'СИЗ':
                        writer.writerow([
                            item.get('name', ''),
                            item.get('type', ''),
                            item.get('protection_class', ''),
                            item.get('expiry_date', ''),
                            item.get('manufacturer', ''),
                            item.get('certificate', ''),
                            item.get('timestamp', '')
                        ])
            
            self.show_success(f"Данные экспортированы: {export_file}")
            
        except Exception as e:
            self.show_error(f"Ошибка экспорта: {str(e)}")

    def clear_history(self, instance):
        """Очистка истории"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        warning_label = Label(
            text="⚠️ ВНИМАНИЕ!\n\nВы уверены, что хотите очистить всю историю?\nЭто действие нельзя отменить.",
            text_size=(350, None),
            halign='center',
            font_size='16sp'
        )
        content.add_widget(warning_label)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
        confirm_btn = Button(text='✅ ДА, ОЧИСТИТЬ', background_color=(0.8, 0.2, 0.2, 1))
        cancel_btn = Button(text='❌ ОТМЕНА')
        
        def do_clear(btn):
            self.history_data.clear()
            self.scan_results.clear()
            self.save_history()
            self.update_display()
            self.update_stats()
            popup.dismiss()
            self.show_success("История очищена")
        
        confirm_btn.bind(on_release=do_clear)
        cancel_btn.bind(on_release=lambda btn: popup.dismiss())
        
        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title="Очистка истории", content=content, size_hint=(0.8, 0.5))
        popup.open()

    def show_app_info(self, instance):
        """Показать информацию о приложении"""
        info_text = """
📱 Сканер СИЗ - Мобильная версия

Версия: 1.0.0
Разработчик: Ваша компания

Функции:
• Сканирование QR-кодов СИЗ
• Управление историей сканирований
• Резервное копирование данных
• Экспорт в CSV

Для поддержки: support@example.com
        """
        
        self.show_info("О приложении", info_text.strip())

    def get_stats_text(self):
        """Получить текст статистики"""
        total = len(self.history_data)
        siz_count = len([x for x in self.history_data if x.get('data_type') == 'СИЗ'])
        
        expired_count = 0
        for item in self.history_data:
            if item.get('data_type') == 'СИЗ' and item.get('expiry_date') != 'Не указан':
                try:
                    expiry = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                    if expiry < datetime.now():
                        expired_count += 1
                except:
                    pass
        
        stats_text = f"📊 Всего: {total} | СИЗ: {siz_count}"
        if expired_count > 0:
            stats_text += f" | ⚠️ Просрочено: {expired_count}"
            
        return stats_text

    def update_stats(self):
        """Обновление статистики"""
        self.stats_label.text = self.get_stats_text()

    def show_settings(self, instance):
        """Показать настройки"""
        self.sm.current = 'settings'

    def show_history(self, instance):
        """Показать историю"""
        self.sm.current = 'history'
        self.update_history_display()

    def back_to_main(self, instance):
        """Вернуться на главный экран"""
        self.sm.current = 'main'

    def show_success(self, message):
        """Показать сообщение об успехе"""
        self.show_popup("✅ Успех", message, (0.2, 0.8, 0.2, 1))

    def show_error(self, message):
        """Показать сообщение об ошибке"""
        self.show_popup("❌ Ошибка", message, (0.8, 0.2, 0.2, 1))

    def show_info(self, title, message):
        """Показать информационное сообщение"""
        self.show_popup(title, message, (0.2, 0.6, 0.8, 1))

    def show_popup(self, title, message, color=(0.2, 0.6, 0.8, 1)):
        """Показать всплывающее окно"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        message_label = Label(
            text=message,
            text_size=(350, None),
            halign='center'
        )
        content.add_widget(message_label)
        
        ok_btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(ok_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()

    def save_history(self):
        """Сохранение истории"""
        try:
            history_file = "siz_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_history(self):
        """Загрузка истории"""
        try:
            history_file = "siz_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.history_data = []

if __name__ == '__main__':
    SIZMobileApp().run()

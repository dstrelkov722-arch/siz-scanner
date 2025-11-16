import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class SimpleApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(
            text='📱 Сканер СИЗ',
            font_size='24sp'
        ))
        layout.add_widget(Button(
            text='Тестовая кнопка',
            size_hint_y=0.3
        ))
        return layout

if __name__ == '__main__':
    SimpleApp().run()

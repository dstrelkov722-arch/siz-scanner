@echo off
echo Сборка приложения Сканер СИЗ для Windows...

echo Установка зависимостей...
pip install pyinstaller
pip install kivy
pip install opencv-python
pip install pyzbar
pip install win10toast

echo Создание исполняемого файла...
pyinstaller --onefile --windowed --name "Сканер_СИЗ" --icon=icon.ico simple_main.py

echo Копирование дополнительных файлов...
if exist dist\Сканер_СИЗ.exe (
    echo Исполняемый файл создан: dist\Сканер_СИЗ.exe
    echo Дополнительные файлы должны находиться в той же папке:
    echo - qr_scanner.py
    echo - notifications.py (опционально)
) else (
    echo Ошибка при создании исполняемого файла!
)

pause
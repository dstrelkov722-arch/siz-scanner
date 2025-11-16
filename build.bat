@echo off
echo Создание исполняемого файла для Windows...

pip install pyinstaller

pyinstaller --onefile --windowed --name "Сканер_СИЗ" --icon=icon.ico simple_main.py

echo Готово! Исполняемый файл находится в папке dist/
pause
#!/bin/bash
echo "Сборка APK для Android..."

echo "Установка Buildozer..."
pip install buildozer

echo "Инициализация Buildozer..."
buildozer init

echo "Сборка APK..."
buildozer android debug

echo "Готово! APK файл находится в папке bin/"
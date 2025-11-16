#!/bin/bash
echo "🚀 Настройка окружения и сборка APK..."

# Проверяем виртуальное окружение
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
fi

echo "📦 Установка/проверка зависимостей..."
pip install --upgrade pip
pip install buildozer setuptools cython jinja2 appdirs colorama toml packaging sh

echo "🔍 Проверка установки buildozer..."
buildozer --version

echo "🧹 Очистка предыдущих сборок..."
buildozer android clean

echo "🔨 Запуск сборки APK..."
buildozer -v android debug

if [ $? -eq 0 ] && [ -f bin/*.apk ]; then
    echo "✅ APK успешно собран!"
    echo "📦 Файлы:"
    ls -la bin/
    # Копируем на рабочий стол Windows
    cp bin/*.apk "/mnt/c/Users/sssst/Desktop/" 2>/dev/null && echo "📁 Скопирован на рабочий стол Windows"
else
    echo "❌ Ошибка сборки APK"
    echo "🔧 Попробуйте запустить вручную: buildozer -v android debug"
fi

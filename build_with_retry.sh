#!/bin/bash
echo "🚀 Запуск сборки APK с автоматическими повторами..."

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Попытка сборки #$((RETRY_COUNT+1))"
    buildozer -v android debug
    
    if [ $? -eq 0 ]; then
        echo "✅ Сборка успешно завершена!"
        if [ -f bin/*.apk ]; then
            echo "📦 APK файл создан:"
            ls -la bin/*.apk
        fi
        exit 0
    else
        echo "❌ Сборка завершилась с ошибкой. Повтор через 10 секунд..."
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 10
        
        # Очищаем кэш перед повторной попыткой
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "🧹 Очистка кэша перед повторной попыткой..."
            buildozer android clean
        fi
    fi
done

echo "❌ Все попытки сборки завершились неудачно"
exit 1

import sys
import os

# Находим файл android.py в buildozer
buildozer_path = os.path.dirname(os.path.abspath(__file__))
android_py = os.path.join(buildozer_path, 'venv/lib/python3.12/site-packages/buildozer/targets/android.py')

# Читаем файл
with open(android_py, 'r') as f:
    content = f.read()

# Заменяем импорт distutils на setuptools
if 'from distutils.version import LooseVersion' in content:
    content = content.replace(
        'from distutils.version import LooseVersion',
        'from setuptools import version as LooseVersion'
    )
    print("✅ Заменили distutils на setuptools")
    
    # Записываем обратно
    with open(android_py, 'w') as f:
        f.write(content)
else:
    print("❌ Импорт distutils не найден")

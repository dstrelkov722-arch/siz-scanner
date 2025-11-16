[app]
title = Сканер СИЗ
package.name = sizscanner
package.domain = org.sizscanner

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:source.exclude_patterns]
bin, .buildozer, .git, __pycache__, *.pyc

android.permissions = INTERNET

# Оптимизации для ускорения сборки
[android]
api = 31
minapi = 21
ndk_api = 21
# Собираем только для одной архитектуры для ускорения
arch = arm64-v8a
# Отключаем некоторые опции для ускорения
android.skip_update = True
android.accept_sdk_license = True

# Дополнительные опции p4a
p4a.branch = master
android.private_storage = True

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
android.recipe_blacklist = sqlite3

[android]
api = 31
minapi = 21
ndk_api = 21
arch = arm64-v8a

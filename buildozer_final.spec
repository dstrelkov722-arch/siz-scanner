[app]
title = Scanner App  
package.name = scanner
package.domain = org.test

source.dir = .
source.include_exts = py

version = 0.1
requirements = python3,kivy

orientation = portrait

[buildozer]
log_level = 1

[app:source.exclude_patterns]
bin, .buildozer, .git, __pycache__, *.pyc

android.permissions = INTERNET

android.recipe_blacklist = sqlite3,openssl,libffi

[android]
api = 31
minapi = 21
ndk_api = 21
arch = arm64-v8a
android.skip_update = True

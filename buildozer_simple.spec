[app]
title = Сканер СИЗ
package.name = sizscanner
package.domain = org.sizscanner

source.dir = .
source.include_exts = py

version = 1.0.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:source.exclude_patterns]
bin, .buildozer, .git, __pycache__, *.pyc

android.permissions = INTERNET

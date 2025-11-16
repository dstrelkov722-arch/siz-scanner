[app]
title = Сканер СИЗ
package.name = sizscanner
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0
requirements = python3,kivy

orientation = portrait

[buildozer]
log_level = 1

[app:source.exclude_patterns]
bin, .buildozer, .git, __pycache__, *.pyc

android.permissions = INTERNET

#!/bin/bash
echo "SQLite amalgamation dummy file" > sqlite3.c
echo "SQLite header dummy file" > sqlite3.h  
echo "SQLite extension dummy file" > sqlite3ext.h
zip sqlite-amalgamation-3350500.zip sqlite3.c sqlite3.h sqlite3ext.h
rm sqlite3.c sqlite3.h sqlite3ext.h
echo "✅ Фиктивный SQLite архив создан"

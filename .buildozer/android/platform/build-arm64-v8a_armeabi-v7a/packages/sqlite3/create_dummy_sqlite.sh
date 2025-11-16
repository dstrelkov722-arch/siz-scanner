#!/bin/bash
echo "Создание фиктивного SQLite архива..."
mkdir -p temp_sqlite
cd temp_sqlite
echo "/* SQLite Amalgamation 3.35.5 */" > sqlite3.c
echo "/* SQLite Header */" > sqlite3.h
echo "/* SQLite Extension Header */" > sqlite3ext.h
zip ../sqlite-amalgamation-3350500.zip *
cd ..
rm -rf temp_sqlite
echo "Фиктивный sqlite-amalgamation-3350500.zip создан"
ls -lh sqlite-amalgamation-3350500.zip

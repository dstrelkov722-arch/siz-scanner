/*
** 2001 September 15
**
** The author disclaims copyright to this source code.  In place of
** a legal notice, here is a blessing:
**
**    May you do good and not evil.
**    May you find forgiveness for yourself and forgive others.
**    May you share freely, never taking more than you give.
**
*************************************************************************
** Header file for SQLite library.
*/
#ifndef SQLITE3_H
#define SQLITE3_H

#define SQLITE_VERSION        "3.35.5"
#define SQLITE_VERSION_NUMBER 3035005
#define SQLITE_SOURCE_ID      "2021-04-19 18:32:05"

#define SQLITE_OK           0

typedef struct sqlite3 sqlite3;
typedef struct sqlite3_stmt sqlite3_stmt;

int sqlite3_dummy_build_function(void);

#endif

---
title: SQLite Metadata via SQL Injection
date: 2023-11-09
programming/languages:
- SQL
programming/topics:
- CTF
- Security
- Exfiltration
- SQL Injection
- SQLite
series:
- 2023 CTF Hints
---
As mentioned in my [[Mongo DB Data Exfiltration via Search Conditions|previous post]](), I recently participated in a security CTF exercise and wanted to write out a few interesting techniques. 

This is the second: extracting SQL metadata from a SQLite database. 

<!--more-->

Let's assume that you already have an endpoint vulnerable to a SQL injection.

![](https://imgs.xkcd.com/comics/exploits_of_a_mom.png)

Now, you're poking around and you want to see what you can see (as one does), but you're not actually sure what content might be there. You can certainly try to guess table names and column names, but ... you don't have to!

If you're dealing with SQLite, there's a handy little table called `sqlite_master`:

```sql
sqlite> select name, sql from sqlite_master;
users|CREATE TABLE `users` (
    `user_id` INTEGER PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) UNIQUE NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `admin` BOOLEAN
)
sqlite_autoindex_users_1|
files|CREATE TABLE `files` (
    `file_key` VARCHAR(255) PRIMARY KEY,
    `user_id` UNSIGNED INTEGER NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `private` BOOLEAN NOT NULL
)
sqlite_autoindex_files_1|
```

What's this? The names of all the tables and the SQL statements used to create them? (nicely parsed and formatted no less?). I mean, you could probably guess that there is a `users` table. And (as in this case) if you have a file sharing service, you might find a `files` table, but to get all the field names? Nice. 

And that's really it. If you have MySQL instead, you can use `information_schema.tables` and `information_schema.colums`. In postgres, `pg_catalog.pg_tables` (and friends). In MSSQL, `sys.tables|columns`. It turns out that when you have a database, the best place to store metadata is... in the database! 

Now, will you always have access to these tables? Absolutely not. Is it worth trying (for a CTF, no black hat stuff now), absolutely! 
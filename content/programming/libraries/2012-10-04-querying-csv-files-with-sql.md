---
title: Querying CSV files with SQL
date: 2012-10-04 14:00:37
programming/languages:
- Python
programming/topics:
- CSV
- Databases
---
Some time ago, I had a bunch of CSV files that I needed to extract some data from. They were all organized into tables with related columns between them all that made me think of a relational database--and it's really easy to query relational databases, just use SQL. So what did I do? I wrote a script that will let me query CSV files as if they were a relational database.

<!--more-->

Using an in-memory SQLite database, the process is actually really straight forward. Read any files specified on the command line, assuming that column headers are specified as the first line. For each file, create a table with the column headers as the attributes. Then allow the user to query those tables as they would normally using SQL commands.

If you want to work along, you can get the full source code here: [csvdb](https://github.com/jpverkamp/small-projects/blob/master/scripts/csvdb.py)

Here's an example, using these two CSV files:


|                                                                       students.csv                                                                       |                                                                        classes.csv                                                                         |
|----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ```csv name,id,gender,dept Alex,101,M,CS Alex,102,F,CS Bob,103,M,Math Claire,104,F,CS David,105,M,CS Elton,106,M,Math Fred,107,M,Math Ginny,108,F,CS ``` | ```csv studentid,courseid,term 101,CS101,Fall 2012 101,MA101,Fall 2012 102,CS101,Fall 2012 103,CS101,Fall 2012 105,MA101,Fall 2012 105,CS101,Fall 2012 ``` |


With these, you can run the command simply (assuming it's in your path):
`csvdb students.csv classes.csv`

From there, you'll get this prompt:


```
8 rows loaded from students.csv as students
6 rows loaded from classes.csv as classes
Enter a SQL query or one of the special commands below.

Current tables:
students
classes

Special commands:
quit - exit
help - display this screen
cols {table} - print out the columns for the given table

~
```

You can ask for the names of any tables or the columns on any table pretty easily:

```
~ tables
students, classes

~ cols students
name, id, gender, dept

~ cols classes
studentid, courseid, term
```

Or you can issue queries:

```sql
~ select distinct dept from students
  dept
    CS
  Math

~ select dept, count(*) from students group by dept
  dept   count(*)
    CS          5
  Math          3

~ select S.name, C.courseid
  from students as S, classes as C
  where S.id = C.studentid
   name   courseid
   Alex      CS101
   Alex      MA101
   Alex      CS101
    Bob      CS101
  David      CS101
  David      MA101
```

And that's really all there is to it.

You can get the full source code here: [csvdb](https://github.com/jpverkamp/small-projects/blob/master/scripts/csvdb.py)

If you find it useful (or manage to find something that I forgot in the code), let me know in the comment section below.

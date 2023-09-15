---
title: CSV to JSON
date: 2015-12-11 00:05:00
programming/languages:
- Python
programming/topics:
- CSV
- JSON
---
Today at work, I had to process a bunch of CSV data. Realizing that I don't have any particularly nice tools to work with streaming CSV data (although I did write about [querying CSV files with SQL]({{< ref "2012-10-04-querying-csv-files-with-sql.md" >}})), I decided to write one:

```bash
$ cat users.csv

"user_id","name","email","password"
"1","Luke Skywalker","luke@rebel-alliance.io","$2b$12$XQ1zDvl5PLS6g.K64H27xewPQMnkELa3LvzFSyay8p9kz0XXHVOFq"
"2","Han Solo","han@rebel-alliance.io","$2b$12$eKJGP.tt9u77PeXgMMFmlOyFWSuRZBUZLvmzuLlrum3vWPoRYgr92"

$ cat users.csv | csv2json | jq '.'

{
  "password": "$2b$12$XQ1zDvl5PLS6g.K64H27xewPQMnkELa3LvzFSyay8p9kz0XXHVOFq",
  "name": "Luke Skywalker",
  "user_id": "1",
  "email": "luke@rebel-alliance.io"
}
{
  "password": "$2b$12$eKJGP.tt9u77PeXgMMFmlOyFWSuRZBUZLvmzuLlrum3vWPoRYgr92",
  "name": "Han Solo",
  "user_id": "2",
  "email": "han@rebel-alliance.io"
}
```

<!--more-->

Luckily, Python has nice CSV and JSON libraries built in:

```python
# If --parse is set, try to parse each entry as json
def parse(thing):
    try:
        return json.loads(thing)
    except:
        return thing

# Assume that headers are the first row
reader = csv.reader(sys.stdin)
headers = None
for row in reader:
    if not headers:
        headers = row
        continue

    if '--parse' in sys.argv:
        row = [parse(thing) for thing in row]

    # Recombine the headers with each row (no one said this was saving space)
    row = dict(zip(headers, row))
    print(json.dumps(row, default = str))
```

Basically, assume that the first row of the CSV data is headers (converting to a JSON dict doesn't make much sense if it isn't) and then combine that with each additional row to write out a dictionary. In addition, I put a bit of code in there to assume that you might be storing JSON in your CSV fields. If so, you can `--parse` the data automagically:

```bash
$ cat users-with-preferences.csv | csv2json --parse | jq '.'

{
  "preferences": {
    "force-user": true
  },
  "name": "Luke Skywalker",
  "user_id": 1,
  "password": "$2b$12$XQ1zDvl5PLS6g.K64H27xewPQMnkELa3LvzFSyay8p9kz0XXHVOFq",
  "email": "luke@rebel-alliance.io"
}
{
  "preferences": {
    "ship": "Millennium Falcon"
  },
  "name": "Han Solo",
  "user_id": 2,
  "password": "$2b$12$eKJGP.tt9u77PeXgMMFmlOyFWSuRZBUZLvmzuLlrum3vWPoRYgr92",
  "email": "han@rebel-alliance.io"
}
```

Note that the `user_id`s are actually numbers, the `preferences` field has been unpacked, and Luke's `force-user` status is a boolean. It's neat how you get all of that more or less for free.

Also, have I mentioned how nice <a href="https://stedolan.github.io/jq/">jq</a> is for working with JSON?

And that's it. The full source is part of my dotfiles now: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/csv2json">github:jpverkamp/dotfiles</a> (although all that's missing above is the [[wiki:shebang]]() and the imports). Enjoy!

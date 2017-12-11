---
title: Automagically storing Python objects in Redis
date: 2015-07-16
programming/languages:
- Python
programming/topics:
- Databases
- Redis
---
When you're starting out on a simple web application, eventually[^1] you will reach the point where you need to store some form of persistant data. Basically, you have three options[^2]:


* Store the information in flat files on the file system
* Store the information in a database ([MySQL](https://www.mysql.com/), [SQLite](https://www.sqlite.org/) etc)
* Store the information in a key/value store ([mongoDB](https://www.mongodb.org/), [reddis](http://redis.io/))


There are all manner of pros and cons to each, in particular how easy they are to get started in, how well they fit the data you are using, and how well they will scale horizontally (adding more machines rather than bigger ones).

<!--more-->

For the project that I was working on (I'll post about it eventually), I didn't have terribly many different kinds of data to store, so it would be easy enough to start with anything. I started with a simple file system backing, with one json file per object that I was storing. That worked well enough, but I didn't particularly care for having to write all of the code myself to join / find child objects. I wanted something a little more powerful.

Next, I considered using a database with an {{< wikipedia page="ORM" text="Object-relational mapping" >}} layer. That would let me define everything as Python objects and let the library handle all of the mappings to the actual database. That way, I could write a bare minimum of code for my actual models. Unfortunately, the data wasn't particularly well structured for a relational database, being more hierarchical in struture. It's entirely possible to represent hierarchical data in a relational database, it's just not what they are best suited for.

Finally, I came to Redis. I've used Redis in a few projects at work and come to really like it. It works great as a simple key/value store and even better when you start taking advatage of some of their other data structures. In particular, Redis hashes and lists map nicely to Python dicts and lists. So that's what I ended up doing: Writing a pair of base classes (`RedisDict` and `RedisList`) which to the programmer act just like a Python dict or list, but actually store all of their data transparently in Redis.

Let's get to it.

First, there is a bit of shared code that both `RedisDict` and `RedisList` share, which we can factor out into a base class for the two of them: `RedisObject`.

```python
import base64
import json
import redis
import os

class RedisObject(object):
    '''
    A base object backed by redis.
    Genrally, use RedisDict or RedisList rather than this directly.
    '''

    def __init__(self, id = None):
        '''Create or load a RedisObject.'''

        self.redis = redis.StrictRedis(host = 'redis', decode_responses = True)

        if id:
            self.id = id
        else:
            self.id = base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8')

        if ':' not in self.id:
            self.id = self.__class__.__name__ + ':' + self.id


    def __bool__(self):
        '''Test if an object currently exists'''

        return self.redis.exists(self.id)

    def __eq__(self, other):
        '''Tests if two redis objects are equal (they have the same key)'''

        return self.id == other.id

    def __str__(self):
        '''Return this object as a string for testing purposes.'''

        return self.id

    def delete(self):
        '''Delete this object from redis'''

        self.redis.delete(self.id)

    @staticmethod
    def decode_value(type, value):
        '''Decode a value if it is non-None, otherwise, decode with no arguments.'''

        if value == None:
            return type()
        else:
            return type(value)

    @staticmethod
    def encode_value(value):
        '''Encode a value using json.dumps, with default = str'''

        return str(value)
```

Most of that should be pretty straight forward. The basic idea is that any `RedisObject`, be it a `RedisDict` or a `RedisList` has an ID. This will be used as the key that Redis stores the object under. In particular, I've used a neat (in my opinion) trick to generate random alphanumeric identifiers:

```python
>>> base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8')
u'UQTfwq8XLZr6'
```

Neat. Alternatively, if you want to use a specific value for an ID (such as a user's email address), you can just specify that instead. Next, the `__bool__` method will make a `RedisObject` 'truthy'. You can use Python's `if` to tell if an object acutally exists or not. Finally, `delete`. I wanted to use `__del__` originally, but that actually gets called when an object is garbage collected, which doesn't quite work for this usage[^3]

Finally, static helper functions `decode_value` and `encode_value`. These will be used in a bit, since Redis only stores strings. Thus a `RedisObject` stores the type of each value and needs to know how to read/write that in a systematic way. For that, I'm using Python's `json` encoding, falling back to `str` (and thus the `__str__` magic function on objects). This will deal nicely with most default Python objects and can be easily extended for all manner of more interesting ones if you'd like (I've done it for `RedisObject`s).

One oddity that you've probably noticed is that I've hard coded the Reids IP to connect to. I'm using <a href="https://github.com/docker/compose">docker-compose</a> to run my project, which sets up hostnames automagically within the various containers.

Next, `RedisDict`:

```python
import json
import redis

from lib.RedisObject import RedisObject

class RedisDict(RedisObject):
    '''An equivalent to dict where all keys/values are stored in Redis.'''

    def __init__(self, id = None, fields = {}, defaults = None):
        '''
        Create a new RedisObject
        id: If specified, use this as the redis ID, otherwise generate a random ID.
        fields: A map of field name to construtor used to read values from redis.
            Objects will be written with json.dumps with default = str, so override __str__ for custom objects.
            This should generally be set by the subobject's constructor.
        defaults: A map of field name to values to store when constructing the object.
        '''

        RedisObject.__init__(self, id)

        self.fields = fields

        if defaults:
            for key, val in defaults.items():
                self[key] = val

    def __getitem__(self, key):
        '''
        Load a field from this redis object.
        Keys that were not specified in self.fields will raise an exception.
        Keys that have not been set (either in defaults or __setitem__) will return the default for their type (if set)
        '''

        if key == 'id':
            return self.id

        if not key in self.fields:
            raise KeyError('{} not found in {}'.format(key, self))

        return RedisObject.decode_value(self.fields[key], self.redis.hget(self.id, key))

    def __setitem__(self, key, val):
        '''
        Store a value in this redis object.
        Keys that were not specified in self.fields will raise an exception.
        Keys will be stored with json.dumps with a default of str, so override __str__ for custom objects.
        '''

        if not key in self.fields:
            raise KeyError('{} not found in {}'.format(key, self))

        self.redis.hset(self.id, key, RedisObject.encode_value(val))

    def __iter__(self):
        '''Return (key, val) pairs for all values stored in this RedisDict.'''

        yield ('id', self.id.rsplit(':', 1)[-1])

        for key in self.fields:
            yield (key, self[key])
```

Basically, there are three interesting parts to this code: `__init__` stores the fields that this object has (and should be set by the constructors in subclasses) and can also be used as as a constructor for new objects. `__get/setitem__` will load/store items via Redis. Given the `encode/decode_value` functions in `RedisObject`, this is actually really straight forward.

So how would you use something like this?

Here's is most of the `User` class from the project I am working on:

```python
import bcrypt

import lib
import models
import utils

class User(lib.RedisDict):
    '''A user. Duh.'''

    def __init__(self, id = None, email = None, **defaults):

        # Use email as id, if specified
        if email:
            id = email
            defaults['email'] = email

        lib.RedisDict.__init__(
            self,
            id = email,
            fields = {
                'name': str,
                'email': str,
                'password': str,
                'friends': lib.RedisList.as_child(self, 'friends', models.User),
            },
            defaults = defaults
        )

    def __setitem__(self, key, val):
        '''Override the behavior if user is trying to change the password'''

        if key == 'password':
            val = bcrypt.hashpw(
                val.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

        lib.RedisDict.__setitem__(self, key, val)

    def verifyPassword(self, testPassword):
        '''Verify if a given password is correct'''

        hashedTestPassword = bcrypt.hashpw(
            testPassword.encode('utf-8'),
            self['password'].encode('utf-8')
        ).decode('utf-8')

        return hashedTestPassword == self['password']
```

A `User` will have four fields: a `name`, an `email`, a `password`, and a list of `friends` (we'll get to how that works in a bit). Then, I've added some custom code to automatically store passwords using {{< wikipedia "bcrypt" >}}[^4]. You can use it just like you would a `dict`:

```python
>>> han = User(
...     name = 'Luke Skywalker',
...     email = 'luke@rebel-alliance.io',
...     password = 'TheForce',
... )
...

>>> print(luke['name'])
Luke Skywalker

>>> luke.verifyPassword('password')
False

>>> luke.verifyPassword('TheForce')
True

>>> han = User(
...     name = 'Han Solo',
...     email = 'han@rebel-alliance.io',
...     password = 'LetTheWookieWin',
... )
...

>>> luke['friends'].append(han)

>>> han['friends'].append(luke)

>>> print(luke['friends'][0]['name'])
'Han Solo'
```

Then we can go into the `redis-cli` to verify that everything saved correctly:

```bash
127.0.0.1:6379> keys *
1) "User:han@rebel-alliance.io:friends"
2) "User:han@rebel-alliance.io"
3) "User:luke@rebel-alliance.io:friends"
4) "User:luke@rebel-alliance.io"

127.0.0.1:6379> hgetall User:luke@rebel-alliance.io
1) "name"
2) "Luke Skywalker"
3) "email"
4) "luke@rebel-alliance.io"
5) "password"
6) "$2b$12$XQ1zDvl5PLS6g.K64H27xewPQMnkELa3LvzFSyay8p9kz0XXHVOFq"

127.0.0.1:6379> lrange User:luke@rebel-alliance.io:friends 0 -1
1) "User:han@rebel-alliance.io"
```

There are two entires for each, since technically the `friends` list is a `RedisList`. Originally, I was storing these as JSON encoded lists, but as they got larger, this started to get a little unweildy.

Another plus is that since all of the objects are backed by Redis, you get automatic persistance. Stop Python completely, start it back up, and you can just load the same objects again (remember, for these objects, I'm using the `email` as the ID):

```python
>>> luke = User('luke@rebel-alliance.io')

>>> print(luke['friends'][0]['name'])
'Han Solo'
```

Very cool.

So, speaking of `RedisList`, how does that work? Mostly the same as `RedisDict` (although I had a few more functions to implement):

```python
import json
import redis

from lib.RedisObject import RedisObject

class RedisList(RedisObject):
    '''An equivalent to list where all items are stored in Redis.'''

    def __init__(self, id = None, item_type = str, items = None):
        '''
        Create a new RedisList
        id: If specified, use this as the redis ID, otherwise generate a random ID.
        item_type: The constructor to use when reading items from redis.
        values: Default values to store during construction.
        '''

        RedisObject.__init__(self, id)

        self.item_type = item_type

        if items:
            for item in items:
                self.append(item)

    @classmethod
    def as_child(cls, parent, tag, item_type):
        '''Alternative callable constructor that instead defines this as a child object'''

        def helper(_ = None):
            return cls(parent.id + ':' + tag, item_type)

        return helper

    def __getitem__(self, index):
        '''
        Load an item by index where index is either an int or a slice
        Warning: this is O(n))
        '''

        if isinstance(index, slice):
            if slice.step != 1:
                raise NotImplemented('Cannot specify a step to a RedisObject slice')

            return [
                RedisObject.decode_value(self.item_type, el)
                for el in self.redis.lrange(self.id, slice.start, slice.end)
            ]
        else:
            return RedisObject.decode_value(self.item_type, self.redis.lindex(self.id, index))

    def __setitem__(self, index, val):
        '''Update an item by index
        Warning: this is O(n)
        '''

        self.redis.lset(self.id, index, RedisObject.encode_value(val))

    def __len__(self):
        '''Return the size of the list.'''

        return self.redis.llen(self.id)

    def __delitem__(self, index):
        '''Delete an item from a RedisList by index. (warning: this is O(n))'''

        self.redis.lset(self.id, index, '__DELETED__')
        self.redis.lrem(self.id, 1, '__DELETED__')

    def __iter__(self):
        '''Iterate over all items in this list.'''

        for el in self.redis.lrange(self.id, 0, -1):
            yield RedisObject.decode_value(self.item_type, el)

    def lpop(self):
        '''Remove and return a value from the left (low) end of the list.'''

        return RedisObject.decode_value(self.item_type, self.redis.lpop(self.id))

    def rpop(self):
        '''Remove a value from the right (high) end of the list.'''

        return RedisObject.decode_value(self.item_type, self.redis.rpop(self.id))

    def lpush(self, val):
        '''Add an item to the left (low) end of the list.'''

        self.redis.lpush(self.id, RedisObject.encode_value(val))

    def rpush(self, val):
        '''Add an item to the right (high) end of the list.'''

        self.redis.rpush(self.id, RedisObject.encode_value(val))

    def append(self, val):
        self.rpush(val)
```

Basically, I'm mapping a lot of the default Python `list` functionality to Redis lists and vice versa[^5]. It's a little odd and some things aren't as efficient as I'd like (you only get `O(1)` access to the beginning and end of the list), but so it goes. It works great, as you saw in the `friends` example above.

The one interesting function is `as_child`. Since either a `RedisDict` or a `RedisList` expect a 'constructor-like' function as the data type, I need something that will correctly store a `RedisList` inside of a `RedisDict` while generating a human readable ID (with `:friends` appended in the example above). I love {{< wikipedia "higher order functions" >}}.

And... that's it. Eventually, I think I'll look into publishing this as a library to `pip` or the like. But since I've never done that before and this post is already a little on the long sice, we'll leave that for another day. All of the code is included in the post, so you can copy and paste it into your project if you'd like to try it out before I publish it. Once I have, I'll edit this post.

[^1]: Pretty quickly actually
[^2]: Yes, there are a few other choices; these are the most common in practice
[^3]: Although I did have a similar model with lazily loaded objects from disk that would only save when they were `del`eted. That was neat.
[^4]: A combination hash+salt; never store plain text or unsalted passwords
[^5]: I can never remember exactly how that's spelled...
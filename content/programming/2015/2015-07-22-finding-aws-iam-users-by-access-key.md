---
title: Finding AWS IAM users by access key
date: 2015-07-22
programming/languages:
- Python
programming/topics:
- AWS
- AWS IAM
---
Every once in a while[^1], I find myself with an <a href="https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html">AWS access key</a> and need to figure out who in the world it belongs to. Unfortunately, so far as I've been able to find, there's no way to directly do this in either the <a href="https://aws.amazon.com/console/">AWS console</a> or with the <a href="https://aws.amazon.com/cli/">AWS api</a>.

<!--more-->

Luckily, <a href="https://aws.amazon.com/cli/">boto</a>:

```python
#!/usr/bin/env python3

import boto.iam.connection
import pprint
import sys

if len(sys.argv) == 1:
    print('Usage: who-iam [access-key ...]')
    sys.exit(0)

conn = boto.iam.connection.IAMConnection()
users = conn.get_all_users()

for user in users['list_users_response']['list_users_result']['users']:
    keys = conn.get_all_access_keys(user['user_name'])
    for key in keys['list_access_keys_response']['list_access_keys_result']['access_key_metadata']:
        for target in sys.argv[1:]:
            if key['access_key_id'] == target:
                print(key['access_key_id'], user['user_name'])
```

Check it out (keys changed on the off chance that actually matters):

```bash
$ who-iam AKIAIOSWISKB6EXAMPLE AKIAIOSGWISN7EXAMPLE
AKIAIOSWISKB6EXAMPLE luke
AKIAIOSGWISN7EXAMPLE han
```

It's rather slow (since it has to make `O(n)` requests and doesn't short circuit), but this should be something you do rarely enough that it doesn't matter.

If you'd like to download the script, it's available in my <a href="https://github.com/jpverkamp/dotfiles">dotfiles</a>: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/who-iam">who-iam</a>

[^1]: Read: entirely too often

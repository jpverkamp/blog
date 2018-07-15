---
title: Finding EC2 instances by tag
date: 2015-10-30
programming/languages:
- Python
programming/topics:
- AWS
- AWS EC2
---
Another script similar to my previous post about [Finding AWS IAM users by access key]({{< ref "2015-07-22-finding-aws-iam-users-by-access-key.md" >}}). This time, we want to do much the same thing for EC2 instances by tag.

<!--more-->

```python
#!/usr/bin/env python3

import argparse
import boto.ec2
import json
import re
import sys

parser = argparse.ArgumentParser(description = 'Find out information about EC2 instances')
parser.add_argument('--region', default = 'us-west-2', help = 'The AWS region to search')
parser.add_argument('--limit', type = int, default = 1, help = 'How many results to report, 0 will return all')
parser.add_argument('--output', default = 'private_ip_address', help = 'The output to fetch for each instance; json will output a json object will all of the outputs')
parser.add_argument('filters', nargs = argparse.REMAINDER, help = 'Regular expressions to apply to each tag')
args = parser.parse_args()

ec2 = boto.ec2.connect_to_region('us-west-2')

if not args.filters:
    raise Exception('You must specify at least one instance')

def include_instance(instance):
    if instance.state != 'running':
        return

    if not args.filters:
        return instance

    for filter in args.filters:
        for tag_key in instance.tags:
            tag_value = instance.tags[tag_key]
            tag = '{}={}'.format(tag_key, tag_value).lower()

            if re.search(filter, tag_value):
                return instance


def filter():
    for reservation in ec2.get_all_instances():
        for instance in reservation.instances:
            if include_instance(instance):
                yield instance

for i, instance in enumerate(filter(), 1):
    if args.output == 'json':
        print(json.dumps(instance.__dict__, default = str))
    else:
        print(getattr(instance, args.output))

    if args.limit and i >= args.limit:
        break
```

It's original goal was to get a single IP from a group of servers with a specific tag so that I could log in and poke around:

```bash
$ ssh &grave;ec2 prod-server&grave;
```

There are a few other uses though, especially when combined with other tools such as <a href="https://stedolan.github.io/jq/">`jq`</a>.

```bash
ec2 --limit 0 --output json | jq '.instance_type' | sort | uniq -c | sort -nr

  27 "t2.micro"
   5 "m3.medium"
   1 "c4.xlarge"
```

That's neat.

Much as `who-iam` it's a bit slow, but it still works great.

If you'd like to download the script, it's available in my <a href="https://github.com/jpverkamp/dotfiles">dotfiles</a>: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/ec2">ec2</a>

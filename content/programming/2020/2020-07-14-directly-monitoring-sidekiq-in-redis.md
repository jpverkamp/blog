---
title: Directly monitoring Sidekiq in Redis
date: 2020-07-14
programming/topics:
- Infrastucture
- Redis
- Sidekiq
- Flask
programming/languages:
- Python
- Ruby
---
Another thing that came up recently: we have many (many) [sidekiq](https://github.com/mperham/sidekiq) queues. Each has their own admin interface, but sometimes you just want all of the information in one place. Of course, you could bookmark all of the pages. Or make a single page with a lot of frames (remember [[wiki:HTML frames]]()?). Or use their API. But where's the fun in that? Instead, let's dig straight into the redis backend and see what we can see!

<!--more-->

First, let's find the queues. [Google + StackOverflow to the rescue](https://stackoverflow.com/questions/46407772/what-is-the-redis-key-for-a-queue-in-sidekiq)[^myday]. The queues are (by default), stored in `queue:default`. 

```bash
$ redis-cli

> get queue:default
(nil)
```

Hmm. There's a comment on the same post that actually answers that question. It turns out, I have ~~one~~ ~~two~~ three problems:

1. If a queue is empty, the key will not currently exist
2. If you have multiple queues/named queues, they won't be named `default`
3. If you used a prefix, that will be part of the queue as well

So... let's look for a more general solution. It turns out there will always be a list of queues stored at `queues` or `{prefix}:queues`. So we can start with:

```bash
> keys *queues*
1) "myservice:queues"

> smembers myservice:queues
1) "high"
2) "low"
3) "critical"
4) "medium"

> llen myservice:queue:low
(integer) 2
```

Nice!

That's all the information I needed for now. Let's throw together a quick UI. Now, I really should do this in Ruby, since sidekiq is a Ruby thing, and I've started exploring [Sinatra](http://sinatrarb.com/) as a really light weight server language. But for now, let's go with what I do best for lightweight services: [Flask](https://flask.palletsprojects.com/en/1.1.x/)

I'm going to take what I found about the Redis/Sidekiq earlier and connect to multiple Redii[^plurals] and pull out all their data:

```python
redii = {
    url: redis.Redis(
        host = url.split(':')[0],
        port = url.split(':')[1],
        decode_responses=True,
    )
    for url in config.get('redii')
}

def get_counts(host):
    logging.info(f'Refreshing data for {host}')

    r = redii[host]
    results = {'host': host, 'timestamp': time.time()}

    try:
        total = 0
        counts = {}

        # Get queue counts
        for queue_key in r.keys('*queues'):
            prefix = queue_key.split(':')[0] + ':' if ':' in queue_key else ''
            for priority in r.smembers(queue_key):
                key = f'{prefix}queue:{priority}'
                count = r.llen(key)
                if count:
                    counts[priority] = count
                    total += count

        results['counts'] = counts
        results['total'] = total

    except redis.exceptions.ConnectionError as ex:
        results['error'] = str(ex)

    return results
```

Get the `*queues`, reformat that as a singular to get the keys, get the lengths, and write it all down. Then to be really fancy, let's make automatic tables:

```python
@app.route('/')
def index():
    return tabulate.tabulate(
        get_all_counts(),
        tablefmt='html',
        headers='keys',
    )
```

[tabulate](https://pypi.org/project/tabulate/) is pretty cool.

Now on top of that, I did a few more things, such as writing down previous values and then calculating the current delta of the system (along with estimated time to clear) and alerting using [Slack incoming webhooks](https://api.slack.com/messaging/webhooks). But that's a post for another day. For now, it's a quick script that probably took me an hour or two to write but can save hours of time recovering from an overloading sidekiq queue that no one noticed. 

Woot. 

[^myday]: I should graph how many searches I make on an average day. Most of my job isn't knowing the answers to everything (although it helps :D), it's knowing how to phrase the question and interpret previous solutions. 

[^plurals]: Hey, it could be right! Maybe Redipodes would be better.
---
title: Pulling more than 5000 logs from datadog
date: 2022-01-25
programming/languages:
- Python
programming/sources:
- Small Scripts
programming/topics:
- Datadog
- Security
- APIs
---
[Datadog](https://www.datadoghq.com/) is pretty awesome. I wish I had it at my previous job, but better late than never. In particular, I've used it a lot for digging through recent logs to try to construct various events for various (security related) reasons. 

One of the problems I've come into though is that eventually you're going to hit the limits of what datadog can do. In particular, I was trying to reconstruct user's sessions and then check if they made one specific sequence of calls or another one. So far as I know, that isn't directly possible, so instead, I wanted to download a subset of the datadog logs and process them locally.

Easy enough, yes? Well: https://stackoverflow.com/questions/67281698/datadog-export-logs-more-than-5-000

Turns out, you just can't export more than 5000 logs directly. *But*... they have an API with pagination!

<!--more-->

End goal:

```bash
python3 dd-export.py 'service:api @log.endpoint:"/login"' > login-calls.json
...
```

How do we do it? 

```python
import coloredlogs
import datetime
import logging
import json
import requests
import sys
import os

coloredlogs.install(level=logging.INFO)

api_key = os.environ.get('DD_API_KEY') or input('DD API Key:')
application_key = os.environ.get('DD_APP_KEY') or input('DD API Key:')

query = sys.argv[1].replace('index:main ', '')

time_to = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
time_from = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

logging.info(f'{query=}, {time_from=} to {time_to=}')

query = {
    'limit': 1000,
    'query': query,
    'sort': 'desc',
    'time': {
        'from': time_from,
        'to': time_to,
    }
}

while True:
    response = requests.post(
        'https://api.datadoghq.com/api/v1/logs-queries/list',
        headers={
            'Content-Type': 'application/json',
            'DD-API-KEY': api_key,
            'DD-APPLICATION-KEY': application_key,
        },
        json=query
    )
    data = response.json()

    if not 'logs' in data:
        break

    logging.info(f'{query.get("startAt")} @ {data["logs"][0]["content"]["timestamp"]}')

    for row in data['logs']:
        print(json.dumps(row))

    if data['nextLogId']:
        query['startAt'] = data['nextLogId']
    else:
        break
```

Works great. Hope it helps you!
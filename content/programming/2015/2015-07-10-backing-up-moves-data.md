---
title: Backing up Moves Data
date: 2015-07-10
programming/languages:
- Python
programming/topics:
- Backups
---
Another [backup post]({{< ref "2015-01-29-ios-backup-apps.md" >}}), this time I'm going to back up my data from the <a href="https://www.moves-app.com/">Moves App</a> (step counter + GPS tracker). Theoretically, it should be possible to get this same data from the app as part of my [iOS Backup]({{< ref "2015-01-29-ios-backup-apps.md" >}}) series, but the data there is in a strange binary format. Much easier to use their API.

<!--more-->

The first step will be to make a few helper methods. As I often do with web scripts, I'll be using [Python]({{< ref "2007-10-20-pymint-a-python-multi-interpreter.md" >}}) and the excellent <a href="http://docs.python-requests.org/en/latest/">Requests</a> library. First things first, we have to get an `access_token` using an {{< wikipedia "OAuth" >}} handshake. It's a little complicated since our app is designed to run from the command line, yet needs to interact with the user on initial set up, but luckily that only has to be done once:

```python
# Request a new access token

if not 'access_token' in config:
    url = 'https://api.moves-app.com/oauth/v1/authorize?response_type=code&client_id={client_id}&scope={scope}'.format(
        client_id = config['client_id'],
        scope = 'activity location'
    )
    print('Opening URL in browser...')
    webbrowser.open(url)
    code = raw_input('Please follow prompts and enter code: ')

    response = requests.post('https://api.moves-app.com/oauth/v1/access_token?grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}'.format(
        code = code,
        client_id = config['client_id'],
        client_secret = config['client_secret'],
        redirect_uri = 'http://localhost/',
    ))
    js = response.json()
    print(js)

    config['access_token'] = js['access_token']
    config['refresh_token'] = js['refresh_token']
    config['user_id'] = js['user_id']

    with open('config.yaml', 'w') as fout:
        yaml.safe_dump(config, fout, default_flow_style=False)
```

Basically, we have to have two values to start the handshake: `client_id` and `client_secret`. I've put those in a separate file (`config.yaml`) so that we don't have secrets in a repository. From there, we make a request to a given endpoint (see above), which opens in a browser. The user then gets an eight digit code which they enter in the app on the phone, prompting the web browser in turn to redirect with a `code` parameter. This part is a little ugly and I could make it much nicer by running a temporary single endpoint server, but since this only needs to be done once, I didn't bother.

After that, we take the `code` we just got, along with the `client_id` and `client_secret` and get the initial `access_token` and a `refresh_token` we can periodically use to prove we're still the same person.

Next, a little bit of framework. We'll wrap the default `requests` object to automatically provide an `access_token` to any `GET` or `POST` requests I want to make to the API, now that I've gotten one:

```python
def makeMethod(f):
    def run(url, **kwargs):

        if 'access_token' in config:
            headers = {'Authorization': 'Bearer {access_token}'.format(access_token = config['access_token'])}
        else:
            headers = {}

        url = 'https://api.moves-app.com/api/1.1' + url.format(**kwargs)

        if 'data' in kwargs:
            return f(url, data = kwargs['data'], headers = headers)
        else:
            return f(url, headers = headers)

    return run

get = makeMethod(requests.get)
post = makeMethod(requests.post)
```

With that, we can just always use that `refresh_token` we got above every time we run the script. This is definitely over kill, but it saves a little bit of logic telling when we have to refresh the code or not and doesn't really cost anything more than a single extra request:

```python
# Perform a refresh on the access token just as a matter of course

response = requests.post('https://api.moves-app.com/oauth/v1/access_token', data = {
    'grant_type': 'refresh_token',
    'refresh_token': config['refresh_token'],
    'client_id': config['client_id'],
    'client_secret': config['client_secret']
})
js = response.json()

config['access_token'] = js['access_token']
config['refresh_token'] = js['refresh_token']
config['user_id'] = js['user_id']

with open('config.yaml', 'w') as fout:
    yaml.safe_dump(config, fout, default_flow_style=False)
```

Next, fetch my user profile:

```python
# Load the user profile to see how far back data goes

user_profile = get('/user/profile').json()
```

The most interesting bit of information here is `.profile.firstDate`, which tells us when we first started using Moves. We can then loop from that date forward in time, grabbing any days we are missing. Since sometimes previous days aren't completely done processing the next morning, I'll also always re-download the last week's worth of data no matter what.

```python
# Loop through all missing files, or force load anything less than a week ago

date = datetime.datetime.strptime(user_profile['profile']['firstDate'], '%Y%m%d')
today = datetime.datetime.now()
oneWeekAgo = today - datetime.timedelta(days = 7)

while date < today:
    dir = os.path.join('data', date.strftime('%Y'), date.strftime('%m'))
    filename = os.path.join(dir, date.strftime('%d') + '.json')

    if not date > oneWeekAgo and os.path.exists(filename):
        date += datetime.timedelta(days = 1)
        continue

    if not os.path.exists(dir):
        os.makedirs(dir)

    print(filename)

    response = get('/user/storyline/daily/{date}?trackPoints=true', date = date.strftime('%Y%m%d'))

    if response.status_code != 200:
        print('Bad response, stopping')
        print(response.text)
        sys.exit(0)

    if int(response.headers['x-ratelimit-minuteremaining']) < 1:
        print('Rate limited, waiting one minute before continuing')
        time.sleep(60)

    if int(response.headers['x-ratelimit-hourremaining']) < 1:
        print('Rate limited, wait one hour and try again')
        time.sleep(3600)

    with codecs.open(filename, 'w', 'utf-8') as fout:
        fout.write(response.text)

    date += datetime.timedelta(days = 1)
```

There is a neat bit in there with the `x-ratelimit-minuteremaining` and `x-ratelimit-hourremaining`. If we're downloading the entire history for the first time, you're going to get rate limited. So in this case, we'll wait a minute or an hour until the rate limit has expired.

And that's it. In the end, I end up with a pile of files, one for each day, each with exactly where I was on that day. I can use that data for all sorts of interesting analytics, like how far I walk in the average week, what my area of influence is, or even to combine with my [photography](/photography/) so that I can geotag my pictures. It's a lot of fun.

So, yes. I am something of a digital hoarder. But on the flip side, storage space is cheap and data is interesting. Perhaps I'll get a post or two out of making pretty pretty pictures out of where all I've been!

If you'd like to see / download the entire script for my Moves backup (or any of my other non-iOS backups, those are [here]({{< ref "2015-01-29-ios-backup-apps.md" >}})), you can do so here: <a href="https://github.com/jpverkamp/backup">jpverkamp/backup on GitHub</a>

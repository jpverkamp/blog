---
title: Observation Server
date: 2020-06-10
programming/topics:
- Websites
- Compression
- Flask
- Email
- SMTP
programming/languages:
- Python
---
For a number of years now, I've been writing down my 'observations'. Essentially, it's a semi-structured set of text files that I keep in Dropbox. One for each day, in a folder by month. I record interesting people I see, things I did worth doing, and things my children did which were adorable.

After a while, I started wanting to look back, so first, I wrote a relatively simple script that would go back through my archives and send me everything I did 1/2/3/4/etc years ago. That worked well enough, but it ended up generating a lot of emails to go through some days. So the second generation is a server that can format those pages and display them as a nice webpage. 

The most interesting part perhaps was dealing with the tarballs that I keep the archives in (they're plain text, so they compress very well). I wanted to keep them compressed, so I had to decompress them in memory on the fly.

<!--more-->


The general format is one folder per year, a sub folder per month, and a file per day. From time to time, I'll compress the previous months and then each new year, I'll uncompress those and stick them back into a whole year. Originally, I would actually nest the tarballs and I have code to deal with that. 

# Unpacking tarballs

```python
def get_observations(date):
    ymstr = date.strftime('%Y-%m')
    datestr = date.strftime('%Y-%m-%d.txt')

    # File exists directly
    path = os.path.join('data', ymstr, datestr)
    if os.path.exists(path):
        with open(path, 'r') as fin:
            return fin.read()

    # Check for an archive
    path = os.path.join('data', date.strftime('%Y.tgz'))
    if os.path.exists(path):
        with tarfile.open(path, 'r') as tf:
            for ti in tf.getmembers():
                # Skip mac files
                if '._' in ti.name:
                    continue

                # We found the date we were looking for
                if ti.name.endswith(datestr):
                    with tf.extractfile(ti) as fin:
                        return fin.read().decode('utf-8', 'replace')

                # Found another tarball with the month
                elif ymstr in ti.name and ti.name.endswith('tgz'):
                    with tf.extractfile(ti) as tf2_fin:
                        with tarfile.open(path, 'r') as tf2:
                            for ti2 in tf2.getmembers():
                                if ti2.name.endswith(datestr):
                                    fin = tf2.extractfile(ti2)
                                    return fin.read().decode('utf-8', 'replace')
```

The easiest case, just open the file. No problem. 

But if we have an archive, we'll open it with {{< doc python "tarfile.open" >}} in memory and scan through the file. Then `tf.extractfile` to get a file pointer and read it. Not even that complicated. It's ugly, but it works! I could probably have structured that better. 

# Going back in time

The next problem is going back in time. I've always liked infinite generators, and this is a good enough case for one:

```python
def naturals(i = 0):
    while True:
        yield i
        i += 1

content = ''
for years_ago in naturals(1):
    year_content = get_content(years_ago)
    if year_content:
        content += '\n=== {year} ===\n\n{content}\n'.format(
            year = datetime.datetime.now().year - years_ago,
            content = year_content
        )
    else:
        break
```

`get_contents` takes a number of years ago and calls `get_observations` with that date. 

# Sending emails

Then, we just send the email off in the off in the next to lowest level way you could do it (at least I'm not generating the bytes/network connections by hand?):

```python
# Generate a plaintext email and send it
msg = email.mime.text.MIMEText(content, _charset = 'utf-8')
msg['Subject'] = 'Daily observations'
msg['From'] = os.environ['EMAIL_TO']
msg['To'] = os.environ['EMAIL_TO']

smtp = smtplib.SMTP_SSL(os.environ['EMAIL_HOST'], int(os.environ['EMAIL_PORT']))
smtp.ehlo()
smtp.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
smtp.sendmail(os.environ['EMAIL_TO'], [os.environ['EMAIL_TO']], msg.as_string())
smtp.quit()
```

There are certainly better ways to do this. Heck, I have *done* the better ways to do this. I'll write those up at some point. But it works.

And that was it. For years, that did it's job. 

But then in my recent push to *server all the things*, I moved on to making an internal server just for my home network.

# Creating a server

Like I generally do for simple one off servers, I used [Flask](https://flask.palletsprojects.com/en/1.1.x/). 

First, a route for specific days:

```python
@app.route('/<int:year>/<int:month>/<int:day>')
def get_date(year, month, day):
    date = datetime.date(year, month, day)
    observations = parse_observations(get_observations(date), include_all = 'all' in flask.request.args)
    categories = set(observations.keys())

    def jumplink(text, **kwargs):
        if kwargs.get('today'):
            new_date = datetime.date.today()
        elif kwargs.get('random'):
            new_date = random_date()
        else:
            new_date = date + dateutil.relativedelta.relativedelta(**kwargs)

        return '<a class="button" href="{link}">{text}</a>'.format(
            link = new_date.strftime('/%Y/%m/%d'),
            text = text
        )

    return flask.render_template(
        'daily.html',
        date = date,
        offset = humanize.naturaldelta(datetime.date.today() - date),
        categories = categories,
        entries = observations,
        jumplink = jumplink,
        is_favorite = is_favorite
    )
```

Get the date first, sure. Then the observations next. Okay. Then I'm doing a bit to break down categories (which are the 'interesting things' / 'things I did worth doing' I mentioned before, the parsing of those isn't super interesting). The `jumplink` nested function is a bit interesting. Basically, you can call it with a bunch of different options to jump around in time:

```html
<ul class="button-list">
    <li>{{ jumplink('today', today = True) | safe }}</li>
    <li>{{ jumplink('random', random = True) | safe }}</li>
    <li>{{ jumplink('yesterday', days = -1) | safe }}</li>
    <li>{{ jumplink('tomorrow', days = 1) | safe }}</li>
    <li>{{ jumplink('last week', weeks = -1) | safe }}</li>
    <li>{{ jumplink('next week', weeks = 1) | safe }}</li>
    <li>{{ jumplink('last month', months = -1) | safe }}</li>
    <li>{{ jumplink('next month', months = 1) | safe }}</li>
    <li>{{ jumplink('last year', years = -1) | safe }}</li>
    <li>{{ jumplink('next year', years = 1) | safe }}</li>
    <li><a class="button" href="/favorites">favorites</a></li>
</ul>
```

Then I use all of that information to render the page via a [Jinja template](https://jinja.palletsprojects.com/en/2.11.x/):

```html
{% if categories %}
    {% for category in categories | sort %}
    <h2>{{ category }}</h2>

    <ul class="entry-list">
        {% for entrylist in entries[category] %}
        <li class="entry">
            <div class="content">
            {% for entry in entrylist %}
            {{ entry }} <br />
            {% endfor %}
            </div>
            <a href="#" data-favorite="{{ is_favorite(hash(entrylist)) }}" onclick="favorite(this, '{{ date }}', '{{ hash(entrylist) }}')">♡</a>
        </li>
        {% endfor %}
    </ul>
    {% endfor %}
{% else %}
    <h2>No entries today (it wasn't always so)</h2>
{% endif %}
```

Pretty nice. 

That's really it. As you can see there, I also added some functionality for 'favoriting' specific observations. Those, I'll create an MD5 hash (it's not great from a security perspective, but I'm not using it for that). I did do a quick trick to make that function available to Jinja though:

```python
app = flask.Flask(__name__)
app.jinja_env.globals['hash'] = lambda el : hashlib.md5(str(el).encode()).hexdigest()
```

I thought that was neat. I can change the hash too, just by changing `md5` for `sha256` for example. I then store the dates and hashes in a [YAML](https://yaml.org/) file in the same observations directory. 

A few more helper routes (that go with the `jumplink` code earlier):

```python
@app.route('/')
@app.route('/today')
def hello_world():
    date = datetime.date.today()
    return get_date(date.year, date.month, date.day)

@app.route('/random')
def get_random():
    date = random_date()
    return get_date(date.year, date.month, date.day)
```

And we're golden. 

I know it's a quick post, but perhaps you'll find something interesting there to use for your own projects!
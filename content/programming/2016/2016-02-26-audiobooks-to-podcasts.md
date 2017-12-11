---
title: Audiobooks to Podcasts
date: 2016-02-26 00:05:00
programming/languages:
- Python
programming/topics:
- Audio
- Flask
- Web Development
- nginx
---
I've recently started to listen to audiobooks again (The Aeronaut's Windlass). If you buy books through Audible or some other setup that has their own app, it's a straight forward enough process. On the other hand, if you have them on CD and want to play them on a mobile device... It's a little more interesting.

I tried a few different apps that purport to do exactly what I wanted: import an audiobook as a folder full of MP3s and play them, but none that quite meet what I wanted. Since I also listen to a lot of podcasts and have more than one podcast app that I really like (I've used and liked both <a href="http://www.downcastapp.com/">Downcast</a> and <a href="http://www.shiftyjelly.com/pocketcasts">Pocket Casts</a>), I decided to see if I couldn't use one of those as an audiobook player.

<!--more-->

My basic set up is one that I've used before. I'll use <a href="https://docs.docker.com/compose/">docker-compose</a> to run a web server running <a href="http://flask.pocoo.org/">flask</a> behind an <a href="https://www.nginx.com/resources/wiki/">nginx reverse proxy</a> (for performance reasons and to serve static files).

Basically, I want a server that when I hit it will give a list of all books in a folder. If I click any of those, it will generate an RSS feed that I can then give to my podcasting application. That in turn can make requests for any of the MP3 files that make up the book, which should be served back to the app. Simple as pie, no? Well, mostly.

Creating a list of books is easy:

```python
@app.route('/')
def index():
    result = '<ul>'

    for path in sorted(os.listdir('books')):
        config_path = os.path.join('books', path, 'book.yml')
        print(config_path)

        if not os.path.exists(config_path):
            continue

        with open(config_path, 'r') as fin:
            config = yaml.load(fin)

        result += '<li><a href="feed/{path}.xml">{title} by {author}</a></li>'.format(
            path = path,
            title = config['title'],
            author = config['author']
        )

    result += '</ul>'
    return result
```

Note: Each book is a subdirectory of the folder `books`. Each book must also contain at least one file named `book.yml` which defines the `title` and `author` of the book, along with any number of MP3 files (we'll see that in a moment).

All this script does is generate an HTML unordered list (`ul`) of links to individual RSS feeds. We generate those in turn with:

```python
@app.route('/feed/<feed>.xml')
def get_feed(feed):
    config_path = os.path.join('books', feed, 'book.yml')

    with open(config_path, 'r') as fin:
        config = yaml.load(fin)

    fg = feedgen.feed.FeedGenerator()
    fg.load_extension('podcast')

    host_url = flask.request.scheme + '://' + flask.request.host

    feed_link = host_url + '/feed/{feed}.xml'.format(feed = feed)

    fg.id = feed_link
    fg.title(config['title'])
    fg.description('{title} by {author}'.format(title = config['title'], author = config['author']))
    fg.author(name = config['author'])
    fg.link(href = feed_link, rel = 'alternate')

    fg.podcast.itunes_category('Arts')

    for file in sorted(os.listdir(os.path.join('books', feed))):
        if not file.endswith('.mp3'):
            continue

        name = file.rsplit('.', 1)[0]

        feed_entry_link = host_url + '/feed/{feed}/{file}'.format(feed = feed, file = file)

        fe = fg.add_entry()

        fe.id(feed_entry_link)
        fe.title(name)
        fe.description('{title} by {author} - {chapter}'.format(
            title = config['title'],
            author = config['author'],
            chapter = name,
        ))
        fe.enclosure(feed_entry_link, 0, 'audio/mpeg')

    return fg.rss_str(pretty = True)
```

Here, I basically just read in the `book.yml` file and any MP3s in the directory and generate a feed. As I did previously in my post on [Generating YouTube user RSS feeds]({{< ref "2015-05-11-generating-youtube-user-rss-feeds.md" >}}), I'm using the <a href="https://lkiesow.github.io/python-feedgen/">feedgen</a> package to generate the RSS feeds. This time I'm using their built in `podcast` extension. Nice.

After that, we just need to serve the MP3s. Originally I was going to serve this with flask as well, but since I'm already going to use nginx as a performance / caching layer, we can use that to serve static files. Something like this for an nginx configuration:

```nginx
server {
    root /var/www/;

    location / {
        try_files $uri @server;
    }

    location @server {
        proxy_set_header Host $host;
        proxy_pass http://server:5000;
    }
}
```

Essentially, it will `try_files` to see if there's a static file at the path requested first. If that fails, it will fall back to the `@server` reverse proxy, which just feeds traffic to the flask server.

To get everything working together, we'll use docker-compose:

```yaml
server:
    build: server
    # environment: {DEBUG: True}
    ports:
        - 5000
    volumes:
        - ./books:/app/books

nginx:
    image: nginx
    links:
        - server
    ports:
        - 80:80
    volumes:
        - ./books:/var/www/feed/
        - ./nginx:/etc/nginx/conf.d/
```

Since I'm mounting the `./books` directory as a volume into both containers, the `nginx` container can use it to server static files while the `server` container can use it to list files.

And that's about it. I have mine running with <a href="http://nginx.org/en/docs/http/ngx_http_auth_basic_module.html">nginx HTTP authentication </a>, which means that I have to use <a href="http://www.downcastapp.com/">Downcast</a> (it's the only one I've used that seems to support it), but other than that it works great. It does require that you have your own server running to initially get the files onto the podcast app, but if you download them, almost all of the apps will let you turn off the server.

The combination of flask and docker is nice. Flask let's you quickly and easily write simple web applications. Docker makes deployment and dependency management a snap.

If you'd like to see the entire codebase, it's on GitHub: <a href="https://github.com/jpverkamp/podbook">podbook</a>. There are a few bits that I didn't include in the writeup above.

Any questions? Let me know below.

---
title: Generating YouTube user RSS feeds
date: 2015-05-11
programming/languages:
- Python
programming/topics:
- Web Development
- YouTube
---
On 4 March 2014, YouTube deprecated the v2.0 API for YouTube (<a href="https://developers.google.com/youtube/2.0/developers_guide_protocol_deprecated">source</a>). One of the unfortunate side effects was that RSS feeds for user uploads were included in what was deprecated.

Previously, you could get an RSS feed with a link of the form: `https://gdata.youtube.com/feeds/base/users/{user}/uploads` For the longest time, even after the deprecation, those links still worked, but a couple weeks ago, more and more of the video feeds I was subscribed to started redirecting to <a href="https://www.youtube.com/channel/UCMDQxm7cUx3yXkfeHa5zJIQ/videos">YouTube Help account</a>. As thrilling as that channel is, it's not what I'm looking for.

Let's fix it.

<!--more-->

First step, we need a YouTube Data API (v3) key. Unfortunately it doesn't look like they provide un-authenticated use of the API as before. That's easy enough though, just <a href="https://developers.google.com/youtube/registering_an_application">go through the steps to register an application</a>. Next, dig through the APIs. It doesn't look like there is a way to directly get a user's videos, but you can get a list of a users 'uploads' playlist, which functions much the same way.

Using Python's <a href="http://docs.python-requests.org/en/latest/">requests</a> library, we just have to hit the correct endpoint:

```python
# Use the channel to get the 'uploads' playlist id
response = requests.get(
    'https://www.googleapis.com/youtube/v3/channels',
    params = {
        'part': 'contentDetails',
        'forUsername': user,
        'key': API_KEY,
    }
)
```

One example response:

```json
{"etag": "\"tbWC5XrSXxe1WOAx6MK9z4hHSU8/6wRGj4eVz7tGNiDQjCMuhP6B4vQ\"",
 "items": [{"contentDetails": {"googlePlusUserId": "112244684143881021368",
                               "relatedPlaylists": {"likes": "LL6nSFpj9HTCZ5t-N3Rm3-HA",
                                                    "uploads": "UU6nSFpj9HTCZ5t-N3Rm3-HA"}},
            "etag": "\"tbWC5XrSXxe1WOAx6MK9z4hHSU8/yMieoczWtu9QiK_MEdJrC0hqmdU\"",
            "id": "UC6nSFpj9HTCZ5t-N3Rm3-HA",
            "kind": "youtube#channel"}],
 "kind": "youtube#channelListResponse",
 "pageInfo": {"resultsPerPage": 5, "totalResults": 1}}
```

That's some progress. Specifically, you can get the playlist ID for the user uploads:

```python
playlistId = response.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
```

From there, we can query the API again in order to get the most recent 20 items from that specific playlist:

```python
# Get the most recent 20 videos on the 'uploads' playlist
response = requests.get(
    'https://www.googleapis.com/youtube/v3/playlistItems',
    params = {
        'part': 'snippet',
        'maxResults': 20,
        'playlistId': playlistId,
        'key': API_KEY
    }
)
```

Some snippets from that output (it's rather large):

```json
{"etag": "\"tbWC5XrSXxe1WOAx6MK9z4hHSU8/PH2ohKtd9aLBba_d7dVtVUfFle0\"",
 "items": [{"etag": "\"tbWC5XrSXxe1WOAx6MK9z4hHSU8/-LUTubHPIceTTTPMrBW-Qs9KOZQ\"",
            "id": "UUKzDohq4XHVIEl9O19Nd8rKuqCo1VravR",
            "kind": "youtube#playlistItem",
            "snippet": {"channelId": "UC6nSFpj9HTCZ5t-N3Rm3-HA",
                        "channelTitle": "Vsauce",
                        "description": "Vsauce is nominated for a Webby "
                                       "in Science & Education! You can "
                                       ...,
                        "playlistId": "UU6nSFpj9HTCZ5t-N3Rm3-HA",
                        "position": 0,
                        "publishedAt": "2015-04-13T19:26:03.000Z",
                        "resourceId": {"kind": "youtube#video",
                                       "videoId": "f8WsO__XcI0"},
                        "thumbnails": {"default": {"height": 90,
                                                   "url": "https://i.ytimg.com/vi/f8WsO__XcI0/default.jpg",
                                                   "width": 120},
                                       ...},
                       "title": "When Will We Run Out Of Names?"}},
           {"etag": "\"tbWC5XrSXxe1WOAx6MK9z4hHSU8/kCpPYobMQgr7w9gfxaR-_cfkJkc\"",
           ...]}
```

In that snippets blob, we have everything we need. Specifically, the `title`, `thumbnails`, and `link` (by way of `resourceID.videoId`). Specifically, we can start to construct an RSS feed using the <a href="https://pypi.python.org/pypi/feedgen/">feedgen</a> library[^1]:

```python
# Generate a list of results that can be used as feed items
feed = feedgen.feed.FeedGenerator()
feed.title(user + ' (YRSS)')
feed.author({'name': user + ' (YRSS)'})
feed.id('YRSS:' + user)

for item in response.json()['items']:
    title = item['snippet']['title']
    video_id = item['snippet']['resourceId']['videoId']
    published = item['snippet']['publishedAt']
    thumbnail = item['snippet']['thumbnails']['high']['url']
    video_url = 'https://www.youtube.com/watch?v=' + video_id

    item = feed.add_entry()
    item.title(title)
    item.link(href = video_url)
    item.published(dateutil.parser.parse(published))
    item.updated(dateutil.parser.parse(published))
    item.id(video_id)
    item.content('''
<a href="{url}"><img src="{img}" /></a>
<a href="{url}">{title}</a>
'''.format(
        url = video_url,
        img = thumbnail,
        title = title,
    ))
```

And generate the feed:

```python
feed.atom_str()
```

I love how (relatively) elegant that was. You don't have to worry about or even know anything about how the underlying XML will be structured.

Since eventually I want this to be a web service, I used Flask to generate a simple API:

```python
app = flask.Flask(__name__)

@app.route('/<user>.xml')
@app.route('/<user>/atom.xml')
def generatefeed(user):
    ...

    return feed.atom_str()
```

That way, if you go to `http://myserver.com/{user}.xml`, you would get an RSS feed for that user's most recent 20 videos. There are a few other considerations to keep in mind (For example, I have a cache that only re-queries the YouTube API once per hour and otherwise re-serves the same feed. And better error handling.)

If you'd like to see the full source in all it's glory, it's available on GitHub: <a href="https://github.com/jpverkamp/yrss">jpverkamp/yrss</a>. You will have to supply an `API_KEY` as an environment variable to run it, but that should be relatively straight forward.

[^1]: I originally used <a href="https://pypi.python.org/pypi/feedgenerator/1.2.1">feedgenerator</a>, but it doesn't seem to support Python3
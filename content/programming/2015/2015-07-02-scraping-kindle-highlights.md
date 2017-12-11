---
title: Scraping Kindle Highlights
date: 2015-07-02
programming/languages:
- Python
programming/topics:
- Amazon
- Backups
---
As part of an ongoing effort to [backup all the things]({{< ref "2015-01-29-ios-backup-apps.md" >}}), combined with a rather agressive [2015 Reading List]({{< ref "2015-12-31-reading-list-retrospective.md" >}}), I wanted to the ability to back up any sections that I've highlighted on my Kindle. Unfortunately, Amazon doesn't seem to have an API to do that, but why should that stop me?

Using a combination of [Python]({{< ref "2007-10-20-pymint-a-python-multi-interpreter.md" >}}) and the Python libraries <a href="http://docs.python-requests.org/en/latest/">Requests</a> and <a href="http://www.crummy.com/software/BeautifulSoup/">BeautifulSoup</a>[^1], it's entirely possible to write a Python script that will log into Amazon, get a list of all of the books on your account, and download the highlights for each.

Let's do it!

<!--more-->

First, we are going to be using a Requests `session`. This will keep track of any cookies that Amazon decides to send us so that we know that we're logged in.

```python
session = requests.Session()
```

After that, the next thing we need to do is to use requests to log into Amazon. Loading up the login page (`https://kindle.amazon.com/login`), we see that the `form` target is a `POST` request to `https://www.amazon.com/ap/signin`, specifying the fields `email` and `password`. Something like this:

```python
signin_data = {}

signin_data[u'email'] = os.environ['AMAZON_USERNAME']
signin_data[u'password'] = os.environ['AMAZON_PASSWORD']

response = session.post('https://www.amazon.com/ap/signin', data = signin_data)
```

I'm reading my Amazon username and password from the environment. In general, that means I can have a simple file like this:

```bash
export AMAZON_USERNAME="me@example.com"
export AMAZON_PASSWORD="correct horse battery staple"
```

Then I can source that script before running my program:

```bash
. ./env.conf && python3 kindle-highlights-backups.py
```

That should work, but unfortunately it doesn't. It looks like Amazon is sending a small pile of hidden fields. Theoretically, I could look at the page and hard code them, but where's the fun in that? Instead, let's use Requests to grab the login page and BeautifulSoup to parse out all of the fiels we're going to send:

```python
# Log in to Amazon, we have to get the real login page to bypass CSRF
print('Logging in...')
response = session.get('https://kindle.amazon.com/login')
soup = bs4.BeautifulSoup(response.text)

signin_data = {}
signin_form = soup.find('form', {'name': 'signIn'})
for field in signin_form.find_all('input'):
    try:
        signin_data[field['name']] = field['value']
    except:
        pass

signin_data[u'email'] = os.environ['AMAZON_USERNAME']
signin_data[u'password'] = os.environ['AMAZON_PASSWORD']

response = session.post('https://www.amazon.com/ap/signin', data = signin_data)
if response.status_code != 200:
    print('Failed to login: {0} {1}'.format(response.status_code, response.reason))
    sys.exit(0)
```

... Still doesn't work. I'm getting a page back that says I need to enable cookies, which I most definitely have enabled (that's why I created the `session`). A bit of Google-fu later, and I find out that Amazon will only allow connections from semi-reasonable {{< wikipedia "User Agents" >}}. Let's set it to a recent Chrome build on Windows 8.1:

```python
session = requests.Session()
session.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.61 Safari/537.36'
}
```

Ah ha! That works. Finally logged in. Next, we know that we can get a list of your current books by going to `https://kindle.amazon.com/your_reading/0/0/0`. The last three numbers are:


* mode (all, read, reading)
* starting index / page (increments in 25)
* all books (0) versus kindle only (1)


So let's write a loop to keep fetching pages of these books, 25 at a time:

```python
# Iterate through pages of books, 25 at a time
# Note: The last three parts of the URL are:
#   - mode (all, read, reading)
#   - starting index / page (increments in 25)
#   - all books (0) versus kindle only (1)
print('Getting books...')
book_page = 0
while True:
    time.sleep(0.5) # Half a second between pages

    response = session.get('https://kindle.amazon.com/your_reading/0/{book_page}/0'.format(book_page = book_page))
    soup = bs4.BeautifulSoup(response.text)
    found_book = False

    ...

    if found_book:
        book_page += 25
    else:
        break
```

Within that page, there are a series of `td` elements linking to books, each with the class `titleAndAuthor`. That's the beauty of BeautifulSoup:

```python
...

    # For each page of books, find all of the individual book links
    # The last part of each URL is Amazon's internal ID for that book
    for el in soup.findAll('td', {'class': 'titleAndAuthor'}, recursive = True):
        time.sleep(0.1) # 1/10 of a second between books

        found_book = True

        book_id = el.find('a')['href'].split('/')[-1]
        title = el.find('a').text
        sys.stdout.write(title + ' ... ')

        highlights = []
        cursor = 0

        ...
```

Luckily, the next part is a little easier to deal with. There is actually an API of sorts of Kindle highlights, once you have a user ID. All you have to do is hit `https://kindle.amazon.com/kcw/highlights?asin={book_id}` (potentially many times, it's {{< wikipedia "paginated" >}}):

```python
...

        # Ask the Amazon API for highlights one page of 10 at a time until we have them all
        while True:
            response = session.get('https://kindle.amazon.com/kcw/highlights?asin={book_id}&cursor={cursor}&count=10'.format(
                book_id = book_id,
                cursor = cursor,
            ))
            js = response.json()

            found_highlight = False
            for item in js['items']:
                found_highlight = True
                item['highlight'] = html_unescape(item['highlight'])
                highlights.append(item)

            if found_highlight:
                cursor +=1
            else:
                break

        ...
```

One caveat is that we don't want to store HTML entities (like `&amp;rsquo;`), we want the real characters. This is a little annoying, since the library to parse that has moved around in various Python versions:

```python
# Get a function to unescape html entites
try:
    import html
    html_unescape = html.unescape
except:
    try:
        import html.parser
        html_unescape = html.parser.HTMLParser().unescape
    except:
        import HTMLParser
        html_unescape = HTMLParser.HTMLParser().unescape
```

Yeah...

Now that we have a list of highlights, let's save them to disk. Generate a filename from the book title, and use the `json` library to write them out. Make sure that we're writing everything as UTF8 so that any more unusual characters (like more interesting quotes) save correctly:

```python
# Use book title as filename, but strip out 'dangerous' characters
        print('{count} highlights found'.format(count = len(highlights)))
        if highlights:
            filename = re.sub(r'[\/:*?"<>|"\']', '', title).strip() + '.json'
            path = os.path.join('Kindle Highlights', filename)

            with open(path, 'w', encoding = 'utf8') as fout:
                fout.write(json.dumps(highlights, fout, indent = 4, sort_keys = True, ensure_ascii = False))
```

And there you have it. A simple(ish) way to download your Kindle highlights.

Unfortunately... that's not all she wrote. After running my script for a few days, it started to fail. Why? Because Amazon detected some strange activity on my account and started displaying a captcha. I can detect it easily enough:

```python
warning = soup.find('div', {'id': 'message_warning'})
if warning:
    print('Failed to login: {0}'.format(warning.text))
    sys.exit(0)
```

Put that just after the previous 'Failed to login' block and you'll seem some text to the order of 'please enter these characters to continue'. It's actually not that hard to solve a catcha programmatically... but we'll save that for another post.

And that's it for today. So far I have 308 highlights spread over 20 books and it's only growing. It's fun to go back and read them again.

[^1]: We called him Tortoise because he taught us
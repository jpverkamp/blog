#!/usr/bin/env python3

import bs4
import datetime
import email.utils
import html2text
import logging
import os
import re
import re
import requests
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree
import yaml

if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser('Import data from goodreads')
    arg_parser.add_argument('--insert', nargs = '+', help = 'Url(s) to add to the database')
    arg_parser.add_argument('--delete', nargs = '+', help = 'Name(s) to remove from the database, will be removed from all types')
    arg_parser.add_argument('--validate', action = 'store_true', help = 'Check if there are any missing entires')
    arg_parser.add_argument('--reviews', nargs = '?', default = False, const = '20', help = 'Import the newest REVIEWS reviews, use ALL to import all reviews')
    arg_parser.add_argument('--overwrite', action = 'store_true', help = 'Use with --reviews, if this is not set, existing posts will not be overwritten')
    arg_parser.add_argument('--debug', action = 'store_true', help = 'Run in verbose/debug mode')
    arg_parser.add_argument('--nocache', action = 'store_true', help = 'Disable loading from cache')
    arg_parser.add_argument('--add-cover', nargs = 2, help = 'Download a cover, specify a URL and the book title')
    args = arg_parser.parse_args()

    if args.debug:
        logging.basicConfig(level = logging.INFO)

markdowner = html2text.HTML2Text()

config = {}
for filename in ['config.yaml', 'secrets.yaml']:
    with open(filename, 'r') as fin:
        config.update(yaml.load(fin))

fields = { # singular: plural
    'book': 'books',
    'author': 'authors',
    'series': 'series',
}

global_data = {}

for filename in os.listdir(os.path.join('data', 'goodreads')):
    path = os.path.join('data', 'goodreads', filename)
    name = filename.rsplit('.', )[0]

    logging.info('Loading data from {} into global_data[{}]'.format(path, name))
    with open(path, 'r') as fin:
        global_data[name] = yaml.load(fin)

for singular, plural in fields.items():
    if plural not in global_data:
        global_data[plural] = {}

def save():
    for name in global_data:
        path = os.path.join('data', 'goodreads', name + '.yaml')

        logging.info('Saving data from global_data[{}] into {}'.format(name, path))
        with open(path, 'w') as fout:
            yaml.dump(global_data[name], fout, default_flow_style = False)

def api(url, params = None, mode = 'soup'):
    '''Make a goodreads web request.'''

    url = url.lstrip('/')
    if not url.startswith('http'):
        url = 'https://www.goodreads.com/' + url

    logging.info('api({}, {})'.format(url, params))

    response = requests.get(url, params = params)

    if mode == 'soup':
        return bs4.BeautifulSoup(response.text, 'html5lib')
    elif mode == 'xml':
        return xml.etree.ElementTree.fromstring(response.text)
    else:
        raise Exception('Unkonwn API mode: {}'.format(mode))


def split_title(text):
    '''
    Given a name like "The Final Empire (Mistborn, #1)", return (The Final Empire, Mistborn, 1).

    Possible series formats:
        The Final Empire (Mistborn, #1) -> The Final Empire, Mistborn, 1
        The Final Empire (Mistborn, #1) -> The Final Empire, Mistborn, 1
        The Final Empire (Mistborn, 1) -> The Final Empire, Mistborn, 1
        The Final Empire (Mistborn 1) -> The Final Empire, Mistborn, 1
        Mistborn, Part 1 of 3 -> None, Mistborn, 1
        The Final Empire -> The Final Empire, None, None
    '''

    text = re.sub(r'\s+', ' ', text).strip()
    logging.info('split_title({})'.format(text))

    # Fallback, no series
    title, series, index = text, None, None

    m_part = re.match(r'^(.*?), [Pp]art (\d+) of (\d+)$', text)
    m_series_index = re.match(r'^(.*?) \((.*?),?\s+#?([\d.-]+)\)$', text)
    m_series_no_index = re.match(r'^(.*?) \((.*?)\)', text)

    # Syntax with part m of n
    if m_part:
        logging.info('split_title({}), matching part'.format(text))
        series, index, _ = m_part.groups()

    # Syntax with paran'ed series and and index
    elif m_series_index:
        logging.info('split_title({}), matching paran and index'.format(text))
        title, series, index = m_series_index.groups()

    # Paran'ed series but no index
    elif m_series_no_index:
        logging.info('split_title({}), matching paran with no index'.format(text))
        title, series = m_series_no_index.groups()

    # If the index looks like a int/float, convert to that
    if index:
        if index.isdigit():
            index = int(index)
        elif re.match('^[\d.]+$', index):
            index = float(index)

    logging.info('split_title({}) -> {}, {}, {}'.format(text, title, series, index))
    return title, series, index

def slugify(text):
    '''Convert text into a 'safe' format for URLs/filenames.'''

    text = text.lower()
    text = re.sub(r'[\'"()]+', '', text)
    text = re.sub(r'[^a-z0-9-]+', '-', text)
    text = text.strip('-')
    return text

def clean_url(url):
    '''For a URL to be a relative URL without query parameters.'''

    clean_url = url

    if url.startswith('http'):
        clean_url = clean_url.split('.com/')[-1]

    clean_url = clean_url.split('?')[0]

    logging.info('clean_url({}) -> {}'.format(url, clean_url))
    return clean_url

def id_to_url(type, id, name = None):
    '''Build a URL from and ID.'''

    for singular, plural in fields.items():
        if type == plural:
            type = singular

    clean_name = slugify(name) if name else type

    if type == 'series':
        url = '/{type}/{id}.{name}'.format(type = type, id = id, name = clean_name)
    else:
        url = '/{type}/show/{id}.{name}'.format(type = type, id = id, name = clean_name)

    logging.info('id_to_url({}, {}, {}) -> {}'.format(type, id, name, url))
    return url

def url_to_id(url):
    '''Pull an ID out of a url.'''

    id = int(re.search(r'/(\d+)(?:[^/]*)$', url).group(1))
    logging.info('url_to_id({}) -> {}'.format(url, id))
    return id

def get(type, query, search_function, update_function):
    '''
    Get a book/series/author.

    search_function takes a name and returns a url for the object
    update_function takes a data array and returns a data array (with more stuff in it)
    '''

    id = url = name = None
    if type in fields:
        type = fields[type]

    logging.info('get({}, {})'.format(type, query))

    # Figure out what we're querying by: id, url, or title
    if isinstance(query, int) or query.isdigit():
        id = int(query)
        url = id_to_url('book', id)

    elif query.startswith('/') or query.startswith('http'):
        url = clean_url(query)
        id = url_to_id(url)

    else:
        name = query

    # If we're querying by an ID we've already seen, get the title from that
    if id and id in global_data.get(type + '-index', {}):
        logging.info('get({}, {}), got name by id: {} = {}'.format(type, query, id, global_data[type + '-index'][id]))
        name = global_data[type + '-index'][id]

    # If the title is already cached, load from there
    if args.nocache:
        logging.info('get({}, {}), caching disabled, loading {} directly'.format(type, query, name))
    else:
        if name in global_data[type]:
            logging.info('get({}, {}), loaded {} from cache'.format(type, query, name))
            return global_data[type][name]
        else:
            logging.info('get({}, {}), name {} is not in cache, using api'.format(type, query, name))

    # Otherwise, load the data from goodreads
    data = {}

    if name and not url:
        logging.info('get({}, {}), finding by name: {}'.format(type, query, name))
        url = search_function(name)
        if url:
            logging.info('get({}, {}), url is {}'.format(type, query, url))
        else:
            raise Exception('No results found when searching for {}: {}'.format(type, name))

    url = clean_url(url)
    id = url_to_id(url)

    data['id'] = id
    data['name'] = name
    data['url'] = url

    data = update_function(data)

    data['url'] = id_to_url(type, data['id'], data['name'])

    logging.info('get({}, {}), result: {}'.format(type, query, data))
    global_data[type][data['name']] = data
    global_data.setdefault(type + '-index', {})[data['id']] = data['name']
    save()

    return data

def download_cover(data, image_url):
    '''
    Download and resize a cover to a specific path.
    '''

    logging.info('Attempting to download cover: {}'.format(image_url))
    data['cover'] = image_url
    response = requests.get(data['cover'], stream = True)
    response.raw.decode_content = True

    if response:
        filename = '{}.{}'.format(
            slugify(data['name']),
            data['cover'].split('.')[-1].lower()
        )
        path = os.path.join('static', 'embeds', 'books', filename)

        if os.path.exists(path):
            logging.info('Cover already downloaded for {}'.format(data['name']))
        else:
            logging.info('Downloading cover for {}'.format(data['name']))
            os.makedirs(os.path.dirname(path), exist_ok = True)
            with open(path, 'wb') as fout:
                shutil.copyfileobj(response.raw, fout)
                subprocess.check_output('mogrify -resize 100x160\! "{}"'.format(path), shell = True)

        data['localCover'] = path.replace('static', '')
    else:
        logging.warning('Failed to download cover for {}'.format(data['name']))

def get_book(query):
    '''
    Get a book. If we're provided a title and the book isn't in the cache, search.
    '''

    logging.info('get_book({})'.format(query))

    def search(title):
        search_soup = api('search', params = {'q': title, 'search_type': 'books', 'search[field]': 'title'})
        for el_book in search_soup.select('tr[itemscope]'):
            return el_book.find('a').attrs['href'].split('?')[0]

    def update(data):
        api_data = api('/book/show.xml', mode = 'xml', params = {
            'id': data['id'],
            'key': config['goodreads']['key'],
        })

        title, series, index = split_title(api_data.find('book/title').text.strip())
        if not data.get('name'):
            data['name'] = title

        # Try to automatically link the series and automatically cache that
        try:
            series_id = api_data.find('book/series_works//series/id')
            if series_id:
                series_url = '/series/{}'.format(series_id)
                get_series(series_url)
        except IndexError:
            pass

        if series:
            data['series'] = series
            data['series_index'] = index

        # Look up author and automatically cache them
        data['author'] = api_data.find('book/authors/author/name').text.strip()
        get_author(api_data.find('book/authors/author/link').text.strip())

        # Get the cover if one is set
        image_url = api_data.find('book/image_url')
        if image_url != None:
            image_url = image_url.text.strip()
            if 'nophoto' in image_url:
                logging.warning('Missing cover for: {}'.format(title))
            else:
                download_cover(data, image_url)

        return data

    return get('book', query, search, update)

def get_series(name):
    '''
    Get a series by title.

    TODO: Search by title if the series isn't cached and the url isn't provided.
    '''

    logging.info('get_series({})'.format(name))

    def search(name):
        search_soup = api('search', params = {'q': name, 'search_type': 'books', 'search[field]': 'title'})
        for el_book in search_soup.select('tr[itemscope]'):
            book_url = el_book.find('a').attrs['href'].split('?')[0]
            book_soup = api(book_url)
            for el_series in book_soup.select('#bookTitle a'):
                return el_series.attrs['href']

    def update(data):
        api_data = api(data['url'], mode = 'xml', params = {
            'format': 'xml',
            'key': config['goodreads']['key'],
        })

        data['name'] = api_data.find('series/title').text.strip()

        data['books'] = {}
        for book_data in api_data.findall('series/series_works/series_work'):
            title, _, index = split_title(book_data.find('work/best_book/title').text.strip())

            try:
                index = book_data.find('user_position').text.split()[0]
            except:
                pass

            if index:
                if index.isdigit():
                    index = int(index)
                elif re.match('^[\d.]+$', index):
                    index = float(index)

            if title and index:
                data['books'][index] = title


        return data

    return get('series', name, search, update)

def get_author(name, url = None):
    '''
    Get an author by name
    '''

    logging.info('get_author({})'.format(name))

    def search(name):
        search_soup = api('search', params = {'q': name, 'search_type': 'books', 'search[field]': 'author'})
        for el_book in search_soup.select('tr[itemscope]'):
            return el_book.select('.authorName')[0].attrs['href'].split('?')[0]

    def update(data):
        soup = api(data['url'])

        if not data.get('name'):
            data['name'] = soup.select('.authorName')[0].text.strip()

        return data

    return get('author', name, search, update)

def reviews(per_page = 20, do_all = False):
    params = {
        'key': config['goodreads']['key'],
        'v': 2,
        'sort': 'date_read',
        'page': 1,
        'per_page': per_page,
        'shelf': 'read',
    }

    def replace_goodreads_links(m):
        text, url = m.groups()
        for type in fields:
            if type in url:
                f = globals()['get_' + type]
                obj = f(url)
                if text == obj['name']:
                    return '{{{{< goodreads {type}="{name}" >}}}}'.format(type = type, name = obj['name'])
                else:
                    return '{{{{< goodreads {type}="{name}" text="{text}" >}}}}'.format(type = type, name = obj['name'], text = text)

    while True:
        print('[Goodreads] Fetching reviews, page {}'.format(params['page']))

        response = requests.get('https://www.goodreads.com/review/list/{}.xml'.format(config['goodreads']['user_id']), params = params)
        tree = xml.etree.ElementTree.fromstring(response.text)

        for review in tree.iter('review'):
            review_id = int(review.find('id').text)
            book = review.find('book')
            book_id = int(book.find('id').text)
            title = book.find('title_without_series').text
            text = review.find('body').text.strip() or None
            rating = int(review.find('rating').text)

            try:
                raw_read_at = review.find('read_at').text or review.find('date_updated').text or review.find('date_added').text
                read_at = email.utils.parsedate(raw_read_at)
                read_at = time.mktime(read_at)
                read_at = datetime.datetime.fromtimestamp(read_at)
            except Exception as ex:
                print('[Goodreads] Failed to parse read at for {}\nException: {}\nread_at: {} (raw: {})'.format(title, ex, read_at, raw_read_at))

            # We started writing reviews in 2015; stop looking for reviews older than that
            if read_at < datetime.datetime(2015, 1, 1):
                return

            data = get_book(book_id)

            if text:
                # If there were spoilers in the original review, we have to fall back to the web version
                if '[spoilers removed]' in text:
                    logging.info('Review for {} contains spoilers, falling back to web scraper'.format(title))
                    response = requests.get('https://www.goodreads.com/review/show/{}'.format(review_id))
                    soup = bs4.BeautifulSoup(response.text, 'html5lib')
                    text = soup.select('.reviewText')[0].prettify()

                # Convert to markdown
                text = markdowner.handle(text)

                # Add the cover on the front
                text = '{{{{< goodreads book="{title}" cover="true" >}}}}\n\n'.format(title = data['name']) + text

                # Fix multiline blockquotes
                text = re.sub(r'^>\s*$', '', text, flags = re.MULTILINE)

                # Fix spacing
                text = re.sub(r'\n\s*\n+', '\n\n', text)
                text = re.sub(r'([^\n])\n([^\n])', r'\1 \2', text)

                # Replace spoilers with shortcodes
                text = re.sub(
                    r'\(view spoiler\)\s*\[\s*(.*?)\s*\(hide spoiler\)\s*\]',
                    r'{{< spoiler >}}\1{{< /spoiler >}}',
                    text,
                )

                # Replace goodreads links with shortcodes
                text = re.sub(
                    r'\[([^\]]*?)\]\(https://www.goodreads.com([^\s]*)(?: ".*?")?\)',
                    replace_goodreads_links,
                    text,
                )

                # Add in a <!--more-->
                # Skip past opening block quotes
                parts = text.split('\n\n')

                more_offset = 3
                while more_offset < len(parts) - 1 and parts[more_offset - 1].startswith('>') and parts[more_offset].startswith('>'):
                    more_offset += 1

                parts.insert(more_offset, '<!--more-->')
                text = '\n\n'.join(parts)

                yield {
                    'review_id': review_id,
                    'book_id': book_id,
                    'title': title,
                    'text': text,
                    'rating': rating,
                    'read_at': read_at,
                }

        page_end_index = int(tree.find('reviews').attrib['end'])
        total_index = int(tree.find('reviews').attrib['total'])
        if page_end_index < total_index:
            params['page'] += 1
        else:
            break

        if not do_all:
            break

if __name__ == '__main__':
    exit_code = 0

    if args.insert:
        print('[Goodreads] Inserting URLs...')
        for url in args.insert:
            for type in fields:
                if type in url:
                    f = globals()['get_' + type]
                    print('Inserted: {} -> {}'.format(url, f(url)))
        print()

    if args.delete:
        print('[Goodreads] Deleting entries...')
        for name in args.delete:
            for type in fields:
                if name in global_data[fields[type]]:
                    id = global_data[fields[type]][name]['id']
                    del global_data[fields[type]][name]
                    del global_data[fields[type] + '-index'][id]
                    print('Delete {} ({}) from {}'.format(name, id, type))
                    save()
        print()

    if args.reviews:
        print('[Goodreads] Generating posts for reviews...')
        if args.reviews.lower() == 'all':
            per_page = 200
        elif args.reviews.isdigit():
            per_page = int(args.reviews)
        else:
            raise arg_parser.error('--reviews must be ALL or an integer')

        if not 1 <= per_page <= 200:
            raise arg_parser.error('--reviews must be in the range 1-200')

        for review in reviews(per_page = per_page, do_all = args.reviews.lower() == 'all'):
            print('-', review['title'], '...', end = ' ')
            data = get_book(review['book_id'])
            date = review['read_at']

            headers = {
                'reviews/lists': ['{year} Book Reviews'.format(year = date.year)],
                'generated': True,
            }

            if data.get('series'):
                headers['reviews/series'] = [data['series']]

            # If we have custom series, add those as well
            for series_name in global_data.get('series-custom', {}):
                if review['title'] in global_data['series-custom'][series_name]:
                    headers.setdefault('reviews/series', []).append(series_name)

            # Make sure the series list is unique
            # Remove any series that we've potentially renamed
            if 'reviews/series' in headers:
                for series_name in global_data.get('series-custom', {}).get('_to_remove', []):
                    if series_name in headers['reviews/series']:
                        headers['reviews/series'].remove(series_name)

                headers['reviews/series'] = list(sorted(set(headers['reviews/series'])))

            content = '''\
---
title: {title}
date: {date}
{headers}---
{text}
'''.format(
    title = review['title'] if ':' not in review['title'] else ('"' + review['title'] + '"'),
    date = date.strftime('%Y-%m-%d'),
    text = review['text'],
    headers = yaml.dump(headers, default_flow_style = False)
)

            filename = '{}-{}.generated.md'.format(
                date.strftime('%Y-%m-%d'),
                slugify(review['title']),
            )
            path = os.path.join('content', 'reviews', 'books', str(date.year), filename)

            if os.path.exists(path) and not args.overwrite:
                print('skipping {}, already exists'.format(path))
            else:
                print('writing {}'.format(path))
                os.makedirs(os.path.dirname(path), exist_ok = True)
                with open(path, 'w') as fout:
                    fout.write(content)

        print()

    if args.add_cover:
        url, title = args.add_cover
        print(f'Downloading cover for {title}: {url}')

        book = get_book(title)
        download_cover(book, url)
        save()

    if args.validate:
        print('[Goodreads] Detecting missing entries...')
        any_missing = False

        for path, _, filenames in os.walk('content'):
            for filename in filenames:
                if not filename.endswith('.md'):
                    continue

                with open(os.path.join(path, filename), 'r') as fin:
                    for raw_params in re.findall('{{<\s*goodreads\s+(.*?)\s*>}}', fin.read()):
                        params = {
                            key: value.strip('"')
                            for key, value in re.findall(r'(.*?)=("(?:[^"\\]|\\.)*"|[^\s]+)', raw_params)
                        }

                        for type in fields:
                            if type in params and params[type] not in global_data[fields[type]]:
                                any_missing = True
                                print('{}: {} not found'.format(type, params[type]))

        print()

        if any_missing:
            exit_code = 1

    sys.exit(exit_code)

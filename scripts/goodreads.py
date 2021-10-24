#!/usr/bin/env python3

import bs4
import click
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

from PIL import Image

import coloredlogs

BYPASS_CACHE = False

markdowner = html2text.HTML2Text()

config = {}
for filename in ['config.yaml', 'secrets.yaml']:
    with open(filename, 'r') as fin:
        config.update(yaml.load(fin, Loader = yaml.Loader))

fields = { # singular: plural
    'book': 'books',
    'author': 'authors',
    'series': 'series',
}

global_data = {}

def load():
    for filename in os.listdir(os.path.join('data', 'goodreads')):
        path = os.path.join('data', 'goodreads', filename)
        name = filename.rsplit('.', )[0]

        logging.debug(f'Loading data from {path} into global_data[{name}]')
        with open(path, 'r') as fin:
            global_data[name] = yaml.load(fin, Loader = yaml.Loader)

    for _, plural in fields.items():
        if plural not in global_data:
            global_data[plural] = {}

def save():
    for name in global_data:
        path = os.path.join('data', 'goodreads', name + '.yaml')

        logging.debug(f'Saving data from global_data[{name}] into {path}')
        with open(path, 'w') as fout:
            yaml.dump(global_data[name], fout, default_flow_style = False)

def api(url, params = None, mode = 'soup'):
    '''Make a goodreads web request.'''

    url = url.lstrip('/')
    if not url.startswith('http'):
        url = 'https://www.goodreads.com/' + url

    logging.info(f'api({url}, {params})')

    response = requests.get(url, params = params)

    if mode == 'soup':
        return bs4.BeautifulSoup(response.text, 'html5lib')
    elif mode == 'xml':
        return xml.etree.ElementTree.fromstring(response.text)
    else:
        raise Exception(f'Unkonwn API mode: {mode}')


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
    logging.debug(f'split_title({text})')

    # Fallback, no series
    title, series, index = text, None, None

    m_part = re.match(r'^(.*?), [Pp]art (\d+) of (\d+)$', text)
    m_series_index = re.match(r'^(.*?) \((.*?),?\s+#?([\d.-]+)\)$', text)
    m_series_no_index = re.match(r'^(.*?) \((.*?)\)', text)

    # Syntax with part m of n
    if m_part:
        logging.debug(f'split_title({text}), matching part')
        series, index, _ = m_part.groups()

    # Syntax with paran'ed series and and index
    elif m_series_index:
        logging.debug(f'split_title({text}), matching paran and index')
        title, series, index = m_series_index.groups()

    # Paran'ed series but no index
    elif m_series_no_index:
        logging.debug(f'split_title({text}), matching paran with no index')
        title, series = m_series_no_index.groups()

    # If the index looks like a int/float, convert to that
    if index:
        if isinstance(index, int) or index.isdigit():
            index = int(index)
        elif re.match('^[\d.]+$', index):
            index = float(index)

    logging.debug(f'split_title({text}) -> {title}, {series}, {index}')
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

    logging.debug(f'clean_url({url}) -> {clean_url}')
    return clean_url

def id_to_url(type, id, name = None):
    '''Build a URL from and ID.'''

    for singular, plural in fields.items():
        if type == plural:
            type = singular

    clean_name = slugify(name) if name else type

    if type == 'series':
        url = f'/{type}/{id}.{clean_name}'
    else:
        url = f'/{type}/show/{id}.{clean_name}'

    logging.debug(f'id_to_url({type}, {id}, {name}) -> {url}')
    return url

def url_to_id(url):
    '''Pull an ID out of a url.'''

    id = int(re.search(r'/(\d+)(?:[^/]*)$', url).group(1))
    logging.debug(f'url_to_id({url}) -> {id}')
    return id

def get(type, query, search_function, update_function):
    '''
    Get a book/series/author.

    search_function takes a name and returns a url for the object
    update_function takes a data array and returns a data array (with more stuff in it)
    '''

    global global_data

    id = url = name = None
    if type in fields:
        type = fields[type]

    logging.debug(f'get({type}, {query})')

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
        name = global_data[type + '-index'][id]
        logging.debug(f'get({type}, {query}), got name by id: {id} = {name}')
        
    # If the title is already cached, load from there
    if BYPASS_CACHE:
        logging.debug(f'get({type}, {query}), caching disabled, loading {name} directly')
    else:
        if name in global_data[type]:
            logging.debug(f'get({type}, {query}), loaded {name} from cache')
            return global_data[type][name]
        else:
            logging.debug(f'get({type}, {query}), name {name} is not in cache, using api')

    # Otherwise, load the data from goodreads
    data = {}

    if name and not url:
        logging.debug(f'get({type}, {query}), finding by name: {name}')
        url = search_function(name)
        if url:
            logging.debug(f'get({type}, {query}), url is {url}')
        else:
            raise Exception(f'No results found when searching for {type}: {name}')

    url = clean_url(url)
    id = url_to_id(url)

    data['id'] = id
    data['name'] = name
    data['url'] = url

    data = update_function(data)

    data['url'] = id_to_url(type, data['id'], data['name'])

    logging.debug(f'get({type}, {query}), result: {data}')
    global_data[type][data['name']] = data
    global_data.setdefault(type + '-index', {})[data['id']] = data['name']
    save()

    return data

def download_cover(data, image_url):
    '''
    Download and resize a cover to a specific path.
    '''

    logging.debug(f'Attempting to download cover: {image_url}')
    data['cover'] = image_url
    response = requests.get(data['cover'], stream = True)
    response.raw.decode_content = True

    if response:
        slug = slugify(data["name"])
        extension = data["cover"].split(".")[-1].lower()

        filename = f'{slug}.{extension}'
        path = os.path.join('static', 'embeds', 'books', filename)

        if os.path.exists(path):
            logging.debug(f'Cover already downloaded for {data["name"]}')
        else:
            logging.debug(f'Downloading cover for {data["name"]}')
            os.makedirs(os.path.dirname(path), exist_ok = True)

            image = Image.open(response.raw)
            image = image.resize((100, 160))
            image.save(path)

        data['localCover'] = path.replace('static', '')
    else:
        logging.warning(f'Failed to download cover for {data["name"]}')

def get_book(query):
    '''
    Get a book. If we're provided a title and the book isn't in the cache, search.
    '''

    logging.debug(f'get_book({query})')

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
                series_url = f'/series/{series_id}'
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
                logging.warning(f'Missing cover for: {title}')
            else:
                download_cover(data, image_url)

        return data

    return get('book', query, search, update)

def get_series(name):
    '''
    Get a series by title.

    TODO: Search by title if the series isn't cached and the url isn't provided.
    '''

    logging.debug(f'get_series({name})')

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
                if isinstance(index, int) or index.isdigit():
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

    logging.debug(f'get_author({name})')

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
                    return f'{{{{< goodreads {type}="{obj["name"]}" >}}}}'
                else:
                    return f'{{{{< goodreads {type}="{obj["name"]}" text="{text}" >}}}}'

    def make_replace_goodreads_images(title):
        counter = {'x': 0}

        def f(m):
            alt, url = m.groups()
            url = url.replace(' ', '')
            counter['x'] += 1

            name = slugify(alt or f'{title} {counter}')
            extension = url.split(".")[-1].lower()

            filename = f'{name}.{extension}'
            path = os.path.join('static', 'embeds', 'books', 'attachments', filename)

            if not os.path.exists(path):
                logging.debug(f'Attempting to download image: {url}')
                response = requests.get(url, stream = True)
                response.raw.decode_content = True

                os.makedirs(os.path.dirname(path), exist_ok = True)

                with open(path, 'wb') as fout:
                    shutil.copyfileobj(response.raw, fout)

            return f'![{alt}](/embeds/books/attachments/{filename})'

        return f

    while True:
        logging.info(f'[Goodreads] Fetching reviews, page {params["page"]}')

        response = requests.get(f'https://www.goodreads.com/review/list/{config["goodreads"]["user_id"]}.xml', params = params)
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
                logging.warning(f'[Goodreads] Failed to parse read at for {title}\nException: {ex}\nread_at: {read_at} (raw: {raw_read_at})')

            # We started writing reviews in 2015; stop looking for reviews older than that
            if read_at < datetime.datetime(2015, 1, 1):
                return

            data = get_book(book_id)

            if text:
                # If there were spoilers in the original review, we have to fall back to the web version
                if '[spoilers removed]' in text:
                    logging.debug(f'Review for {title} contains spoilers in {review_id=}, falling back to web scraper')
                    response = requests.get(f'https://www.goodreads.com/review/show/{review_id}')
                    soup = bs4.BeautifulSoup(response.text, 'html5lib')
                    text = soup.select('.reviewText')[0].prettify()

                # Convert to markdown
                text = markdowner.handle(text)

                # Add the cover on the front
                text = f'{{{{< goodreads book="{data["name"]}" cover="true" >}}}}\n\n' + text

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

                # Download and replace embedded images
                text = re.sub(
                    r'!\[([^\]]*?)\]\(([^\)]*?)\)',
                    make_replace_goodreads_images(data['name']),
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

# ----- CLI -----

@click.group()
@click.option('-v', '--verbose', count = True, help = 'How verbose to be (multiple levels available -vvv)')
@click.option('--disable-cache', is_flag = True, help = 'Load all information from goodreads')
def goodreads(verbose, disable_cache = False):
    '''Import information from goodreads.'''

    if verbose:
        coloredlogs.install(
            level = 'INFO' if verbose == 1 else 'DEBUG',
            fmt = '%(asctime)s %(levelname)s %(message)s'
        )
    
    if verbose > 2:
        logging.warning('Maximum verbosity is 2')

    if disable_cache:
        logging.warning('Disabling cache')

        global BYPASS_CACHE
        BYPASS_CACHE = True

    load()

@goodreads.command()
@click.argument('urls', nargs = -1)
def insert(urls):
    '''Insert a goodreads url into the local database.'''

    click.echo(f'[Goodreads] Inserting {len(urls)} URL(s)...')
    for url in urls:
        for type in fields:
            if type in url:
                f = globals()['get_' + type]
                result = f(url)
                logging.info(f'Inserted: {url} -> {result}')

@goodreads.command()
@click.argument('names', nargs = -1)
def delete(names):
    '''Delete an entry from the local database (all exact matches will be deleted).'''

    global global_data

    click.echo(f'[Goodreads] Deleting {len(names)} entry/entries...')
    for name in names:
        for type in fields:
            if name in global_data[fields[type]]:
                id = global_data[fields[type]][name]['id']
                del global_data[fields[type]][name]
                del global_data[fields[type] + '-index'][id]
                logging.info(f'Deleted {name} ({id}) from {type}')
                save()

@goodreads.command(name = 'import')
@click.option('--all', is_flag = True, help = 'Load all posts')
@click.option('--overwrite', is_flag = True, help = 'Overwrite all existing posts with new generated posts')
@click.argument('per_page', type = int, default = 20)
def import_reviews(all, overwrite, per_page):
    '''
    Import reviews from goodreads.
    
    Will load [per_page] entries at a time. If --all is not set, will stop after the first page where no posts are generated.
    '''

    global global_data

    click.echo('[Goodreads] Generating posts for reviews...')
    if all:
        per_page = 200
    
    if not 1 <= per_page <= 200:
        raise click.ClickException('Cannot load more than 200 reviews per page')

    for review in reviews(per_page = per_page, do_all = all):
        logging.info(f'- {review["title"]}')
        data = get_book(review['book_id'])
        date = review['read_at']

        headers = {
            'reviews/lists': [f'{date.year} Book Reviews'],
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

        title = review['title'] if ':' not in review['title'] else ('"' + review['title'] + '"')
        formatted_date = date.strftime('%Y-%m-%d')
        text = review['text']
        headers = yaml.dump(headers, default_flow_style = False)

        content = f'''\
---
title: {title}
date: {date}
{headers}---
{text}
'''

        date_string = date.strftime('%Y-%m-%d')
        slug = slugify(review['title'])

        filename = f'{date_string}-{slug}.md'
        path = os.path.join('content', 'reviews', 'books', str(date.year), filename)

        if os.path.exists(path) and not overwrite:
            logging.info(f'skipping {path}, already exists')
        else:
            logging.info(f'writing {path}')
            os.makedirs(os.path.dirname(path), exist_ok = True)
            with open(path, 'w') as fout:
                fout.write(content)

@goodreads.command()
@click.option('--url', default = None)
@click.option('--title', default = None)
@click.option('-i', '--interactive', is_flag = True)
def cover(url, title, interactive):
    '''Download new covers that Goodreads couldn't find.'''

    while True:
        if not url: 
            url = click.prompt('Cover image URL').strip()

        if not title:
            title = click.prompt('Book title').strip()

        book = get_book(title)
        logging.info(f'Downloading cover for {title}: {url}')
        download_cover(book, url)
        save()

        if interactive and click.confirm('Add another cover?'):
            url = title = None
            continue
        else:
            break   

@goodreads.command()
def validate():
    click.echo('[Goodreads] Detecting missing entries...')
    any_missing = False

    global global_data

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
                            logging.warning(f'{type}: {params[type]} not found')

    if any_missing:
        logging.warning('Entries missing')

if __name__ == '__main__':
    goodreads()

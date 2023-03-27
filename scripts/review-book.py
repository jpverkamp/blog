import atexit
import bs4
import coloredlogs
import datetime
import json
import logging
import os
import re
import readline
import requests
import subprocess
import urllib.parse
import yaml

from PIL import Image

TARGET_COVER_SIZE = (214, 317)
BLOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COVER_DIR = os.path.join(BLOG_DIR, 'static', 'embeds')
REVIEW_BASE_DIR = os.path.join(BLOG_DIR, 'content', 'reviews')
GOODREADS = 'https://www.goodreads.com/'

coloredlogs.install(logging.INFO)

histfile = os.path.join(os.path.expanduser("~"), ".blog.review-book.history")
try:
    readline.read_history_file(histfile)
    readline.set_history_length(1000)
except FileNotFoundError:
    pass
atexit.register(readline.write_history_file, histfile)


while True:
    date = str(datetime.date.today())
    date = input(f'Date for review (default {date}): ') or date
    year = date[:4]

    title = input('Title (or legacy ID): ').strip()

    # If we have an ID, just directly use that
    if title.isdigit():
        id = int(title)

    # Otherwise, use the HTML based search
    # I haven't found a graphql search yet
    else:
        response = requests.get(urllib.parse.urljoin(GOODREADS, '/search'), params={'q': title})
        soup = bs4.BeautifulSoup(response.text, features='html.parser')

        urls = []
        for i, el in enumerate(soup.select('a.bookTitle'), 1):
            title = el.text.strip()
            author = el.parent.select_one('a.authorName').text.strip()

            print(f'{i}: {title} by {author}')
            urls.append(el.attrs['href'])

        choice = input('Choose a book (leave blank to skip and quit): ')
        if not choice:
            break
        if not choice.isdigit():
            print('Enter a number')
            continue

        url = urls[int(choice) - 1]
        id = int(url.split('/')[-1].split('.')[0].split('-')[0])

    # Use my goodreads (gr) command line tool to fetch via graphql
    output = subprocess.check_output(['gr', 'book', '--legacy', str(id)])
    book = json.loads(output)

    # Set basic headers not from goodreads
    data = {}
    data['date'] = date
    data['rating'] = -1
    data['goodreads_id'] = id
    data['reviews/lists'] = [f'{year} Book Reviews']
    data['draft'] = True

    # Copy over title and author
    data['title'] = book['title']

    data['reviews/authors'] = [
        book['primaryContributorEdge']['node']['name']
    ]

    # NOTE: This doesn't currently work, gr author is not supported as there isn't graphql for it
    # for id in book['contributors']:
    #     output = subprocess.check_output(['gr', 'author', id])
    #     author = json.loads(output)
    #     print(data, author, id)

    #     if author['name'] not in data['reviews/authors']:
    #         name = author['name']

    #         name = re.sub('\s+', ' ', name)
    #         name = name.strip()

    #         data['reviews/authors'].append(name)

    # Add series data (if any is set)
    if book.get('bookSeries'):
        for series in book['bookSeries']:
            series_title = series['title']

            # Don't care about this for graphic novels/comics
            if ' (Single Issues)' in series_title:
                continue

            # Because we don't have single issues, combine this
            series_title = series_title.replace(' (Collected Editions)', '')
            data.setdefault('reviews/series', []).append(series_title)

            # Set a series index typed to int/float if possible; default to 0 for none
            if index := series.get('seriesPlacement'):
                if index.isdigit():
                    index = int(index)
                else:
                    try:
                        index = float(index)
                    except ValueError:
                        pass
            else:
                index = 0

            data.setdefault('series_index', []).append(index)

    # Save the cover
    if cover_url := book['imageUrl']:
        cover_filename = re.sub('[^a-z0-9-]+', '-', data['title'].lower()).strip('-') + '.jpg'
        cover_path = os.path.join(COVER_DIR, 'books', cover_filename)
        logging.info(f'- Saving cover {cover_filename} <- {cover_url}')

        image = Image.open(requests.get(cover_url, stream=True).raw)
        image = image.resize(TARGET_COVER_SIZE)
        image = image.convert('RGB')
        image.save(cover_path)

        data['cover'] = f'/embeds/books/{cover_filename}'

    # Generate the path based on author,series,title (if set)
    path_parts = [REVIEW_BASE_DIR, 'books']
    if data.get('reviews/authors'):
        path_parts.append(data['reviews/authors'][0])

    if data.get('reviews/series'):
        path_parts.append(data['reviews/series'][0])
        path_parts.append(f'{data["series_index"][0]} - {data["title"]}.md')
    else:
        path_parts.append(f'{data["title"]}.md')

    path = os.path.join(*path_parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Actually write out what we have
    logging.info(f'- Writing entry: {path}')
    with open(path, 'w') as f:
        f.write(f'---\n{yaml.dump(data)}---\n')

    choice = input('Another? [yN] ')
    if not (choice and choice.lower().startswith('y')):
        break

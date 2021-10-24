import coloredlogs
import datetime
import json
import logging
import os
import yaml

import goodreads

from PIL import Image

coloredlogs.install(logging.INFO)

TARGET_COVER_SIZE = (214, 317)
BLOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COVER_DIR = os.path.join(BLOG_DIR, 'static', 'embeds')
REVIEW_BASE_DIR = os.path.join(BLOG_DIR, 'content', 'reviews')

goodreads.load()

while True:
    date = str(datetime.date.today())
    date = input(f'Date for review (default {date}): ') or date
    year = date[:4]

    title = input('Title: ')

    print()
    book = goodreads.get_book(title)
    print(book)
    print()

    headers = {
        'reviews/lists': [f'{year} Book Reviews'],
    }

    if book.get('series'):
        headers['reviews/series'] = [book['series']]

    # Make sure the series list is unique
    if 'reviews/series' in headers:
        headers['reviews/series'] = list(sorted(set(headers['reviews/series'])))

    headers = yaml.dump(headers, default_flow_style=False)

    content = f'''\
---
title: {json.dumps(book['name'])}
date: {date}
{headers}---
{{{{< goodreads book="{book['name']}" cover="true" >}}}}
'''

    slug = goodreads.slugify(book['name'])
    filename = f'{date}-{slug}.md'
    path = os.path.join('content', 'reviews', 'books', year, filename)

    logging.info(f'writing {path}')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fout:
        fout.write(content)

    if not input('Create another post? (yN) ').lower().startswith('y'):
        break
    print()

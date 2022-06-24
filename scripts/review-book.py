import requests
import bs4
import coloredlogs
import datetime
import logging
import os
import re
import urllib.parse
import yaml

from PIL import Image

coloredlogs.install(logging.INFO)

TARGET_COVER_SIZE = (214, 317)
BLOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COVER_DIR = os.path.join(BLOG_DIR, 'static', 'embeds')
REVIEW_BASE_DIR = os.path.join(BLOG_DIR, 'content', 'reviews')
GOODREADS = 'https://www.goodreads.com/'

while True:
    date = str(datetime.date.today())
    date = input(f'Date for review (default {date}): ') or date
    year = date[:4]

    title = input('Title: ').strip()

    response = requests.get(urllib.parse.urljoin(GOODREADS, '/search'), params={'q': title})
    soup = bs4.BeautifulSoup(response.text, features='lxml')

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

    url = urllib.parse.urljoin(GOODREADS, urls[int(choice) - 1])
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, features='lxml')

    data = {}
    data['date'] = date
    data['rating'] = -1

    # Check for different AB Tests
    if title_el := soup.select_one('#bookTitle'):
        logging.info('- Loading data in old format')
        data['title'] = title_el.text.strip()

        if series_el := soup.select_one('#bookSeries'):
            if series_el.text.strip():
                print(series_el.text.strip().strip('()'))
                series, index = series_el.text.strip().strip('()').rsplit('#', 1)
                series = series.strip()
                index = index.strip()

                if index.isdigit():
                    index = int(index)
                else:
                    try:
                        index = float(index)
                    except ValueError:
                        pass

                data['reviews/series'] = [series]
                data['series_index'] = [index]

        data['reviews/authors'] = [
            el.text.strip()
            for el in soup.select('a.authorName')
        ]

        for row in soup.select('#bookDataBox > div'):
            if el := row.select_one('.infoBoxRowTitle'):
                if el.text.strip().lower() == 'isbn':
                    value = row.select_one('.infoBoxRowItem').text.strip()
                    data['isbn'] = value.split()[0]

                    if 'isbn13' in value.lower():
                        data['isbn13'] = value.split()[-1].strip(')')

        data['page_count'] = int(soup.select_one('[itemprop="numberOfPages"]').text.strip().split()[0])

        cover_url = soup.select_one('.bookCoverPrimary img').attrs['src']
        cover_filename = re.sub('[^a-z0-9-]+', '-', data['title'].lower()).strip('-') + '.jpg'
        cover_path = os.path.join(COVER_DIR, 'books', cover_filename)
        logging.info(f'- Saving cover {cover_filename} <- {cover_url}')

        image = Image.open(requests.get(cover_url, stream=True).raw)
        image = image.resize(TARGET_COVER_SIZE)
        image.save(cover_path)

        data['cover'] = f'/embeds/books/{cover_filename}'

    elif title_el := soup.select_one('h1[data-testid="bookTitle"]'):
        logging.warning('- Loading data from new format')
        logging.warning('- Not sure how to process this yet')
        break

        data['title'] = title_el.text.strip()

    else:
        logging.warning('- Unknown page format')
        break

    data['goodreads_id'] = int(url.split('/')[-1].split('-')[0].split('.')[0])
    data['reviews/lists'] = [f'{year} Book Reviews']
    data['draft'] = True

    path_parts = [REVIEW_BASE_DIR, 'books', data['reviews/authors'][0]]

    if data['reviews/series']:
        path_parts.append(data['reviews/series'][0])
        path_parts.append(f'{data["series_index"][0]} - {data["title"]}.md')
    else:
        path_parts.append(f'{data["title"]}.md')

    path = os.path.join(*path_parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    logging.info(f'- Writing entry: {path}')
    with open(path, 'w') as f:
        f.write(f'---\n{yaml.dump(data)}---\n')

    choice = input('Another? [yN] ')
    if not (choice and choice.lower().startswith('y')):
        break

import coloredlogs
import datetime
import imdb
import logging
import os
import re
import requests
import yaml

from PIL import Image

# TODO: Automatically add reviews to lists

coloredlogs.install(logging.INFO)

api = imdb.Cinemagoer()

TARGET_COVER_SIZE = (214, 317)
BLOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COVER_DIR = os.path.join(BLOG_DIR, 'static', 'embeds')
REVIEW_BASE_DIR = os.path.join(BLOG_DIR, 'content', 'reviews')


def slugify(text):
    return re.sub('[^a-z0-9-]+', '-', text.lower()).strip('-')


while True:
    date = str(datetime.date.today())
    date = input(f'Date for review (default {date}): ') or date
    year = date[:4]

    title = input('Title: ')

    if title.startswith('tt'):
        movie = api.get_movie(title[2:])

    else:
        print()
        movies = api.search_movie(title)
        for i, movie in enumerate(movies[:10], 1):
            print(i, f'{movie.get("title")} ({movie.get("year")}, {movie.get("kind")}) ')
        choice = input('Selection (1-10, leave blank to skip): ')
        print()

        try:
            choice = int(choice) - 1
            if choice < 0 or choice >= 10:
                raise ValueError('Out of bounds')
        except ValueError:
            print('Invalid choice')
            print()
            continue

        movie = movies[choice]

    more_data = api.get_movie(movie.getID())

    additional_headers = {}
    keys = {
        'imdbID': 'imdb_id',
        'year': 'reviews/year',
        'director': 'reviews/directors',
        'writer': 'reviews/writers',
        'composer': 'reviews/composers',
        'cinematographer': 'reviews/cinematographers',
        'editor': 'reviews/editors',
    }
    for key, header_key in keys.items():
        if key not in more_data:
            continue

        value = more_data[key]

        if isinstance(value, list):
            value2 = []
            for v in value:
                v = str(v)

                if v == 'None' or v == '':
                    continue
                if v in value2:
                    continue

                value2.append(v)
            value = value2

        additional_headers[header_key] = value

    additional_headers['reviews/cast'] = {person['name']: str(person.currentRole) for person in more_data['cast']}

    # Ask for series information
    series_input = input('Part of a series? (ex "The Matrix #1" (multiple comma delimited) or leave blank to skip) ')
    if series_input:
        additional_headers['reviews/series'] = []
        additional_headers['series_index'] = []

        for series in series_input.split(','):
            series_index = series.strip().split(' #')

        series, index = series.split(' #')
        series = series.strip()

        if index.isdigit():
            index = int(index)
        else:
            try:
                index = float(index)
            except ValueError:
                pass

        additional_headers['reviews/series'].append(series)
        additional_headers['series_index'].append(index)
    else:
        series = None

    # Potentially fix the title provided if it's not a perfect match
    if title != movie['title']:
        if input(f'{title} doesn\'t match {movie["title"]}, update? (yN) ').lower().startswith('y'):
            title = movie['title']

    slug = slugify(title)

    # Determine which type of content we're talking about
    content_type = 'movies'
    if 'tv' in movie.get('kind'):
        content_type = 'tv'

    # Download cover
    cover_url = movie['full-size cover url']
    cover_filename = slug + '.jpg'
    logging.info(f'Saving cover {cover_filename} <- {cover_url}')

    image = Image.open(requests.get(cover_url, stream=True).raw)
    image = image.resize(TARGET_COVER_SIZE)
    image.save(os.path.join(COVER_DIR, content_type, cover_filename))

    # Create post
    if content_type == 'tv':
        review_dir = os.path.join(REVIEW_BASE_DIR, 'tv')
        review_filename = f'{title}.md'
    else:
        if series:
            review_dir = os.path.join(REVIEW_BASE_DIR, content_type, series)
            review_filename = f'{index} - {title}.md'

        else:
            review_dir = os.path.join(REVIEW_BASE_DIR, content_type)
            review_filename = f'{title}.md'

    os.makedirs(review_dir, exist_ok=True)

    if os.path.exists(os.path.join(review_dir, review_filename)):
        if not input(f'{review_filename} already exists, overwrite? (yN) ').lower().startswith('y'):
            continue

    logging.info(f'Generating post {review_filename}')

    with open(os.path.join(review_dir, review_filename), 'w') as fout:
        fout.write(f'''---
title: "{title}"
date: {date}
draft: True
cover: /embeds/{content_type}/{slug}.jpg
reviews/lists:
- {year} {"TV" if content_type == "tv" else "Movie"} Reviews
{yaml.dump(additional_headers)}---
''')
    print()

    if not input('Create another post? (yN) ').lower().startswith('y'):
        break
    print()

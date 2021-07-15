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

api = imdb.IMDb()

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
    else:
        review_dir = os.path.join(REVIEW_BASE_DIR, content_type, year)

    os.makedirs(review_dir, exist_ok=True)
    
    review_filename = f'{date}-{slug}.md'  
    if os.path.exists(os.path.join(review_dir, review_filename)):
        if not input(f'{review_filename} already exists, overwrite? (yN) ').lower().startswith('y'):
            continue

    logging.info(f'Generating post {review_filename}')

    with open(os.path.join(review_dir, review_filename), 'w') as fout:
        fout.write(f'''---
title: "{title}"
date: {date}
reviews/lists:
- {year} Movie Reviews
''')
        #yaml.dump({'data': {'imdb': dict(movie)}}, fout, default_flow_style=False)
        fout.write(f'''---
{{{{< figure class="cover-image" src="/embeds/{content_type}/{slug}.jpg" >}}}}

''')
    print()

    if not input('Create another post? (yN) ').lower().startswith('y'):
        break
    print()

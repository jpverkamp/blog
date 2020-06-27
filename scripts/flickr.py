#!/usr/bin/env python3

import click
import datetime
import itertools
import flickrapi
import os
import re
import sys
import tqdm
import yaml

PATH_PHOTOS = os.path.join('data', 'flickr', 'photos.yaml')
PATH_PHOTOSETS = os.path.join('data', 'flickr', 'sets', '{id}.yaml')

DELFIELDS_PHOTOS = ['isfamily', 'isfriend', 'ispublic', 'owner']
DELFIELDS_PHOTOSETS = [
    'can_comment', 'needs_interstitial', 'username', 'videos', 'visibility_can_see_set',
    'count_comments', 'count_photos', 'count_videos', 'count_views',
]

GENERATED_POST_TEMPLATE = '''\
---
title: "{title}"
date: {date}
photography/types:
- Flickr Album
generated: true
---
{description}

{{{{< flickr set="{id}" >}}}}
'''

def fix_content_objects(obj):
    '''Fix a nested dictionary so that {key: {_content: abc}} becomes {key: abc}'''

    if isinstance(obj, dict) and len(obj) == 1 and '_content' in obj:
        return obj['_content']
    elif isinstance(obj, dict):
        return {key: fix_content_objects(obj[key]) for key in obj}
    elif isinstance(obj, list):
        return [fix_content_objects(each) for each in obj]
    else:
        return obj

@click.command()
@click.option('--generate', is_flag = True, help = 'Generate blog posts automatically')
@click.option('--overwrite', is_flag = True, help = 'Overwrite existing posts (implies --generate)')
def flickr(generate = False, overwrite = False, all = False):
    '''Import information from flickr.'''

    if overwrite:
        generate = True
    


    config = {}
    for filename in ['config.yaml', 'secrets.yaml']:
        with open(filename, 'r') as fin:
            config.update(yaml.load(fin, Loader = yaml.Loader))

    post_date_path = os.path.join('data', 'flickr', 'post-dates.yaml')
    if os.path.exists(post_date_path):
        with open(post_date_path, 'r') as fin:
            post_dates = yaml.load(fin, Loader = yaml.Loader)
    else:
        post_dates = {}

    print('[Flickr] Authenticating')
    flickr = flickrapi.FlickrAPI(config['flickr']['key'], config['flickr']['secret'], cache = True, format = 'parsed-json')

    thumbnail_sizes = {
        'square': 's', # 75x75
        'thumbnail': 't', # max 100
        'small': 'm', # max 240
        'medium': 'z', # max 640
        'large': 'b', #max 1024
    }

    cache_paths = [
        ('_cache', 'photosets'),
    ]
    for cache_path in cache_paths:
        try:
            os.makedirs(os.path.join(*cache_path))
        except:
            pass

    # s	small square 75x75
    # t	thumbnail, 100 on longest side
    # m	small, 240 on longest side
    # z	medium 640, 640 on longest side
    # b	large, 1024 on longest side*

    user = flickr.people.findByUsername(username = config['flickr']['username'])
    user_id = user['user']['id']

    # --- Import individual pictures ---
    if os.path.exists(PATH_PHOTOS):
        with open(PATH_PHOTOS, 'r') as fin:
            photo_data = yaml.safe_load(fin) 
    else:
        photo_data = {}

    with tqdm.tqdm(desc = '[Flickr] Loading photos') as progress:
        for page in itertools.count(1):
            progress.update(1)

            response = flickr.people.getPhotos(
                user_id = user_id,
                page = page,
                privacy_filter = 1,
                extras = 'description,date-upload,date-taken',
            )['photos']
            progress.total = response['pages']

            for photo in response['photo']:
                photo = fix_content_objects(photo)

                # Remove fields we don't care about
                for key in DELFIELDS_PHOTOS:
                    if key in photo:
                        del photo[key]
                
                # Add a few fields that are useful to precalculate
                photo['url'] = 'https://farm{farm}.staticflickr.com/{server}/{id}_{secret}.jpg'.format(**photo)
                photo['thumbnails'] = {
                    name: 'https://farm{farm}.staticflickr.com/{server}/{id}_{secret}_{size}.jpg'.format(size = size, **photo)
                    for name, size in thumbnail_sizes.items()
                }
                photo['page'] = 'https://www.flickr.com/photos/{username}/{photo_id}'.format(
                    username = config['flickr']['username'],
                    photo_id = photo['id'],
                )
                
                photo_data[photo['id']] = photo

            if page >= response['pages']:
                break

    with open(PATH_PHOTOS, 'w') as fout:
        yaml.dump(photo_data, fout, default_flow_style = False)

    # --- Import photosets ---
    print('[Flickr] Collecing photosets')
    raw_photosets = []
    for page in itertools.count(1):
        response = flickr.photosets.getList(user_id = user_id)['photosets']
        raw_photosets += response['photoset']
        if page >= response['pages']:
            break

    for photoset in tqdm.tqdm(raw_photosets, desc = '[Flickr] Importing photosets'):
        photoset = fix_content_objects(photoset)
        path = PATH_PHOTOSETS.format(**photoset)

        # Remove fields we don't care about
        for key in DELFIELDS_PHOTOSETS:
            if key in photo:
                del photo[key]

        # Check if we've cached this photoset (avoids one call per photoset)
        if os.path.exists(path):
            with open(path, 'r') as fin:
                cached_photoset = yaml.load(fin, Loader = yaml.Loader)

            if int(cached_photoset['date_update']) >= int(photoset['date_update']):
                continue
        
        # Add IDs of photos in that set
        photoset['photos'] = []
        photos = flickr.photosets.getPhotos(user_id = user_id, photoset_id = photoset['id'])
        for photo in photos['photoset']['photo']:
            photoset['photos'].append(photo['id'])

        os.makedirs(os.path.dirname(path), exist_ok = True)
        with open(path, 'w') as fout:
            yaml.dump(photoset, fout, default_flow_style = False)
    print()

    # TODO: Generate posts based on this data
    # NOTE: I don't know if I actually want to do this, since I don't have the date that I actually took the pictures available

    if generate:
        print('[Flickr] Generating posts...')
        for filename in os.listdir(os.path.join('data', 'flickr', 'sets')):
            with open(os.path.join('data', 'flickr', 'sets', filename), 'r') as fin:
                photoset = yaml.load(fin, Loader = yaml.Loader)

            photoset_id = int(photoset['id'])

            if photoset_id in post_dates:
                date_created = datetime.datetime.strptime(post_dates[photoset_id], '%Y-%m-%d')
            else:
                date_created = datetime.datetime.fromtimestamp(int(photoset['date_create']))

            slug = re.sub('[^a-z0-9-]+', '-', photoset['title'].lower()).strip('-')
            filename = '{}-{}.md'.format(date_created.strftime('%Y-%m-%d'), slug)
            path = os.path.join('content', 'photography', str(date_created.year), filename)

            print('{}'.format(photoset['title'], path), end = '... ')

            if not os.path.exists(path) or overwrite:
                os.makedirs(os.path.dirname(path), exist_ok = True)
                with open(path, 'w') as fout:
                    fout.write(GENERATED_POST_TEMPLATE.format(
                        date = date_created,
                        title = photoset['title'],
                        description = photoset.get('description', ''),
                        id = photoset['id'],
                ))
        print()

if __name__ == '__main__':
    flickr()
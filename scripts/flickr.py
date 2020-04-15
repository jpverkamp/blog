#!/usr/bin/env python3

import click
import datetime
import flickrapi
import os
import re
import yaml

@click.command()
@click.option('--generate', is_flag = True, help = 'Generate blog posts automatically')
@click.option('--overwrite', is_flag = True, help = 'Overwrite existing posts (implies --generate)')
def flickr(generate = False, overwrite = False):
    '''Import information from flickr.'''

    if overwrite:
        generate = True
    
    generated_post_template = '''\
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
    thumbnail_size = 'm'

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

    user = flickr.people.findByUsername(username = config['flickr']['username'])
    user_id = user['user']['id']

    raw_photosets = flickr.photosets.getList(user_id = user_id)

    if raw_photosets['photosets']['pages'] != 1:
        raise Exception('Cannot currently deal with multiple pages')

    # Import flickr data
    print('[Flickr] Importing photosets...')
    for photoset in sorted(raw_photosets['photosets']['photoset'], key = lambda ps: int(ps['date_create'])):
        photoset = fix_content_objects(photoset)
        photoset_path = os.path.join('data', 'flickr', 'sets', '{}.yaml'.format(photoset['id']))

        # Check if we've cached this photoset
        if os.path.exists(photoset_path):
            with open(photoset_path, 'r') as fin:
                cached_photoset = yaml.load(fin, Loader = yaml.Loader)

            if int(cached_photoset['date_update']) < int(photoset['date_update']):
                print(photoset['id'], photoset['title'], 'already exists but out of date')
            else:
                print(photoset['id'], photoset['title'], 'already exists and up to date')
                continue

        # Override the default information with more useful information
        print(photoset['id'], photoset['title'], 'downloading...')
        photoset['photos'] = []
        photos = flickr.photosets.getPhotos(user_id = user_id, photoset_id = photoset['id'])
        for photo in photos['photoset']['photo']:
            photo = fix_content_objects(photo)

            photo['url'] = 'https://farm{farm}.staticflickr.com/{server}/{id}_{secret}.jpg'.format(**photo)
            photo['thumbnails'] = {
                name: 'https://farm{farm}.staticflickr.com/{server}/{id}_{secret}_{size}.jpg'.format(size = size, **photo)
                for name, size in thumbnail_sizes.items()
            }
            photo['page'] = 'https://www.flickr.com/photos/{username}/{photo_id}/in/album-{photoset_id}/'.format(
                username = config['flickr']['username'],
                photo_id = photo['id'],
                photoset_id = photoset['id'],
            )

            photoset['photos'].append(photo)

        os.makedirs(os.path.dirname(photoset_path), exist_ok = True)
        with open(photoset_path, 'w') as fout:
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

            if os.path.exists(path) and not overwrite:
                print('already exists, skipping')
            else:
                os.makedirs(os.path.dirname(path), exist_ok = True)
                with open(path, 'w') as fout:
                    fout.write(generated_post_template.format(
                        date = date_created,
                        title = photoset['title'],
                        description = photoset.get('description', ''),
                        id = photoset['id'],
                ))
                print('written')
        print()

if __name__ == '__main__':
    flickr()
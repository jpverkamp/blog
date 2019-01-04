---
title: Listing and Downloading S3 Versions
date: 2019-01-04
programming/topics:
- AWS
- AWS S3
- Boto3
programming/languages:
- Python
- JavaScript
---
Today I found the need to look through all old versions of a file in S3 that had versioning turned on. You can do it through the AWS Console, but I prefer command line tools. You can do it with [awscli](https://aws.amazon.com/cli/), but the flags are long and I can never quite remember them. So let's write up a quick script using [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (and as a bonus, try out [click](https://click.palletsprojects.com/en/7.x/))!

<!--more-->

```python
#!/usr/bin/env python3

import boto3
import click
import re
import shutil
import sys

@click.command(help = 'List S3 versions, optionally download all versions as well')
@click.option('--bucket', required = True, help = 'The s3 bucket to scan')
@click.option('--prefix', default = '', help = 'Prefix of files to scan')
@click.option('--download', default = False, is_flag = True, help = 'Download all versions (prefix filenames with ISO datetime of edit and version), paths not preserved')
def s3versions(bucket, prefix, download):
    '''List all versions of files in s3.'''

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    versions = bucket.object_versions.filter(Prefix = prefix)

    for version in versions:
        object = version.get()

        path = version.object_key
        last_modified = object.get('LastModified')
        version_id = object.get('VersionId')
        print(path, last_modified, version_id, sep = '\t')

        if download:
            filename = path.rsplit('/')[-1]
            with open(f'{last_modified}-{version_id}-{filename}', 'wb') as fout:
                shutil.copyfileobj(object.get('Body'), fout)

if __name__ == '__main__':
    s3versions()
```

There's not actually that much too it, it's mostly a matter of getting everything in the right place once so you don't have to do it again later. Works great too:

```bash
$ s3versions --help

Usage: s3versions [OPTIONS]

  List S3 versions, optionally download all versions as well

Options:
  --bucket TEXT  The s3 bucket to scan  [required]
  --prefix TEXT  Prefix of files to scan
  --download     Download all versions (prefix filenames with ISO datetime of
                 edit and version), paths not preserved
  --help         Show this message and exit.

$ s3versions --bucket example-configs --prefix config

example-configs/project-1/database.yml	2019-01-04 18:18:16+00:00	bcWAUc.g3YBpYRRA6z5l28R99la_HbhH
example-configs/project-1/database.yml	2018-12-20 16:45:57+00:00	5I8WgKGhFl134cRyLqlD4a3SnVCVr3n.
example-configs/project-1/database.yml	2018-01-22 23:44:02+00:00	dxe_xbJaOTW_20UxtU9tw8aUaXY7S6vU
example-configs/project-1/system.yml	2018-01-26 04:27:12+00:00	pQRmVt.ljrvEsjNQVTzuRNpZ3G4IAioT
example-configs/project-1/system.yml	2017-10-25 23:44:48+00:00	VLtlw9YayUsChTEJHOkqg2S7agCkgsbw
example-configs/project-1/system.yml	2017-10-25 16:56:35+00:00	1O2EgtL_9Fkfir3REdmzPUhxQQUOch1n
```

And you can even download them:

```bash
$ s3versions --bucket example-configs --prefix config --download

...

$ ls

2019-01-04 18:18:16+00:00-bcWAUc.g3YBpYRRA6z5l28R99la_HbhH-database.yml
2018-12-20 16:45:57+00:00-5I8WgKGhFl134cRyLqlD4a3SnVCVr3n.-database.yml
2018-01-22 23:44:02+00:00-dxe_xbJaOTW_20UxtU9tw8aUaXY7S6vU-database.yml
2018-01-26 04:27:12+00:00-pQRmVt.ljrvEsjNQVTzuRNpZ3G4IAioT-system.yml
2017-10-25 23:44:48+00:00-VLtlw9YayUsChTEJHOkqg2S7agCkgsbw-system.yml
2017-10-25 16:56:35+00:00-1O2EgtL_9Fkfir3REdmzPUhxQQUOch1n-system.yml
```

Sweet.

It's stored with my [dotfiles](https://github.com/jpverkamp/dotfiles) if you'd like to download it: [s3versions](https://github.com/jpverkamp/dotfiles/blob/master/bin/s3versions).

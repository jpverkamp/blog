import click
import io
import hashlib
import urllib.parse
import os
import re

from PIL import Image

IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
RESIZE_WIDTH = 600
SRC_ROOT = '/Users/jp/Library/Mobile Documents/iCloud~md~obsidian/Documents'
DST_ROOT = os.path.join(os.path.dirname(__file__), '..')

EMBED_PATHS = {
    'tv': 'embeds/tv/attachments',
    'movie': 'embeds/movies/attachments',
    'book': 'embeds/books/attachments',
}

@click.command()
@click.argument('mode', type=click.Choice(['movie', 'tv', 'book']))
@click.argument('path')
def import_obsidian(mode, path):
    url = urllib.parse.urlparse(path)
    if url.scheme != 'obsidian' or url.netloc != 'open':
        raise Exception('Expecting an obsidian URL (incorrect scheme or netloc')

    query = urllib.parse.parse_qs(url.query)
    if 'vault' not in query or 'file' not in query:
        raise Exception('Expecting an obsidian URL (missing vault or file from query string)')

    vault = query['vault'][0]
    file = query['file'][0]
    slug = re.sub(r'[^a-z0-9]+', '-', file.lower()).strip('-')

    src_root = os.path.join(SRC_ROOT, vault)
    src_path = os.path.join(src_root, file) + '.md'

    with open(src_path, 'r') as f:
        content = f.read()

    embeds = []

    for match in re.findall(f'\!\[\[(.*?)\]\]', content):
        src_file = match
        src_path = os.path.join(src_root, src_file)
        extension = src_file.lower().rsplit('.', 1)[-1]

        # Resize images
        if extension in IMAGE_EXTENSIONS:
            src_image = Image.open(src_path)
            (old_width, old_height) = src_image.size

            if old_width > 600:
                new_width = RESIZE_WIDTH
                new_height = int(1.0 * new_width / old_width * old_height)
                dst_image = src_image.resize((new_width, new_height))

            with io.BytesIO() as f:
                dst_image.save(f, format=extension)
                dst_bytes = f.getvalue()
        else:
            with open(src_path, 'rb') as f:
                dst_bytes = f.read()
        
        dst_hash = hashlib.sha256(dst_bytes).hexdigest()[:6]
        dst_file = f'{slug}-{dst_hash}.{extension}'
        dst_path = os.path.join(DST_ROOT, 'static', EMBED_PATHS[mode], dst_file)
        dst_link = f'/{EMBED_PATHS[mode]}/{dst_file}'

        content = content.replace(f'![[{src_file}]]', f'![]({dst_link})')

        with open(dst_path, 'wb') as f:
            f.write(dst_bytes)

    content = re.sub(r'\n+', '\n\n', content)

    print(content)


if __name__ == '__main__':
    import_obsidian()
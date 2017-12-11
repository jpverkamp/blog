#!/usr/bin/env python3

import argparse
import dashtable
import html2text
import os
import re
import shutil
import sys
import yaml

import imp
goodreads = imp.load_source('scripts.import_goodreads', './scripts/import-goodreads.py')

parser = argparse.ArgumentParser(description = 'Import all posts from my old racket based blog')
parser.add_argument('path', help = 'The root of the old blog')
args = parser.parse_args()

markdowner = html2text.HTML2Text()

# (Substring of filename, something in output just before the problem)
debug_on = [
    #('monkey-grid', 'going to take'),
]

post_lists = {
    'Programming/By Source/Advent of Code': ('programming/sources', 'Advent of Code'),
    'Programming/By Project/iOS Backup': ('series', 'iOS Backups in Racket'),
    'Programming/By Source/Project Euler': ('programming/sources', 'Project Euler'),
    'Other/Book Reviews/2015 Reading List': ('reviews/lists', '2015 Book Reviews'),
    'Other/Book Reviews/2016 Reading List': ('reviews/lists', '2016 Book Reviews'),
    'Writing/Novels/A Sea of Stars': ('writing/novels', 'A Sea of Stars'),
    'Writing/Novels/Confession': ('writing/novels', 'Confession'),
    'Writing/Novels/Computational Demonology': ('writing/novels', 'Computational Demonology'),
}

# Use ❮ and ❯ instead of {{< and >}} to avoid nesting problems
replacements = [
    ('@ escapes', r'@"@"', '@'),
    ('italic text', r'<i\b[^>]*>(.*?)</i>', r'**\1**'),
    ('italic text', r'<em\b[^>]*>(.*?)</em>', r'*\1*'),
    ('bold text', r'<b\b[^>]*>(.*?)</b>', r'**\1**'),
    ('bold text', r'<strong\b[^>]*>(.*?)</strong>', r'**\1**'),
    ('headers', r'<h([1-6])\b[^>]*>(.*?)</h\1>', lambda m : ('#' * int(m.group(1))) + ' ' + m.group(2)),
    ('horizontal breaks', r'<hr\b[^>]*>', '* * *'),
    ('centered breaks', r'<center>[\*\s]+</center>', '* * *'),
    ('deleted text', r'<del\b[^>]*>(.*?)</del>', r'~~\1~~'),
    ('divs', r'<div\b[^>]*>(.*?)</div>', r'\1'),

    ('emoji woo', r'@emoji{(.*?)}', r':\1:'),

    ('remove fragments', r'<!--EndFragment-->', ''),
    ('re align more', r'\s*<!--more-->\s*', '\n\n<!--more-->\n\n'),

    ('wikipedia autolinks', r'@wikipedia{(.*?)}', r'❮ wikipedia "\1" ❯'),
    ('wikipedia autolinks with text', r'@wikipedia\[\s*"(.*?)"\s*\]{\s*(.*?)\s*}', r'❮ wikipedia page="\2" text="\1" ❯'),
    ('youtube', r'@youtube{(.*?)}', r'❮ youtube \1 ❯'),
    ('trope', r'@trope{(.*?)}', r'❮ trope "\1" ❯'),
    ('counter', r'@counter{(.*?)}', r''),

    ('block latex', r'\s*@latex\|{\s*(.*?)\s*}\|\s*', r'\n\n❮ latex ❯\1❮ /latex ❯\n\n'),
    ('block latex', r'\s*@latex{\s*(.*?)\s*}\s*', r'\n\n❮ latex ❯\1❮ /latex ❯\n\n'),
    ('inline latex', r'@latex\[\'inline\]\|{\s*(.*?)\s*}\|', r'❮ inline-latex "\1" ❯'),
    ('inline latex', r'@latex\[\'inline\]{\s*(.*?)\s*}', r'❮ inline-latex "\1" ❯'),

    ('codeblocks w/o bars', r'@codeblock\["((?:[^"\\]|\\.)*)"\]{\s*(.*?)\s*}', r'```\1\n\2\n```'),
    ('codeblocks w/o bars, symbol', r'@codeblock\[\'(.*?)\]{\s*(.*?)\s*}', r'```\1\n\2\n```'),
    ('codeblocks with bars', r'@codeblock\["((?:[^"\\]|\\.)*)"\]\|{\s*(.*?)\s*}\|', r'```\1\n\2\n```'),
    ('codeblocks with bars and symbol', r'@codeblock\[\'(.*?)\]\|{\s*(.*?)\s*}\|', r'```\1\n\2\n```'),
    ('single line codeblocks', r'@codeblock\["((?:[^"\\]|\\.)*)"\]{\s*(.*?)\s*}', r'```\1\n\2\n```'),
    ('other preformatted text', r'\s*<pre>(.*?)</pre>\s*', r'\n\n```\n\1\n```\n\n'),

    ('flickr photosets', r'@flickr-gallery{(.*?)}', r'❮ flickr set="\1" ❯'),
    ('flickr images', r'<a[^/]*?href="http://www.flickr.com/photos/jpverkamp/(.*?)/"[^/]*?>.*?</a>', r'❮ flickr image="\1" ❯'),

    ('simple links', r'<a.*?href=\'(.*?)\'[^>]*>(.*?)</a>', r'[\2](\1)'),
    ('single quoted links', r'<a.*?href=\'(.*?)\'[^>]*>(.*?)</a>', r'[\2](\1)'),
    ('racketdoc links', r'@racket-doc{(.*?)}', r'❮ doc racket "\1" ❯'),

    ('photosynths', r'@photosynth{(.*?)}', r'❮ photosynth "\1" ❯'),

    ('lists', r'(\s*)<(ul|ol)[^>]*>\n(.*?)\n\1</\2>', lambda m : re.sub(r'\n\s*', '\n', markdowner.handle(m.group(3)))),
    ('tables', r'((\s*)<(table)(?:.*?)>\n.*?\n\2</\3>)', lambda m : '\n' + (dashtable.html2md(m.group(1)) or ('FAILED' + m.group(3))) + '\n'),
    ('blockquotes', r'\s*<blockquote>(.*?)</blockquote>\s*', lambda m : '\n\n' + '\n'.join(
        '> ' + line.strip()
        if line.strip() else ''
        for line in m.group(1).split('\n')
    ) + '\n\n'),

    ('replace movie rankings', r'@ranking\[\d+\]{(\d+) Movie Rankings}', r'❮ ranking "\1 Movie Reviews" ❯'),

    ('replace post lists 1', r'@post-list\[\s*"((?:[^"\\]|\\.)*)".*?\]', lambda m : r'❮ taxonomy-list "{}" "{}" ❯'.format(*post_lists[m.group(1)])),
    ('replace post lists 2', r'@post-list\[.*?\]{(.*?)}', lambda m : r'❮ taxonomy-list "{}" "{}" ❯'.format(*post_lists[m.group(1)])),
    ('replace post lists 3', r'@post-list{(.*?)}', lambda m : r'❮ taxonomy-list "{}" "{}" ❯'.format(*post_lists[m.group(1)])),

    # Spoilers
    ('spoilers', r'<spoiler>(.*?)</spoiler>', r'{{< spoiler >}}\1{{< /spoiler >}}'),
    ('spoiler spans', r'<span class="spoiler">(.*?)</span>', r'{{< spoiler >}}\1{{< /spoiler >}}'),

    # Specific to Confession
    ('confession headers 1', r'<h1 style="text-align: center;?">(.*?)</h1>', r'# \1'),
    ('confession headers 2', r'<p style="text-align: center;?">\**(.*?)\**</p>', r'**\1**'),

    # Move crosslinks out of the way to fix footnotes with crosslinks in them
    ('move crosslinks', r'@crosslink{(.*?)}', r'⟦ crosslink "\1" ⟧'),
    ('move crosslinks', r'@crosslink\["((?:[^"\\]|\\.)*)"\]{(.*?)}', r'⟦ crosslink "\1" "\2" ⟧'),

    # Not sure how these exist...
    ('fix paragraphs', r'<p>(.*?)</p>', r'\1\n'),
    ('fix broken links', r'a href="blog.jverkamp.com', r'a href="//blog.jverkamp.com"'),
]

category_rewrites = [
    ('Procedurally Generated Content', 'Procedural Content'),
]

remove_header_keys = [
    'comments',
    'layout',
    'published',
]

header_key_order = [
    'title',
    'date',
    'aliases',
]

blacklist = [
    # Writing I don't care to keep any more
    #'Writing',
    'Japanses Class',
    'Name That Artist',
    'Rose Thorn',

    # Board game reviews (only did the one, maybe some day)
    'Board Game Reviews',

    # Single pages that are being done by hugo now
    '404.htm',
    'feed.htm',
    'feed_index.htm',
    'home.htm',

    # Generated files
    '.DS_Store',
]

path_rewrites = [
    ('other/book-reviews', 'reviews/books'),
    ('other/movie-reviews', 'reviews/movies'),
    ('other/cooking', 'reviews/cooking'),
    ('programming/other', 'programming'),
    #('other/', ''),
]

title_replacements = [
    ('--', '-'),
    ('Project Euler #', 'Project Euler '),
]

taxonomies = {
    'Programming/By Language': 'programming/languages',
    'Programming/By Source': 'programming/sources',
    'Programming/By Topic': 'programming/topics',
    'Writing/By Genre': 'writing/genres',
}

new_headers = {
    'Writing/Novels': 'novel',
}

section_crosslinks = {
    'Daily Programmer': '/programming/sources/daily-programmer/',
    'Research': '/research/',
    'movie reviews': '/reviews/lists/',
    'photography': '/photography/',
}

crosslinks = {
    'Cabin and Louie\'s': '2005-04-17-cabin-and-louies.md',
    'Stinklets ... And then Some': '2005-05-31-stinklets-and-then-some.md',
    'a-brainfk-interpreter': '2012-12-30-a-brainf-k-interpreter.md',
    'cornbreaded-everything': '2010-11-12-corn-breaded-everything.md',
    'evaluating-prefixinfixpostfix': '2012-10-08-evaluating-prefix-infix-postfix-expressions.md',
    'extending-rackets-dns-capabilities': '2013-09-25-extending-racket-s-dns-capabilities.md',
    'isccaida-workshop': '2012-10-22-isc-caida-workshop.md',
    'isma-2013-aims-5-dns-based-censorship': '2013-02-09-isma-2013-aims-5.md',
    'line-art-with-html5-canvas': '2012-09-26-line-art-with-an-html5-canvas.md',
    'racket-roguelike-1-a-gui-screens-io-and-you': '2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md',
    'so-ive-been-writing': '2012-08-28-so-i-ve-been-writing.md',
    'usenixfoci-2013-five-incidents-one-theme-twitter-spam-as-a-weapon-to-drown-voices-of-protest': '2013-08-13-usenix-foci-2013.md',
    'usenixfoci-inferring-mechanics-of-web-censorship-around-the-world': '2012-08-06-usenix-foci-2012.md',
    'wombat-ide-schemejava-interop': '2012-02-23-wombat-ide-scheme-java-interop.md',
}

# (start of title, series title)
series = [
    ('Advent of Code', 'Advent of Code 2015'),
    ('Ludum Dare 30', 'Ludum Dare 30'),
    ('iOS Backups in Racket', 'iOS Backups in Racket'),
    ('Chess Puzzles', 'Chess Puzzles'),
    ('Cracker Barrel Peg Game', 'Cracker Barrel Peg Game'),
    ('Wombat IDE', 'Wombat IDE'),
]

aliases = {
    '2016-01-02-inlining-plaintext-attachments-in-gmail': '/2016/12/02/inlining-plaintext-attachments-in-gmail/',
    '2016-01-04-command-line-emoji-search': '/2016/12/04/command-line-emoji-search/',
    '2016-01-06-command-line-unicode-search': '/2016/12/06/command-line-unicode-search/',
}

copyable_embed_parameters = [
    'width',
    'height',
]

rename_embeds = {}
photoset_dates = {}

def slugify(text):
    return re.sub(r'[^a-z0-9/\.-]+', r'-', text.lower()).strip('-')

DEBUG_MODE = False
DEBUG_PRINT_FROM = False

def set_debug_mode(mode, print_from = None):
    global DEBUG_MODE, DEBUG_PRINT_FROM
    DEBUG_MODE = mode
    DEBUG_PRINT_FROM = print_from

def debug(text):
    if DEBUG_MODE:
        if DEBUG_PRINT_FROM:
            index = text.index(DEBUG_PRINT_FROM)
        else:
            index = 0

        print('***** ***** <DEBUG> ***** *****')
        print(text[index:index+1000])
        input('***** ***** </DEBUG> ***** *****\nPress any key to continue')

def process_post(old_path):
    '''Process posts. If it turns out it isn't a post, move on to treating it as an attachment.'''

    set_debug_mode(False)
    for pattern, print_from in debug_on:
        if pattern in old_path:
            set_debug_mode(True, print_from)

    if any(re.search(regex, old_path) for regex in blacklist):
        print('- Matches blacklist, skipping')
        return

    with open(old_path, 'r') as fin:
        content = fin.read()

    # No yaml header, probably an embed
    if '\n---\n' not in content:
        return process_attachment(old_path)

    directory, filename = old_path.split('/_posts/')[1].rsplit('/', 1)

    new_filename = filename.rsplit('.', 1)[0] + '.md'
    new_path = slugify(os.path.join('.', 'content', directory, new_filename))

    for old, new in path_rewrites:
        new_path = new_path.replace(old, new)

    header, content = content.split('\n---\n', 1)
    header = yaml.load(header)

    for key in remove_header_keys:
        if key in header:
            del header[key]

    header['tags'] = []
    for category in header.get('categories', []):
        for pattern, replacement in category_rewrites:
            category = category.replace(pattern, replacement)

        parts = category.split('/')

        # HACK
        if parts[-1] == 'Programming Languages':
            continue

        for taxonomy in taxonomies:
            if category.startswith(taxonomy):
                header.setdefault(taxonomies[taxonomy], set()).add(parts[-1])

        for new_header_pattern, new_header in new_headers.items():
            if category.startswith(new_header_pattern):
                header[new_header] = parts[-1]

        if category.startswith('Other/Book Reviews'):
            # NOTE: This post will actually be generated automatically by import-flickr, so don't copy it
            # NOTE: Keep the reading list posts, skip everything else
            if not 'reading-list' in new_path:
                return

            header.setdefault('reviews/lists', set()).add('{} Book Reviews'.format(header['date'].year))

        if category.startswith('Other/Movie Reviews'):
            header.setdefault('reviews/lists', set()).add('{} Movie Reviews'.format(header['date'].year))

        if category.startswith('Other/Cooking'):
            header.setdefault('reviews/lists', set()).add('Cooking')

        if category.startswith('Writing/Novels'):
            header.setdefault('writing/types', set()).add('Novel')

        if category.startswith('Writing/Short Stories'):
            header.setdefault('writing/types', set()).add('Short Story')

        for subcategory in ('Ideas', 'Writing Excuses'):
            if category.startswith('Writing/' + subcategory):
                header.setdefault('writing/types', set()).add('Writing Prompt')

        if category.startswith('Writing/NaNoWriMo'):
            header.setdefault('writing/types', set()).add('NaNoWriMo')

        for part in parts[2:]:
            header['tags'].append(part)

    for novel in ('A Sea of Stars', 'Computational Demonology', 'Confession', 'The City on the Lake'):
        if novel in header.get('title', '') or slugify(novel) in new_path:
            header.setdefault('writing/novels', set()).add(novel)

    if '@flickr-gallery' in content:
        # NOTE: This post will actually be generated automatically by import-flickr, so don't copy it
        # photoset_dates is used to post the photoset when it was taken rather than when it was posted
        # If a flickr gallery is included in multiple posts, use the oldest one
        for photoset_id in re.findall(r'@flickr-gallery{(.*?)}', content):
            photoset_id = int(photoset_id)
            photoset_dates[int(photoset_id)] = min(
                str(header['date']).split()[0],
                photoset_dates.get(photoset_id, '9999-99-99'),
            )

        return

        # Old version, comment return out above to use this
        header.setdefault('photography/types', set()).add('Flickr Set')

    if 'dpchallenge' in content:
        header.setdefault('photography/types', set()).add('DP Challenge')

    # Photosynts no longer exist :(
    if '@photosynth' in content:
        header.setdefault('photography/types', set()).add('Photosynth')
        print('- Photosynths no longer exist... :(')

    # TODO: Don't overlap book reviews

    for path_part, alias in aliases.items():
        if path_part in new_path:
            print('- Assing alias: {}'.format(alias))
            header.setdefault('aliases', set()).add(alias)

    for each in header:
        if isinstance(header[each], set):
            header[each] = list(sorted(set(header[each])))

    debug(content)

    # <goodreads> Has to be before replacments since it looks for HTML links
    def replace_goodreads(m, cover = False):
        url, text = m.groups()
        url = url.split('?')[0]

        if 'book' in url:
            type = 'book'
            name = goodreads.get_book(url)['name']
        elif 'author' in url:
            type = 'author'
            name = goodreads.get_author(url)['name']
        elif 'series' in url:
            type = 'series'
            name = goodreads.get_series(url)['name']

        print('- Replacing goodreads {}, got name = {}, text = {}'.format(type, name, text))

        params = {type: name}

        if text and name != text:
            params['text'] = text

        if cover:
            params['cover'] = 'true'

        param_str = ' '.join('{}="{}"'.format(key, value) for key, value in params.items())
        return '❮ goodreads {} ❯'.format(param_str)

    content = re.sub(r'<a href="https://www.goodreads.com(/(?:author|book|series)(?:/show)?/.*?)">(.*?)</a>', replace_goodreads, content)
    content = re.sub(r'@embed\[[^\]]*#:target "https://www.goodreads.com(/book/show/.*?)"[^\]]*]{.*?()}', lambda m : replace_goodreads(m, True), content)

    #('goodreads linked covers', r'@embed\[#:target "https://www.goodreads.com/book/show/.*?"\]{(.*?).jpg}', r'❮ goodreads book_cover "\1" ❯'),
    # </goodreads>

    for description, regex, replacement in replacements:
        new_content = re.sub(regex, replacement, content, flags = re.MULTILINE | re.DOTALL)
        if content != new_content:
            print('- Applying regex: {}'.format(description))
            content = new_content
            debug(content)

    for old, new in title_replacements:
        header['title'] = header['title'].replace(old, new)

    # If we're not in a section, set it manually
    if new_path.count('/') == 2:
        header['type'] = 'post'

    # <footnotes> Have state so have to be done by hand
    footnotes = []
    def replace_footnote(m):
        footnotes.append(m.group(1))
        return '[^{}]'.format(len(footnotes))

    content = re.sub(r'@footnote{(.*?)}', replace_footnote, content, flags = re.MULTILINE | re.DOTALL)
    if footnotes:
        content = content.rstrip() + '\n\n' + '\n'.join('[^{}]: {}'.format(i, el) for i, el in enumerate(footnotes, 1))
    # </footnotes>

    # <embeds> Need to rewrite paths, so done by hand
    def replace_embed(m):
        raw_parameters = m.group(1) or ''
        filename = m.group(2)
        input_parameters = dict(re.findall(r'#:(.*?)\s+("(?:[^"\\]|\\.)*"|[^\s]+)', raw_parameters))
        output_parameters = {}
        tag = "figure"

        if 'target' in input_parameters:
            output_parameters['link'] = input_parameters['target']

        for name in copyable_embed_parameters:
            if name in input_parameters:
                output_parameters[name] = input_parameters[name]

        # HACK: bleh
        if filename == 'http://blog.jverkamp.com/wp-content/uploads/2013/11/greensleeves.mp3':
            filename = '/embeds/2013/greensleeves.mp3'

        if filename.startswith('http'):
            if 'youtube' in filename:
                output_parameters['data-embedded-video'] = 'true'
                url_patterns = [
                    r'https://www.youtube.com/watch\?v=(.*)',
                ]
                for url_pattern in url_patterns:
                    m = re.match(url_pattern, filename)
                    if m and m.group(1).strip():
                        return '❮ youtube {} ❯'.format(m.group(1))

                print(filename)
                sys.exit(0)
            else:
                src = filename
        elif filename.endswith('.pdf'):
            # TODO: not sure
            src = filename
        elif filename.endswith('.mp3') or filename.endswith('.wav') or filename.endswith('.ogg'):
            return '❮ audio type="{extension}" src="{filename}" ❯'.format(
                extension = filename.split('.')[-1],
                filename = filename,
            )

        elif filename.endswith('.htm') or filename.endswith('.html'):
            tag = "iframe"
            year = header['date'].year
            src = '/embeds/{year}/{filename}'.format(year = year, filename = filename)

        else:
            year = header['date'].year
            src = '/embeds/{year}/{filename}'.format(year = year, filename = filename)

        if 'Reviews' in old_path:
            output_parameters['class'] = "cover-image"
            new_filename = re.sub(r'^[\d.]+-', r'', filename).lower()

            if 'Book' in old_path:
                rename_embeds[src] = None
            else:
                rename_embeds[src] = '/embeds/movies/{filename}'.format(filename = new_filename)

            src = rename_embeds[src]

        if output_parameters:
            output_parameters_str = ' '.join('{}="{}"'.format(k, v.strip('"')) for (k, v) in sorted(output_parameters.items())) + ' '
        else:
            output_parameters_str = ''

        return '❮ {tag} {params}src="{src}" ❯'.format(tag = tag, params = output_parameters_str, src = src)

    content = re.sub(r'@embed(?:\[(.*?)\])?{(.*?)}', replace_embed, content)
    # </embeds>

    # Add other series
    for post_title_prefix, series_title in series:
        if header['title'].startswith(post_title_prefix):
            header.setdefault('series', set()).add(series_title)

    # Remaining rankings
    def add_series(m):
        header.setdefault('series', set()).add(m.group(1))
        return ''

    content = re.sub(r'@ranking\[\d+\]{(.*?)}', add_series, content)
    if 'series' in header:
        header['series'] = list(sorted(header['series']))

    # Fix brackets
    content = content.replace('❮', '{{<').replace('❯', '>}}')

    potential_crosslinks = [
        header['title'],
        slugify(header['title']),
        slugify(header['title']).replace('/', '-'),
        filename.rsplit('.', 1)[0],
    ]
    crosslink_target = new_path.replace('content/', '').replace('./', '').strip()
    for potential_crosslink in potential_crosslinks:
        if potential_crosslink:
            crosslinks[potential_crosslink] = crosslink_target

    if 'tags' in header:
        del header['tags']
    if 'categories' in header:
        del header['categories']

    print('- Writing to {}'.format(new_path))
    os.makedirs(os.path.dirname(new_path), exist_ok = True)
    with open(new_path, 'w') as fout:
        fout.write('---\n')
        for key in header_key_order:
            if key in header:
                yaml.dump({key: header[key]}, fout, default_flow_style = False)
                del header[key]
        if header:
            yaml.dump(header, fout, default_flow_style = False)
        fout.write('---\n')
        fout.write(content)

    return True

def process_attachment(old_path):
    '''Process non-posts, usually images or other embeded content.'''

    directory, filename = old_path.split('/_posts/')[1].rsplit('/', 1)
    new_filename = filename
    new_path = os.path.join('.', 'static', 'static', directory, new_filename)

    if filename in blacklist:
        return

    # Go up a directory to load the related post for the date
    # HACK: this
    post_path = os.path.dirname(old_path) + '.htm'
    with open(post_path, 'r') as fin:
        header, _ = fin.read().split('---', 1)
        header = yaml.load(header)

        year = str(header['date'].year)
        new_path = os.path.join('.', 'static', 'embeds', year, filename)

    for old, new in path_rewrites:
        new_path = new_path.replace(old, new)

    os.makedirs(os.path.dirname(new_path), exist_ok = True)

    print('- Copying to {}'.format(new_path))

    with open(old_path, 'rb') as fin:
        with open(new_path, 'wb') as fout:
            fout.write(fin.read())

# First pass, do most all of the formatting
for path, _, filenames in os.walk(os.path.join(args.path, '_posts')):
    for filename in filenames:
        old_path = os.path.join(path, filename)
        print('\nProcessing {}'.format(old_path))

        if old_path.endswith('.htm'):
            process_post(old_path)
        else:
            process_attachment(old_path)
            continue
print()

# Second pass, rewrite crosslinks
missing_crosslinks = set()

def replace_crosslink(m):
    target = m.group(1)
    text = m.group(2)

    if not target:
        target = text

    target = target.strip('"')
    text = text.strip('"')

    slug_target = slugify(target)

    print('- target: {target}, text: {text}'.format(target = target, text = text))

    if target in section_crosslinks:
        print('- Replacing with direct section link')
        return '[{text}]({url})'.format(text = text, url = section_crosslinks[target])

    url = None
    for each in crosslinks:
        if target in each or slug_target in each:
            print('- matching url: {}'.format(crosslinks[each]))
            url = crosslinks[each]

    if not url:
        print('- NOT FOUND')
        missing_crosslinks.add((target, text))
        return text

    url_filename = url.split('/')[-1]

    #return '[{text}]({{< ref "{url}" >}})'.format(target = target, text = text, url = url)
    #return '{{{{< ref "{url}" >}}}}'.format(url = url)
    #return '{{< relref "%s" >}}'.format(url = url_filename)
    return '[%s]({{< ref "%s" >}})' % (text, url_filename)

for path, _, filenames in os.walk('content'):
    for filename in filenames:
        new_path = os.path.join(path, filename)
        print('\nProcessing crosslinks in {}'.format(new_path))

        with open(new_path, 'r') as fin:
            raw_content = fin.read()

        updated_raw_content = re.sub(r'⟦ crosslink (?:"((?:[^"\\]|\\.)*)" )?"((?:[^"\\]|\\.)*)" ⟧', replace_crosslink, raw_content)

        if raw_content != updated_raw_content:
            print('- Content updated, writing back to disk')
            with open(new_path, 'w') as fout:
                fout.write(updated_raw_content)
print()

print('Writing flickr photoset date overrides')
with open(os.path.join('data', 'flickr', 'post-dates.yaml'), 'w') as fout:
    yaml.dump(photoset_dates, fout, default_flow_style = False)

print('Moving embeds that are following a non-standard naming system')
for old_src, new_src in rename_embeds.items():
    print('- {} -> {}'.format(old_src, new_src))
    old_path = 'static' + old_src

    if new_src:
        new_path = 'static' + new_src

        os.makedirs(os.path.dirname(new_path), exist_ok = True)
        shutil.move(old_path, new_path)
    else:
        os.remove(old_path)

print()

print('Resizing all book covers to be the same size\n')
os.system('mogrify -resize 100x160\! static/embeds/books/*.jpg')

if missing_crosslinks:
    print('Missing crosslinks:')
    for each in sorted(missing_crosslinks):
        print('- target: {}, text: {}'.format(*each))
print()

# Copy content that needs/is manually fixed
print('Copying manually edited content:')
for path, _, filenames in os.walk('_copy_content'):
    for filename in filenames:
        old_path = os.path.join(path, filename)
        new_path = old_path.replace('_copy_', '')

        print('- {} -> {}'.format(old_path, new_path))

        os.makedirs(os.path.dirname(new_path), exist_ok = True)
        shutil.copy(old_path, new_path)
print()

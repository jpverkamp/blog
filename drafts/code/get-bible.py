from __future__ import print_function

import bs4
import json
import pprint
import os
import re
import requests

def clean(text):
    try:
        text = text.encode('utf-8')
    except:
        pass

    text = re.sub(r'[\s]+', ' ', text)
    text = re.sub(r'\xc2\xa0', ' ', text)
    text = text.strip()

    return text

def get_footnote(soup, tag):
    for link in soup.find_all('a', {'name': tag}):
        for node in link.parents:
            if node.name == 'font':
                return clean(node.next_sibling.text)

def load_content(href):
    url = 'http://www.vatican.va/archive/ENG0839/{0}'.format(href)
    print(url)

    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.text)

    #return soup

    result = ''

    verse_number = None
    for line in soup.find_all('p'):
        if 'align' in line.attrs and line['align'] == 'center':
            continue

        text = clean(line.text)
        if not text:
            continue

        # Extract footnotes
        footnotes = []
        for sup in line.find_all('sup', recursive = False):
            for link in sup.find_all('a'):
                tag = link['href'][1:]
                footnotes.append(get_footnote(soup, tag))
            sup.extract()

        # Redo text (in case of footnotes)
        text = clean(line.text)

        # Only a verse number
        if re.match(r'^\d+$', text):
            verse_number = int(text)
            continue

        # A verse number and a line
        elif re.match(r'^\d\s+', text):
            verse_number, text = text.split(None, 1)
            verse_number = int(verse_number.strip())
            text = text.strip()

        if not text:
            continue

        if verse_number:
            result += '{0}: {1}\n'.format(verse_number, text)
        else:
            result += '{0}\n'.format(text)

        if footnotes:
            for footnote in footnotes:
                result += '\t{0}\n'.format(footnote)

        result += '\n'

    return result

index = requests.get('http://www.vatican.va/archive/ENG0839/_INDEX.HTM')
soup = bs4.BeautifulSoup(index.text)

bible = []

for section in soup.find_all('li'):
    if not section.find('font', {'size': '3'}):
        continue

    section_title = section.find('font', {'size': '3'}).text
    print(section_title)

    section_summary = load_content(section.find('font', {'size': '3'}).find('a')['href'])

    bible.append({
        'title': section.find('font', {'size': '3'}).text,
        'books': [],
        'summary': section_summary
    })

    for book in section.find_all('li'):
        if not book.find('font', {'size': '2'}):
            continue

        book_title = book.find('font', {'size': '2'}).text
        print('- ' + book_title)

        bible[-1]['books'].append({
            'title': book_title,
            'chapters': []
        })

        for link in book.find_all('a'):
            bible[-1]['books'][-1]['chapters'].append({
                'title': link.text,
                'content': load_content(link['href']),
            })

def directory(*args):
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

for section_index, section in enumerate(bible, 1):
    section_directory = directory('output', '{0:02d} {1}'.format(section_index, section['title']))
    with open(os.path.join(section_directory, '00 Summary.txt'), 'w') as fout:
        fout.write(section['summary'])

    for book_index, book in enumerate(section['books'], 1):
        book_directory = directory(section_directory, '{0:02d} {1}'.format(book_index, book['title']))

        for chapter in book['chapters']:
            filename = os.path.join(book_directory, chapter['title'] + '.txt')
            print(filename)

            with open(filename, 'w') as fout:
                fout.write(chapter['content'])

with open(os.path.join('output', 'bible.json'), 'w') as fout:
    json.dump(bible, fout, indent = 4, sort_keys = True)

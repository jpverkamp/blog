import argparse
import coloredlogs
import datetime
import logging
import os
import re
import requests
import yaml

from dataclasses import dataclass
from PIL import Image
from typing import Any

coloredlogs.install(logging.INFO)

TARGET_COVER_SIZE = (214, 317)
BLOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
COVER_DIR = os.path.join(BLOG_DIR, 'static', 'embeds')
REVIEW_BASE_DIR = os.path.join(BLOG_DIR, 'content', 'reviews')


def slugify(text: str) -> str:
    return re.sub('[^a-z0-9-]+', '-', text.lower()).strip('-')


def normalize_people(values: list[Any]) -> list[str]:
    output = []
    for value in values:
        value_str = str(value).strip()
        if not value_str or value_str == 'None' or value_str in output:
            continue
        output.append(value_str)
    return output


def parse_index(value: str) -> Any:
    value = value.strip()
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def parse_series(series_input: str) -> tuple[list[str], list[Any]]:
    series_names = []
    series_indexes = []

    for raw_entry in series_input.split(','):
        entry = raw_entry.strip()
        if not entry:
            continue

        if ' #' in entry:
            series_name, raw_index = entry.rsplit(' #', 1)
            series_names.append(series_name.strip())
            series_indexes.append(parse_index(raw_index))
        else:
            series_names.append(entry)
            series_indexes.append(0)

    return series_names, series_indexes


@dataclass
class Candidate:
    backend: str
    id: str
    title: str
    year: Any
    kind: str
    payload: Any


@dataclass
class ReviewData:
    backend: str
    title: str
    date: str
    year: int
    content_type: str
    ids: dict[str, Any]
    details: dict[str, Any]
    cover_url: str | None


class ImdbBackend:
    def __init__(self):
        self.base_url = 'https://v3.sg.media-imdb.com/suggestion'

    def _request(self, path: str) -> list[dict[str, Any]]:
        response = requests.get(f'{self.base_url}/{path}', timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload.get('d') or []

    def _classify(self, item: dict[str, Any]) -> str:
        qid = (item.get('qid') or '').lower()
        q = (item.get('q') or '').lower()
        if qid.startswith('tv') or 'tv' in q:
            return 'tv'
        return 'movies'

    def search(self, title: str, media_type: str) -> list[Candidate]:
        token = re.sub(r'[^a-zA-Z0-9]+', '_', title).strip('_').lower()
        if not token:
            return []

        shard = token[0]
        results = self._request(f'{shard}/{token}.json')
        candidates: list[Candidate] = []

        for result in results:
            if not result.get('id', '').startswith('tt'):
                continue

            kind = str(result.get('qid') or result.get('q') or '')
            content_type = self._classify(result)
            if media_type != 'auto':
                want_tv = media_type == 'tv'
                if want_tv and content_type != 'tv':
                    continue
                if not want_tv and content_type == 'tv':
                    continue

            candidates.append(
                Candidate(
                    backend='imdb',
                    id=result.get('id', '').replace('tt', ''),
                    title=result.get('l') or 'Unknown',
                    year=result.get('y') or '?',
                    kind=kind or 'unknown',
                    payload=result,
                )
            )

        return candidates

    def fetch_by_id(self, raw_id: str) -> Candidate:
        cleaned = raw_id if raw_id.startswith('tt') else f'tt{raw_id}'
        results = self._request(f't/{cleaned}.json')
        if not results:
            raise RuntimeError(f'IMDb id not found: {raw_id}')

        result = results[0]
        return Candidate(
            backend='imdb',
            id=cleaned.replace('tt', ''),
            title=result.get('l') or 'Unknown',
            year=result.get('y') or '?',
            kind=result.get('qid') or result.get('q') or 'unknown',
            payload=result,
        )

    def to_review_data(self, candidate: Candidate, date: str) -> ReviewData:
        data = candidate.payload or {}
        title = data.get('l') or candidate.title
        year = data.get('y') or datetime.date.today().year
        content_type = self._classify(data)

        details: dict[str, Any] = {'reviews/year': year}
        if stars := data.get('s'):
            cast_map = {}
            for name in [part.strip() for part in stars.split(',') if part.strip()]:
                cast_map[name] = 'Unknown'
            if cast_map:
                details['reviews/cast'] = cast_map

        cover_url = (data.get('i') or {}).get('imageUrl')

        return ReviewData(
            backend='imdb',
            title=title,
            date=date,
            year=year,
            content_type=content_type,
            ids={'imdb_id': str(candidate.id)},
            details=details,
            cover_url=cover_url,
        )


def prompt(prompt_text: str, default: str | None = None) -> str:
    if default is None:
        return input(prompt_text)
    return input(f'{prompt_text} (default {default}): ') or default


def choose_candidate(candidates: list[Candidate]) -> Candidate | None:
    if not candidates:
        return None

    print()
    for i, candidate in enumerate(candidates[:20], 1):
        print(f'{i}. [{candidate.backend}] {candidate.title} ({candidate.year}, {candidate.kind})')
    choice = input('Selection (1-20, leave blank to skip): ').strip()
    print()

    if not choice:
        return None

    if not choice.isdigit():
        logging.error('Selection must be numeric')
        return None

    index = int(choice) - 1
    if index < 0 or index >= min(20, len(candidates)):
        logging.error('Selection out of bounds')
        return None

    return candidates[index]


def build_paths(title: str, content_type: str, series_names: list[str], series_indexes: list[Any]) -> tuple[str, str, str, str]:
    slug = slugify(title)
    cover_filename = f'{slug}.jpg'

    if content_type == 'tv':
        review_dir = os.path.join(REVIEW_BASE_DIR, 'tv')
        review_filename = f'{title}.md'
    else:
        if series_names:
            review_dir = os.path.join(REVIEW_BASE_DIR, 'movies', series_names[0])
            review_filename = f'{series_indexes[0]} - {title}.md'
        else:
            review_dir = os.path.join(REVIEW_BASE_DIR, 'movies')
            review_filename = f'{title}.md'

    review_path = os.path.join(review_dir, review_filename)
    cover_path = os.path.join(COVER_DIR, content_type, cover_filename)
    cover_web = f'/embeds/{content_type}/{cover_filename}'
    return review_path, cover_path, cover_filename, cover_web


def save_cover(cover_url: str, cover_path: str):
    os.makedirs(os.path.dirname(cover_path), exist_ok=True)
    image = Image.open(requests.get(cover_url, stream=True, timeout=30).raw)
    image = image.resize(TARGET_COVER_SIZE)
    image = image.convert('RGB')
    image.save(cover_path)


def generate_frontmatter(review: ReviewData, title: str, series_names: list[str], series_indexes: list[Any], cover_web: str | None) -> dict[str, Any]:
    list_year = review.year
    if isinstance(review.date, str) and len(review.date) >= 4 and review.date[:4].isdigit():
        list_year = int(review.date[:4])

    data = {
        'title': title,
        'date': review.date,
        'draft': True,
        'reviews/lists': [f'{list_year} {"TV" if review.content_type == "tv" else "Movie"} Reviews'],
    }

    if cover_web:
        data['cover'] = cover_web

    for key, value in review.ids.items():
        data[key] = value

    for key, value in review.details.items():
        data[key] = value

    if series_names:
        data['reviews/series'] = series_names
        data['series_index'] = series_indexes

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate movie/tv review markdown with metadata')
    parser.add_argument('--title', help='Title to search for (interactive prompt if omitted)')
    parser.add_argument('--date', help='Date for the review, format YYYY-MM-DD (defaults to today)')
    parser.add_argument('--id', help='Direct id (IMDb tt123 or numeric backend id)')
    parser.add_argument('--type', choices=['auto', 'movie', 'tv'], default='auto', help='Preferred media type')
    parser.add_argument('--backend', choices=['imdb'], default='imdb', help='Metadata backend')
    parser.add_argument('--series', help='Series data like "The Matrix #1, Franchise #2"')
    parser.add_argument('--save', action='store_true', help='Save generated files without confirmation')
    parser.add_argument('--dry-run', action='store_true', help='Preview output and do not write files')
    parser.add_argument('--no-cover', action='store_true', help='Skip downloading/saving covers')
    parser.add_argument('--single', action='store_true', help='Generate one review and exit')
    return parser.parse_args()


def main():
    args = parse_args()

    imdb_backend = ImdbBackend()

    run_once = bool(args.single or args.title or args.id)

    while True:
        date = args.date or str(datetime.date.today())
        entered_date = prompt('Date for review: ', date) if not args.date else date
        year_default = int(entered_date[:4]) if len(entered_date) >= 4 and entered_date[:4].isdigit() else datetime.date.today().year

        title_input = args.title.strip() if args.title else prompt('Title: ').strip()
        if not title_input:
            logging.info('No title entered, exiting')
            break

        media_type = args.type
        if media_type == 'movie':
            media_type = 'movies'
        elif media_type == 'tv':
            media_type = 'tv'
        else:
            media_type = 'auto'

        selected: Candidate | None = None

        if args.id or title_input.startswith('tt'):
            raw_id = args.id or title_input
            selected = imdb_backend.fetch_by_id(raw_id)
        else:
            candidates: list[Candidate] = imdb_backend.search(title_input, media_type)

            if not candidates:
                logging.error(f'No matches found for: {title_input}')
                if run_once:
                    break
                continue

            selected = choose_candidate(candidates)
            if not selected:
                if run_once:
                    break
                continue

        review = imdb_backend.to_review_data(selected, entered_date)

        effective_title = review.title
        if title_input != effective_title:
            if input(f'{title_input} does not match {effective_title}, use fetched title? (yN) ').lower().startswith('y'):
                title_input = effective_title

        series_input = args.series
        if series_input is None:
            series_input = input('Part of a series? (ex "The Matrix #1", comma delimited, blank to skip): ').strip()

        series_names: list[str] = []
        series_indexes: list[Any] = []
        if series_input:
            series_names, series_indexes = parse_series(series_input)

        if not review.year:
            review.year = year_default

        review_path, cover_path, cover_filename, cover_web = build_paths(title_input, review.content_type, series_names, series_indexes)

        if args.no_cover:
            cover_web = None

        frontmatter = generate_frontmatter(review, title_input, series_names, series_indexes, cover_web)
        rendered = f'---\n{yaml.dump(frontmatter, sort_keys=False)}---\n'

        print('Preview:\n')
        print(f'Backend: {review.backend}')
        print(f'Review path: {review_path}')
        if cover_web and review.cover_url:
            print(f'Cover path: {cover_path} <- {review.cover_url}')
        elif cover_web:
            print(f'Cover path: {cover_path} (no source image provided by backend)')
        print('\nFrontmatter:\n')
        print(rendered)

        should_save = args.save
        if args.dry_run:
            should_save = False
        elif not args.save:
            should_save = input('Write files? (yN) ').lower().startswith('y')

        if should_save:
            os.makedirs(os.path.dirname(review_path), exist_ok=True)

            if os.path.exists(review_path):
                overwrite = input(f'{os.path.basename(review_path)} already exists, overwrite? (yN) ').lower().startswith('y')
                if not overwrite:
                    logging.info('Skipped writing existing file')
                else:
                    with open(review_path, 'w') as fout:
                        fout.write(rendered)
                    logging.info(f'Wrote review file: {review_path}')
            else:
                with open(review_path, 'w') as fout:
                    fout.write(rendered)
                logging.info(f'Wrote review file: {review_path}')

            if cover_web and review.cover_url and not args.no_cover:
                try:
                    logging.info(f'Saving cover {cover_filename} <- {review.cover_url}')
                    save_cover(review.cover_url, cover_path)
                except Exception as ex:
                    logging.error(f'Error downloading cover: {ex}')
        else:
            logging.info('Dry run / preview only: no files were written')

        if run_once:
            break

        if not input('Create another post? (yN) ').lower().startswith('y'):
            break
        print()


if __name__ == '__main__':
    main()

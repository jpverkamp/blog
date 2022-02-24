---
title: A CLI Tool for Bulk Processing Github Dependabot Alerts (with GraphQL!)
date: 2022-02-03
programming/languages:
- Python
programming/sources:
- Small Scripts
programming/topics:
- Security
- Dependabot
- Vulnerability Management
- CLI
- Requests
- GraphQL
---
Dependabot is ... *somewhat useful*. When it comes to letting you know that there are critical issues in your dependencies that can be fixed simply by upgrading the package (they did all the work for you*). The biggest problem is that it can just be *insanely* noisy. In a busy repo with multiple Node.JS codebases (especially), you can get dozens to even hundreds of reports a week. And for each one, you optimally would update the code... but sometimes it's just not practical. So you have to decide which updates you actually apply. 

So. How do we do it? 

Well the traditional rest based Github APIs don't expose the dependabot data, *but* the newer GraphQL one does! I'll admit, I haven't used as much GraphQL as I probably should, it's... a bit more complicated than REST. But it does expose what I need.

<!--more-->

Specifically, I have two relevant queries. 

First, the ability to get a list of all dependabot alerts for a specific repo:

```graphql
query getAlerts($repo: String!, $owner: String!) {
  repository(name: $repo, owner: $owner) {
    vulnerabilityAlerts($cursor) {
      nodes {
        createdAt
        dismissedAt
        securityVulnerability {
          package {
            name
          }
          advisory {
            description
            severity
          }
        }
        id
        vulnerableManifestPath
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
}
```

I'll have to do pagination, but otherwise it works pretty well. I'll come back to that (that's what the `$cursor` psuedo-variable is, I'll replace that before sending it to the server).

And then even better, we need to be able to automatically close an issue with a given reason (and what's better: you can store arbitrary reasons, which is better than what you normally get). 

```graphql
mutation dismissAlert($id: String!, $reason: String!) {
  dismissRepositoryVulnerabilityAlert(
    input: {
      clientMutationId: "JP's Dependabot CLI"
      dismissReason: $reason
      repositoryVulnerabilityAlertId: $id
    }
  ) {
    clientMutationId
    repositoryVulnerabilityAlert {
      id
    }
  }
}
```

Nice!

Now, wrap it up in a [click](https://click.palletsprojects.com/en/8.0.x/) based CLI and you're golden.

```python
import click
import coloredlogs
import functools
import logging
import requests
import os
import re

if 'GITHUB_TOKEN' not in os.environ:
    print('GITHUB_TOKEN must be set')
    exit(1)
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

REASONS = {
    'tolerable': 'Risk is tolerable to this project',
    'tolerable-regex': 'Risk is tolerable to this project (regex DoS/complexity)',
    'not-used': 'Vulnerable code is not actually used',
}


@functools.cache
def load_query(path):
    '''Load a graphql query from disk'''

    logging.info(f'Loading query {path} from disk')
    with open(path, 'r') as fin:
        return fin.read()


def graphql(name, cursor=None, **variables):
    '''Execute a graphql query against the Github API'''

    query = load_query(os.path.join('queries', name + '.graphql'))
    logging.info(f'Executing query {name} with {variables=}')

    if '$cursor' in query:
        query = query.replace('$cursor', cursor or '')

    logging.info(f'\n{query}')

    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers={'Authorization': f'Bearer {GITHUB_TOKEN}'},
    )

    if response and 'data' in response.json():
        return response.json()['data']

    else:
        logging.critical(f'''\
Query {name} failed:
Variables:
{variables}
Request:
{query}
Response:
{response.text}
''')
        exit(1)


def mark(id, reason):
    '''Dismiss an issue with the given reason.'''

    reason_text = REASONS.get(reason, reason)
    logging.info(f'Marking {id} as {reason}={reason_text}')

    graphql('dismiss-alert', id=id, reason=reason_text)


@click.command()
@click.option('--debug', is_flag=True, default=False)
@click.argument('repo', default='blog')
@click.argument('owner', default='jpverkamp')
@click.argument('package-regex', default='')
def main(repo, owner, debug, package_regex):
    '''
    A CLI to help quickly sort through github dependabot alerts.
    
    REPO: The repository to scan (defaults to 'ethos')
    PACKAGE_REGEX: An (optional) regex to only process packages matching this name 
    '''

    if debug:
        coloredlogs.install(level=logging.INFO)

    previously_marked = {}
    previously_skipped = set()

    count = 0
    cursor = 'first:100'
    while cursor:
        logging.info(f'Querying with {cursor=}')
        response = graphql('get-alerts', cursor=cursor, repo=repo, owner=owner)
        total_count = response['repository']['vulnerabilityAlerts']['totalCount']

        for alert in response['repository']['vulnerabilityAlerts']['nodes']:
            count += 1
            if alert['dismissedAt']:
                continue

            id = alert['id']
            path = alert['vulnerableManifestPath']
            description = alert['securityVulnerability']['advisory']['description']
            package = alert['securityVulnerability']['package']['name']
            severity = alert['securityVulnerability']['advisory']['severity']

            if package_regex and not re.search(package_regex, package):
                logging.info(f'Skipping {package}, does not match regex')
                continue

            CACHE_KEY = (package, description)
            previous_reason = previously_marked.get(CACHE_KEY)

            if not debug:
                print('\033[H\033[J', end='')
            print(f'[{count}/{total_count} {severity}] {package} in {path} ({id})\n\n{description}\n')

            if CACHE_KEY in previously_skipped:
                logging.info(f'Previously skipped {CACHE_KEY}')
                continue

            elif (
                'inefficient regular expression complexity' in description.lower()
                or 'regular expression denial of service' in description.lower()
                or 'redos' in description.lower()
            ):
                mark(id, 'Risk is tolerable to this project (regex dos/complexity)')

            elif (
                previous_reason
                and click.confirm(f'Previously marked "{REASONS.get(previous_reason, previous_reason)}", repeat', default=True)
            ):
                mark(id, previous_reason)

            else:
                option = click.prompt('''\
Please choose an option:
[s] Skip (default)
[t] Dismiss as "tolerable risk"
[r] Dismiss as "regex DoS/complexity"
[u] Dismiss as "not actually used"
[c] Dismiss with custom reason
[q] Quit
        ''', type=click.Choice('strucq'), default='s', show_choices=True, show_default=True)

                if option == 's':
                    previously_skipped.add(CACHE_KEY)

                    if CACHE_KEY in previously_marked:
                        del previously_marked[CACHE_KEY]

                    continue

                elif option == 't':
                    previously_marked[CACHE_KEY] = 'tolerable'
                    mark(id, 'tolerable')
                elif option == 'r':
                    previously_marked[CACHE_KEY] = 'tolerable-regex'
                    mark(id, 'tolerable-regex')
                elif option == 'u':
                    previously_marked[CACHE_KEY] = 'not-used'
                    mark(id, 'not-used')
                elif option == 'c':
                    reason = input('Reason: ')
                    previously_marked[CACHE_KEY] = reason
                    mark(id, reason)

                elif option == 'q':
                    exit(0)

            print('\n')

        pagination = response['repository']['vulnerabilityAlerts']['pageInfo']
        if pagination['hasNextPage']:
            logging.info(f'Advancing cursor to {pagination["endCursor"]}')
            cursor = f'first:100 after:"{pagination["endCursor"]}"'
        else:
            break


if __name__ == '__main__':
    main()
```

There are so many regex based denial of service issues that until we actually see them attacked, we're going to ignore them for the moment. You can remove that case easily enough if you disagree. Then other than that, bulk removal.

And that's it. Hope it's helpful, if nothing else at least for the GraphQL queries!
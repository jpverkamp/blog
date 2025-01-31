---
title: Iterating the GitHub API (For users sans MFA)
date: 2015-12-01
programming/languages:
- Python
programming/topics:
- GitHub
slug: iterating-the-github-api
---
Today I found myself auditing an organization's users to see which have [[wiki:multifactor authentication]]() enabled[^1]. Since we have a not insignificant number of users, I wanted to write a quick script to automate it. Down the rabbit hole I go... and now I have a clean way of iterating across paginated GitHub API responses.

<!--more-->

First, the full script:

```python
#!/usr/bin/env python3

import requests
import os

try:
    token = os.environ['GITHUB_TOKEN']
except:
    print('$GITHUB_TOKEN must be set with proper permission')
    sys.exit(0)

headers = {'Authorization': 'token {}'.format(token)}

def api_iterator(endpoint):
    url = 'https://api.github.com' + endpoint

    while True:
        response = requests.get(url, headers = headers)
        yield from response.json()

        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            return
```

The core of this script once again leans against the excellent <a href="http://docs.python-requests.org/en/latest/">Requests</a> library for Python. It makes making simple requests and parsing the <a href="http://www.w3.org/wiki/LinkHeader">HTTP Link Header</a> trivial. Also, `yield from` is pretty cool.

Basically, we use these instructions to <a href="https://help.github.com/articles/creating-an-access-token-for-command-line-use/">create a GitHub access token</a>. You'll need at least the organization rights, I don't have an exact list. Unfortunately, it doesn't look like there is a way to do this with a username, password, and MFA token. I tried a few variations but it kept claiming that I wasn't an owner of the organization. So it goes.

Now, if we wanted to use this for my original goal of finding users without MFA, you need the `/orgs/:organization/members` endpoint, with a specific filter:

```python
endpoint = '/orgs/{}/members?filter=2fa_disabled'.format(organization)
for user in api_iterator(endpoint):
    print(user['login'])
```

Alternatively, you can use it just as easily to get all of your repositories (similar to what I did for my post on [backing up GitHub repositories]({{< ref "2015-09-08-backing-up-github-repos.md" >}})):

```python
for repo in api_iterator('/user/repos'):
    print(repo['url'])
```

Cool. Hope it's helpful!

The full source for the MFA version is also available on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/missing-mfa.py">missing-mfa.py</a>

[^1]: As you should
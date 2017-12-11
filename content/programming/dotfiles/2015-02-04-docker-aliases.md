---
title: docker-bash and docker-stop-all
date: 2015-02-04
programming/topics:
- Docker
- Dotfiles
- Open Source
- Unix
---
I've been using <a href="https://www.docker.com/">Docker</a> a fair bit at work, so I've added a few quick aliases to my dotfiles make that a little bit easier:


* `docker-bash` - attach a `bash` shell to the first available docker instance
* `docker-stop-all` - stop all running docker instances


<!--more-->

The implementation for both is pretty straight forward:

`docker-bash`:

```bash
docker exec -it &#96;docker ps -q | head -n 1&#96; bash
```

`docker-stop-all`:

```bash
docker ps -q | xargs docker stop
```

Neither is *that* complicated to remember, but I type both often enough throughout the day that it's nice to save that dozen or so characters.

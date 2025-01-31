---
title: Ensuring docker-machine is running
date: 2016-04-19
programming/languages:
- ZSH
programming/topics:
- Docker
---
When developing using <a href="https://www.docker.com/">docker</a> on OS X, you'll currently[^1] have to use <a href="https://docs.docker.com/machine/">docker-machine</a> to spin up a virtual machine that is actually running the docker containers. Running a virtual machine takes up a bit more in the way of resources than just the docker containers, so if you're not actually developing at the moment, it's helpful to be able to start up the virtual machine only when you need it.

The current way I have to do that:

```bash
$ docker-machine start default
$ eval $(docker-machine env default)
```

What's worse, the latter command has to be run for every shell that you start up. It's by no means a hard pair of commands and you could easily wrap them in an alias or put them in your `.profile` equivalent (which is what I used to do). But unfortunately, I found a completely unrelated bug in <a href="https://github.com/tony/tmuxp">`tmuxp`</a>: if the shell takes too long to start up, `tmuxp` essentially won't work. The above `eval` command took long enough to hit this limit.

<!--more-->

So how do we fix it? Essentially (using <a href="http://www.zsh.org/">zsh</a>, my current shell of choice, although others should be similar):

```zsh
assert-docker() {
    command docker ps 2> /dev/null > /dev/null
    if [ $? -ne 0 ]; then
        echo "Starting docker..."
        docker-machine start default
        eval $(docker-machine env default)
        echo
    fi
}

docker () { assert-docker && command docker $@ }
docker-compose () { assert-docker && command docker-compose $@ }
```

The basic idea is that `assert-docker` first checks if `docker` is running by trying to run `docker ps`. `$?` contains the status code, which will be non-zero if `docker ps` failed, so check that. If that's the case, assume `docker ps` failed because `docker-machine` wasn't running, so start it up. This will run `docker-machine start default` more often than needed, but it turns out it's a `[[wiki:NOP]]()` if it's already running.

The only interesting part here is the use of the keyword `command` that prefixes `docker` or `docker-machine` within the functions. Basically, this tells ZSH to use the system version of `docker` or `docker-compose` rather than the one that I defined, thus preventing an infinite loop. Whee!

How's it work?

```bash
$ docker ps

Starting docker...
(dev) OUT | Starting VM...
Started machines may have new IP addresses. You may need to re-run the `docker-machine env` command.

CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES

$ docker ps

CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
```

Switching to another terminal:

```bash
$ docker ps

Starting docker...
Machine "default" is already running.

CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES

$ docker ps

CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
```

Neat. That should <a href="https://xkcd.com/1205/">eventually save me a fraction of the time</a> it took to get it right. :)

[^1]: <a href="https://blog.docker.com/2016/03/docker-for-mac-windows-beta/">Docker for Mac and Windows Beta</a> should help this
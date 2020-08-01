---
title: Docker Magic - Arbitrary docker runtimes in place
date: 2020-08-01
programming/topics:
- Docker
programming/languages:
- Fish
---
A quick post today.

I find myself working with a surprising number of different languages/environments day to day. In the last week, I've worked with PHP, Python, Go, Ruby, and Javascript. And different versions of several of those. While I could install something like [virtualenv](https://virtualenv.pypa.io/en/latest/) for Python / [rbenv](https://github.com/rbenv/rbenv) for Ruby / etc, I already have a tool exactly designed for this sort of thing: Docker!

<!--more-->

In a nutshell, what I made was a very very simple alias that lets me do this:

```bash
><> ^_^ jp@jupiter {git master} ~/Projects/mydata2
$ ls

Gemfile       Gemfile.lock  data/         models/       mydata.db     mydata.rb     packs.csv     public/       routes/       views/

><> ;_; jp@jupiter {git master} ~/Projects/mydata2
$ magic ruby -p 4567:4567

root@f9144a17cf7e:/Users/jp/Projects/mydata2# ls
Gemfile  Gemfile.lock  data  models  mydata.db  mydata.rb  packs.csv  public  routes  views

root@f9144a17cf7e:/Users/jp/Projects/mydata2# bundle install
Fetching gem metadata from https://rubygems.org/...
...
Bundle complete! 2 Gemfile dependencies, 8 gems now installed.
Use `bundle info [gemname]` to see where a bundled gem is installed.

root@f9144a17cf7e:/Users/jp/Projects/mydata2# ruby mydata.rb
...
/usr/local/bundle/gems/sinatra-2.0.8.1/lib/sinatra/base.rb:1526: warning: Using the last argument as keyword parameters is deprecated; maybe ** should be added to the call
/usr/local/bundle/gems/rack-2.2.3/lib/rack/handler/webrick.rb:26: warning: The called method `run' is defined here
[2020-08-01 18:19:48] INFO  WEBrick 1.6.0
[2020-08-01 18:19:48] INFO  ruby 2.7.1 (2020-03-31) [x86_64-linux]
== Sinatra (v2.0.8.1) has taken the stage on 4567 for development with backup from WEBrick
[2020-08-01 18:19:48] INFO  WEBrick::HTTPServer#start: pid=184 port=4567

...

><> ^_^ jp@jupiter {git master} ~/Projects/mydata2
$ docker ps

CONTAINER ID        IMAGE                         COMMAND                  CREATED              STATUS              PORTS                          NAMES
f9144a17cf7e        ruby                          "bash"                   About a minute ago   Up About a minute   0.0.0.0:4567->4567/tcp         strange_faraday
```

I don't have to have to have Ruby installed on my host system. Instead, I run `magic` with the container I want (and any other args, such as ports) and it will automatically run `bash` in the container and map the current directory into the container as the working directory.

The code?

```fish
#!/usr/bin/env fish

docker run -it -v (pwd):(pwd) -w (pwd) $argv[2..-1] $argv[1] bash
```

Okay, so it's not much, but it saves me typing `-it -v (pwd):(pwd) -w (pwd)` and the `bash` all the time. And it just works™. 

You can also specify tags:

```bash
><> ^_^ jp@jupiter /tmp/5cwqRAsB
$ magic python:2

root@eaebe94ec9e9:/tmp/5cwqRAsB# python --version
Python 2.7.18
root@eaebe94ec9e9:/tmp/5cwqRAsB# exit
exit

><> ^_^ jp@jupiter /tmp/5cwqRAsB
$ magic python:3

root@f99476788be0:/tmp/5cwqRAsB# python --version
Python 3.8.3
root@f99476788be0:/tmp/5cwqRAsB# exit
exit
```

Like I said, quick. 

I might extend it to detect things like requirements.txt and Gemfiles and automatically install packages (or possibly keep a volume between containers), but it's easy enough to do manually for now. 

I vaguely remember seeing someone else doing this before, but I can't find the link at the moment. If someone has seen it, let me know!
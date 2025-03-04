---
title: Performance problems with Flask and Docker
date: 2015-04-03
programming/languages:
- Python
programming/topics:
- AWS
- AWS EC2
- AWS ELB
- Docker
- Flask
- Networks
- Websites
- nginx
---
I had an interesting problem recently on a project I was working on. It's a simple <a href="http://flask.pocoo.org/">Flask</a>-based webapp, designed to be deployed to <a href="https://aws.amazon.com/">AWS</a> using <a href="https://www.docker.com/">Docker</a>. The application worked just fine when I was running it locally, but as soon as I pushed the docker container...

Latency spikes. Bad enough that the application was failing AWS's healthy host checks, cycling in and out of existence[^1]:

{{< figure src="/embeds/2015/health-check.png" >}}

<!--more-->

At that time, the only traffic to the container was the health checks, every 30 seconds, as regular as clockwork. So it wasn't load that was making them fail. And it was exactly the same code each time[^2][^3]:

```python
@app.route('/', methods = ['GET'])
def healthcheck():
    return "I'm a teapot"
```

So not that either. So what in the world was going on?

Google to the rescue! `<a href="https://www.google.com/search?q=flask application periodically slow">flask application periodically slow</a>`

The very first link is a response on StackOverflow:


> On operating systems that support ipv6 and have it configured such as modern Linux systems, OS X 10.4 or higher as well as Windows Vista some browsers can be painfully slow if accessing your local server. The reason for this is that sometimes “localhost” is configured to be available on both ipv4 and ipv6 socktes and some browsers will try to access ipv6 first and then ivp4. -- <a href="http://stackoverflow.com/questions/11150343/slow-requests-on-local-flask-server">Slow Requests on Local Flask Server</a>


Huh. Get a shell into my docker container, and what do you know:

```bash
$ cat /etc/hosts
172.17.1.112	27392a3e0fa5
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
```

Yup. `localhost` routes to both IPv4's `127.0.0.1` and IPv6's `::1`. Comment out the `::1` line and give it a shot... Yup. That did it. Waited ten minutes and the hosts weren't marked unhealthy once. All I should need to do is add it to the `Dockerfile` and we should be golden, yes?

```text
$ vi Dockerfile
...
RUN sed -i "s/::1.*//g"
...

$ docker build .
...
Step 9 : RUN sed -i "s/::1.*//g" /etc/hosts
 ---> Running in 7c73dc473507
sed: cannot rename /etc/sedXZv0Yy: Device or resource busy
```

What.

```text
$ vi Dockerfile
...
RUN sed "s/::1.*//g" /etc/hosts > /etc/hosts-new && mv /etc/hosts-new /etc/hosts
...

$ docker build .
...
RUN sed "s/::1.*//g" /etc/hosts > /etc/hosts-new && mv /etc/hosts-new /etc/hosts
 ---> Running in d6b896f4fc9e
sed: cannot rename /etc/sedqYrfxO: Device or resource busy
```

Double what.

Back to Google: `<a href="https://www.google.com/search?q=docker edit hosts">docker edit hosts</a>`

Specifically: <a href="https://github.com/docker/docker/issues/1951">Unable to modify /etc/hosts file in a container #1951</a>. Looks like there was a fix that would let you edit `/etc/hosts` if you were in a container (that used to not be possible), but (because it's actually mounted rather than just a container file), it's non-trivial to edit it as part of a build.

All righty then.

That's about when I decided to listen to the Flask documentation:

> You can use the builtin server during development, but you should use a full deployment option for production applications. (Do not use the builtin development server in production.)

All right. Not only is it what I'm actually supposed to be doing, but if I used CGI, I can avoid Flask trying to resolve `localhost` at all. I've worked with <a href="http://wiki.nginx.org/Main">nginx</a> before. Let's use that.

Picking some documentation from a hat, I decided to use <a href="https://uwsgi-docs.readthedocs.org/en/latest/">uWSGI</a> as the glue between nginx and Flask. Easy enough to install with pip (although I had to grab a C compiler from the apt package `build-essential`) and off we go.

First, a small `nginx` config:

```nginx
location / { try_files $uri @project; }
location @project {
    include uwsgi_params;
    uwsgi_pass unix:/tmp/uwsgi.sock;
}
```

Then, to start it all up, a change to the `Dockerfile` `CMD`:

```bash
CMD uwsgi -s /tmp/uwsgi.sock -w project:app --chown-socket=www-data:www-data --enable-threads & \
    nginx -g 'daemon off;'
```

That `--chown-socket` flag really drove me a bit batty. Basically, `uwsgi` was starting as the `root` user (within the Docker container). `nginx` was starting as `root`. But the `nginx` threads were not. They were starting as `www-data` and thus couldn't read the Unix socket between the two.

All righty then.

Let's go!

Starting successfully... And it's running. Not on the first try or even the 10th (I left out quite a bit of fumbling around tweaking flags), but eventually as was well in the world.

Push it out to AWS...

Health check passed.

Bam.

Awesome.

Now I not only have a neat little webapp, I have one that doesn't randomly decide to take forever on every other request or so.

If you're looking for the bare minimum `requirements.txt` and `Dockerfile` that I'm using (in addition to that `nginx` host configuration file above), here they are:

`requirements.txt`

```text
flask
flup6
uwsgi
```

`Dockerfile`:

```text
FROM ubuntu:14.04

RUN apt-get update && apt-get install -y build-essential nginx python3.4 python3.4-dev
RUN easy_install3 pip

WORKDIR /project

ADD requirements.txt /project/requirements.txt
RUN pip install -r requirements.txt

ADD . /project

ADD nginx /etc/nginx

CMD uwsgi -s /tmp/uwsgi.sock -w project:app --chown-socket=www-data:www-data --enable-threads & \
    nginx -g 'daemon off;'
```

It's for moments like these that I do software. That little moment when everything comes together just right and it all just ... works.

[^1]: The tighter spikes are when I was playing with the health check timeout to see if that would help
[^2]: See [[wiki:HTTP 418]]()
[^3]: I really want to implement that properly one day

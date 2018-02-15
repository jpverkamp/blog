---
title: Automatic self-signed HTTPS for local development
date: 2018-02-15
programming/topics:
- Docker
- nginx
- HTTPS
- Proxies
- TLS
- Web Development
---
From time to time when doing web development, you need to test something related to HTTPS. In some cases, the application you're writing already supports HTTPS natively and that's no problem. But more often (and probably better, in my opinion) is the case when you have another service (be it an AWS ELB or an nginx layer) that will terminate the HTTPS connection for you so your application doesn't have to know how to speak HTTPS.

In those cases, how can you test functionality that specifically interacts with HTTPS?

Today I will show you `autohttps`, a thin nginx proxy using Docker and a {{< wikipedia "self signed certificate" >}} to automatically create an HTTPS proxy in front of your application.

<!--more-->

# Setting up nginx

First, we need an nginx config file that will listen for HTTPS, terminate the encryption, and then talk over HTTP to the backend connection:

```nginx
server {
    listen 443 ssl;

    ssl on;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_certificate /etc/nginx/ssl/nginx.cert;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_pass http://localhost:80;
        proxy_read_timeout 90;
    }
}
```

First, we create an nginx `server` block that listens to the standard HTTPS port (443) and is expecting encrypted communication (`ssl`)[^ssl]. Then, we make sure `SSL` is on and tell it where we can find a certificate pair--we'll generate this in the next step.

After that, we want to redirect all traffic with a `location /` block. We're going to pass along the `host` header from the host and then set a couple of expected headers. In particularly the `X-Forwarded-Proto` header is often used by applications to determine if they need to be forwarding HTTP connections to HTTPS (since the application itself would otherwise not know that the client thinks we're speaking HTTPS, since all it sees is HTTP).

Finally, we'll pass the connections along to the local web server running on the standard HTTP port: 80 (we'll parameterize this in a bit).

# Setting up docker

Next, we're going to use Docker in order to turn that configuration file into an actual nginx instance:

```docker
FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -y nginx openssl

RUN mkdir -p /etc/nginx/ssl/ \
    && openssl req \
            -x509 \
            -subj "/C=US/ST=Denial/L=Nowhere/O=Dis" \
            -nodes \
            -days 365 \
            -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/nginx.key \
            -out /etc/nginx/ssl/nginx.cert

ADD nginx.conf /etc/nginx/sites-enabled/default

CMD nginx \
    && tail -f /var/log/nginx/*
```

We're starting with `Ubuntu 16.04` mostly since that's the current LTS version. I could use something more lightweight, but I'm most familiar with how Ubuntu works. Next, we'll install nginx and openssl, the two components we need to make this actually work.

After that, we need to set up a certificate. This is actually most of the work of this application, the correct parameters that `openssl` needs in order to make a valid (enough) certificate. This one will last for one year (`-days 365`) and is baked into the image so if you go longer than that, you'll have to regenerate the certificate. If this becomes a problem, that could be run in the `CMD` step intead.

And that's really all we need. We can already use it for what I need:

```bash
$ docker build -t autohttps .

Sending build context to Docker daemon  3.584kB
Step 1/7 : FROM ubuntu:16.04
 ---> 2a4cca5ac898
...
Successfully built f962bea5f236

$ docker run --rm -it -p 443:443 autohttps

...
```

Go to `https://localhost/` and we should have a glorious error page telling us we're using a self-signed cert...

Except it doesn't work.

Because Docker is running in a container, the `localhost` that's in the nginx config file is actually the Docker container. So it can't see a service running on the host or in another container. In order to work around that, we need to know what the host thinks it's IP address is. There are a few different ways to do that, but we're going ahead and use the relatively cross platform way: Python:

```python
import socket

local_ip = socket.gethostbyname(socket.gethostname())
```

We have to tweak one line of the nginx config:

```nginx
proxy_pass http://dockerhost:80;
```

And then we can then pass that into the Docker container on run:

```python
os.system(f'docker run --rm -it --add-host=dockerhost:{local_ip} -p 443:443 autohttps')
```

That command will add the IP that we found into the Docker container's hosts file so that when you would go to `http://dockerhost` in the container, you'll get the given IP without having to resolve it.

And that actually works. You get a nice warning page:

{{< figure src="/embeds/2018/connection-not-private.png" >}}

But if you click `Advanced` and `Proceed to localhost (unsafe)`, you get your server's content over HTTPS. Neat.

# Custom ports

One final thing I'd like to do is make the IP customizable (otherwise you need superuser permissions in order to bind something to ports 80 or 443). We'll wrap everything up in a neat Python script and do just that:

```python
arg_parser = argparse.ArgumentParser('Automatically map an HTTP port to HTTPS with a self signed certificate')
arg_parser.add_argument('--http-port', type = int, default = 80, help = 'The port your HTTP server is listening on')
arg_parser.add_argument('--https-port', type = int, default = 443, help = 'The port your HTTPS server should listen on')
arg_parser.add_argument('--rebuild', action = 'store_true', help = 'Force the container to rebuild')
args = arg_parser.parse_args()

local_ip = socket.gethostbyname(socket.gethostname())

def write_dockerfile(fout):
    fout.write('''\
FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -y nginx openssl

RUN mkdir -p /etc/nginx/ssl/ \
    && openssl req \
            -x509 \
            -subj "/C=US/ST=Denial/L=Nowhere/O=Dis" \
            -nodes \
            -days 365 \
            -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/nginx.key \
            -out /etc/nginx/ssl/nginx.cert

ADD nginx.conf /etc/nginx/sites-enabled/default

ENV HTTP_PORT 80
ENV HTTPS_PORT 443

CMD sed -i -e "s/HTTP_PORT/$HTTP_PORT/; s/HTTPS_PORT/$HTTPS_PORT/" /etc/nginx/sites-enabled/default \
    && nginx \
    && tail -f /var/log/nginx/*
''')

def write_nginx_config(fout):
    fout.write('''\
server {
    listen HTTPS_PORT ssl;

    ssl on;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_certificate /etc/nginx/ssl/nginx.cert;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_pass http://dockerhost:HTTP_PORT;
        proxy_read_timeout 90;
    }
}
''')

def build():
    temp_directory = tempfile.mkdtemp()

    with open(os.path.join(temp_directory, 'Dockerfile'), 'w') as fout:
        write_dockerfile(fout)

    with open(os.path.join(temp_directory, 'nginx.conf'), 'w') as fout:
        write_nginx_config(fout)

    subprocess.check_call('docker build -t autohttps .', shell = True, cwd = temp_directory)

    shutil.rmtree(temp_directory)

def run():
    subprocess.check_call('docker run --rm -it -e HTTP_PORT={http} -e HTTPS_PORT={https} --add-host=dockerhost:{ip} -p {https}:{https} autohttps'.format(
        http = args.http_port,
        https = args.https_port,
        ip = local_ip,
    ), shell = True)

if args.rebuild:
    build()

run()
```

The main interesting bit here is the changed nginx config (the ports are now just HTTP_PORT and HTTPS_PORT) and a Docker run line that will replace those:

```bash
sed -i -e "s/HTTP_PORT/$HTTP_PORT/; s/HTTPS_PORT/$HTTPS_PORT/" /etc/nginx/sites-enabled/default
```

Now we can map arbitrary ports and rebuild the container if/when things change:

```bash
$ autohttps --https-port 445 --http-port 8000
```

That will make `https://localhost:445` work and serve whatever is running on 8000. You can even run more than one of these at once if you have multiple applications you're testing. Neat. Also, it even works if the other application is running in a docker container as well, so long as you've exposed the port so it can be seen from the localhost[^dockernet].

It's all wrapped up in my dotfiles: [autohttps](https://github.com/jpverkamp/dotfiles/blob/master/bin/autohttps) (that's why the Dockerfile and nginx config are in the Python script rather than separate files). Give it a try and let me know what you think. 

[^ssl]: {{< wikipedia SSL >}} is the older protocol that later became {{< wikipedia TLS >}}. In modern applications, there is really no reason that you should actually support SSL or even TLS 1.0, but in many cases people will use the two terms interchangably.

[^dockernet]: Alternatively, you could put the two containers on the same Docker network, but I haven't had a need to do that yet.

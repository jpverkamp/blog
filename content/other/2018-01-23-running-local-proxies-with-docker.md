---
title: Running local proxies
date: 2018-01-23 00:00:05
programming/topics:
- Docker
- SSH
- Tor
---
As I've mentioned a couple of times recently[^refproxy] [^refssh], I have set a handful of different things on my local machines to make remote development a bit easier. This time around, I have two more to add to that list:

- Setting up a local SOCKS proxy with SSH
- Setting up a local TOR proxy for testing / more anonymous browsing
- Configuring your browser to use these proxies for some/all traffic

In both cases, I have these running on an always-on server that I use for various projects just like this. It could just as easily be set up to run on a [Raspberry Pi](https://www.raspberrypi.org/) or on your local machine.

<!--more-->

## Setting up a SOCKS proxy

First, let's set up a `SOCKS5` proxy. That's actually enough for most purposes, but if you really need an HTTP/HTTPS proxy, we can use [Polipo](https://www.irif.fr/~jch/software/polipo/)[^deprecated] on top of that.

To set up an SSH `SOCKS5` / `DynamicProxy`, the easiest way I've found is to add it to your SSH config:

```ssh
Host workproxy
    HostName bastion.example.com
    User jp
    Port 6622
    DynamicForward 7769
```

In this case, `bastion.example.com` is running SSH on port 6622, which we are connection to. We're then setting up the local port `7769` to accept incoming connections on the `SOCKS5` protocol. Then you open the tunnel with:

```bash
$ ssh workproxy
```

The SSH connection has to stay open in order to use the proxy, so it's best if you run it in a [tmux](https://github.com/tmux/tmux/wiki) or [screen](https://www.gnu.org/software/screen/) session (I prefer tmux personally). You could also use something like [autossh](http://www.debianadmin.com/autossh-automatically-restart-ssh-sessions-and-tunnels.html) to automatically restart it, but thus far, I've not particularly found it necessary.

## Adding an HTTP/HTTPS proxy

In most cases, that's all you need.

When I first set this up, I also wanted to be able to use an HTTP/HTTPS proxy, which meant that I wanted to use something like [Polipo](https://www.irif.fr/~jch/software/polipo/)[^deprecated]. Apparently though, in the face of pervasive HTTPS traffic, Polipo has is no longer being maintained. I actually learned this as I was writing the post. TIL.

In any case, the set up I had for Polipo was:

```bash
$ polipo \
    socksProxyType=socks5 \
    socksParentProxy=192.168.0.50:7769  \
    proxyPort=7770 \
    proxyAddress=::0 \
    allowedClients=192.168.0.0/24 \
    logFile=/dev/stdout \
    logLevel=0xFF
```

`socksProxyType` tells it that we're going to use an SSH `DynamicTunnel` proxy and `socksParentProxy` tells Polipo where it is. `proxyPort` is where the new Polipo proxy will be listening, while `proxyAddress` is necessary so that hosts on other machines can here it as well (this could be far more restrictive, but I'm using my router to prevent external traffic to that port, so I don't have to limit this). `allowedClients` lets other hosts on the same network connect and the last two options are just for logging.

That's really it. Set the `HTTP_PROXY` / `HTTPS_PROXY` environment variables (possibly with [Dynamic Automatic Proxies]({{< ref "2017-12-13-dynamic-automatic-proxy.md" >}}) :smile:) and many things will automatically use it. That's actually why I still have Polipo still running despite the deprecation warning. It does what I need it to do, in particularly when using the AWS CLI and/or the Python [requests](http://docs.python-requests.org/en/master/) library, which both accept HTTP/HTTPS proxies, but not SOCKS5.

If/when I can figure out how to configure those to use SOCKS5[^justworks], I can stop running Polipo, but until then, this works.

## Setting up a TOR proxy

Next up, we can use a TOR proxy. If you absolutely need a guarantee that none of your traffic is going to leak your identity (for any number of reasons), this is probably not the way you want to go. If that's the case, you should at least be running the [Tor Browser](https://www.torproject.org/projects/torbrowser.html.en). Or even better yet, run [Tails](https://tails.boum.org/) in a {{< wikipedia "virtual machine" >}} on a {{< wikipedia "burner laptop" >}}.

However, if you're just looking for a basic / better than nothing level of anonymity--which I generally use for testing things that should be restricted to internal networks or behave differently on externals ones.

In order to do this, you could either set up Tor yourself (which isn't that bad, but is a bit more involved) or you could just use [this](https://github.com/dperson/torproxy) [Docker](https://www.docker.com/) image:

```bash
docker run -it -p 8118:8118 -p 9050:9050 -d dperson/torproxy
```

That's it. It exposes a SOCKS5 proxy that routes to the TOR network on port 9050. That's it. If you wanted, you could put Polipo in front of it same as above for an HTTP/HTTPS proxy, but I haven't needed to.  

## Configuring your browser

Finally, we want to be able to use a browser to actually use these proxies. [Since 2013]({{< ref "2013-05-18-firefox-vs-chrome.md" >}}), I've been using Chrome. For proxying, [Proxy SwitchyOmega](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif?hl=en) works pretty well.

In order to use the SSH proxy, we set the host and port and then set the protocol to SOCKS5:

{{< figure src="/embeds/2018/proxy-switchyomega-ssh.png" >}}

Likewise for TOR:

{{< figure src="/embeds/2018/proxy-switchyomega-tor.png" >}}

One thing that I particularly enjoy about Proxy SwitchOmega is the ability to dynamically choose proxies based on hostname. For example, if I wanted to visit a {{< wikipedia ".onion" >}} domain (only available via Tor), I could set up a rule like this:

{{< figure src="/embeds/2018/proxy-switchyomega-onion.png" >}}

That way, normal traffic will not be proxied, but if I tried to go to [https://facebookcorewwwi.onion/](https://facebookcorewwwi.onion/) (for example)[^httpstor], it will automatically use my Tor proxy.

Neat.

[^refproxy]: [Dynamic Automatic Proxies]({{< ref "2017-12-13-dynamic-automatic-proxy.md" >}})
[^refssh]: [SSH Config ProxyCommand Tricks]({{< ref "2017-12-18-ssh-config-tricks.md" >}})
[^deprecated]: Which is apparently no longer being maintained? I had no idea. It works for what I'm using it for though?
[^justworks]: It might be easy, I honestly haven't tried since Polipo just works™.
[^httpstor]: Yup. Facebook via HTTPS via a Tor hidden service.

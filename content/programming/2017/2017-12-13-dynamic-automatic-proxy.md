---
title: Dynamic Automatic Proxies
date: 2017-12-13
programming/languages:
- Python
programming/topics:
- Command line
- Dotfiles
- Proxies
---
On of the advantages of working in computer programming is that I can work from anywhere I have a computer and an internet connection. One of the disadvantages is that many of the resources that I need to do my job are locked to only be accessible within a specific network (albeit with a [[wiki:bastion host]]()).

I long ago set up my SSH config to create an SSH tunnel and I can proxy many applications through that just by setting the `HTTP_PROXY` and/or `HTTPS_PROXY` environment variables. The downside of this though is that if I'm actually on a 'safe' network, there's no reason to use the bastion host and I would actually be putting extra load on it.

My goal: write something that would let me automatically proxy applications when I need to but not when I don't.

<!--more-->

The basic idea that I want is to be able to specify a command that I will run and, based on the exit code, either set proxy variables or not:

```bash
# On network

$ curl https://secure-subdomain.example.com
OK

$ autoproxied curl https://secure-subdomain.example.com
OK

# Off network

$ curl https://secure-subdomain.example.com
curl: (7) Failed to connect to secure-subdomain.example.com port 443: Operation timed out

$ autoproxied curl https://secure-subdomain.example.com
OK
```

So how do we do that? First, we need to collect a few command line parameters: {{< doc python "argparse" >}}.

```python
import argparse

arg_parser = argparse.ArgumentParser('Automatically set environment variables based on a condition')
arg_parser.add_argument('-c', '--condition', default = None, help = 'If this is set and returns true, set proxy variables; if not set, assume true')
arg_parser.add_argument('-x', '--invert', action = 'store_true', help = 'Invert the conditional so that proxy variables on false')
arg_parser.add_argument('-p', '--prefix', default = 'AUTOPROXY_', help = 'The prefix of environment variables to be copied')
arg_parser.add_argument('-v', '--verbose', action = 'store_true', help = 'Print out debugging information')
arg_parser.add_argument('command', nargs = '+', help = 'The command to run')
args, unknown = arg_parser.parse_known_args()
args.command += unknown
```

One interesting thing that I'm doing here is making use of the {{< doc python "ArgumentParser.parse_known_args" >}} function rather than {{< doc python "ArgumentParser.parse_args" >}}. What this does is ignore any parameters that I haven't explicitly configured and pass them back as a second return value. This lets me pass flags to the command I am proxying.

Next, we want to set up the environment we'll use for the `command`. Specifically, we need to call the `condition`. If it's true (or false and `invert` is set), update the environment for the command. If not, keep the same command:

```python
env = os.environ.copy()

if args.condition:
    with open(os.devnull, 'w') as fp:
        exit_code = subprocess.call(args.condition, shell = True, stdout = fp, stderr = fp)
else:
    exit_code = 0

if operator.xor(exit_code == 0, args.invert):
    logging.info('Setting environment variables:')

    for key, value in os.environ.items():
        if key.startswith(args.prefix):
            key = key[len(args.prefix):]
            env[key] = value
```

A new trick that I hadn't see before there: {{< doc python "os.devnull" >}}. If you ever need a file pointer that will just throw away anything you give it, there you go.

What this code assumes is that you have set a series of environment variables that you want copied without prefix. For example, if I want to set the `HTTP_PROXY` and `HTTPS_PROXY` variables, all I have to set is this[^polipo]:

```bash
AUTOPROXY_HTTPS_PROXY=192.168.0.50:7770
AUTOPROXY_HTTP_PROXY=192.168.0.50:7770
```

If `condition` returns true, these variables will be set:

```bash
HTTPS_PROXY=192.168.0.50:7770
HTTP_PROXY=192.168.0.50:7770
```

If you want to have multiple different `autoproxied` settings available, you can just use different prefixes.

Finally, run the command:

```python
logging.info('Running command: {}'.format(args.command))
exit_code = subprocess.call(args.command, env = env)
sys.exit(exit_code)
```

And now for a final trick, what if you want to automatically use `autoproxied`? You can use shell aliases. {{< doc python "subprocess.call" >}} doesn't use Shell configs, so even if you give the alias the same name, it won't collide[^mosh]. Using [Fish shell](https://fishshell.com/), I can automatically wrap my [ec2]({{< ref "2015-10-30-finding-ec2-instances-by-tag.md" >}}) script since the AWS API is only available when I'm on a specific network:

```fishshell
set -gx AUTOPROXY_HTTP_PROXY 192.168.0.50:7770
set -gx AUTOPROXY_HTTPS_PROXY 192.168.0.50:7770
alias ec2="autoproxied --condition='dig +short myip.opendns.com @resolver1.opendns.com | egrep \"^(10|50|52)\\.\"' --invert ec2"
```

What's going on with that command? Turns out [OpenDNS](https://www.opendns.com/) allows you to query their DNS server to get your IP address. There are a few services where you can do the same thing using `curl` to a web service instead, but `dig` will almost always be faster[^whydns]. I want to check if my IP starts with one of three specific IP ranges that will show I'm either already on the local network (`10.*`) or using a VPN hosted in our AWS range (`52.*`). It's not perfect, but it's been working well enough for me so far.

And... that's it. 50 lines, including some debugging and configuration: [autoproxied](https://github.com/jpverkamp/dotfiles/blob/master/bin/autoproxied).

Originally it was just designed for use with automatically choosing a proxy, but it's flexible enough that it can be used for anything that can be configured by environment variables. I'm going to have to see if there are any other problems that I can solve with this.

[^polipo]: I'm using [Polipo](https://www.irif.fr/~jch/software/polipo/) on a server on my home network to turn the SSH proxy into an HTTP/HTTPS proxy
[^mosh]: I picked up this when experimenting with [advanced-ssh-config](https://github.com/moul/advanced-ssh-config/).
[^whydns]: For one, a web service has to make a DNS request itself. For two, DNS uses [[wiki:UDP]]() rather than [[wiki:TCP]]() so there is no initial handshake.

---
title: SSH Config ProxyCommand Tricks
date: 2017-12-18
programming/topics:
- AWS
- AWS EC2
- Command line
- Dotfiles
- Proxies
---
Working in security/operations in the tech industry, I use {{< wikipedia SSH >}} a lot. To various different machines (some with hostnames, some without), using various different users and keys, and often (as was the case in my [previous post]({{< ref "2017-12-13-dynamic-automatic-proxy.md" >}})) via a {{< wikipedia "bastion host" >}}. Over the years, I've collected a number of SSH tricks that make my life easier.

<!--more-->

{{< toc >}}

# Using ProxyCommand to automatically use / not use an SSH tunnel

First up, almost all of the machines that I need access to cannot be SSHed to directly when I'm not on a specific network. Instead, I need to log in via a {{< wikipedia "bastion host" >}}. But if I do happen to already be within the network (SSHing from one machine to another for example), I don't want to connect via the bastion host any longer. Luckily, you can use `ProxyCommand` to do exactly that:

```text
Host bastion
    User jp
    IdentityFile ~/.ssh/keys/work/jp.rsa
    HostName bastion.example.com

Host work-server
    ProxyCommand bash -c "dig +short myip.opendns.com @resolver1.opendns.com | egrep '^(10|50|52)\\.' && nc %h %p || ssh bastion nc %h %p"
```

This uses the same [OpenDNS](https://www.opendns.com/) trick as my [previous post]({{< ref "2017-12-13-dynamic-automatic-proxy.md" >}})) along with Bash conditionals. If my IP starts with `10.`, I will use the `&& nc %h %p` part of the command, which will use {{< wikipedia netcat >}} locally to create the connection. If it does not, then I will set up an SSH tunnel using netcat instead (which will otherwise still use my local ssh config, so the bastion and final hosts can use different users/keys).

It's quite lovely to just be able to type `ssh work-server` and have things just work™ no matter if I'm on network or not.

# Using ProxyCommand to dynamically resolve 'fake' hostnames

Finally, we can actually use the same basic idea to dynamically resolve hostnames. Say we have a bunch of servers that we don't necessary known the IP for (and that don't have a hostname) but have a way to look it up. Perhaps we can use my previous [ec2 script]({{< ref "2015-10-30-finding-ec2-instances-by-tag.md" >}}) combined with [autoproxied]({{< ref "2017-12-13-dynamic-automatic-proxy.md" >}}) to automatically look up hosts in EC2 without having to spawn a subshell explicitly:

```text
Host *.aws
    ProxyCommand bash -c "nc $(ec2 $(echo %h | sed "s/.aws//") --ip) %p"
```

What that will do is allow you to SSH to `prod-frontend.aws` and automatically get logged into the private IP address of the first server with a tag matching `prod-frontend` (assuming you have the credentials to access said machine). Even better, you could (and probably would) combine it with the automatic SSH tunnel above:

```text
Host *.aws
    ProxyCommand bash -c "dig +short myip.opendns.com @resolver1.opendns.com | egrep '^(10|50|52)\\.' && nc %h %p || nc $(ec2 $(echo %h | sed "s/.aws//") --ip) %p"
```

It's ugly, but it totally works.

Note: `.aws` is actually a valid TLD: [ICANN .aws](https://icannwiki.org/.aws). If you need to actually SSH to a host using a `.aws` TLD, you could easily choose a different suffix.

# Automatically choosing SSH key based on user

Finally, as a non-ProxyCommand bonus, I have a number of different users that I use to SSH to various different machines, based on how limited access is to the machine or, in some cases, how old it is. In order to deal with that, I don't always want to type `ssh -i {key name} {user}@{host}`. Luckily, since [version 4.4](https://www.openssh.com/txt/release-4.4) SSH has has the ability to apply configuration sections conditionally based on various fields. One of those is the `User` being used for the connection:

```text
Match User jp
    IdentityFile ~/.ssh/keys/work/jp.rsa

Match User automation
    IdentityFile ~/.ssh/keys/work/automation.rsa

Match User superuser
    IdentityFile ~/.ssh/keys/work/superuser.rsa
```

In this case, logging into a remote machine using the `superuser` user and key is as easy as `ssh superuser@{host}`. Better yet, if I do need to override this setting for some reason, I can. The `-i` flag overrides the config file.

<hr>

And... that's it. There are a handful of other tricks I use to stay organized (like keeping my various SSH keys in folders), but those three tips save me the lion's share of time.

Along the way, I came across an interesting alternative: [advanced-ssh-config](https://github.com/moul/advanced-ssh-config). Basically, it's a 'smarter' system that can handle automatically proxying and some dynamic configuration for you. The one downside I've found is that I couldn't figure out how to quickly use the SSH tunnel when I need to but not when I don't. It has the ability to have fallback gateways, but the failover takes a long time. This just works.

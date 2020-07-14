---
title: A Smart MySQL Wrapper
date: 2020-07-07
programming/topics:
- Dotfiles
- MySQL
programming/languages:
- Python
- MySQL
---
One thing that I often need to do is deal with a large collection of database servers in different clusters and in different environments. On top of that, sometimes, I want a UI, sometime I want a CLI to script. And sometimes I'm on a VPN and sometimes I'm not. All together, it's a rather complicated number of saved connections and CLI switches and everything else. All together, I want:

* Specify the cluster, environment, and mode (read/write/adhoc)
* Specify if I want to run via CLI or via UI
* Specify an optional user with safely stored and used passwords
* Automatically connected via SSH tunnel if I'm not on VPN, but not if I am (for CLI or VPN)

Let's do it!

<!--more-->

# Parsing command line parameters

First problem, let's get some command line arguments. I'm going to use it like this:

```bash
$ my-mysql {environment} {cluster} {mode} [--ui] [--user {user}] [--verbose]
```

So that means we need to {{< doc python argparse >}} it like so:

```python
parser = argparse.ArgumentParser(description = 'MySQL wrapper, connects to a MySQL wrapper or runs a query from stdin')
parser.add_argument(dest = 'environment', help = 'Environment to run in, if an IP is specified it will be used as hostname')
parser.add_argument(dest = 'database', help = 'Database to connect to')
parser.add_argument(dest = 'mode', help = 'Mode to run in (read,write,adhoc)')
parser.add_argument('--ui', action = 'store_true', help = 'Launch in SQL pro')
parser.add_argument('-u', '--user', default = 'default', help = 'The credentials block to use')
parser.add_argument('-s', '--sshtunnel', default = 'my-tunnel', help = 'The SSH tunnel host to use')
parser.add_argument('-v', '--verbose', action = 'store_true', help = 'Run in verbose mode')
args = parser.parse_args()
```

# Determining DB hostname

Our hostnames are made somewhat easier by the fact that our DB folks have named the hosts nicely with CNAMEs everywhere, so that `{cluster}-{mode}.{domain}` always resolves to what we need. We just need a map of `environment` to `domain`:

```python
domain_map = {
    'prod': 'domain.com',
    'qa': 'staging-domain.com',
    'dev': 'development-domain.com',
}

if '.' in args.environment:
	host = args.environment
	args.mode = 'custom'
else:
	host = '{db}-{mode}.{domain}'.format(
	    db = args.database,
	    mode = args.mode,
	    domain = domain_map.get(args.environment) or args.environment,
	)
```

That takes care of connecting to the correct DB mode/host, but next we need to determine if we're on a VPN or not:

# VPN detection

```python
on_vpn = (os.system('dig +short myip.opendns.com @resolver1.opendns.com | egrep "^(10|50|52)\\." > /dev/null') == 0)
```

It's a trick I'd previously used in [Dynamic Automatic Proxy]({{< ref "2017-12-13-dynamic-automatic-proxy" >}}) and [SSH Config Tricks]({{< ref "2017-12-18-ssh-config-tricks" >}}), using DNS to tell what my local IP is. If it's in a private range (or in this case, an AWS IP starting with `50` or `52`), then I'm already on VPN and don't need another step. Otherwise, I do. 

# Connecting to the `mysql` client

Let's start with the CLI mode. If we're on VPN, connect directly. If not, we want to establish an SSH tunnel with the {{< doc python sshtunnel >}} library and then connect via that:

```python
env = os.environ.copy()
env['MYSQL_PWD'] = credentials['password']

if on_vpn:
    subprocess.check_call(
        ['mysql', '-A', '-h', host, '-u', credentials['user'], db_map.get(args.database) or args.database],
        env = env,
    )

else:
    with sshtunnel.open_tunnel((args.sshtunnel, 22), remote_bind_address = (host, 3306)) as tunnel:
        logging.info(f'Established SSH tunnel from {tunnel.local_bind_host}:{tunnel.local_bind_port} via {args.sshtunnel}:22 to {host}:3306')
        subprocess.check_call(
            ['mysql', '-A', '-h', '127.0.0.1', '-P', str(tunnel.local_bind_port), '-u', credentials['user'], db_map.get(args.database) or args.database],
            env = env,
        )
```

On additional trick is setting the `MYSQL_PWD` environment variable before calling the command with {{< doc python subprocess >}}. That way we can pass the password without it being displayed when we're in verbose mode. 

Connecting via the SSH tunnel was something that I was particularly proud of. Essentially, we can make an SSH tunnel via a {{< wikipedia "bastion host" >}} to the MySQL host inside a private network and then connecting to that tunnel, which in turn forwards the connection through the tunnel. It doesn't even cost that much performancewise. 

Because we're using `subprocess`, we can actually do fun things with pipes:

```bash
$ echo 'select * from users where user_id = 1337' | my-mysql prod primary adhoc
...

$ echo 'select * from files where creator_id in (' \
    (echo 'select user_id from users where creation_date > "2020-01-01"' | my-mysql prod primary adhoc | skiphead | commaify) \
    | my-mysql prod secondary adhoc
```

References for `skiphead` and `commaify`: [Tiny Helper Scripts for Command Line MySQL]({{< ref "2019-04-27-tiny-helper-scripts-for-command-line-mysql" >}})

Pretty cool. 

# Connecting via SequelPro

Next, I want to use a UI sometimes. Since I'm on a Mac, the best client I've found by far is [SequelPro](http://sequelpro.com/). At first, I despired at finding a way to launch SequelPro from a script, it doesn't have helpful switches for that. But then I came across `.spf` file associations. It turns out that `.spf` files are associated with SequelPro by default. So what is a SPF file? 

XML (more specifically a {{< wikipedia plist >}}!

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>version</key><integer>1</integer>
	<key>encrypted</key><false/>
	<key>format</key><string>connection</string>
	<key>ContentFilters</key><dict/>
	<key>auto_connect</key><true/>

	<key>rdbms_type</key><string>mysql</string>

	<key>data</key>
	<dict>
		<key>connection</key>
		<dict>
			<key>name</key><string>{user} @ {host} ({mode})</string>
			<key>colorIndex</key><integer>{color}</integer>

			<key>host</key><string>{host}</string>
            <key>database</key><string>{db}</string>
			<key>user</key><string>{user}</string>
			<key>password</key><string>{password}</string>

			<key>rdbms_type</key><string>mysql</string>

			<key>type</key><string>SPSSHTunnelConnection</string>
			<key>ssh_host</key><string>{tunnel}</string>
		</dict>
	</dict>

	<key>queryFavorites</key><array/>
	<key>queryHistory</key><array/>
</dict>
</plist>
```

It took a bit to work out coloring so that I could tell different type of connections apart (if you have enough tabs open, things go all sorts of sideways). We do have to have a file somewhere, so I used {{< doc python tempfile >}} to make a quick file and then tell the `system` to `open` it. It works pretty well. 

```python
path = os.path.join(tempfile.tempdir or '/tmp', 'db-{}-{}.spf'.format(host, args.mode))
os.makedirs(os.path.dirname(path), exist_ok = True)
logging.info('Using temporary file: {}'.format(path))

with open(path, 'w') as fout:
    fout.write(sqlpro_template.format(
        color = mode_color_map[args.mode],
        db = db_map.get(args.database) or args.database,
        host = host,
        user = credentials['user'],
        password = credentials['password'],
        mode = args.mode,
        tunnel = args.sshtunnel,
    ))

os.system('open "{}"'.format(path))
```

`tempfile` should automatically clean up the files (since they have passwords stored...), but just in case, we should deal with them ourselfs.

Now, there is a gotcha here. We always use the SSH tunnel. I could very easily select a template just without the `SPSSHTunnelConnection` key, it just hasn't really come up. 

And that's about it. Handy for me. Hope there is at lteast something interesting in there for you. 
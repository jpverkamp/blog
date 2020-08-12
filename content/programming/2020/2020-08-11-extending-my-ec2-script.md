---
title: Extending my EC2 script
date: 2020-08-11
programming/topics:
- AWS
programming/languages:
- Fish
- Python
---
Another quick post. 

What feels like a lifetime ago, I [wrote a post]({{< ref "2015-10-30-finding-ec2-instances-by-tag.md" >}}) about finding `ec2` instances by name. I honestly use that script just about every day, mostly for automatically finding instances to SSH to (a la [SSH config tricks]({{< ref "2017-12-18-ssh-config-tricks.md" >}})). But there are a few other quick things I've done with it:

* `ec2-script` - Run a script on all instances of a given name
* `ec2-disk` - A specialization of `ec2-script` to check main disk usage
* `terminate` - A script that I use with `ec2` to terminate instances from the command line
* `ec2-cycle` - Slow cycle a given set of `ec2` instances by terminating so many per minute

All of which are included in my [dotfiles](https://github.com/jpverkamp/dotfiles/tree/master/bin).

<!--more-->

# `ec2-script`

Run a command on every instance returned by `ec2`:

```fish
#!/usr/bin/env fish

for ip in (ec2 $argv[1] --ips)
    echo $ip
    ssh ubuntu@$ip $argv[2..-1]
    echo
end
```

Mostly, this is a loop I write all the time, so it's easier to wrap it in a script. I really do like [fish](https://fishshell.com/) scripting compared to bash. Slightly easier loops, more reasonable subshell syntax, and array slicing with better quoted argument behavior. Nice. 

You can do some pretty powerful things with this:

```fish
$  ec2-script app-server 'sudo docker exec -dt `sudo docker ps | awk \'/app/ { print $1 }\'` python scripts/do-stuff.py'
```

For each instance, look at the running docker containers, get the one named `app`, and run a Python command in that container. 


# `ec2-disk`

Another specialization of the above:

```fish
#!/usr/bin/env fish

ec2-script $argv[1] 'df -h | egrep /$'
```

This is a one liner that will find the disk usage specifically of the root disk (the one who's line ends with `/`). 


# `terminate`

This doesn't directly use `ec2`, but I almost always call it as `terminate (ec2 some-service --ip)`, so it might as well be:

```fish
#!/usr/bin/env fish

for ip in $argv
    set -lx instance_data (aws ec2 describe-instances --filters Name=private-ip-address,Values=$ip)
    set -lx instance_id (echo $instance_data | jq .Reservations[].Instances[].InstanceId | tr -d '"')
    if test "$instance_id" = ""
        echo "No instance found"
    else
        set -lx prompt "Terminate: $instance_id (name = "(echo $instance_data | jq -c '.Reservations[0].Instances[0].Tags[] | select(.Key == "Name") | .Value' | tr -d '"')") ? [y/N] "
        read -lp 'echo "$prompt"' confirm
        switch $confirm
            case Y y
                echo "Terminating $instance_id"
                aws ec2 terminate-instances --instance-ids $instance_id
        end
    end
end
```

You can of course do all of this with the built in `aws` CLI (I'm in fact doing eaxctly that), but remembering all that... nah.

# `ec2-cycle`

Finally, something a bit different, a script to cycle a fleet of servers:

```fish
#!/usr/bin/env fish

if test (count $argv) -eq 1
    set name $argv[1]
    set time 60
else if test (count $argv) -eq 2
    set name $argv[1]
    set time $argv[2]
else
    echo "Usage: ec2-cycle {name} {time=60}"
    exit
end

echo "Cycling $name, waiting $time second(s) between each cycle"

for ip in (ec2 $name --ips)
    echo $ip
    yes | terminate $ip
    sleep $time
end
```

It uses `terminate` above, slow cycling instances 1 per every given number of seconds. 
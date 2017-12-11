---
title: Parsing AWS instance data with jq
date: 2015-04-01
programming/languages:
- Bash
- JSON
programming/topics:
- AWS
- Unix
---
Semi-random amusing code snippet of the day:

```bash
aws ec2 describe-instances | jq << EOF
    .[][].Instances[]
    | select(.Tags[]?.Value == "production")
    | .PrivateIpAddress
EOF
```

<!--more-->

Basically, it's combining the <a href="https://aws.amazon.com/cli/">AWS command line tools</a> and the excellent <a href="https://stedolan.github.io/jq/">`jq`</a> tool for parsing JSON to extract a field from all instances with a particular tag on your AWS account (whatever account you have configured in your `~/.aws/` directory).

To describe it a little bit more, the data is structured as a list of `Instance` objects. The first line of the `jq` query loops over each instance object.

Next, each of those has zero or more `Tags` (the `[]?` is to not fail if the tag object is empty), with `Key` and `Value` entries. `select` is a new feature I hadn't seen before which will pass along an object if the condition holds. These are essentially equivalent:

```text
select(condition)
```

```text
if condition then . else empty end
```

After that, we extract a given field. In this particular case, I wanted IP addresses, but there are a bunch of other fields you can access. Here are a few other interesting ones:


* AmiLaunchIndex
* Architecture
* ImageId
* InstanceId
* InstanceType
* LaunchTime
* PrivateDnsName
* PrivateIpAddress
* PublicDnsName
* PublicIpAddress
* SecurityGroups
* State
* SubnetId
* Tags


The beauty of doing this directly in the shell is that you can then chain it to something else. For example, what if I wanted to log into every production server in turn and ask how much free disk space they have:

```bash
for IP in aws ec2 describe-instances | jq << EOF
    .[][].Instances[]
    | select(.Tags[]?.Value == "production")
    | .PrivateIpAddress
EOF
do
    echo $IP
    ssh $IP du -h
    echo
done
```

I'm really starting to admire the 'Do One Thing and Do It Well' philosophy of Unix and chaining things together.

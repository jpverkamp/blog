---
title: Clock drift in Docker containers
date: 2017-11-15
programming/topics:
- AWS
- Docker
---
I was working on a docker container which uses the aws cli to mess around with some autoscaling groups when I got a somewhat strange error:

```bash
A client error (SignatureDoesNotMatch) occurred when calling the DescribeAutoScalingGroups operation: Signature not yet current: 20171115T012426Z is still later than 20171115T012420Z (20171115T011920Z + 5 min.)
```

Hmm.

Are the clocks off?

<!--more-->

```bash
$ date
Sat Nov 14 21:21:54 EDT 2017

$ docker run alpine date
Sun Nov 15 01:26:58 UTC 2017
```

There's a time zone difference, but that's not a big deal. The big problem is that the clock has drifted just over five minutes...

A bit of Google later shows that it could be a problem with docker-for-mac: https://github.com/docker/for-mac/issues/1260. It seems that the virtual machine that docker is using under the hood is drifting. All that you have to do is set the hardware clock *of the virtual machine.

```bash
$ docker run --rm --privileged alpine hwclock -s
```

No output. Let's see if it worked:

```bash
$ date
Sat Nov 14 21:23:20 EDT 2017

$ docker run alpine date
Sun Nov 15 01:23:22 UTC 2017
```

Bam. The drift now is due to the time between me running the commands. Nothing else.

Weird. But fixable.

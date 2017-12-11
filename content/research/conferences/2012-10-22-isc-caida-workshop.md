---
title: ISC/CAIDA Workshop
date: 2012-10-22 23:00:58
programming/topics:
- DNS
slug: isccaida-workshop
---
I've spent the day in Baltimore at the <a title="ISC/CAIDA Workshop" href="http://rsf.isc.org/events/data-collab-workshop-2-2012/">ISC/CAIDA Data Collaboration Workshop</a> learning about and presenting about all things DNS related. It's not really the sort of thing that my PhD work is focusing on but it's still interesting.

<!--more-->

The presentation that I actually gave was *Rebuilding zone files from passive DNS data* (<a title="Rebuilding zone files from passive DNS data" href="research.jverkamp.com/papers/verkampj-isc-2012-slides.pdf">slides</a>):

> DNS zone files can be a great asset in security and networking research, yet they are available only for gTLDs, such as .com and .net, leaving out ccTLDs, such as .uk and .ru. Our collaborative project with CAIDA aims to leverage passive DNS queries from SIE and other data sources to rebuild zone files for all TLDs. I will describe the design challenges in implementing a practical system that accomplishes this goal. I will also discuss preliminary results on what percentage of zone files can be successfully reconstructed using this data.

Unfortunately, it still seems that a lot of my work has already been done (and done more thoroughly) by <a title="DNSDB@ISC" href="http://rsf.isc.org/projects/dnsdb/">ISC's DNSDB</a>, but at least that shows that it is/was a valid approach. If you have any questions / comments about the details, feel free to leave a comment below or send me an email.

Here are some of the other presentations I found particularly interesting:

**Eric Ziegast (ISC): *<a title="Building your own SIE" href="http://www.caida.org/workshops/isc-caida/1210/slides/isc1210_eziegast.pdf">Build your own SIE</a>***

The talk here was basically about how the SIE architecture works and what you can do about processing the data once you have access to it. I'd already gone through the talk once with him before, but there where still a few interesting bits I hadn't heard before.

**Robert Edmonds (ISC), *<a title="Sorted String Tables: ISC mtbl and ISC dnstable" href="http://www.caida.org/workshops/isc-caida/1210/slides/isc1210_redmonds.html">Sorted String Tables: ISC mtbl and ISC dnstable</a>***

The presenter basically explained how the DNSDB project actually goes about storing it's data in a way that doesn't just grow out of control. It's based on a similar idea to Google's {{< wikipedia page="Bigtable" text="BigTable file format" >}} (<a title="Bigtable: A Distributed Storage System for Structured Data" href="http://dl.acm.org/citation.cfm?id=1365816">original paper</a>). Essentially, it lets you store key/value data in a particularly quick and efficient way in exchange for making it immutable. It looks like an interesting work from a data structures perspective; I'll have to take a look at it at some point.

**Damon McCoy (George Mason University), *Manufacturing Compromise: The Emergence of Exploit-as-a-Service***

It turns out that exploit-as-a-service is kind of terrifying. There are software tools that look rather professional that will do all of the work of deploying and executing and exploit and just charge you a rental fee. It does make sense as it's a rather lucrative market--I had just never thought about it before. There was some talk about how long a malware site remains up and it seems that exploit domains only exist for as little as 2.5 hours, but even that is vastly overestimating how long it takes. According to one member of the audience, the majority of visits to spam sites take place within the first 20 minutes.

**Roberto Perdisci (University of Georgia), *<a href="http://www.caida.org/workshops/isc-caida/1210/slides/isc1210_rperdisci.pdf">FluxBuster</a>***

A flux network is a collection of machines that have been compromised by some sort of malware where an infected DNS resolver can switch from one to another quickly in effort to defeat IP based blacklists. The goal here was to use the SIE passive DNS data to monitor and detect such networks in real time.

As a semi-random side note, it's definitely been an interesting trip thus far:

* I flew Southwest for the first time (which was exciting--apparently they don't assign seats ahead of time...)
* The plane landed half an hour early. It turns out that I wouldn't have made the Light Rail I was planning on if we had landed on time as the last train of the night leaves at 8:40 pm.
* Walking around downtown Baltimore around 10 pm is a bit creepy. I'm still not so much a fan of large cities.
* I stayed at a [hostel](http://www.hiusa.org/baltimore "Hosteling International - Baltimore") in Baltimore. Pros: much cheaper and more interesting than a hotel; cons: dorm style rooms (smaller beds and snoring roommates).
* Walking during the day is much less creepy. Baltimore does have a feeling of age about it that you don't get as often in the US.

Let's hope the trip back isn't quite so interesting...
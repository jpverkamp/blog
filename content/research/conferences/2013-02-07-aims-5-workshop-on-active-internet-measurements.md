---
title: AIMS-5 - Workshop on Active Internet Measurements
date: 2013-02-07 14:00:41
programming/topics:
- Censorship
- DNS
- Networks
---
Yesterday was the first of three days for the fifth annual [ISC/CAIDA Workshop]({{< ref "2012-10-22-isc-caida-workshop.md" >}}) I went to in Baltimore back in October at least, but even the ones that weren't have still been interesting.

I'll be presenting on Friday and I'll share my slides when I get that far (they aren't actually finished yet). I'll be talking about new work that I'm just getting off the ground focusing specifically on DNS-based censorship. There is a lot of interesting ground to cover there and this should be only the first in a series of updates about that work (I hope).

<!--more-->

In any case, here are some of the presentations from the first day that I found particularly interesting / relevant to my research. Even those that I've left off were great presentations, but with my own limited focus, there are others I'm sure have summarized them better. If you'd like, you can see the entire agenda (along with links to many of the presentations) online <a title="AIMS-5 Agenda" href="http://www.caida.org/workshops/isma/1302/index.xml#agenda">here</a>.

My goal is to do the same for the next two days as well. Hopefully, this will force me to keep all of my notes straight and will act as a filter to help everything important settle in my memory.

**Ann Cox (Department of Homeland Security): **<a title="Internet Measurement and Attack Modeling Project" href="http://www.caida.org/workshops/isma/1302/slides/aims1302_acox.pdf">Internet Measurement and Attack Modeling Project</a>****

I'm pretty sure that I saw a similar presentation from her back at Usenix, but it was interesting to see how the focus changes slightly with a (slightly) less security and more measurement focused group. Specifically, she talked about <a title="Defense Technology Experimental Research" href="http://www.cyber.st.dhs.gov/deter/">DETER</a>, <a title="Protected Repository for the Defense of Infrastructure Against Cyber Threats" href="https://www.predict.org/">PREDICT</a>, and <a title="Software Assurance Marketplace" href="http://www.cyber.st.dhs.gov/swamp/">SWAMP</a> (they do like their acronyms...). Then there was a nice bit about {{< wikipedia "DNSSEC" >}} and Internet Measurement and Attack Modeling. Overall, a bit strongly government for my taste, but still interesting to see what's out there.

**Bradley Huffaker (UCSD/CAIDA), **<a title="DatCat: Overview, Lessons Learned, Current Status" href="http://www.caida.org/publications/presentations/2013/datcat_lessons_learned">DatCat: Overview, Lessons Learned, Current Status</a>****
**

<a title="DatCat: Home" href="http://www.datcat.org/">DatCat</a> is essentially a central index for publicly available research data, with tags and links to help bring researchers and data together. It's a great idea in theory, but a little rough to get people to work on in practice, so they've recently streamlined a lot of their requirements. Hopefully that will help bring more data to them. I should look into making some of my own data available through them.

**Srikanth Sundesaran (Georgia Tech),** **Localizing Performance Bottlenecks in Home Networks + State of Project BISmark**

<a title="Project BISmark" href="http://projectbismark.net/">Project BISmark</a> essentially aims to put a little device in your home network to unobtrusively actively measure parts of the internet that would otherwise be hard (if not impossible) to get access to. It's actually a really interesting take on measurement with 300 current nodes, roughly half of which are registered on their website (on 6 continents and more than 25 countries). I'm actually tempted to run one in my own home (or maybe my lab?), but I'm not sure how exciting my own personal network would be. We'll see.

**Sarthak Grover (Georgia Tech), **End-to-end Routing Behavior in the Internet: A Re-Appraisal from Access Networks** **

This talk seemed well paired with Project BISmark in that both were looking to measure home networks. In this case, they are looking for traceroute data, taking a software approach that actively sends out a trace to a known server every 70 minutes, followed by an incoming trace by the same 10 minutes after that. The goal is to map end-to-end routing behavior on the Internet and to that end, they've collected over a year's worth of data at 230+ home devices and 59 servers. I'd love to take a closer look at some of their routing information, but I don't know if I have the time.

**<a href="http://www.caida.org/workshops/isma/1302/abstracts.xml#NicholasWeaver">Nicholas Weaver</a> (ICSI), **ICSI Updates: Netalyzr****

<a title="ICSI Netalyzr" href="http://netalyzr.icsi.berkeley.edu/">Netalyzr </a>is a relatively simple (at least to the user) Java-based tool that runs in a web browser (or as a command line application) and analyzes your network, as the name suggests. It's really interesting and pinpointed a number of vulnerabilities that I hadn't even considered on my own laptop. Adding one of my own, they have something like 790,000 individual sessions recorded now, from over half a million unique IPs. With 20-70 new sessions coming in every hour, I can only imagine how such a network might be instrumented to actively keep tabs on censorship around the world. Unfortunately, I'm sure we'd again run into the problem that the most interesting countries are exactly those that won't have users using this tool, but one can hope. If I had one wish though, it was that Netalyzr were open source. I'd love to see how they run a few of their tests.

**Alistair King (UCSD/CAIDA), **<a title="Toward Realtime Visualization of Garbage" href="http://www.caida.org/publications/presentations/2013/realtime_visualization_garbage/">Toward Realtime Visualization of Garbage</a>****

I've seen CAIDA's research into {{< wikipedia page="Network telescope" text="darknets / network telescopes" >}} before--using portions of the IPv4 address space that aren't assigned to machines to observe large scale events on the Internet. Basically, they have a {{< wikipedia page="Cidr" text="/8 prefix" >}} (that's 16 million addresses) that captures a full packet trace for every single packet addressed to it. Right now, that's 150 TB of data, with another 4.5 TB added every month. Most of his talk was how in the world can you deal with that much data--either analyzing it or visualizing it. He had some very interesting slides showing generated maps that I wish I could link to, but I didn't catch the address. If I find it, I'll add it here.

Finally, there was the round table at the end about data sharing. Essentially, the goal was to come up with a list of data providers (particularly those at the workshop, but a few others were added that weren't represented) and talking a bit about the uses and drawbacks of each. Here's the list as best as I managed to get down, I'm sure I'm missing a few of them. (I've you run one that was mentioned and I've forgotten, please <a title="my email address" href="mailto:me@jverkamp.com">email me</a> and let me know)

* [BISmark](http://projectbismark.net/ "Project BISmark")
* [CAIDA](http://www.caida.org/home/ "CAIDA"): [Ark](http://www.caida.org/projects/ark/ "CAIDA - Ark"), etc
* [EdgeScop](http://www.aqualab.cs.northwestern.edu/projects/EdgeScope.html "EdgeScope")
* [ICSI](http://www.icsi.berkeley.edu/icsi/ "ISCI at UC Berkeley"): [Netalyzr](http://netalyzr.icsi.berkeley.edu/ "Netalyzr")
* [MobiPerf](http://www.mobiperf.com/ "MobiPerf")
* Reverse Traceroute data
* [RIPE](https://www.ripe.net/ "RIPE"): [Atlas](https://atlas.ripe.net/ "Home - RIPE Atlast") / [RIS](http://www.ris.ripe.net/ "RIPE Routing Information Services")
* [Route Views](http://www.routeviews.org/ "Route Views")
* [Simple Web](http://www.simpleweb.org/ "The Simple Web Homepage")

Personally, this is the sort of thing we should be doing more of. Research data needs to be available, at least to other researchers. Without being able to duplicate and validate results, you might as well just be making them up.

As a semi-random side note (tradition!), by complete random chance I met {{< wikipedia page="Paul Tanner" text="Paul Tanner's " >}}stepson in the shuttle on the way to the hotel. If you've ever heard the {{< wikipedia "Good Vibrations" >}} by the {{< wikipedia "Beach Boys" >}}, you've heard Paul Tanner. He played (and developed actually) the {{< wikipedia "electrotheremin" >}} heard in that piece. It's a small, strange world sometimes.

Also I went to stand in the ocean. Actually easier said than done; I'll just leave it at that...
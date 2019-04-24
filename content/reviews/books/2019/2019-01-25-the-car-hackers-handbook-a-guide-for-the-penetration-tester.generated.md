---
title: "The Car Hacker's Handbook: A Guide for the Penetration Tester"
date: 2019-01-25
generated: true
reviews/lists:
- 2019 Book Reviews
---
{{< goodreads book="The Car Hacker's Handbook: A Guide for the Penetration Tester" cover="true" >}}

> A car can be a daunting hacking target. Most cars don’t come with a keyboard and login prompt, but they do come with a possibly unfamiliar array of protocols, CPUs, connectors, and operating systems. This book will demystify the common components in cars and introduce you to readily available tools and information to help get you started. By the time you’ve finished reading the book, you’ll understand that a car is a collection of connected computers—there just happen to be wheels attached. Armed with appropriate tooling and information, you’ll have the confidence to get hacking.

Well. If you want a textbook to reference when you want to break into a car, this could be a good place to start. It's not really a good high level overview, since it spends most of the book on specific examples. While those are fascinating, they feel too low level and specific to actually read through all of them.  

<!--more-->

One bit worth reading is for an amusingly dry sense of humor:  

> You might find that you’re unable to shut the car down. This is a bad, but fortunately rare, situation. First, check that you aren’t flooding the CAN bus with traffic; if you are, stop and disconnect from the CAN bus. If you’re already disconnected from the CAN bus and your car still won’t turn off, you’ll need to start pulling fuses until it does.

And then you lean a few neat things. For example:  

> The California Air Resources Board (CARB) began testing roadside readers for OBD-III in 1994 and is capable of reading vehicle data from eight lanes of traffic traveling at 100 miles per hour.

> DSRC data rates depend on the number of users accessing the local system at the same time. A single user on the system would typically see data rates of 6 to 12Mbps, while users in a high-traffic area—say, an eight-lane freeway—would likely see 100 to 500Kbps. A typical DSRC system can handle almost 100 users in high-traffic conditions, but if the vehicles are traveling around 60 km/h, or 37 mph, it’ll usually support around only 32 users.

These are both talking about wirelessly talking to the car and getting various information out of it. Heck, they even talked about the idea of software updates being delivered over a peer-2-peer (vehicle-2-vehicle!) network, which is neat.  

In any case, I'm not really sure who this book is for. Someone that's definitely going to hack their car perhaps as a starter? Neat in theory. Probably something I'll never get around to in practice. So it goes.



---
title: Wombat IDE - A new way
date: 2012-04-11 04:55:36
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Up until now, the [Petite bindings]({{< ref "2012-01-19-wombat-ide-the-first-petite-versions.md" >}}) have been built around a threaded model where one thread existed solely to send new commands to the Petite process and another solely to read responses back. Mostly, this would stop <a title="Five Common java.lang.Process pitfalls" href="http://kylecartmell.com/?p=9">the problem</a> with the Java <a title="Java Process API" href="http://docs.oracle.com/javase/1.4.2/docs/api/java/lang/Process.html">Process</a> model that would cause it to deadlock if the data was not actually being consumed--the reading thread could act as a buffer in this instance.

<!--more-->

However, there's been a few problems with this model, mostly that it requires the rest of the code throughout the project to [[wiki:Polling (computer science)|poll]]() the Petite system when it wants input and that it's also difficult to split that input to multiple destinations (whenever one destination reads the data, it no longer exists for the others, so whoever reads has to forward it to everywhere else). In addition, each of the loops is written with a tight loop that must either constantly be eating up processor time or have a constant waiting time between polls which would in turn potentially slow down responses.

Because of this, I finally decided to go ahead and invert the model to a pushing model rather than a polling one.  Essentially, I've added a new set of events to the Petite codebase, such as OnOutput, OnError, etc. Whenever any of these events occurs, all of the event listeners of that type will be triggered, thus solving the problem with multiple destinations. In addition, because the events only fire when there is output from the Petite process, there is only one loop that has to busy-wait, rather than each loop that wanted to read from the Petite process as before.

I think that this will be a beneficial change all around and I hope that I got everything moved over correctly. I guess we'll find out soon enough.
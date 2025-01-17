---
title: Wombat IDE - Git
date: 2011-10-06 04:55:52
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Long story short, I switched from <a title="Apache Subversion" href="http://subversion.apache.org/">SVN</a> to <a title="Git" href="http://git-scm.com/">Git</a>. I could go probably go into a long list of reasons why, but really it comes down to two:

* I want a lightweight branching model (to keep things like the screen sharing out of the deployed builds)
* I want to learn a new version control system (I've used Git a bit, but this is the largest project I'm working on so will force me to learn more quickly)

It took a bit to get everything moved over, but I think everything is working correctly now. I'm still on Google Code, just using their Git back-end.

<!--more-->

One unfortunate bit is that the previous versioning system will not work any more. Previously, I was using the SVN revision number, but Git doesn't have consecutive revision numbers (it just doesn't make sense in the branching model), instead using SHA-1 hashes. So I needed a new model. Finally, what I settled on was using the Ant `tstamp`/`format` task to generate a daily build number:

```xml
<tstamp>
	<format property="version" pattern="1.D.k" />
</tstamp>
```

`D` is the `D` of the year (1-366) and `k` is the current hour (0-23). So basically, I can put out a new, unique build each hour and the version number will automatically be updated. I can't really think of much reason that I would need to actually deploy a version more often than this, but if so I could override the version number.

Under the new system, the new build (as of today) will be <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.278.21</a>.
---
title: Wombat IDE - Automatic updating
date: 2011-10-29 04:55:18
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
For a while now, we've been using Java Webstart to keep local copies of Wombat updated but I've been having issues keeping everything up to date. It doesn't seem that I'm the <a title="No Web Start" href="http://kylecordes.com/2006/auto-update-no-web-start">only one</a> either. So I've started writing my own update system, using a simple version file on the servers on campus that will automatically be fetched to verify that all of the files are up to date.

<!--more-->

```text
Wombat,{VERSION},Wombat-{VERSION}.jar
Kawa,1.11,kawa-1.11.jar
Infonode Docking Windows,1.6.1,idw-gpl.jar
```

The {VERSION} strings will be automatically replaced, as they are in the main Wombat file (where it sets the title bar. The others are the two libraries that we use, Kawa for the Scheme back-end and InfoNode for the dockable windows. Theoretically, only the first will generally change but the other two are included just in case.

The new version (with the auto-updater) is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">1.301.3</a>.
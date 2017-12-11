---
title: Wombat IDE - Shutdown hook
date: 2012-01-21 04:55:37
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
An interesting feature:

```java
Runtime.getRuntime().addShutdownHook(new Thread() {
	public void run() {
		NativeProcess.destroy();
	}
});
```

(`NativeProcess` is the Petite `Process` object.)

Theoretically, this code will run whenever the Java Virtual Machine shuts down normally, so if it crashes there will still be problems (although it's harder than you might think to get the JVM to crash unless you're specifically trying to do so).

I just thought that was neat and should avoid some of the problems that Odete was having with zombie processes.
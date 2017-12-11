---
title: Wombat IDE - And so it begins
date: 2011-07-26 05:10:00
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: and-so-it-begins
---
The second (and it turned out final) iteration of Wombat was based on <a title="java.com: Java + You" href="http://www.java.com/en/">Java</a>. With nearly 10 years of Java experience at that point, I could write Java code more quickly and efficiently than most other languages. In addition, it had the advantage of being portable, running on essentially every modern operating system with no changes to the deployed class files.

<!--more-->

The original project was hosted in a local <a title="Apache Subversion" href="http://subversion.apache.org/">SVN</a> repository and consisted of an <a title="Intellij IDEA Java IDE" href="http://www.jetbrains.com/idea/">IntelliJ IDEA</a> project which I almost immediately converted to a <a title="NetBeans Java IDE" href="http://netbeans.org/">NetBeans</a> project. My goal was a to have a simple and lightweight IDE that I could use to develop my desktop, laptop, or any of the machines at Indiana University.

So far as Scheme backend went, I was looking for something simple and fast that could easily be embedded in Java and hopefully would support the <a title="The Revised^6 Report on the Algorithmic Language Scheme" href="http://www.r6rs.org/">R6RS</a> Scheme Standard. The last was to ensure as much compatibility as I could with <a title="Chez Scheme Homepage" href="http://www.scheme.com/chezscheme.html">Chez Scheme</a> as many of the grading scripts used in the course are run using Chez Scheme. Here are the options that I considered and potential advantages or disadvantages of each one.

* [Jaja](http://pagesperso-systeme.lip6.fr/Christian.Queinnec/Java/Jaja.html "Jaja: Scheme in Java") \-- No longer active, old (written for Java 1.0.2 - 1.1.7), incomplete, Licensed under GPL v2
* [JScheme](http://norvig.com/jscheme.html "Jscheme: \(Scheme \(in Java \(by Peter Norvig\)\)\)") \-- Incomplete R4RS, old (Java 1.1)
* [Kawa](http://www.gnu.org/software/kawa/ "The Kawa Language Framework") \-- R6RS, actively developed, relatively large and complex project including more than just a Scheme, XIT/MIT license
* [SISC](http://sisc-scheme.org/ "Second Interpreter of Scheme Code") \-- R5RS, complete standard, claimed fasted, Licensed under MPL v1.1 and GPL v2

I removed Jaja and JScheme as they were too old. After trying both Kawa and SISC, I settled on SISC as it was much easier to embed in a Java program where Kawa seemed primarily focused on being a stand alone system. At this point, I was using Subversion revision numbers for my versioning system and with a good number of revisions before I got a successful release build, this build was known as r83. Prior to r75, I stored Wombat in a private SVN repository, but as of r75, I moved to Google Code at <a href="http://code.google.com/p/wombat-ide/">http://code.google.com/p/wombat-ide/</a>.

The first release of Wombat was somewhat underwhelming, but nevertheless supported multiple open documents; syntax highlighting for a limited number of keywords, strings, and comments; and bracket matching, all of which can be seen in the below screenshot.

{{< figure src="/embeds/2011/Wombat-build-83.png" >}}
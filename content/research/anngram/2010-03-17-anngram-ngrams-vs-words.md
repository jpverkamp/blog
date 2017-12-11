---
title: AnnGram - nGrams vs Words
date: 2010-03-17 05:05:37
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
**Overview**

For another comparison, I've been looking for a way to replace the nGrams with another way of turning a document into a vector.  Based on word frequency instead of nGrams, I've run a number of tests to see how the accuracy and speed of the algorithm compares for the two.

**nGrams**

{{< figure src="/embeds/2010/SOM-ngram.png" >}}

I still intend to look into why the Tragedy of Macbeth does not stay with the rest of Shakespeare's plays.  I still believe that it is because portions of it were possible written by another author.

<!--more-->

From Wikipedia:

*The text that survives had been plainly altered by later hands. Most notable is the inclusion of two songs from Thomas Middleton's play The Witch (1615); Middleton is conjectured to have inserted an extra scene involving the witches and Hecate, for these scenes had proven highly popular with audiences. These revisions, which since the Clarendon edition of 1869 have been assumed to include all of Act III, scene v, and a portion of Act IV, scene I, are often indicated in modern texts. *

Soon, I intend to try to remove the noted portions of my copy of the Tragedy of Macbeth to see if that makes it fit better with the others of Shakespeare's plays.

Timing:

* 32.5 seconds, error = 1.14
* 65.1 seconds, error = 0.54
* 97.9 seconds, error = 0.27
* 130.1 seconds, error = 0.11
* 164.5 seconds, error = 0.04
* 196.5 seconds, error = 0.01
* 230.1 seconds, error = 0.006
* 264.5 seconds, error = 0.002
* 300.3 seconds, error = 0.0007
* 336.3 seconds, error = 0.0001
* 372.5 seconds, complete

**Words**

{{< figure src="/embeds/2010/SOM-words.png" >}}

There is still some grouping; however, the groups that would otherwise have been William Blake and the Bible are not as distinct as they are when using nGrams.  This actually makes sense as William Blake uses a less complex set of words on average than Shakespeare, more similar to the writing in many of the books of the Bible.  nGrams, on the other hand, can capture the transitions between words, showing the differences in word usage between Blake and the Bible.

Timing:

* 34.4 seconds, error = 2.33
* 69.1 seconds, error = 1.38
* 103.7 seconds, error = 0.64
* 138.2 seconds, error = 0.25
* 172.5 seconds, error = 0.10
* 207.0 seconds, error = 0.03
* 241.3 seconds, error = 0.01
* 277.0 seconds, error = 0.004
* 314.6 seconds, error = 0.001
* 352.4 seconds, error = 0.0003
* 390.2 seconds, error = 0.0002
* 427.8 seconds, error = 0.0001
* 503.2 seconds, complete

**Results**

Essentially, the nGrams appear to produce better grouping more quickly.  Using the results from my last post, it appears that the SOM part of the code is providing a larger portion of my results, but both parts are working together to improve the results.  Replacing either with an alternative yields poorer results.
The text that survives had been plainly altered by later hands. Most  notable is the inclusion of two songs from {{< wikipedia "Thomas Middleton" >}}'s play *{{< wikipedia page="The Witch" text="The  Witch" >}}* (1615); Middleton is conjectured to have inserted an extra  scene involving {{< wikipedia page="Weird Sisters" text="the witches" >}} and {{< wikipedia page="Hecate#Hecate in literature" text="Hecate" >}}, for these scenes had proven highly popular  with audiences. These revisions, which since the Clarendon edition of  1869 have been assumed to include all of Act III, scene v, and a portion  of Act IV, scene I, are often indicated in modern texts
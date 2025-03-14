---
title: Crossing hands
date: 2014-02-27 04:55:39
programming/languages:
- Racket
- Scheme
programming/topics:
- Mathematics
- Time
---
Thirty second programming problem <a href="http://programmingpraxis.com/2014/02/25/crossing-hands/">from Programming Praxis</a>:

> Your task is to write a progam that determines how many times the hands cross in one twelve-hour period, and compute a list of those times.

Ready?

<img src="http://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/BahnhofsuhrZuerich_RZ.jpg/220px-BahnhofsuhrZuerich_RZ.jpg" />

<!--more-->

Go!

First thought: convert the hour hand into 'minute hand units'. The hour hand has 5 'minutes' to move each hour, so it moves ever twelves minutes. Combine that with those 5 minutes for each hour you've already passed and you have:

{{< latex >}}h_m = 5 h+ \left \lfloor m/12 \right \rfloor{{< /latex >}}

Loop over the 12 hours of a clock (with a bit of formatting):

```scheme
> (define f (curry ~a #:min-width 2 #:align 'right #:pad-string "0"))
> (for* ([h (in-range 12)]
         [m (in-range 60)]
         #:when (= m (+ (* h 5) (quotient m 12))))
    (printf "~a:~a\n" (f h) (f m)))
00:00
01:05
02:10
03:16
04:21
05:27
06:32
07:38
08:43
09:49
10:54
11:59
```

Bam. Quick, if you're near any of those times, wait and see if they actually do cross over. (Assuming of course that you still even have an analogue clock around...). 

Technically though, this problem doesn't even need programming to solve. You know that the hour hand must cross the minute hand once each hour. Furthermore, you know that there are twelve hours to go around the clock. Put these two together and you know that the two must cross eleven times ever twelve hours. Divide that out:

> 1 hour 5 minutes 27.27 seconds
> -- <a href="http://www.wolframalpha.com/input/?i=12+hours+%2F+11">Wolfram Alpha</a>

Repeatedly add that to midnight (rounding down, since we'll assume that the hour hand moves once per minute on the minute) and you should get those exact same numbers as above. Neat how that works out.

And that's it. Probably wasn't thirty seconds, but it's a neat little problem all the same. Fun to solve something quick every now and again.
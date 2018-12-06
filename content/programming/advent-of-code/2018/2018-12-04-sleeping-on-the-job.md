---
title: "AoC 2018 Day 4: Sleeping on the job"
date: 2018-12-04
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Repose Record](https://adventofcode.com/2018/day/4)

> **Part 1:** Given a log of guard shifts and times asleep/awake, calculate the guard that was asleep most often and which minute they were most asleep for.

<!--more-->

I'll admit, this one took me far longer than it should. Not because it's a particularly hard problem, but mostly because I missed a *very* important sentence in the puzzle description:

> While this example listed the entries in chronological order, your entries are in the order you found them. You'll need to organize them before they can be analyzed.

Since the input looks like this:

```
[1518-02-23 00:02] Guard #1913 begins shift
[1518-05-07 00:22] wakes up
[1518-07-23 00:26] wakes up
[1518-10-07 00:40] wakes up
[1518-02-18 00:02] Guard #263 begins shift
[1518-06-08 00:18] falls asleep
[1518-04-28 00:00] Guard #3301 begins shift
[1518-02-04 00:49] wakes up
[1518-09-08 00:13] falls asleep
```

I was dealing with all sorts of edge cases, such as:

- When a guard ends a shift while still asleep, add minutes up to the end of the hour
- If a guard logs waking up/falling asleep multiple times in a row, only take the last one
- If a guard sleeps across multiple days, log that properly

But it turns out if you actually *read* the problem description and sort the input, the problem gets much easier... Each record starts with a `begins shift`, will alternate `falls asleep` and `wakes up`, and will *always* end awake. Much easier.

Anyways. First thing we need is to read the data. I'm going to actually write a quick helper function that will read a file and iterate over lines in sorted order:

```racket
; Wrapper around in-lines to sort the values
; This is very important!
(define (in-sorted-lines [in (current-input-port)])
  (in-list (sort (port->lines) string<?)))
```

After that, we can read in the guard data:

```racket
; Read guard data from stdin
(define (read-guard-data [in (current-input-port)])
  (define-values (guard-data _id _state _last-minute)
    (for/fold ([data (hash)]
               [id #f]
               [state 'awake]
               [last-minute 0])
              ([line (in-sorted-lines in)])
      (match line
        ; Switching to a new guard
        ; If we had a previous guard that was asleep, finish their shift
        ; This doesn't appear to be the case any more
        [(regexp #px"Guard #(\\d+) begins shift" (list _ raw-new-id))
         (define new-id (string->number raw-new-id))
         (define new-data (if (eq? state 'asleep) (add-minutes data id last-minute 60) data))
         (values new-data new-id 'awake 0)]
        ; Current guard fell asleep, update their state
        [(regexp #px"(\\d+)\\] falls asleep" (list _ raw-minute))
         (define minute (string->number raw-minute))
         (values data id 'asleep minute)]
        ; Current guard woke up, record their asleep time
        [(regexp #px"(\\d+)\\] wakes up" (list _ raw-minute))
         (define minute (string->number raw-minute))
         (values (add-minutes data id last-minute minute) id 'awake minute)])))
  guard-data)
```

The goal is to read the data into a nested hash. The first key is the `id` of the guard, the second is the `minute`. The values are how many times that guard was asleep for that minute.

{{< doc racket match >}} with `regexp` values is really nice for parsing values. I left in one bit of the more complicated code (what happens if they end the shift asleep), but in the end it wasn't actually necessary.

In order to actually use this, we do have one more helper function that will increment the nested hash:

```racket
; Add minutes to guard `id` from `start` to `end`
(define (add-minutes data id start end)
  (define minute-hash (hash-ref data id (hash)))
  (define updated-minute-hash
    (for/fold ([minute-hash minute-hash])
              ([minute (in-range start end)])
      (hash-update minute-hash minute add1 0)))
  (hash-set data id updated-minute-hash))
```

Once we have all that data, we can solve the problem in what's probably an entirely overly verbose manner:

```racket
; Which guard was asleep for the most minutes
(define (most-asleep-minutes data)
  (define-values (max-id max-minutes)
    (for*/fold ([max-id #f]
                [max-minutes 0])
               ([(id sleep-data) (in-hash data)]
                [minutes-asleep (in-value (apply + (hash-values sleep-data)))]
                #:when (> minutes-asleep max-minutes))
      (values id minutes-asleep)))
  max-id)

; What minute was a given guard the most asleep for
(define (sleepiest-minute data id)
  (define-values (max-minute max-value)
    (for/fold ([max-minute #f]
               [max-value 0])
              ([(minute value) (in-hash (hash-ref data id (hash)))]
               #:when (> value max-value))
      (values minute value)))
  max-minute)

; Find the sleepiest guard and his most asleep minute
(define guard-data (read-guard-data))
(define sleepiest-guard-id (most-asleep-minutes guard-data))
(define break-in-minute (sleepiest-minute guard-data sleepiest-guard-id))

(printf "[part 1] guard: ~a, minute: ~a, product: ~a\n"
        sleepiest-guard-id
        break-in-minute
        (* sleepiest-guard-id break-in-minute))
```

Give it a run:

```bash
$ cat input.txt | racket snooze-detector.rkt

[part 1] guard: 3187, minute: 45, product: 143415
```

Works fine!

Of course, it took probably five failed attempts before I figured out the very important bit of information there...

One bit of code I particularly like is using a `for/fold` along with a `#:when` clause to find a maximum value. Pretty nice!

> **Part 2:** Find the one guard/minute that is mostly likely to be asleep.

To me at least, this is actually easier. You just need to find the highest value of any value in that entire hash:

```racket
; Find the overall sleepiest guard/minute
(define-values (max-guard-id max-minute _max-value)
  (for*/fold ([max-guard-id #f]
              [max-minute #f]
              [max-value 0])
             ([(id minute-data) (in-hash guard-data)]
              [(minute value) (in-hash minute-data)]
              #:when (> value max-value))
    (values id minute value)))

(printf "[part 2] guard: ~a, minute ~a: product: ~a\n"
        max-guard-id
        max-minute
        (* max-guard-id max-minute))
```

Same trick, simpler code. Weird that this was part 2. :shrug:

```bash
$ cat input.txt | racket snooze-detector.rkt

[part 1] guard: 3187, minute: 45, product: 143415
[part 2] guard: 2081, minute 24: product: 49944
```

*NOTE*: You may have noticed that I only have a Racket solution. Writing both up when I'm really just translating between the two took far more time than I expected; time I just don't have this month. So I'll do Racket and now and possibly backfill the Python solutions some day™. 

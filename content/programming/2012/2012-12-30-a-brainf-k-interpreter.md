---
title: A Brainf**k Interpreter
date: 2012-12-30 14:00:14
programming/languages:
- Brainf**k
- Racket
programming/sources:
- PLT Games
programming/topics:
- Esolangs
slug: a-brainfk-interpreter
---
The <a title="PLT Games" href="http://www.pltgames.com/">PLT Games</a> website has a competition going where each month there will be some sort of theme for a completely new program. The <a title="PLT Games: December 2012" href="http://www.pltgames.com/competition/2012/12">first theme</a> is a [[wiki:Turing Tarpit]]()--a language that is technically Turing complete and thus can do anything any other Turing complete language can, but is so minimal as to make doing anything worthwhile overly difficult.

> 54. Beware of the Turing tar-pit in which everything is possible but nothing of interest is easy.
> -- Alan Perlis, <cite>**[[wiki:Epigrams on Programming]]()**</cite>

To that end, I've been working on a little something special which I may or may not finish by the end of the month (yes, I know that's tomorrow). But while I was working on it, I put together a Brainf**k (BF) interpreter which I found pretty interesting to play with.

<!--more-->

The virtual machine that BF is designed to run on is made of a tape / series of cells, a pointer to a current location on that tape / current cell, and a sequence of instructions (8 plus 1 for debugging):

| > |            Move the cell pointer to the right             |
|---|-----------------------------------------------------------|
| < |             Move the cell pointer to the left             |
| + |                Add one to the current cell                |
| - |            Subtract one from the current cell             |
| , |       Read a value and store it in the current cell       |
| . |        Output the value stored in the current cell        |
| [ |    If the current cell is 0, jump past the matching ]     |
| ] | If the current cell is not 0, jump back to the matching [ |
| # |      *DEBUG*: Output the current values on the tape       |


Believe it or not, the first 8 instructions are all that you need to make a fully Turing complete language (just so long as either the tape is unbounded or the values that you can store in each cell are and you have at least 5). There are actually some really interesting proofs (if you're in to that sort of thing) available on the <a title="Esolang: Brainf**k" href="http://esolangs.org/wiki/Brainfuck#Computational_class">Esolang wiki</a>.

There are still a few choices to make if you're going to implement a BF interpreter: specifically how large your tape is, how large each value that you can store in a cell is, and how you treat reading an EOF character. For the sample implementation that I'm going to include below, the answers are unbounded, unbounded, and store a 0, although it would be easy enough to implement other options.

Speaking of implementation...

The first thing to do is set up the system. I've implemented two versions, either of which will allow the tape to grow in an unbounded manner. You can see the full source for both of them on <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/bf.rkt" title="GitHub: BF interpreter in Racket">my GitHub</a> if you'd like to follow along.

In this post, I'll be describing the second one that I wrote, which uses two lists for the values on the tape to the left and right, and a value between them for the current cell. For example, if the current tape has the values ... 0 0 1 2 3 4 5 0 0 ... and the pointer is at the 3, then the values of those variables would be:


| tape-left  | '(2 1) |
|------------|--------|
| tape-cell  |   3    |
| tape-right | '(4 5) |


Note how the 0s that stretch off indefinitely in either direction are not stored. I've made the interface for this somewhat clearer by defining the functions `car+` and `cdr+` which will act just as the normal `car` and `cdr`, except on `null?` lists will treat is as an infinite list of 0s. 

```scheme
>; special cdr and car that make infinite lists of 0s
(define (cdr+ ls) (if (null? ls) ls (cdr ls)))
(define (car+ ls) (if (null? ls) 0 (car ls)))
```

With that all out of the way, here's the start of our code. The first thing we need is the main loop:

```scheme
; loop across the tape 
(let loop ([pc 0]            ; current instructions
           [tape-left '()]   ; values on the tape to the left
           [tape-cell 0]     ; current cell on the tape
           [tape-right '()]) ; values on the tape to the right
  ...)
```

As mentioned, we're keeping track of the current program counter (`pc`) and the three variables that determine the tape. The tape starts with infinitely many 0s in either direction. 

The next step will be to dispatch on each character in the input in turn. We'll use a `case` statement for this. There's also the code to exit when we reach the end of the input. 

```scheme
; only keep running so long as we have more program to run
(when (< pc (string-length in))
  ; dispatch based on the current input
  (case (string-ref in pc)
     ...))
```

Next, the first two commands which move the current tape pointer either to the left (<) or to the right (>). For these, it's just a matter of using `cons`, `car+`, and `cdr+` to shift a value off one of the tape lists and put the current cell onto the other.

```scheme
; move the tape pointer to the left
[(#\<)
 (loop (+ pc 1)
       (cdr+ tape-left)
       (car+ tape-left)
       (cons tape-cell tape-right))]
```

Of course, the command to shift right would be much the same. 

Next, we have to be able to increment or decrement the current. Since that's just one of the looping variables, the code is also pretty straight forward:

```scheme
; increment the current cell
[(#\+)
 (loop (+ pc 1)
       tape-left
       (+ tape-cell 1)
       tape-right)]
```

The next two are a little more tricky since I wanted to either deal with numeric or character input. This will be controlled by the parameter `current-i/o-mode` which will either have the value `numeric` or `unicode`. There's a bit of code to choose the correct input and output functions and to deal with `eof-object`s, but it's still not too bad:

```scheme
; output the current cell
[(#\.)
 (case (current-i/o-mode)
   [(numeric) (display tape-cell) (display " ")]
   [(unicode) (display (integer->char tape-cell))]
   [else (error 'bf (format "invalid i/o mode: ~s" (current-i/o-mode)))])

 (loop (+ pc 1) tape-left tape-cell tape-right)]

; input into the current cell
; on eof, write 0
[(#\,)
 (define cin
   (case (current-i/o-mode)
     [(numeric) (read)]
     [(unicode) (read-char)]
     [else (error 'bf (format "invalid i/o mode: ~s" (current-i/o-mode)))]))

 (loop (+ pc 1) 
       tape-left
       (cond
         [(eof-object? cin) 0]
         [(eq? (current-i/o-mode) 'unicode) (char->integer cin)]
         [else cin])
       tape-right)]
```

Finally, we come to by far the most powerful part of the language, the branching/looping construct. The code for the two of these is actually pretty similar, but it's still non-trivial to write, basically requiring a loop to find the next **matching** bracket. 

```scheme
; jump past the matching ] if the cell under the pointer is 0
[(#\[)
 (if (= tape-cell 0)
     ; find the matching ]
     (let bracket-loop ([pc (+ pc 1)] [stk 1])
       (case (string-ref in pc)
         [(#\[) (bracket-loop (+ pc 1) (+ stk 1))]
         [(#\])
          (if (= stk 1)
              (loop (+ pc 1) tape-left tape-cell tape-right)
              (bracket-loop (+ pc 1) (- stk 1)))]
         [else
          (bracket-loop (+ pc 1) stk)]))

     ; otherwise, just skip
     (loop (+ pc 1) tape-left tape-cell tape-right))]
```

And that's pretty much it. There's still the debugging output, but that's pretty straightforward. If you'd like to see it, you can do so <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/bf.rkt" title="GitHub: BF interpreter in Racket">on GitHub</a>. 

All that being said, how does it actually work? Well, all we have is a new function `bf` that takes a string of BF code and interprets it. So let's try a few examples.

First, how about a simple cat program (copy the input to the output until we get an EOF):

```scheme
> (bf "
,   read the first character
[   loop while not eof (0)
 .  output the current character we just read
 ,  read another one
]
")
Hello World!
Hello World!
```

That was easy enough, how about a function to add two numbers:

```scheme
> (current-i/o-mode 'numeric)
> (bf "
,   read the first number into cell 0
>,  read the second number into cell 1
[   loop while cell 1 is not 0
 - remove one from cell 1
]
<.  move back to cell 0 and output
")
15 27
42
```

Or we can go with the ever-loved Hello World program (original code form the <a href="http://esolangs.org/wiki/Brainfuck#Hello.2C_World.21" title="Esolang Wiki: Brainf**k: Hello World!">Esolang Wiki</a>, comments added by me):

```scheme
> (current-i/o-mode 'unicode)
> (bf "
>           go to box 1
+++++++++   set box 1 to 9
[           if box 1 is 0 skip ahead
 <          go to box 0
 ++++++++   add 8 to box 0
 >          go to box 1
 -          subtrack 1 from box 1
]           if box 1 is not 0 skip back
            this will end up with 72 (9 * 8) in box 0 and 0 in box 1
<.>         go to box 0 output the 72 ('H') go to box 1
+++++++     set box 1 to 7
[           while box 1 is not 0
 <++++>-    add 4 to box 0 and subtract 1 from box 1
]           loop back until box 1 is 0 (7 times)
            now box 0 is 100 (72 minus 28) which would be 'd'
<+.         add 1 to box 0 (for 101 = 'e') and output
+++++++..   add 7 to box 0 (for 108 = 'l') and output twice
+++.        add 3 to box 0 (for 111 = 'o') and output
>>>         go to box 3
++++++++    set box 3 to 8
[           loop over that box
 <++++>-    add 4 to box 2 and subtract 1 from box 3
]           loop until 0
            now box 2 has 32 (8 * 4) and box 3 has 0
<.          go to box 2 and print (32 = ' ')
>>>         go to box 5
++++++++++  set box 5 to 10
[
 <
 +++++++++  add multiples of 9
 >-
]
<
---.        subtract 3 more for 87 (10 * 9 - 3)
<<<<.       go back to box 0 and output (111 = 'o')
+++.        add 3 and output (114 = 'r')
------.     subtract 6 and output (108 = 'l')
--------.   subtract 8 and output (100 = 'd')
>>+.        go to box 2 (which had 32) and add 1 (33 = '!') and output
")
Hello World!
```

If you don't want all of the comments, here's just the code:

```java
>+++++++++[<++++++++>-]<.>+++++++[<++++>
-]<+.+++++++..+++.>>>++++++++[<++++>-]<.
>>>++++++++++[<+++++++++>-]<---.<<<<.+++
.------.--------.>>+.
```

And that's about all I have for today. Hopefully I'll have my own Turing Tarpit up tomorrow (just in time!)

If you'd like to download the source code for today (with both this version and my first version using a hash table rather than lists for the tape), you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/bf.rkt" title="GitHub: BF interpreter in Racket">BF interpreter</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/hello.bf.rkt" title="GitHub: Hello world in BF">Hello World in BF</a>
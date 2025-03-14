---
title: Rock-paper-scissors
date: 2013-12-21 04:55:29
programming/languages:
- Racket
- Scheme
programming/topics:
- Artificial intelligence
---
Quick and to the point: let's write a program to play rock-paper-scissors[^1][^2].

<!--more-->

**

How do we do it? Well, first we need to decide on a scheme for user input. Since Racket is pretty much awesome and `read` will deal rather nicely with symbolic input, let's go ahead and use `rock` for rock, `paper` for paper, etc[^3]. Then we can impose an ordering on the three possible values:

```scheme
; Ordering function for rock/paper/scissors
(define (rps>? p1 p2)
  (or (and (eq? p1 'rock)     (eq? p2 'scissors))
      (and (eq? p1 'scissors) (eq? p2 'paper))
      (and (eq? p1 'paper)    (eq? p2 'rock))))
```

Now we want a [[wiki:REPL]]()--a read, eval, print loop. Basically, we want to `read` in input from the user, `eval`uate it as either a play or a special `quit` command, print out the results, and then loop back (unless we're told to `quit`.) Sounds straight forward enough:

```scheme
; Play a game of rock/paper/scissors against a given opponent
(define (play-rps brain)
  (printf "Enter rock, paper, or scissors (quit to exit).\n")

  ; Read player input, evaulate it, print response, loop (unless quit)
  (let repl ([wins 0] [rounds 0])
    (printf "> ")
    (define player (read))
    (case player 
      ; Playing a round, run the computer brain
      [(rock paper scissors)
       (define computer (brain))
       (printf " computer chooses ~a" computer)
       (cond
         ; Player beats computer
         [(rps>? player computer)
          (printf ", you win!\n")
          (brain 'lose)
          (repl (+ wins 1) (+ rounds 1))]
         ; Computer beats player
         [(rps>? computer player)
          (printf ", computer wins :(\n")
          (brain 'win)
          (repl wins (+ rounds 1))]
         ; Player and computer tie
         [else
          (printf ", it's a tie\n")
          (brain 'tie)
          (repl (+ wins 1/2) (+ rounds 1))])]
      ; Done player, print stats and exit
      [(quit)
       (printf "You won ~a%. Good job.\n" (round (* 100 (/ wins rounds))))]
      ; Who knows. Maybe if we repeat ourselves it will be helpful
      [else
       (printf "Unknown input.\nEnter rock, paper, or scissors (quit to exit).\n")
       (repl wins rounds)])))
```

One particular oddity that might stand out in this code is the usage of the `brain` function which is passed in as our opponent. There are two different ways that it could be called. Either it's called with no arguments in order to chose a next play or it's given a single argument (either `win`, `lose`, or `tie`) to potentially update the brain's internal state. That's really all you need to do some really interesting things as we get to later.

To start with though, let's make a really simple, completely random brain:

```scheme
(define (random-symbol)
  (list-ref '(rock paper scissors) (random 3)))

; Just choose at random
(define random-brain
  (case-lambda
    [()
     (random-symbol)]
    [(result)
     (void)]))
```

Here, we'll use `case-lambda` to control which way we're calling the function and a helper function to choose a random symbol (we'll need that again later). In this case, the update functionality never actually does anything. Let's see it in practice:

```scheme
> (play-rps random-brain)
Enter rock, paper, or scissors (quit to exit).
> rock
 computer chooses paper, computer wins :(
> rock
 computer chooses rock, it's a tie
> paper
 computer chooses scissors, computer wins :(
> scissors
 computer chooses rock, computer wins :(
> rock
 computer chooses paper, computer wins :(
> rock
 computer chooses paper, computer wins :(
> quit
You won 8%. Good job.
```

Sarcastic, isn't it? Anyways, let's try to right a few more brains. For example, what if we make a really stubborn brain that always chooses the same symbol, no matter what:

```scheme
; Always choose the same thing
(define (make-stubborn-brain favorite)
  (case-lambda
    [()
     favorite]
    [(result)
     (void)]))
```

Here we're using a higher order function. If we wanted to play with a stubborn brain, we'd do it something like this:

```scheme
> (play-rps (make-stubborn-brain 'rock))
```

Or perhaps one that tends to play in streaks and only rarely (and randomly) changes what they're going to play:

```scheme
(define (random-symbol-except not-me)
  (let loop ([maybe-me (random-symbol)])
    (if (eq? maybe-me not-me)
        (loop (random-symbol))
        maybe-me)))

; Tend to be 'streaky', potentially change reponse a given % of the time
(define (make-streaky-brain swap-chance)
  (define current-choice (random-symbol))
  (case-lambda 
    [()
     (when (< (random) swap-chance)
       (when (currently-chatty)
         (printf "It's okay, I didn't like ~a anyways...\n" current-choice))
       (set! current-choice (random-symbol-except current-choice)))
     current-choice]
    [(result)
     (void)]))
```

Interesting, you can also make the exact opposite (a brain that always changes) by upping that to 100%:

```scheme
> (play-rps (make-streaky-brain 1.0))
```

Now we have a second function that choose a random *different* symbol. Only sometimes do we change the state of the brain. Also mostly because it's amusing, we can now have chatty brains. To do that though, you'll have to turn on the `currently-chatty` parameter:

```scheme
> (parameterize ([currently-chatty #t])
    (play-rps (make-streaky-brain 0.25)))
Enter rock, paper, or scissors (quit to exit).
> rock
 computer chooses paper, computer wins :(
> scissors
 computer chooses paper, you win!
> scissors
It's okay, I didn't like paper anyways...
 computer chooses scissors, it's a tie
> quit
You won 50%. Good job.
```

Building on that idea, we could actually make use of the feedback and make a scaredy brain. For this one, it will play the same thing over and over until it loses and then switches.

```scheme
; Choose the same thing until you lose, then switch
(define scaredy-brain
  (let ([current-choice (random-symbol)])
    (case-lambda
      [()
       current-choice]
      [(result)
       (case result
         [(lose)
          (when (currently-chatty)
            (printf "Maybe ~a isn't so great after all...\n" current-choice)
            (set! current-choice (random-symbol-except current-choice)))])])))
```

It does have a pretty big weakness though, can you figure out what it is?

Finally, let's do something a little more complicated and make a copycat. Basically, whatever you play, it will play next round:

```scheme
; Copy the last thing the player chose
(define copycat-brain
  (let ([next-choice (random-symbol)])
    (case-lambda 
      [()
       next-choice]
      [(result)
       (set! next-choice
             (case (list next-choice result)
               [((rock win) (scissors tie) (paper lose)) 'scissors]
               [((rock tie) (scissors lose) (paper win)) 'rock]
               [((rock lose) (scissors win) (paper tie)) 'paper]))])))
```

That same technique could easily be used to always choose the symbol that would beat your last play (based on the idea that you'll be streaky). Why don't you try it out yourself?

Now we have a bunch of different brains, what if we wanted to play them against each other? Well, you can just write another function, a lot like `play-rps` above. Only this time, we'll pass in two brains and a number of rounds to play:

```scheme
; Play two computers versus each other for n rounds
(define (play-cpu/cpu brain1 brain2 rounds)
  (define wins
    (for/sum ([i (in-range rounds)])
      (define play1 (brain1))
      (define play2 (brain2))
      (cond
        [(rps>? play1 play2)
         (brain1 'win) (brain2 'lose)
         1]
        [(rps>? play2 play1)
         (brain1 'lose) (brain2 'win)
         0]
        [else
         (brain1 'tie) (brain2 'tie)
         1/2])))
  (printf "Player 1 won ~a% of ~a rounds.\n" (round (* 100 (/ wins rounds))) rounds)
  wins)
```

Let's write up a quick script to try all of the different brains off against each other:


|                | random | stubborn:rock | stubborn:paper | streaky:0.1 | streaky:1.0 | scaredy | copycat |
|----------------|--------|---------------|----------------|-------------|-------------|---------|---------|
|     random     |  50%   |      50%      |      50%       |     50%     |     50%     |   50%   |   50%   |
| stubborn:rock  |  50%   |      50%      |       0%       |     49%     |     50%     |  100%   |   50%   |
| stubborn:paper |  50%   |     100%      |      50%       |     53%     |     50%     |   0%    |   50%   |
|  streaky:0.1   |  50%   |      51%      |      48%       |     50%     |     50%     |   49%   |   50%   |
|  streaky:1.0   |  50%   |      50%      |      50%       |     50%     |     51%     |   50%   |   50%   |
|    scaredy     |  50%   |      0%       |      100%      |     50%     |     50%     |   50%   |   50%   |
|    copycat     |  50%   |      50%      |      50%       |     50%     |     50%     |   50%   |   50%   |


Yay for pretty much completely arbitrary comparisons![^4]

And that's all there is to it. Like always, I've got my code up on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/rps.rkt">jpverkamp:rps.rkt</a>

Enjoy!

[^1]: Or **[[wiki:roshambo]]() for those of you otherwise inclined
[^2]: Inspired by <a href="http://programmingpraxis.com/2013/12/10/rock-paper-scissors/">a post on Programming Praxis</a>
[^3]: You get the idea
[^4]: Can you figure out why almost all of them are 50%?
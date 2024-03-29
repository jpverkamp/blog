---
title: Cracker Barrel Peg Game, Part 3
date: 2014-07-10 09:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Games
- Graph Theory
series:
- Cracker Barrel Peg Game
---
If you were paying attention when I posted part 2 to GitHub (<a href="https://github.com/jpverkamp/small-projects/blob/master/blog/pegs.rkt">pegs.rkt</a>), you might have noticed a function I hadn't talked about: <code>play</code>

<!--more-->

With everything we've done over the past two posts, we have everything we need to actually play the peg game:

```scheme
(define (play p)
  (cond
    [(= 1 (count p))         (displayln "YOU WIN!")]
    [(= 0 (length (next p))) (display "You lose. :(")]
    [else
     (render-text p)
     (displayln "Enter the peg to use and the peg to jump")
     (define from (read))
     (define over (read))
     (cond
       [(jump p from over) => play]
       [else 
        (displayln "Invalid move.")
        (play p)])]))
```

Let's play!

```racket
> (play (invert (make-puzzle 1)))

        2   3   
      4   5   6   
    7   8   9   10  
  11  12  13  14  15  

Enter the peg to use and the peg to jump
4 2
          1   
            3   
          5   6   
    7   8   9   10  
  11  12  13  14  15  

Enter the peg to use and the peg to jump
9 5
          1   
        2   3   
              6   
    7   8       10  
  11  12  13  14  15  

Enter the peg to use and the peg to jump
12 8
          1   
        2   3   
          5   6   
    7           10  
  11      13  14  15  

Enter the peg to use and the peg to jump
11 7
          1   
        2   3   
      4   5   6   
                10  
          13  14  15  

Enter the peg to use and the peg to jump
14 13
          1   
        2   3   
      4   5   6   
                10  
      12          15  

Enter the peg to use and the peg to jump
3 5
          1   
        2       
      4       6   
        8       10  
      12          15  

Enter the peg to use and the peg to jump
12 8
          1   
        2       
      4   5   6   
                10  
                  15  

Enter the peg to use and the peg to jump
2 4
          1   

          5   6   
    7           10  
                  15  

Enter the peg to use and the peg to jump
6 5
          1   

      4           
    7           10  
                  15  

Enter the peg to use and the peg to jump
7 4
          1   
        2       

                10  
                  15  

Enter the peg to use and the peg to jump
1 2

      4           
                10  
                  15  

Enter the peg to use and the peg to jump
15 10
You lose. :(
```

Oops. 

Can you do any better? (Without using [part 1]({{< ref "2014-07-10-cracker-barrel-peg-game-part-3.md" >}})?)
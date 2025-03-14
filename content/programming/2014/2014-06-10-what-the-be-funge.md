---
title: "What the (be)funge\u203D"
date: 2014-06-10 14:00:29
programming/languages:
- Racket
- Scheme
programming/topics:
- Esolangs
slug: what-the-befunge%e2%80%bd
---
Here's a fun little bit of code for you:

```bash
55*4*v    _   v
v   <>:1-:^
    |:<$      <    ,*48 <
    @>0"zzif">:#,_$      v
>:3%!|    >0"zzub">:#,_$^
     >:5%!|
v "buzz"0<>:.           ^
         |!%5:           <
>:#,_   $>              ^
```

Gibberish you say? No! [[wiki:Befunge|Befuge]]()!

<!--more-->

More specifically:

> Befunge is a stack-based, reflective, esoteric programming language. It differs from conventional languages in that programs are arranged on a two-dimensional grid. "Arrow" instructions direct the control flow to the left, right, up or down, and loops are constructed by sending the control flow in a cycle. It has been described as "a cross between Forth and Lemmings."

-- [[wiki:Befunge|Wikipedia]]()

There's not much of a write up this time, since pretty much the entire code is the state machine that actually drives the language. We'll go ahead and assume that we have a whole suite of helper functions (see <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/befunge.rkt">GitHub</a> for details):


* `wrapped-vector-ref` - `vector-ref `where indexes out of bounds wrap
* `wrapped-vector-set!` - likewise for `vector-set!`
* `grid-ref` - ref for a vector of vectors, using wrapping
* `grid-set!` - set! for a vector of vectors
* `read-befunge` - read a befunge program from input
* `write-befunge` - write a befunge grid out for debugging


Next, we have the state of the machine. I'll store it in a parameter, so we can access it from a number of helper functions (up in a bit):

### State functions

```scheme
; Befunge state
(struct state (x y facing stack grid running) #:transparent #:mutable)
(define current-state (make-parameter #f))
```

Next, said helpers to manipulate the stack, move the pointer, and get the current character. All of them are safe to use even if there is no current state, they just won't do anything.

```scheme
; Stack maniuplation. Pop 0 on an empty stack
(define (pop!)
  (when (current-state)
    (define stack (state-stack (current-state)))
    (if (null? stack)
        0
        (begin0
          (car stack)
          (set-state-stack! (current-state) (cdr stack))))))

(define (push! v)
  (when (current-state)
    (set-state-stack! (current-state) (cons v (state-stack (current-state))))))

; Move in the current direction
(define (move!)
  (when (current-state)
    (case (state-facing (current-state))
      [(right) (set-state-x! (current-state) (+ (state-x (current-state)) 1))]
      [(left)  (set-state-x! (current-state) (- (state-x (current-state)) 1))]
      [(down)  (set-state-y! (current-state) (+ (state-y (current-state)) 1))]
      [(up)    (set-state-y! (current-state) (- (state-y (current-state)) 1))])))

; Get the current character from the state
(define (grid-@)
  (if (current-state)
      (grid-ref (state-grid (current-state)) 
                (state-x (current-state)) 
                (state-y (current-state)))
      #\space))
```

### Stepper

Now it's just a literal translation of the instructions into state transitions. I'll have one function to advance the state to make it easier to make a debugging rendering function:

```scheme
; Advance the befunge program to the next step
(define (step!)
  (when (and (current-state) (state-running (current-state)))
    ; Decode the next instruction
    (define cmd (grid-@))
    (case cmd
      ; Push this number on the stack
      [(#\0 #\1 #\2 #\3 #\4 #\5 #\6 #\7 #\8 #\9)
       (push! (string->number (string cmd)))]
      ; Addition: Pop a and b, then push a+b
      ; Subtraction: Pop a and b, then push b-a
      ; Multiplication: Pop a and b, then push a*b
      ; Integer division: Pop a and b, then push b/a, rounded down. If a is zero, ask the user what result they want.[dubious – discuss]
      ; Modulo: Pop a and b, then push the remainder of the integer division of b/a. If a is zero, ask the user what result they want.[dubious – discuss]
      ; Greater than: Pop a and b, then push 1 if b>a, otherwise zero.
      [(#\+ #\- #\* #\/ #\% #\`)
       (define a (pop!))
       (define b (pop!))
       (define op (cdr (assoc cmd `((#\+ . ,+) 
                                    (#\- . ,-) 
                                    (#\* . ,*)
                                    (#\/ . ,quotient) 
                                    (#\% . ,remainder)
                                    (#\` . ,(λ (b a) (if (> b a) 1 0)))))))
       (push! (op b a))]
      ; Logical NOT: Pop a value. If the value is zero, push 1; otherwise, push zero.
      [(#\!)
       (push! (if (zero? (pop!)) 1 0))]
      ; Change direction
      [(#\> #\< #\^ #\v)
       (set-state-facing! (current-state) (cdr (assoc cmd `((#\> . right) 
                                                            (#\< . left) 
                                                            (#\^ . up) 
                                                            (#\v . down)))))]
      ; Start moving in a random cardinal direction
      [(#\?)
       (set-state-facing! (current-state) (list-ref `(right left up down) (random 4)))]
      ; Pop a value; move right if value=0, left otherwise
      [(#\_)
       (set-state-facing! (current-state) (if (zero? (pop!)) 'right 'left))]
      ; Pop a value; move down if value=0, up otherwise
      [(#\|)
       (set-state-facing! (current-state) (if (zero? (pop!)) 'down 'up))]
      ; Start string mode: push each character's ASCII value all the way up to the next "
      ; Note: uses one fuel
      [(#\quote) ; (should be a quote character but that breaks syntax highlighting)
       (let loop ()
         (move!)
         (define c (grid-@))
         (when (not (equal? c #\quote)) ; ditto
           (push! (char->integer c))
           (loop)))]
      ; Duplicate value on top of the stack
      [(#\:smile:
       (define v (pop!))
       (push! v)
       (push! v)]
      ; Swap two values on top of the stack
      [(#\\)
       (define a (pop!))
       (define b (pop!))
       (push! a)
       (push! b)]
      ; Pop value from the stack and discard it
      [(#\$)
       (pop!)]
      ; Pop value and output as an integer
      [(#\.)
       (display (pop!))
       (display " ")]
      ; Pop value and output as ASCII character
      [(#\,)
       (display (integer->char (pop!)))]
      ; Trampoline: Skip next cell
      [(#\#)
       (move!)]
      ; A "put" call (a way to store a value for later use).
      ; Pop y, x and v, then change the character at the position (x,y)
      ; in the program to the character with ASCII value v
      [(#\p)
       (define y (pop!))
       (define x (pop!))
       (define v (pop!))
       (grid-set! (state-grid (current-state))
                  x y 
                  (with-handlers ([exn? (λ _ v)])
                    (integer->char v)))]
      ; A "get" call (a way to retrieve data in storage). 
      ; Pop y and x, then push ASCII value of the character at that position in the program
      [(#\g)
       (define y (pop!))
       (define x (pop!))
       (define v (grid-@))
       (push! (if (number? v) v (char->integer v)))]
      ; Ask user for a number and push it
      [(#\&)
       (display "Enter a number: ")
       (push! (read))]
      ; Ask user for a character and push its ASCII value
      [(#\~)
       (display "Enter a character: ")
       (push! (read-char))
       (newline)]
      ; End program
      [(#\@)
       (set-state-running! (current-state) #f)])

    (move!)))
```

There are a few interesting cases:


* `#\"` - nested loop to read the rest of a string (counts as one 'step')
* `#\\#` - one `move!` is called here, the next at the end of the function
* `#\p` - we're extending support out to the full [[wiki:Unicode]]() character set, but not every integer represents a code point, so for those store the number instead
* `#\@` - trust that the caller will actually check the `state-running` parameter


### Main loop

Around that, we need a loop that just keeps calling `step!` until `state-running` is false. Something like this:

```scheme
; Run a befunge program
(define (run-befunge [input   (current-input-port)] 
                     #:debug  [debug #f] 
                     #:fuel   [fuel +inf.0])
  ; Load the grid
  (define grid
    (cond
      [(input-port? input) (read-befunge input)]
      [(string? input) (call-with-input-string input read-befunge)]
      [(vector? input) input]))

  ; Set up initial state (x y facing stack grid running)
  (parameterize ([current-state (state 0 0 'right '() grid #t)])
    (let loop ([step 0])
      (when (and (state-running (current-state))
                 (< step fuel))
        (when debug
          (write-befunge (state-grid (current-state)))
          (printf "~a x ~a, ~a\nstack: ~a\n\n" 
                  (state-x (current-state))
                  (state-y (current-state))
                  (state-facing (current-state))
                  (state-stack (current-state))))

        (step!)
        (loop (+ step 1))))))
```

I went ahead and stuck in a debug view (which will print out the grid, cursor, and stack on each step) and a limited fuel on the case that we don't want to accidently run a program for forever.

### Examples

And that's all we need. Let's test it with a few sample programs:

#### Hello World (Wikipedia)

```scheme
> (run-befunge)
>              v ; hello world
v  ,,,,,"Hello"< ; source: wikipedia
>48*,          v
v,,,,,,"World!"<
>25*,@

Hello World!
```

#### Hello World (Wikipedia)

```scheme
> (run-befunge)
>25*"!dlrow ,olleH":v  ; hello world v2
                 v:,_@ ; source: wikipedia
                 >  ^ 

Hello, world!
```

#### Fizz Buzz (RosettaCode)

```scheme
> (run-befunge)
55*4*v    _   v            ; fizz buzz
v   <>:1-:^                ; source: rosettacode
    |:<$      <    ,*48 <  
    @>0"zzif">:#,_$      v 
>:3%!|    >0"zzub">:#,_$^  
     >:5%!|                
v "buzz"0<>:.           ^  
         |!%5:           < 
>:#,_   $>              ^

1  2  fizz 4  buzz fizz 7  8  fizz buzz 11  fizz 13  14  fizzbuzz 16  17  fizz 19  buzz fizz 22  23  fizz buzz 26  fizz 28  29  fizzbuzz 31  32  fizz 34  buzz fizz 37  38  fizz buzz 41  fizz 43  44  fizzbuzz 46  47  fizz 49  buzz fizz 52  53  fizz buzz 56  fizz 58  59  fizzbuzz 61  62  fizz 64  buzz fizz 67  68  fizz buzz 71  fizz 73  74  fizzbuzz 76  77  fizz 79  buzz fizz 82  83  fizz buzz 86  fizz 88  89  fizzbuzz 91  92  fizz 94  buzz fizz 97  98  fizz buzz
```

#### Random digit generator (Wikipedia)

```scheme
> (run-befunge #:fuel 1000)
v>>>>. ; random digit generator
 12345 ; source: wikipedia
 ^?^
> ? ?^
 v?v
v6789>

4 3 5 7 1 8 5 1 7 3 3 2 6 3 5 8 5 1 4 9 9 2 6 4 5
```

Looks pretty good from here!

### Pretty pretty pictures

One last trick, let's do much the same that we did a [bit ago]({{< ref "2014-05-28-quadtree-image-compression.md" >}}) and make a rendering function:

#### Hello World (Wikipedia)

{{< figure src="/embeds/2014/hello-world.gif" >}}

#### Random digit generator (Wikipedia)

{{< figure src="/embeds/2014/random.gif" >}}

#### Fizz Buzz (RosettaCode)

(Limited to 10 in interest of time)

{{< figure src="/embeds/2014/fizz-buzz.gif" >}}

And that's it. Check out the full source on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/befunge.rkt">befunge.rkt</a>

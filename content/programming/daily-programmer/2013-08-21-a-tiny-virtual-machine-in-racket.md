---
title: A 'Tiny' virtual machine in Racket
date: 2013-08-21 00:00:28
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Assemblers
- Compilers
- Memory
- Virtual Machines
---
<a href="http://www.reddit.com/r/dailyprogrammer/comments/1kqxz9/080813_challenge_132_intermediate_tiny_assembler/">Today's challenge</a> at /r/dailyprogrammer asks to implement an assembler for a small virtual machine. It has only 16 [[wiki:Assembly language#Opcode mnemonics and extended mnemonics|mnemonics]]() which in unique [[wiki:Opcode|opcodes]]() (each instruction can have multiple forms for if they're accessing memory or literals), so it's a simple virtual machine indeed. As a challenge, you're supposed to write an interesting program (I actually wrote a virtual machine as well to test them). As an even better challenge, we're supposed to prove that Tiny is [[wiki:Turing complete]](). Well, let's get to it!

<!--more-->

There's a bit more code than normal, so I made it into its own repository. You can check it out here: <a href="https://github.com/jpverkamp/tiny">tiny on GitHub</a>

First, here's a short version of the specification of the language showing just the opcodes. Many of these instructions have multiple versions depending on if you're accessing memory or using a literal. For example, `MOV [0] 5` moves the literal value 5 into memory index 0 while `MOV [0] [5]` moves the value in memory index 5 to 0. In the following table, `[a]` represents a memory address, `a` represents a literal and `[a]?` represents that a value can be either. Here are the opcodes:

|     AND/OR/XOR `[a]` `[b]?`     |           `[a]` = `[a]` and/or/xor `[b]?`            | `0x00 - 0x05` |
|---------------------------------|------------------------------------------------------|---------------|
|            NOT `[a]`            |                  `[a]` = not `[a]`                   |    `0x06`     |
|        MOV `[a]` `[b]?`         |                    `[a]` = `[b]?`                    | `0x07 - 0x08` |
|          RANDOM `[a]`           |                `[a]` = a random byte                 |    `0x09`     |
|      ADD/SUB `[a]` `[b]?`       |           `[a]` = `[a]` plus/minus `[b]?`            | `0x0a - 0x0d` |
|           JMP `[x]?`            |              jump to instruction `[x]?`              | `0x0e - 0x0f` |
|        JZ `[x]?` `[a]?`         |     jump to instruction `[x]?` if `[a]?` is zero     | `0x10 - 0x13` |
| JEQ/JLS/JGT `[x]?` `[a]` `[b]?` | jump to instruction `[x]?` if `[a]` = / < / > `[b]?` | `0x14 - 0x1f` |
|              HALT               |                   stop the program                   |    `0xff`     |
|      APRINT/DPRINT `[a]?`       |   print `[a]?` as an ASCII character or a decimal    | `0x20 - 0x23` |

That `a` can be literal for `JZ` is a little strange (why would we jump if a literal value is zero or not?), but other than that, everything seems pretty standard. So what's the first step? For me, I want to define the structure of the eventual virtual machine. The original code calls for 256 cells of memory, each of which can hold a byte. But since we eventually want to simulate an arbitrary Turing machine (one of the ways to prove Turing completeness), we're going to have unlimited memory instead. For that, we'll use a hash:

```scheme
; Represent memory as a hash to allow for unlimited memory
(define current-memory (make-parameter (make-hasheq)))
(define memory
  (case-lambda
    [(key)     (hash-ref! (current-memory) key 0)]
    [(key val) (hash-set! (current-memory) key val)]))
```

This gives us two important pieces. Whenever we run the function, we'll {{< doc racket "paramterize" >}} over `current-memory` so that each function has it's own memory space. Technically, this also allows for a future expansion I want to add: function calls. For now though, all we have to know is that `memory` acts as a parameter itself. Calling it with one argument reads a value (memory defaults to all zeros, `hash-ref!` sets a default in the hash if the value doesn't currently exist); calling it with two write a new value. So something like `(memory a (+ (memory a) (memory b))` is a direct translation of `ADD [a] [b]`.

In addition to that, we want a program counter. That will just be another simple parameter:

```scheme
; Represent the current program counter
(define current-pc (make-parameter 0))
```

And finally, a third parameter to help `HALT` along: 

```scheme
; Set this to halt the virtual machine
(define currently-running (make-parameter #f))
```

Okay, we have all of that. But now we need some instructions. I would like to abstract this out as much as possible (so we can easily change out for more languages), so everything will be stored in a pair of data structures. We'll have a hash from mnemonic to a list of possible implementations and a another that goes from opcodes to a specific version. Something like this:

```scheme
; Store instructions for the current virtual machine
(define-struct multiop (arity ops) #:transparent)
(define-struct op (name arity code pattern app) #:transparent)
(define current-instructions (make-parameter (make-hasheq)))
(define current-opcodes      (make-parameter (make-hasheq)))
```

A `multiop` associates a mnemonic with multiple `op`s, each of which has the opcode, variable pattern (which are memory references and which are literals), and an application for that function written in Racket. Of course, we don't want to have to enter there all manually, that's a lot of copying and pasting. We'd rather type something like this:

```scheme
(define-op (AND a b)
  [#x01 ([a] [b]) (? (a b) (memory a (bitwise-and (memory a) (memory b))))]
  [#x02 ([a] b  ) (? (a b) (memory a (bitwise-and (memory a) b)))]))
```

So here's a macro that will do exactly that:

```scheme
; Macro to define instructions
; Add them both to the name -> multiop hash and the opcode -> op hash
(define-syntax-rule (define-op (NAME ARGS ...) [OPCODE (PARAMS ...) APP] ...)
  (let ()
    (define arity (length '(ARGS ...)))

    (define ops 
      (for/list ([opcode  (in-list '(OPCODE ...))]
                 [pattern (in-list '((PARAMS ...) ...))]
                 [app     (in-list (list APP ...))])
        (op 'NAME arity opcode pattern app)))

    (hash-set! (current-instructions) 'NAME (multiop arity ops))

    (for/list ([opcode (in-list '(OPCODE ...))]
               [op     (in-list ops)])
      (hash-set! (current-opcodes) opcode op))

    (void)))
```

Essentially, it does exactly what it says on the tin: defines an op. To do that, we do some pattern matching magic to pull apart a sequence of rules. I'm not going to go through it piece by piece, but trust that it does work.

With that, we can define any of our opcodes. But we don't want to. There's still a heck of a lot of copying and pasting between different sets. For example, `AND`/`OR`/`XOR`/`ADD`/`SUB` (and `AND` actually) are all the same except for the operator they apply. So let's write another layer of macros to handle that:

```scheme
(define-syntax-rule (define-simple-pair NAME OP1 OP2 f)
  (define-op (NAME a b)
    [OP1 ([a] [b]) (? (a b) (memory a (f (memory a) (memory b))))]
    [OP2 ([a] b  ) (? (a b) (memory a (f (memory a) b)))]))

(define-simple-pair AND #x00 #x01 bitwise-and)
(define-simple-pair OR  #x02 #x03 bitwise-ior)
(define-simple-pair XOR #x04 #x05 bitwise-xor)

(define-simple-pair MOV #x07 #x08 (? (a b) b))

(define-simple-pair ADD #x0a #x0b +)
(define-simple-pair SUB #x0c #x0d -)
```

Easy enough. Some though, we can't do this way and have to just write. Like `NOT` and `RANDOM`:

```scheme
(define-op (NOT a)
  [#x06 ([a]) (? (a) (memory a (bitwise-not (memory a))))])

(define-op (RANDOM a)
  [#x09 ([a]) (? (a) (memory a (random 256)))])
```

Since they don't match any other parameter patterns, the first two jumps we have to define separately as well:

```scheme
(define-op (JMP x)
  [#x0e ([x]) (? (x) (current-pc (memory x)))]
  [#x0f (x)   (? (x) (current-pc x))])

(define-op (JZ x a)
  [#x10 ([x] [a]) (? (x a) (when (zero? (memory a)) (current-pc (memory x))))]
  [#x11 ([x] a)   (? (x a) (when (zero? a) (current-pc (memory x))))]
  [#x12 (x   [a]) (? (x a) (when (zero? (memory a)) (current-pc x)))]
  [#x13 (x   a)   (? (x a) (when (zero? a) (current-pc x)))])
```

But now we can write a macro for the other three:

```scheme
(define-syntax-rule (define-comparison-jump NAME OP1 OP2 OP3 OP4 f)
  (define-op (NAME x a b)
    [OP1 ([x] [a] [b]) (? (x a b) (when (f (memory a) (memory b)) (current-pc (memory x))))]
    [OP2 (x   [a] [b]) (? (x a b) (when (f (memory a) (memory b)) (current-pc x)))]
    [OP3 ([x] [a] b)   (? (x a b) (when (f (memory a) b) (current-pc (memory x))))]
    [OP4 (x   [a] b)   (? (x a b) (when (f (memory a) b) (current-pc x)))]))

(define-comparison-jump JEQ #x14 #x15 #x16 #x17 =)
(define-comparison-jump JLS #x18 #x19 #x1a #x1b <)
(define-comparison-jump JGT #x1c #x1d #x1e #x1f >)
```

Then finally, we have `HALT` and the print functions:

```scheme
(define-op (HALT)
  [#xff () (? () (currently-running #f))])

(define-syntax-rule (define-print NAME OP1 OP2 f)
  (define-op (NAME a)
    [OP1 ([a]) (? (a) (f (memory a)))]
    [OP2 (a)   (? (a) (f a))]))

(define-print APRINT #x20 #x21 (? (byte) (display (integer->char byte))))
(define-print DPRINT #x22 #x23 (? (byte) (display byte)))
```

There we have it. Everything is nicely defined. Now we can get into the real meat of the code: parsing, assembling, and running.

First parsing. This is actually trivial. Since everything in the input is either a symbol, a number, or a list, Racket's `read` function will handle it just fine:

```scheme
; Parse instructions from input
(define (parse [in (current-input-port)])
  (port->list read in))
```

All `port->list` will do is repeatedly call the first argument on the second. This will give us a list of symbols, numbers, and numbers in lists, something like this:

```scheme
> (define TEST-CODE "
MOV [0] 5
MOV [1] 7
ADD [0] [1]
DPRINT [0]
HALT
")
> (call-with-input-string TEST-CODE parse)
'(MOV (0) 5 MOV (1) 7 ADD (0) (1) DPRINT (0) HALT)
```

Next, we have to assemble the functions. Since that's the actual problem at hand, we'll look at that a little more carefully although it's not a terribly long function. First, the entire function:

```scheme
; Assemble a list of ops
(define (assemble code)
  (cond
    [(null? code) '()]
    [else
     (define name (first code))
     (define multiop (hash-ref (current-instructions) name))
     (define params (take (rest code) (multiop-arity multiop)))
     (define op
       (let loop ([ops (multiop-ops multiop)])
         (cond
           [(null? ops)                
            (error 'assemble "unmatched pattern ~a for ~a\n" params name)]
           [(matched-patterns? params (op-pattern (first ops))) 
            (first ops)]
           [else
            (loop (rest ops))])))
     `(,(op-code op) ,@(flatten params) . ,(assemble (drop code (+ 1 (multiop-arity multiop)))))]))
```

The first interesting part is the decoding. We'll pull the `first` thing in the current `code` list out as the mnemonic. That lets us access the `(current-instructions)` hash and figure out the arity of the function we're working on. After that, we'll use the `let loop` to find which op matches that (to get the op code). That needs the `matched-patterns?` function:

```scheme
; Match two patterns of possibly matching lists
(define (matched-patterns? ls1 ls2)
  (or (and (null? ls1) (null? ls2))
      (and (not (null? ls1))
           (not (null? ls2))
           (or (and (list? (first ls1)) 
                    (list? (first ls2))
                    (matched-patterns? (rest ls1) (rest ls2)))
               (and (not (list? (first ls1)))
                    (not (list? (first ls2)))
                    (matched-patterns? (rest ls1) (rest ls2)))))))
```

It looks complicated, but all it says is that the patterns have to be the same length and when there's a list in one, it has to be in both. That way `((a) b)` will match `((0) 5)` but not <code((0) (5))</code>. 

Finally, we build the opcode with this line:

```scheme
`(,(op-code op) ,@(flatten params) . ,(assemble (drop code (+ 1 (multiop-arity multiop)))))
```

It uses quasiquote to build the list, but if you're not familiar with that, it's essentially the same as this:

```scheme
(append (list (op-code op)) (flatten params) (assemble (drop code (+ 1 (multiop-arity multiop)))))
```

And that's it. Now we can assemble the code:

```scheme
> (assemble (call-with-input-string TEST-CODE parse))
'(8 0 5 8 1 7 10 0 1 34 0 255)
```

It doesn't print in hex, but those are the correct values. To see them in hex, we can use these:

```scheme
(define (format-hex byte)
  (format (if (< byte 16) "0x0~x" "0x~x") byte))

(define (bytecode->string code)
  (string-join (map format-hex code) " "))
```

```scheme
> (bytecode->string (assemble (call-with-input-string TEST-CODE parse)))
"0x08 0x00 0x05 0x08 0x01 0x07 0x0a 0x00 0x01 0x22 0x00 0xff"
```

That would be the end of the actual challenge. But I already have all of these functions defined, so let's go ahead and run them! The `run` function isn't actually any longer than the `assemble` function:

```scheme
; Run a given assembled code
(define (run code)
  (define vcode (list->vector code))
  (parameterize ([current-pc 0] [current-memory (make-hasheq)] [currently-running #t])
    (let loop ()
      (define op (hash-ref (current-opcodes) (vector-ref vcode (current-pc))))
      (define args 
        (for/list ([i (in-range (+ 1 (current-pc)) (+ 1 (current-pc) (op-arity op)))])
          (vector-ref vcode i)))
      (current-pc (+ (current-pc) 1 (op-arity op))) ; Apply first to not break jumps
      (apply (op-app op) args)
      (when (currently-running)
        (loop)))))
```

Essentially, we turn the code into a vector (since we're going to be jumping around a bit). Then we use the `(current-opcodes)` hash to look up the function. `args` come from the code vector</code>. About the only sneaky part of this code is that we update the `pc` before we run the code. As the note mentions, this is so that the jumps will work correctly when they override it. Then, so long as we haven't called `HALT` we just keep looping.

I did originally have a heck of a time getting this to work correctly since I wasn't updating the `pc` correctly. You need 1 for the opcode **and** 1 for each argument that you're consuming. Oops. :smile:

But now we can run our code:

```scheme
> (run (assemble (call-with-input-string TEST-CODE parse)))
12
```

If you remember correctly, this function was supposed to add 5 and 7. Looks like a job well done. :smile: For something a little more complicated though, why don't we try multiplying two numbers (the example given in the original problem). I wrote a function `tiny` which parses, assembles, and then runs any code you give it, here is the results:

```bash
source:
MOV [0] 5
MOV [1] 7
MOV [2] 0
MOV [3] 0
DPRINT [0]
APRINT 42
DPRINT [1]
APRINT 61
JEQ 32 [1] [3]
ADD [3] 1
ADD [2] [0]
JMP 20
MOV [0] [2]
DPRINT [0]
HALT

bytecode:
0x08 0x00 0x05 0x08
0x01 0x07 0x08 0x02
0x00 0x08 0x03 0x00
0x22 0x00 0x21 0x2a
0x22 0x01 0x21 0x3d
0x15 0x20 0x01 0x03
0x0b 0x03 0x01 0x0a
0x02 0x00 0x0f 0x14
0x07 0x00 0x02 0x22
0x00 0xff

running:
5*7=35
```

Looks pretty good, eh?

We still have one more step though. We want to be able to prove that Tiny is [[wiki:Turing complete]](). One way to do that is to be able to simulate a Turing machine. That sounds simple(ish), let's do that. :smile:

**A while later.**

~~Okay, so it's not so simple. It's possible to get close, but I don't think the language as stated is actually Turing complete... I don't have a format proof, but so far as informal goes, there's a strictly finite address space. Once you've written a Tiny program, you know exactly how many memory address you will have (anything like this: `[a]`), which means simulating a Turing machine is out of the question so far as I can tell. I'd love to be proven wrong though; leave a comment if you can figure out how to do it.~~

**Update 22 August 2013**: You can also prove it by only allowing for unbounded integers in memory cells: [‘Tiny’ Turing completeness without MMOV]({{< ref "2013-08-22-tiny-turing-completeness-without-mmov.md" >}})

Other than that, it seems like we need one more instruction. You could add a few to make it cleaner, but it can be done with just this:

`MMOV [a] [b]` - set `M[M[A]]` = `M[M[B]]`

Essentially, this gives us the ability to set memory based on an address also in memory. This way, we can actually encode vectors or any other manner of more complicated data structure. Given that though, we have enough to encode any arbitrary Turing machine in Tiny. 

To do so, we'll start with the definition for a Turing machine [[wiki:Turing machine|on Wikipedia]](): 


* Q is a finite, non-empty set of **states**
* Γ is a finite, non-empty set of the **tape alphabet/symbols**
* b ∋ Γ is the **blank symbol** (the only symbol allowed to occur on the tape infinitely often at any step during the computation)
* ∑ ⊆ {b} ∪ Γ is the set of **input symbols**
* q0 ∋ Q is the **initial state**
* F ⊆ Q is the set of **final** or **accepting states**.
* δ is a [[wiki:partial function]]() called the **[[wiki:transition function]]()**, where L is left shift, R is right shift. (A relatively uncommon variant allows "no shift", say N, as a third element of the latter set.)


We're going to simplify that a little bit by assuming that the blank symbol is 0 (and that 0 ∋ Γ), so b no longer needs to be defined and ∑ = Γ. Furthermore, we'll restrict F to only a single state. This is a valid transition since you can add transitions from all previous final states to F that do not modify the tape. 

With all that, we're going to have a function something like this:

```scheme
; Convert a Turing machine into a Tiny program
(define (turing->tiny states      ; A list of values (must be eq?-able) denoting states
                      symbols     ; A list of values (ditto) denoting symbols on the tape, default is 0
                      start-state ; The starting state (must be in states)
                      final-state ; The halt state (ditto)
                      transition  ; A list of lists of the form (current-state current-symbol next-state write-symbol move-tape)
                                  ;   states and symbols must come from their respective lists
                                  ;   move-tape must be either L or R for left and right respectively
                      initial     ; The initial tape (list of symbols)
                      )
  ...)
```

Inside of that function, we'll first want to set up a few transition functions to convert from states and symbols to integers:

```scheme
; Assign an integer value to each state and symbol
(define state->index (for/hash ([i (in-naturals)] [v (in-list states)]) (values v i)))
(define symbol->index (for/hash ([i (in-naturals)] [v (in-list symbols)]) (values v i)))
```

Then we can start converting. For my case, I'm going to assign the first memory addresses as follows:


* `M[0]` = current state, starts as `start-state`
* `M[1]` = current tape pointer, starts at 4
* `M[2]` = 3, so we can use `MMOV` to access `M[3]`
* `M[3]` = variable to store the current symbol, starts as 0
* `M[4+]` = initial tape


To generate this, we'll have to output the following code:

```scheme
`(; Store the current state in M[0]
  MOV [0] ,(hash-ref state->index start-state)
  ; Store the current tape pointer in M[1]
  MOV [1] 4
  ; M[2] stores the 3 offset so we can use mmov, M[3] is for the current state
  MOV [2] 3
  ; Encode initial state in M[4] ... (tape expands infinitely to the right)
  ,@(apply 
     append
     (for/list ([offset (in-naturals)]
                [value (in-list initial)])
       `(MOV [,(+ 4 offset)] ,(hash-ref symbol->index value))))
  ...)
```

We're going straight to the parsed version of Tiny. It seems more sensible than outputting a string only to read it right back in... That's what Lisp-like languages do after all, treat code and data as one.

Next, we want to do the main loop. Here we'll check if we're in the `final-state`. If so, `JMP` to a `HALT`. Otherwise, `JMP` to the first code block. Something like this:

```scheme
...
; Halt if we're in the final state, otherwise enter the main body
JEQ ,(+ 15 (* 3 (length initial))) [0] ,(hash-ref state->index final-state)
JMP ,(+ 16 (* 3 (length initial)))
HALT
...
```

Finally, we need to encode the states. Essentially, we need to check two things: the current state and the symbol at the tape pointer. If they both match a given transition, use that. Otherwise, keep going. Here's where we need `MMOV`. We'll need it twice: first to copy the value from the tape pointer to `M[3]` so we can actually work with it then later to copy it back if we actually use this block. One particularly unfortunate bit about this code is the lack of relative offsets. There's a reason that compiler writers often seem just a bit mad... :smile:

```scheme
...
; Encode the transitions
,@(apply
   append
   (for/list ([offset (in-naturals)]
              [each (in-list transition)])
     ; Get the offset of this transition block
     (define block-offset (+ 16 (* 3 (length initial)) (* 29 offset)))
     ; Unpack each transition
     (define-values (current-state current-symbol next-state write-symbol move-tape)
       (apply values each))
     ; Jump over if we don't match
     `(MMOV [2] [1] ; Set M[M[2]] = M[3] to M[M[1]] = M[tape index]
       JEQ ,(+ block-offset 9) [0] ,(hash-ref state->index current-state)
       JMP ,(+ block-offset 29)
       JEQ ,(+ block-offset 15) [3] ,(hash-ref symbol->index current-symbol)
       JMP ,(+ block-offset 29)
       ; We match, update the symbol and state
       MOV [0] ,(hash-ref state->index next-state)
       MOV [3] ,(hash-ref symbol->index write-symbol)
       ; Write that value back into memory
       MMOV [1] [2] ; Set M[M[1]] = M[tape index] to M[M[2]] = M[3]
       ; Move the tape
       ,@(if (eq? move-tape 'R)
             '(ADD [1] 1)
             '(SUB [1] 1))
       ; Loop back to get a new function
       JMP ,(+ 9 (* 3 (length initial))))))
; Halt if we get an invalid transition
HALT))
```

And that's all there is to it. Theoretically, we have something that will let us take any Turing machine and compile it to a Tiny program. One problem is that it won't actually work with the bytecode as specified if the Turning machines start getting large. Since we only have direct addressing, we can't jump further than instruction 255. Since we're using 29 bytes per block and a header of 16 bytes, that only leaves us room for about 8 transitions... Still, the code I'm using will work fine since under the hood I'm not actually using bytes--so I'm not going to fix it at the time being.

Let's try compiling a few test Turing programs.

First, here's on that will turn a list of 1s into a list of 2s:

```scheme
(define ones-to-twos
  (make-tiny-turing
   '(start one halt)
   '(0 1 2)
   'start
   'halt
   '((start 1 start 2 R)
     (start 0 halt  0 R))))
```

As long as it sees 1s, it will change them and move right. As soon as it sees a 0 (so we're off the input), it will stop. Let's try it:

```scheme
Tiny version:
0: MOV (0) 0
3: MOV (1) 4
6: MOV (2) 3
9: MOV (4) 1
12: MOV (5) 1
15: MOV (6) 1
18: JEQ 24 (0) 2
22: JMP 25
24: HALT
25: MMOV (2) (1)
28: JEQ 34 (0) 0
32: JMP 54
34: JEQ 40 (3) 1
38: JMP 54
40: MOV (0) 0
43: MOV (3) 2
46: MMOV (1) (2)
49: ADD (1) 1
52: JMP 18
54: MMOV (2) (1)
57: JEQ 63 (0) 0
61: JMP 83
63: JEQ 69 (3) 0
67: JMP 83
69: MOV (0) 2
72: MOV (3) 0
75: MMOV (1) (2)
78: ADD (1) 1
81: JMP 18
83: HALT

Bytecode:
0x08 0x00 0x00 0x08
0x01 0x04 0x08 0x02
0x03 0x08 0x04 0x01
0x08 0x05 0x01 0x08
0x06 0x01 0x17 0x18
0x00 0x02 0x0f 0x19
0xff 0xf0 0x02 0x01
0x17 0x22 0x00 0x00
0x0f 0x36 0x17 0x28
0x03 0x01 0x0f 0x36
0x08 0x00 0x00 0x08
0x03 0x02 0xf0 0x01
0x02 0x0b 0x01 0x01
0x0f 0x12 0xf0 0x02
0x01 0x17 0x3f 0x00
0x00 0x0f 0x53 0x17
0x45 0x03 0x00 0x0f
0x53 0x08 0x00 0x02
0x08 0x03 0x00 0xf0
0x01 0x02 0x0b 0x01
0x01 0x0f 0x12 0xff

Input:
(1 1 1)

Result:
(2 2 2)
```

That's actually really cool looking... Let's try something a bit more complicated: a doubling function. Given a list of 1s of any length, double it.

```scheme
(define double-list
  (make-tiny-turing
   '(start goto-end goto-start loop restart clear halt)
   '(0 1 start old new)
   'start
   'halt
   '(; Mark the starting position
     (start      1     goto-end   start R) 
     ; Go to the first 0, replace it with new
     (goto-end   old   goto-end   old   R)
     (goto-end   new   goto-end   new   R)
     (goto-end   0     goto-start new   L) 
     (goto-end   1     goto-end   1     R)
     ; Go back to the start
     (goto-start start loop       start R)
     (goto-start old   goto-start old   L) 
     (goto-start new   goto-start new   L)
     (goto-start 1     goto-start 1     L)
     ; Loop back or check if we're done
     (loop       old   loop       old   R)
     (loop       new   restart    new   L)
     (loop       1     goto-end   old   R)
     ; Go back to the start symbol
     (restart    old   restart    old   L)
     (restart    start clear      1     R)
     ; Write out all 1s
     (clear      old   clear      1     R)
     (clear      new   clear      1     R)
     (clear      0     halt       0     R))))
```

And here's it running:

```scheme
> (double-list '(1 1 1))
Tiny version:
0: MOV (0) 0
3: MOV (1) 4
...
516: JMP 18
518: HALT

Bytecode:
0x08 0x00 0x00 0x08
0x01 0x04 0x08 0x02
...
0x02 0x0b 0x01 0x01
0x0f 0x12 0xff

Input:
(1 1 1)

Result:
(1 1 1 1 1 1)
```

You can't ask for better than that. :smile: I wonder how long it takes to run on a hundred element list?

```scheme
> (time (length (double-list (map (λ (_) 1) (range 10)))))
Tiny version:
0: MOV (0) 0
3: MOV (1) 4
...
537: JMP 39
539: HALT

Bytecode:
0x08 0x00 0x00 0x08
0x01 0x04 0x08 0x02
...
0x0b 0x01 0x01 0x0f
0x135 0xff

Input:
(1 1 ... 1 1)

Result:
(1 1 ... 1 1)

200
cpu time: 3947 real time: 3922 gc time: 139
```

You can't really ask for better than that. :smile: 

Well, that's it. If it I wanted to be more formal about it, I would have to prove that each possible Turning machine works, but we'll leave that as an exercise to the reader. 

The code for this post is a bit more substantial than normal, so I made a seperate GitHub for it. You can check it out here: <a href="https://github.com/jpverkamp/tiny">tiny on GitHub</a>

---
title: '''Tiny'' Turing completeness without MMOV'
date: 2013-08-22 21:00:54
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
Something was bugging me about my proof from yesterday. If we take another tack on proving Turing completeness, all we would have to prove is that we can simulate [[wiki:Subleq#Subtract and branch if less than or equal to zero|`SUBLEQ`]](). Since `SUBLEQ` is Turing complete, that's all we need--just convert each `SUBLEQ` into a `SUB`, `JZ`, and a `JLS`. So that means that Tiny as written should be Turing complete.

So how does that work?

<!--more-->

The basic idea came from comment on a comment on [my previous post]({{< ref "2013-08-21-a-tiny-virtual-machine-in-racket.md" >}}). Essentially, we should be able to encode the Turing machine's tape in a single number. That way we don't have to use unlimited memory, we just have to have unbounded integers in each cell. Since that's actually how my implementation already works, it should be entirely doable.

The full code is in the same place as yesterday (<a href="github.com/jpverkamp/tiny/">GitHub: jpverkamp/tiny</a>) and has much the same structure. We're just going to have to tweak the details.

First, we're going to make the code a little cleaner by defining the memory addresses ahead of time:

```scheme
(define state '[0]) ; M[0] is current state
(define left  '[1]) ; M[1] is the leftward side of tape
(define curr  '[2]) ; M[2] is the current state
(define right '[3]) ; M[3] is the rightward side of the tap
(define (buffer n) `[,(+ n 4)]) ; M[4+] are buffers
```

After that, we'll set up the initial state. This time we don't have a variable size header. It's a static 19 bytes (the numbers at the beginning of each comment are the offsets to make actually writing the jump offsets easier):

```scheme
`(; 0: Create the initial state
  MOV ,state ,(state->value 'start)
  MOV ,left  0
  MOV ,curr  ,(symbol->value (first initial))
  MOV ,right ,(digits->number
               (map symbol->value (reverse (rest initial)))
               symbol-count)

  ; 12: Check for halt condiction
  JEQ 18 ,state ,(state->value 'halt)
  JMP 19
  HALT

  ...
```

Essentially, we're going to have something like this to represent the tape:

```
(assuming 10 input symbols)

tape = 8 6 7 5 3 0 9
pointer =   / \

 / M[1] = left part of tape in reverse
|      / M[2] = current tape symbol
|     |      / M[3] = right part of tape
|     |     |
7 6 8 5 3 0 9

M[1] = 768
M[2] = 5
M[3] = 309
```

That's why we need `digits->number`. It's a general base conversion function, so we can do things like this:

```scheme
> (digits->number '(8 6 7 5 3 0 9) 16)
140989193
> #x8675309
140989193
```

After we have that, we want to decode the transitions. To make things cleaner again, we're going to alias the `left` and `right` addresses as `move-from` (the side we're reading form) and `move-to`:

```scheme
...

  ; 19: Decode state transitions
  ,@(apply
     append
     (for/list ([i (in-naturals)]
                [transition (in-list transition)])
       ; Calculate the offset for the start of this block
       (define block-size 72)
       (define block (+ 19 (* i block-size)))

       ; Unpack the transition
       (define-values (current-state current-symbol next-state write-symbol move-tape)
         (apply values transition))

       ; Figure out which side we're moving from/to
       (define move-to   (if (eq? move-tape 'L) right left))
       (define move-from (if (eq? move-tape 'L) left  right))
       ...
```

Within each block, we'll have the same checking structure. It's a little cleaner this time since we directly have the current state and symbol available (the numbers now are offsets within the blocks):

```scheme
...
       `(; +0: Check the current state and symbol
         JEQ ,(+ block 6) ,state ,(state->value current-state)
         JMP ,(+ block block-size)
         JEQ ,(+ block 12) ,curr ,(symbol->value current-symbol)
         JMP ,(+ block block-size)
         ...
```

If we make it through those checks, then we want to update the state and symbol:

```scheme
...
         ; +12: Update the state and symbol
         MOV ,state ,(state->value next-state)
         MOV ,curr  ,(symbol->value write-symbol)
         ...
```

After that comes the interesting part. Originally, I was going to limit the Turing machine to just 2 states, but I'm not actually 100% sure that's still Turing complete. And it turns out that it's just as each to do any arbitrary number as base 2. So here we're going to take the current value (`M[2]`) and push it into the `move-to` value. To do that we need to multiply the current `move-to` by the base (the number of symbols) and then add in the current. Something like this:

```scheme
...
         ; +18: Move the current state into the buffer
         ;      Multiply by symbol count, add current
         MOV ,(buffer 0) ,(- symbol-count 1)
         MOV ,(buffer 1) ,move-to
         JZ  ,(+ block 35) ,(buffer 0)
         ADD ,move-to ,(buffer 1)
         SUB ,(buffer 0) 1
         JMP ,(+ block 24)
         ADD ,move-to ,curr
         ...
```

Then we have to pull out the next current value from the other (`move-from`) buffer. To do this, we're going to essentially take the modulus of that array and the base:

```scheme
...
         ; +35: Get the next symbol from the other buffer
         MOV ,curr ,move-from
         JLS ,(+ block 50) ,curr ,symbol-count
         SUB ,curr ,symbol-count
         JMP ,(+ block 41)
         ...
```

And finally, remove that from the `move-from` buffer. Removing it is easy enough (just subtract), but to shift that array in memory we need to divide. It turns out that division is interesting (and slow) in Tiny. :smile:

```scheme
...
         ; +47: Remove current from other buffer
         ;      Subtract current, divide by symbol count
         SUB ,move-from ,curr
         MOV ,(buffer 0) 0
         JZ  ,(+ block 67) ,move-from
         ADD ,(buffer 0) 1
         SUB ,move-from ,symbol-count
         JMP ,(+ block 56)
         MOV ,move-from ,(buffer 0)
         ...
```

Now everything is set for the next iteration. Jump back to decode another line in the transition. Also, put in the code to immediately `HALT` if we don't match any of the transitions:

```scheme
...
         ; +67: Jump back to the loop
         JMP 12
         )))

  ; If we don't match any transition, stop
  HALT)))
```

And that's what we need. We can test it with the same test cases as last time:

```bash
> (ones-to-twos '(1 1 1))
Tiny source:
0: MOV (0) 0
3: MOV (1) 0
6: MOV (2) 1
9: MOV (3) 4
12: JEQ 18 (0) 2
16: JMP 19
18: HALT
19: JEQ 25 (0) 0
23: JMP 91
25: JEQ 31 (2) 1
29: JMP 91
31: MOV (0) 0
34: MOV (2) 2
37: MOV (4) 2
40: MOV (5) (1)
43: JZ 54 (4)
46: ADD (1) (5)
49: SUB (4) 1
52: JMP 43
54: ADD (1) (2)
57: MOV (2) (3)
60: JLS 69 (2) 3
64: SUB (2) 3
67: JMP 60
69: SUB (3) (2)
72: MOV (4) 0
75: JZ 86 (3)
78: ADD (4) 1
81: SUB (3) 3
84: JMP 75
86: MOV (3) (4)
89: JMP 12
91: JEQ 97 (0) 0
95: JMP 163
97: JEQ 103 (2) 0
101: JMP 163
103: MOV (0) 2
106: MOV (2) 0
109: MOV (4) 2
112: MOV (5) (1)
115: JZ 126 (4)
118: ADD (1) (5)
121: SUB (4) 1
124: JMP 115
126: ADD (1) (2)
129: MOV (2) (3)
132: JLS 141 (2) 3
136: SUB (2) 3
139: JMP 132
141: SUB (3) (2)
144: MOV (4) 0
147: JZ 158 (3)
150: ADD (4) 1
153: SUB (3) 3
156: JMP 147
158: MOV (3) (4)
161: JMP 12
163: HALT

Bytecode:
0x08 0x00 0x00 0x08
0x01 0x00 0x08 0x02
0x01 0x08 0x03 0x04
0x17 0x12 0x00 0x02
0x0f 0x13 0xff 0x17
0x19 0x00 0x00 0x0f
0x5b 0x17 0x1f 0x02
0x01 0x0f 0x5b 0x08
0x00 0x00 0x08 0x02
0x02 0x08 0x04 0x02
0x07 0x05 0x01 0x12
0x36 0x04 0x0a 0x01
0x05 0x0d 0x04 0x01
0x0f 0x2b 0x0a 0x01
0x02 0x07 0x02 0x03
0x1b 0x45 0x02 0x03
0x0d 0x02 0x03 0x0f
0x3c 0x0c 0x03 0x02
0x08 0x04 0x00 0x12
0x56 0x03 0x0b 0x04
0x01 0x0d 0x03 0x03
0x0f 0x4b 0x07 0x03
0x04 0x0f 0x0c 0x17
0x61 0x00 0x00 0x0f
0xa3 0x17 0x67 0x02
0x00 0x0f 0xa3 0x08
0x00 0x02 0x08 0x02
0x00 0x08 0x04 0x02
0x07 0x05 0x01 0x12
0x7e 0x04 0x0a 0x01
0x05 0x0d 0x04 0x01
0x0f 0x73 0x0a 0x01
0x02 0x07 0x02 0x03
0x1b 0x8d 0x02 0x03
0x0d 0x02 0x03 0x0f
0x84 0x0c 0x03 0x02
0x08 0x04 0x00 0x12
0x9e 0x03 0x0b 0x04
0x01 0x0d 0x03 0x03
0x0f 0x93 0x07 0x03
0x04 0x0f 0x0c 0xff

Input:
(1 1 1)

Result:
(2 2 2 0 0 0)
```

There are a few extra values on the resulting tape, but that's what we expected. Any time we read into new memory, we create an extra index to the right.

Just because I can, here's another example Turing machine:

```scheme
(define duck-duck-goose
  (make-tiny-turing
   '(start go-back halt)
   '(0 1 duck goose)
   'start
   'halt
   '((start   0    go-back 0    L)
     (start   1    start   duck R)
     (go-back duck halt goose R))))
```

As you might be able to guess, this one will take a list of 1s and turn all but the last one into the symbol `duck`. The last one becomes `goose`:

```bash
> (duck-duck-goose '(1 1 1 1 1))
Tiny source:
0: MOV (0) 0
3: MOV (1) 0
6: MOV (2) 1
9: MOV (3) 85
12: JEQ 18 (0) 2
16: JMP 19
18: HALT
19: JEQ 25 (0) 0
23: JMP 91
25: JEQ 31 (2) 0
29: JMP 91
31: MOV (0) 1
34: MOV (2) 0
37: MOV (4) 3
40: MOV (5) (3)
43: JZ 54 (4)
46: ADD (3) (5)
49: SUB (4) 1
52: JMP 43
54: ADD (3) (2)
57: MOV (2) (1)
60: JLS 69 (2) 4
64: SUB (2) 4
67: JMP 60
69: SUB (1) (2)
72: MOV (4) 0
75: JZ 86 (1)
78: ADD (4) 1
81: SUB (1) 4
84: JMP 75
86: MOV (1) (4)
89: JMP 12
91: JEQ 97 (0) 0
95: JMP 163
97: JEQ 103 (2) 1
101: JMP 163
103: MOV (0) 0
106: MOV (2) 2
109: MOV (4) 3
112: MOV (5) (1)
115: JZ 126 (4)
118: ADD (1) (5)
121: SUB (4) 1
124: JMP 115
126: ADD (1) (2)
129: MOV (2) (3)
132: JLS 141 (2) 4
136: SUB (2) 4
139: JMP 132
141: SUB (3) (2)
144: MOV (4) 0
147: JZ 158 (3)
150: ADD (4) 1
153: SUB (3) 4
156: JMP 147
158: MOV (3) (4)
161: JMP 12
163: JEQ 169 (0) 1
167: JMP 235
169: JEQ 175 (2) 2
173: JMP 235
175: MOV (0) 2
178: MOV (2) 3
181: MOV (4) 3
184: MOV (5) (1)
187: JZ 198 (4)
190: ADD (1) (5)
193: SUB (4) 1
196: JMP 187
198: ADD (1) (2)
201: MOV (2) (3)
204: JLS 213 (2) 4
208: SUB (2) 4
211: JMP 204
213: SUB (3) (2)
216: MOV (4) 0
219: JZ 230 (3)
222: ADD (4) 1
225: SUB (3) 4
228: JMP 219
230: MOV (3) (4)
233: JMP 12
235: HALT

Bytecode:
0x08 0x00 0x00 0x08
0x01 0x00 0x08 0x02
0x01 0x08 0x03 0x55
0x17 0x12 0x00 0x02
0x0f 0x13 0xff 0x17
0x19 0x00 0x00 0x0f
0x5b 0x17 0x1f 0x02
0x00 0x0f 0x5b 0x08
0x00 0x01 0x08 0x02
0x00 0x08 0x04 0x03
0x07 0x05 0x03 0x12
0x36 0x04 0x0a 0x03
0x05 0x0d 0x04 0x01
0x0f 0x2b 0x0a 0x03
0x02 0x07 0x02 0x01
0x1b 0x45 0x02 0x04
0x0d 0x02 0x04 0x0f
0x3c 0x0c 0x01 0x02
0x08 0x04 0x00 0x12
0x56 0x01 0x0b 0x04
0x01 0x0d 0x01 0x04
0x0f 0x4b 0x07 0x01
0x04 0x0f 0x0c 0x17
0x61 0x00 0x00 0x0f
0xa3 0x17 0x67 0x02
0x01 0x0f 0xa3 0x08
0x00 0x00 0x08 0x02
0x02 0x08 0x04 0x03
0x07 0x05 0x01 0x12
0x7e 0x04 0x0a 0x01
0x05 0x0d 0x04 0x01
0x0f 0x73 0x0a 0x01
0x02 0x07 0x02 0x03
0x1b 0x8d 0x02 0x04
0x0d 0x02 0x04 0x0f
0x84 0x0c 0x03 0x02
0x08 0x04 0x00 0x12
0x9e 0x03 0x0b 0x04
0x01 0x0d 0x03 0x04
0x0f 0x93 0x07 0x03
0x04 0x0f 0x0c 0x17
0xa9 0x00 0x01 0x0f
0xeb 0x17 0xaf 0x02
0x02 0x0f 0xeb 0x08
0x00 0x02 0x08 0x02
0x03 0x08 0x04 0x03
0x07 0x05 0x01 0x12
0xc6 0x04 0x0a 0x01
0x05 0x0d 0x04 0x01
0x0f 0xbb 0x0a 0x01
0x02 0x07 0x02 0x03
0x1b 0xd5 0x02 0x04
0x0d 0x02 0x04 0x0f
0xcc 0x0c 0x03 0x02
0x08 0x04 0x00 0x12
0xe6 0x03 0x0b 0x04
0x01 0x0d 0x03 0x04
0x0f 0xdb 0x07 0x03
0x04 0x0f 0x0c 0xff

Input:
(1 1 1 1 1)

Result:
(duck duck duck duck goose 0 0)
```

Unfortunately, it's wicked slow (that's what we get from encoding our entire memory structure in a single number and not having native multiplication or division functions). Still, it works. And that's all that matters.

If you'd like to see the full source, you can do so here:
- <a href="github.com/jpverkamp/tiny/">GitHub: jpverkamp/tiny</a>

Let me know if you have any questions / comments / concerns.

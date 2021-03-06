---
title: Novel compression
date: 2014-05-19 14:00:56
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
---
Last week on /r/dailyprogrammer, there was a neat trio of posts all about a new compression algorithm:


* [Novel Compression, pt. 1: Unpacking the Data](http://www.reddit.com/r/dailyprogrammer/comments/25clki/5122014_challenge_162_easy_novel_compression_pt_1/)
* [Novel Compression, pt. 2: Compressing the Data](http://www.reddit.com/r/dailyprogrammer/comments/25hlo9/5142014_challenge_162_intermediate_novel/)
* [Novel Compression, pt. 3: Putting it all together](http://www.reddit.com/r/dailyprogrammer/comments/25o2bd/5162014_challenge_162_hard_novel_compression_pt_3/)


More specifically, we're going to represent compressed text with the following rules:


* If the chunk is just a number (eg. 37), word number 37 from the dictionary (zero-indexed, so 0 is the 1st word) is printed lower-case.
* If the chunk is a number followed by a caret (eg. 37^), then word 37 from the dictionary will be printed lower-case, with the first letter capitalised.
* If the chunk is a number followed by an exclamation point (eg. 37!), then word 37 from the dictionary will be printed upper-case.
* If it's a hyphen (-), then instead of putting a space in-between the previous and next words, put a hyphen instead.
* If it's any of the following symbols: . , ? ! ; : (**edit:** also ' and "), then put that symbol at the end of the previous outputted word.
* If it's a letter R (upper or lower), print a new line.
* If it's a letter E (upper or lower), the end of input has been reached.
* **edit:** any other block of text, represent as a literal 'word' in the dictionary


Got it? Let's go! 

(If you'd like to follow along: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/novel-compression.rkt">full source</a>)

<!--more-->

## Decompression

Given the ordering above (and the relative difficulty of the tasks) we'll start with decoding first. Eventually, we're going to have a single `decompress` function:

```scheme
; Decompress input compressed by the previous function
(define (decompress [in (current-input-port)])
  ...)
```

Each 'function' will take an input port to read from as input and write to the `current-output-port`. So if you want to wrap it in a string, do something like this:

```scheme
; Decompress in string mode
(define (decompress/string str)
  (with-output-to-string
   (thunk
     (with-input-from-string str decompress))))
```

All righty then. First, as we noted in the file format, the compressed file starts with the size of the dictionary than a series of words. 

We can pull these right out with the right application of a loop and {{< doc racket "read" >}}:

```scheme
; Read the dictionary; number of words followed by that many words
(define words 
  (for/vector ([i (in-range (read in))])
    (~a (read in))))
```

Now we just have to {{< doc racket "vector-ref" >}} into `words` to decode words. 

Second things second, we need to break apart all of the tokens. Normally, I'd use the {{< doc racket "read" >}} function and let Racket do some processing for us, but one token in particular (`.`) will cause some trouble. So instead, we'll read via loading the content into a string and splitting on spaces[^1].

Something like this:

```scheme
; Read the rest of the file into a list of chunks
; Split on any whitespace, space vs tab vs newline are all the same
(define chunks (string-split (port->string in)))
(let/ec return
  (for/fold ([prefix ""]) ([chunk (in-list chunks)])
    (match chunk
      ...)))
```

It's a bit strange to be using {{< doc racket "for/fold" >}}, but it seemed the cleanest way to be able to go 'back in time' in the special case characters. Specifically, this will help a lot with "-" tokens, in that we know if we're going to use the normal space or not.

The first case within the fold will be words. This is straight forward enough if it's purely numeric, but we might also have a suffix of either `!` (for upper case) or `^` (for titlecase). Regular expressions to the rescue[^2]!

```scheme
(match chunk
  ; Numbers indicate words from the dictionary
  ; ^ means upcase the first letter
  ; ! means upcase the entire word
  [(regexp #px"(\\d+)(\\^|!|)" (list _ index flag))
   (define word (vector-ref words (string->number index)))
   (display prefix)
   (display
    (case flag
      [("^") (string-titlecase word)]
      [("!") (string-upcase word)]
      [else  word]))
   " "]
  ...)
```

The extra string at the end there is part of the `for/fold`. Since that's what's returned from the `match`, that means for the next iteration it will be the value of `prefix`. So if we're not done with a sentence, write out a space before the word (as shown earlier in this block).

Next, the special cases:

```scheme
(match chunk
  ...
  ; Use a hyphen as a seperator rather than a space
  ["-" "-"]
  ; Punctuation literals
  [(or "." "," "?" "!" ";" ":" "\"" "'") (display chunk) " "]
  ; Newlines
  [(or "R" "r") "\n"]
  ; Early end of output (should generally be the last chunk)
  [(or "E" "e")
   (return)])
```

First, the hyphens. Those are a little strange, since we don't actually output anything. Instead, we let the `prefix` pass through to the next word. This does have the interesting effect of not being able to output something like "-." (since punctuation doesn't output the prefix). I guess it's just something that we'll have to deal with. After that punctuation is literally sent to output (and a space is sent to the next prefix). Newlines are newlines. 

Finally, we have an end of input signifier, although we already deal with that above. This could have an interesting effect where you could store information past the end of the file if you wanted...

And that's actually it. That's all we need to decompress the sample text given:

```scheme
> compressed
"20 i do not like them a green sam mouse eggs or anywhere and here am house there with in ham 0! 1 2 3 4 18 5 15 . R 0! 1 2 3 4 17 5 8 . R 0! 1 2 3 4 13 10 16 . R 0! 1 2 3 4 11 . R 0! 1 2 3 6 9 12 19 . R 0! 1 2 3 4 , 7^ - 0! - 14 . E\n"

> (with-input-from-string compressed decompress)
I do not like them in a house.
I do not like them with a mouse.
I do not like them here or there.
I do not like them anywhere.
I do not like green eggs and ham.
I do not like them, Sam-I-am.
```

Shiny. So how about compression?

## Compression

Same basic structure as before:

```scheme
; Compress a file into a word-list based format
(define (compress [in (current-input-port)])
  ...)

; Compress in string mode
(define (compress/string str)
  (with-output-to-string
   (thunk
     (with-input-from-string str compress))))
```

I'm going to actually do something a little more than I strictly speaking have to. Instead of just taking the words in order to build the dictionary, I'm actually going to order them in descending order of frequency. That way, if we have a lot of words, the most common will have one byte aliases, while less common words will have longer aliases. It won't amount to *that* much in the way of savings (at least not as much as duplicate words themselves), but it's something.

That being said, we'll start with a struct for 'words' and the dictionary itself:

```scheme
; While processing, store words as a special struct
; mode is one of downcase, titlecase, upcase, specialcase
(struct word (text mode) #:transparent)

; Store words we've already seen along with a count
; Later we're going to sort these so the most common are first
(define words (make-hash))
```

`specialcase` is another extension that I'm adding. Basically, if we have a word like LaTeX, we wouldn't be able to encode it as stands. What I'm going to do is encode the three cases as described, but then anything else will get its own entry in the dictionary. So something like this would be a valid compressed file[^3]:

```
 plaintext: latex Latex LATEX LaTeX
compressed: 2 latex LaTeX 0 0^ 0! 1
```

The first step is going to be to parse words. Assuming that we can get just the alphabetic characters of a word (which we'll do in a bit), we need to figure out what sort of word it is. In addition, we want to add each new word to the dictionary, so we can write that out later. Something like this:

```scheme
; Helper to add a word to the dictionary and return the struct form
(define (decode-word chunk)
  (define chunk/downcase (string-downcase chunk))
  (hash-update! words chunk/downcase (curry + 1) 1)
  (word chunk/downcase
        (cond
          [(equal? chunk chunk/downcase)                    'downcase]
          [(equal? chunk (string-upcase chunk/downcase))    'upcase]
          [(equal? chunk (string-titlecase chunk/downcase)) 'titlecase]
          [else                                             'specialcase])))
```

After that, the next second will be to use that function to parse 'chunks'. Same as before, we'll break apart the input string by spaces. Unfortunately, that means that we might get chunks like this: "Sam-I-am." Eventually, that will be 6 tokens: "{sam}^ - {i}! - {am} ." So the solution I went with is recursive. It will look for any special characters (including newlines, hyphens, and punctuation) and break them apart, perhaps multiple times. 

```scheme
; Encode a 'chunk' which might actually turn into one or more tokens
(define (decode-chunk chunk)
  (match chunk
    ; Break apart hyphens / punctuation / newlines
    [(regexp #px"(.*)([.,?!;:\\-\n\"'])(.*)" (list _ subchunk1 break subchunk2))
     (append (decode-chunk subchunk1)
             (list (if (equal? break "\n") 'newline (string->symbol break)))
             (decode-chunk subchunk2))]
    ; Process words
    [(regexp #px"([a-z]+|[A-Z][a-z]*|[A-Z]+)")
     (list (decode-word chunk))]
    ; Empty strings are empty lists (base case for breaking apart chunks)
    ["" '()]
    ; Anything else is a weird empty string, add it directly to the dictionary
    [any 
     (hash-update! words any (curry + 1) 1)
     (list (word any 'specialcase))]))
```

Note that this function always returns a list, even if it contains zero or one items. This is a trick I've done a number of times, in that we'll be appending this lists together shortly. Similarly, in the breaking apart recursive case, we append the sublists, so the base case of the empty string "" deals nicely with "am." -> "am" "." "" -> ({am} .). Exactly what we need.

Now that we have all of the processing done, we can actually do the bulk of the work:

```scheme
; Pull apart chunks, process them, put them back together
(define chunks
  (apply append 
         (map decode-chunk 
              (string-split 
               (string-replace (port->string in) "\r" "")
               " "))))
```

That was easy. :smile:

Kind of amazing how much work can be done with such relatively little effort. We still have word structs though. We need to use our `words` hash to turn them into numbers. But to do that, we need to assign a number to each:

```scheme
; Replace word counts with an ascending count
; Write out the dictionary as we go
(display (hash-count words)) 
(display " ")
(for ([i (in-naturals)]
      [word (in-list (map car (sort (hash->list words)
                                    (λ (a b) (> (cdr a) (cdr b))))))])
  (hash-set! words word i)
  (display word)
  (display " "))
```

As a bonus, we're already writing the first part of the output: the dictionary.

After that, we have enough to write the rest of the file. Just loop through each chunk. If it's a word, write the number then possibly a control character. Newlines become "R". Anything else (punctuation) is written as a literal. At the end, write an "E".

```scheme
; Replace each word with the numeric form
; Print out chunks as we go
(for ([chunk (in-list chunks)])
  (match chunk
    [(word text mode)
     (display (hash-ref words text))
     (display 
      (case mode
        [(upcase)    "!"]
        [(titlecase) "^"]
        [else        ""]))]
    ['newline
     (display "R")]
    [any
     (display any)])
  (display " "))
(displayln "E")
```

Testing it out:

```scheme
> input
"I do not like them in a house.\nI do not like them with a mouse.\nI do not like them here or there.\nI do not like them anywhere.\nI do not like green eggs and ham.\nI do not like them, Sam-I-am."

> (with-input-from-string input compress)
20 i do not like them a green sam mouse eggs or anywhere and here am house there with in ham 0! 1 2 3 4 18 5 15 . R 0! 1 2 3 4 17 5 8 . R 0! 1 2 3 4 13 10 16 . R 0! 1 2 3 4 11 . R 0! 1 2 3 6 9 12 19 . R 0! 1 2 3 4 , 7^ - 0! - 14 . E
```

Is it invertible?

```scheme
> (display (decompress/string (compress/string input)))
I do not like them in a house.
I do not like them with a mouse.
I do not like them here or there.
I do not like them anywhere.
I do not like green eggs and ham.
I do not like them, Sam-I-am.
```

Nice!

One last thing though (from Friday). Let's make it a little easier to run from the command line.

## Command line

From the <a href="http://www.reddit.com/r/dailyprogrammer/comments/25o2bd/5162014_challenge_162_hard_novel_compression_pt_3/">description page</a>:

> The program will take 3 arguments on the command line: the first one will be one of the following:


> * -c Will compress the input.
> * -d Will decompress the input.


> The second argument will be a path to a file that the input data will be read from, and the third argument will be a path to a file that output data will be written to.

We could make it a little more bullet proof (and compress or decompress many files at once) but instead we'll just go with the specification: 

```scheme
(module+ main
  (match (current-command-line-arguments)
    [(vector "-c" in-file out-file)
     (printf "Compress ~a -> ~a\n" in-file out-file)
     (with-output-to-file out-file #:exists 'replace
       (thunk (with-input-from-file in-file compress)))]
    [(vector "-d" in-file out-file)
     (printf "Decompress ~a -> ~a\n" in-file out-file)
     (with-output-to-file out-file #:exists 'replace
       (thunk (with-input-from-file in-file decompress)))]
    [any
     (void)]))
```

{{< doc racket "match" >}} is pretty awesome.

Right from Racket, we can compile it to an executable. From then, it acts just like any other program:

```bash
$ ./novel-compression -c eggs.txt eggs.txt.nc
Compress eggs.txt -> eggx.txt.nc

$ cat eggs.txt.nc
20 i do not like them a green sam mouse eggs or anywhere and here am house there with in ham 0! 1 2 3 4 18 5 15 . R 0! 1 2 3 4 17 5 8 . R 0! 1 2 3 4 13 10 16 . R 0! 1 2 3 4 11 . R 0! 1 2 3 6 9 12 19 . R 0! 1 2 3 4 , 7^ - 0! - 14 . R E

$ ./novel-compress -d eggs.txt.nc eggs.d.txt
Decompress eggs.txt.nc -> eggs.d.txt

$ cat eggs.d.txt
I do not like them in a house.
I do not like them with a mouse.
I do not like them here or there.
I do not like them anywhere.
I do not like green eggs and ham.
I do not like them, Sam-I-am.
```

But does it actually do any good?

```bash
$ ls -lah eggs*
-rwx------+ 1 me None 190 May 18 19:14 eggs.d.txt
-rwx------+ 1 me None 197 May 18 19:07 eggs.txt
-rwx------+ 1 me None 235 May 18 19:10 eggs.txt.nc
```

So... It actually made it bigger (and the output isn't *exactly* the same as the input, the newlines are different). Most of our compression is 1:2 (for I) or 2:2 (for do)[^4]. But if you have a larger text that still has a lot of duplicate text, say the first chapter of the Book of Genesis:

```scheme
$ ./novel-compression -c genesis.txt genesis.txt.nc
Compress genesis.txt -> genesis.txt.nc

$ ls -lah genesis*
-rwx------+ 1 me None 4.1K May 18 19:15 Genesis.txt
-rwx------+ 1 me None 3.6K May 18 19:16 Genesis.txt.nc
```

Much better!

There is one more trick that we can pull:

```scheme
$ ./novel-compression -c eggs.txt.nc eggs.txt.nc.nc
Compress eggs.txt.nc -> eggs.txt.nc.nc

$ cat eggs.txt.nc.nc
43 0 3 2 r 1 4 5 green 8 mouse 15 19 am 14 10 eggs anywhere 13 here there them 11 with like ham 6 sam a 12 16 9 or e and not 18 house 20 17 do 7^ in i 37 42 39 34 23 20 27 7 26 9 15 31 16 33 18 12 36 19 22 41 24 0 ! 4 2 1 5 35 6 10 . 3! 0 ! 4 2 1 5 38 6 8 . 3! 0 ! 4 2 1 5 17 14 29 . 3! 0 ! 4 2 1 5 21 . 3! 0 ! 4 2 1 25 30 28 11 . 3! 0 ! 4 2 1 5 , 40 - 0 ! - 13 . 3! 32! R E
```

Certainly doesn't compress it any more, but it is amusing. :smile: Especially when the numbers are getting encoded to other numbers (such as 1 is actually 3, which in turn is actually like). Love it!

And that's it. Compression, of a sort. If you'd like to download the entire code for today's post, it's all on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/novel-compression.rkt">novel-compression.rkt</a>

[^1]: Which has unfortunate implications if we compress really large files, but if you're using this scheme on large files... You get what's coming to you.
[^2]: Perhaps a bit overkill, but it certainly works.
[^3]: Pure luck that they're the same length.
[^4]: Don't forget the space...
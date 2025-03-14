---
title: 'Making music, part 1: Reading ABC notation'
date: 2013-10-29 14:00:12
programming/languages:
- Racket
- Scheme
programming/topics:
- ABC Notation
- Audio
- Lexing
- Music
- Parsing
---
It's been a bit since I've had time to post[^1], but I've got an interesting new project that I've been working on. It's a bit more complicated, ergo spread out over a few posts, but those tend to be the more interesting posts anyway, eh? 

The basic idea is that I want to be able to write and play music in Racket. One end goal would be to make a library available for the C211 class to give them something else to work with (in addition to <a href="//blog.jverkamp.com"/wombat-ide/c211-image-api/">images</a> and <a href="//blog.jverkamp.com"/wombat-ide/c211-turtle-api/">turtles</a>). To that end, here's my current plan of attack[^2]:


* Write a [[wiki:Lexical analysis|lexer]]() for [[wiki:ABC notation]]() to turn raw text into a list of tokens
* Write a parser to turn those tokens into a song (for example dealing with the interactions between key signature/accidentals and meter/note duration)
* Use the [rsound](http://pkg.racket-lang.org/#\[rsound\]) library on [Planet2 / pkg](http://pkg.racket-lang.org/) to play back individuals notes and chords
* Tie it all together to play a parsed song in ABC notation using the rsound library
* *(maybe)*: Use the rsound library to save ABC files as WAV audio
* *(maybe)*: Figure out the format and save ABC files as MIDI
* *(maybe)*: Render songs as music sheets/li>


Sounds like fun! Let's get started.

<!--more-->

First, we need to build a lexer. I've seen Racket's {{< doc racket "parser-tools/lex" >}} module before, but I've never had the chance to try it out. No time like the present.

The format for creating a lexer looks like this:

```scheme
(lexer [trigger action-expr] ...)
```

You have a series of trigger / action pairs. For each of the triggers, you have a regular expression written as s-expressions. One such extension that looks a lot like the standard regex patterns we all known and love is {{< doc racket "parser-tools/lex-sre" >}}. With that you could write something like this to match simple mathematical expressions:

```scheme
(require parser-tools/lex
         (prefix-in : parser-tools/lex-sre))

(define math-lexer
  (lexer 
   [(:+ numeric) (string->number lexeme)]
   [#\+ 'PLUS]
   [#\* 'TIMES]
   [whitespace   (math-lexer input-port)]))
```

There are a few interesting things here:


* The `lex-sre` module is prefixed with `:`. Since it exports functions like `*` and `+`, this prevents conflicts with Racket's operators of the same name(s).
* In the first line, we match one or more digits. Several character identifiers (such as `numeric` are pre-defined.
* On that same line, we use on of the built in identifiers bound within the action parts: lexeme. This is the string that was matched by the trigger.
* The next two lines are simple tokens. If you had more information you could use a 'heavier' data structure (I'll be doing this later).
* The last line matches against any whitespace character. We just want to ignore it, so we use another variable defined for us (input-port) to recursively call the lexer and move ahead.


Once you have all of this, `math-lexer` is a function that takes a single parameter: an input port. It will then read off a single token. To make it read more than one, you need a fairly simple wrapper:

```scheme
(define (lex lexer in)
  (for/list ([token (in-port lexer in)]
             #:break (eq? token 'eof))
    token))
```

This says to read until we get an `'eof` (provided by `lexer` by default), wrapping everything into a list. Here's it in action:

```scheme
> (call-with-input-string "8 + 7 * 6 + 5"
    (curry lex math-lexer))
'(8 PLUS 7 TIMES 6 PLUS 5)
```

All `curry` does is provide the first argument (the lexer) and returning a function that takes only the input port (which `call-with-input-string`) expects. With this basic framework, we should be able to build some rather complicated constructs. 

All right, let's get to ABC notation. For the next bit, I'm just going to show each lexer pattern in turn with a short explanation between each. You can see the entire code <a href="https://github.com/jpverkamp/abc/">here</a> or just copy paste them into a lexer body (like the example above) to try them out yourself.

To see what we're dealing with, here's a sample ABC file for Greensleeves:

```css
X:0994
T:"Green Sleeves"
C:Unattributed
B:O'Neill's Music Of Ireland (The 1850) Lyon & Healy, Chicago, 1903 edition
Z:FROM O'NEILL'S TO NOTEWORTHY, FROM NOTEWORTHY TO ABC, MIDI AND .TXT BY VINCE BRENNAN July 2003 (HTTP://WWW.SOSYOURMOM.COM)
I:abc2nwc
M:6/8
L:1/8
K:C
(A/2B/2|c2)c cde|dBG GAB|cBA ABc|BGE E2(A/2B/2|
c2)c cde|dBG GAB|cBA GE^G|A3A2:|
|:(e/2^f/2|g)ag gfe|dBG GBd|aba aba|gee e2(e/2^f/2|
g)ag gfe|dBG GAB|cBA GE^G|A3A2:|
```

The first thing to note is a series of character + colon + text lines at the beginning. These form the header section of the piece and include such information as the *T*title, *C*omposer, *M*eter (time signature), *K*ey, and default note *L*ength. For the moment, we're not going to try to parse the information we need out of these, just recognize them and wrap them up in a struct:

```scheme
; Header lines / inline headers
   [(:or (:: (:/ "AZ") #\: (:* whitespace) (:* (:~ #\newline)) (:* whitespace) (:? #\newline))
         (:: #\[ (:/ "AZ") #\: (:* whitespace) (:* (:~ #\])) (:* whitespace) #\]))
    (token-header lexeme)]
```

Originally I was pulling these apart here as well, but that's really the job of the parser, so I'll just go back to lexing them now. For that matter, I could have lexed the header keys and values differently, but I do think they should be treated as a single unit. As a side note, you might be wondering where `token-header` came from. It actually comes from the {{< doc racket "define-tokens" >}} function in `parser-tools/lex`:

```scheme
(define-tokens abc 
  (header pitch duration text comment ending))
```

Each of these tokens will be a structure with a `token-id` (set by the name, so `header`, `pitch`, etc. and `token-value`. For these, I'll just be using the string values that we parse. We can make more sense of them later this week with the parser. In addition to these tokens, we also have a set of 'empty' tokens--simpler tokens without any variation:

```scheme
(define-empty-tokens abc-empty
  (tie
   chord-start chord-end
   slur-start slur-end
   grace-start grace-end
   rest long-rest 
   bar double-bar double-bar-start double-bar-end 
   repeat-start repeat-end repeat-end-start
   break linebreak))
```

So what does it look like to parse these headers? 

```scheme
> (call-with-input-file "greensleeves.abc" (curry lex abc-lexer))
(list
 (token 'header "X:0994\n")
 (token 'header "T:\"Green Sleeves\"\n")
 (token 'header "C:Unattributed\n")
 ...)
```

Looks sensible thus far. 

As you may have noticed though, there were actually two options in the header definition. On continued for a whole line, the other was in square brackets. It turns out that the latter is for changing things like the meter or key signature within a song. I'm sure there are other uses, but those again we can deal with as we parse various songs. 

After the headers, the next target is notes. Notes are relatively straight forward and can have up to three parts: accidentals, pitch, and octave. The accidental is `^` or `^^` for sharps and double sharps and likewise `_` or `__` for flats. Naturals are `=`. The pitch is just a letter `a-g` or `A-G` (capital letters `C-B` start at middle C while lower case `c-b` are the octave below that. If you want more range, each `'` at the end will raise an octave and each `,` will lower it.

Here are a few example notes:

```scheme
C = middle C
^f = f sharp below middle C
_b,, = b flat three octaves below middle C
^^E', = e double sharp (so f sharp) just above middle C, the comma and apostrophe cancel out
```

There are a lot of combinations that don't really make much sense, but then again there are a lot of ... interesting ... composers out there that use them. So we're better off safe than sorry. Here's how I'm lexing these:

```scheme
; Pitches
   [(:: (:? (:or "^^" "^" "__" "_" "="))
        (:/ "agAG")
        (:* (:or "'" ",")))
    (token-pitch lexeme)]
```

Straight forward enough. It will be interesting to parse these when we get that far, but it shouldn't be too hard. Especially because at that point we'll have context information so we can also take into account the keysignature.

After that, we're almost through the complicated cases. Next, we have timing information. Essentially, the `L`ength header sets the default length for notes, but a song made of a single length wouldn't be very interesting, now would it[^3]? So after any pitch, we can have a length. This will consist essentially of any rational number (fraction):

```scheme
; Timing information
   [(:or (:: (:+ numeric) (:+ #\/) (:+ numeric))
         (:: (:+ #\/) (:+ numeric))
         (:+ numeric)
         (:+ #\/))
    (token-duration lexeme)]
```

Here there are several parts. You can write a full fraction like `1/2` to get a note half as long as the duration or you can write a whole number like `2` to get one twice as long. Alternatively, you can leave out the first number for a fraction, just so long as you want 1 over something (so `1/2` could be written as `/2`). Even better, if you want to just write  a slash, it's equivalent to `1/2`. Two slashes is `1/4`.

With these, we should be able to lex note/duration pairs (I'll do the definition of the bar lines soon):

```scheme
> (call-with-input-string "A/2B/2|c2" (curry lex abc-lexer))
(list
 (token 'pitch "A")
 (token 'duration "/2")
 (token 'pitch "B")
 (token 'duration "/2")
 'bar
 (token 'pitch "c")
 (token 'duration "2"))
```

We'll put the pitch/duration pairs back together in the next step. 

Now we've got the hard stuff out of the way, most of what's left is single character or short strings. For example, we have bar lines. These are almost as simple as the above, but since each has it's own meaning we'll wrap them up in a structure. I may change this when I get to parsing if it's not working out, but it makes sense for the time being.

```scheme
; Bar lines
   ["||" (token-double-bar)]
   ["[|" (token-double-bar-start)]
   ["|]" (token-double-bar-end)]
   ["|:" (token-repeat-start)]
   [":|" (token-repeat-end)]
   [(:or ":|:" "::") (token-repeat-end-start)]
   ["|"  (token-bar)]
```

After that, we have chords, slurs, and grace notes in square bracket, parentheses, and  curvy brackets respectively. Also dashes as ties and z (lower or capital) as various rests. Since none of these is associated with additional information, we'll just use straight forward symbols:

```scheme
; Simple tokens
   [#\- (token-tie)]
   [#\[ (token-chord-start)] [#\] (token-chord-end)]
   [#\( (token-slur-start)]  [#\) (token-slur-end)]
   [#\{ (token-grace-start)] [#\} (token-grace-end)]
   [#\z (token-rest)]        [#\Z (token-long-rest)]
```

We're going to have to pair the various brackets at some point (read: in the parser), but this is all we need in a lexer. 

Finally, we have notes or chord marks for a guitar which will be placed with the song when rendered but that we can mostly ignore. These are in the same format that double quoted strings are in just about every language, so they're pretty easy to parse:

```scheme
; Text / guitar chords
   [(:: #\" (:* (:or (:: #\\ any-char) (:~ #\"))) #\")
    (token-text (string-trim lexeme "\""))]
```

Next we have comments. ABC notation allows for line comments which have the same format as any other, using `%` as the comment character and running to the end of the line. The closing newline is optional since we may have a comment at the end of the file. 

```scheme
; Line comments
   [(:: #\% (:* (:~ #\newline)))
    (token-comment lexeme)]
```

And finally whitespace. In the math example we could just ignore this. Here we could as well if we were just playing music, but it's possible that I may try to render the music as well (and then the breaks matter). So we'll leave it in the lexer and ignore it sometimes later. One caveat is that if there's a `\` at the end of a line, we should treat it as a normal break rather than a linebreak (for formatting purposes). That may be important later.

```scheme
; Whitespace breaks notes sharing a bar (\ continues lines, so treat as a normal break)
   [(:or (:: #\\ (:* whitespace))
         (:+ whitespace))
    (abc-lexer input-port)]

   ; Newlines break lines in output as well (unless escaped with \, see above)
   [#\newline (token-linebreak)]))
```

And that's all we need. This is enough to lex the Greensleeves example we had above:

```scheme
> (call-with-input-file "greensleeves.abc" (curry lex abc-lexer))
(list
 (token 'header "X:0994\n")
 ...
 (token 'header "K:C\n")
 'slur-start
 (token 'pitch "A")
 (token 'duration "/2")
 (token 'pitch "B")
 (token 'duration "/2")
 'bar
 ...
 'bar
 (token 'pitch "A")
 (token 'duration "3")
 (token 'pitch "A")
 (token 'duration "2")
 'repeat-end)
```

Looks like something we can work with! Later this week (if all goes well), I'll work on a parser that can turn those notes and timings along with the headers into an actual sequence of notes to play. 

As always, the entire code for this project is / will be available on GitHub: <a href="https://github.com/jpverkamp/abc/">jpverkamp / abc</a>. If you check it out between now and when I next post, you might even get a sneak peak at the parser[^4]. :smile:

[^1]: Moving across the country will do that...
[^2]: Although it's been said "no battle plan survives contact with the enemy" -- [[wiki:Helmuth von Moltke the Elder|Helmuth von Moltke]]()
[^3]: Yes, I'm sure there are many, many counter examples...
[^4]: Assuming of course that I don't write it the night before as I'm wont to do
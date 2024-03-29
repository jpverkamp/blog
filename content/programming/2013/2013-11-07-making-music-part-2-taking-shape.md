---
title: 'Making music, part 2: Taking shape'
date: 2013-11-07 14:00:55
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
It's been a bit, but as you may have noticed life is a bit mad at the moment. But I've still made some progress.

When we left off [last time]({{< ref "2013-10-29-making-music-part-1-reading-abc-notation.md" >}}), we'd finished the first step towards making some lovely music with Racket: [[wiki:tokenization]](). Now we want to take those songs and form them into something actually approaching music.

<!--more-->

My first attempt at this was to keep every bit of information I could, making it possible to either parse music for display use or for playback. Unfortunately, it turns out that's kind of complicated (there's a lot that can go oddly with music), so I've since narrowed it down to just playback. After we've actually gotten something actually making noise (with the <a href="http://pkg.racket-lang.org/#[rsound]">rsound library</a> I mentioned earlier), I'll potentially come back to this.

If you'd like to follow along, here's the GitHub: <a href="https://github.com/jpverkamp/abc/">jpverkamp/abc</a>. 

Now that that is out of the way, we want a structure to convert the music into. The parser here will be doing a bit more heavy lifting than parsers sometimes do. My end goal is to make a linked list of notes. Each note will have a pitch, a duration, and the next note to play. The structs will look something like this:

```scheme
; item    : Linked list of note, chord, rest; see note below
; note    : Single pitch
; chord   : Multiple notes at once
; silence : Silence, blessed silence

(struct item          (next length) #:transparent #:mutable) 
(struct note     item (pitch)       #:transparent #:mutable)
(struct chord    item (notes)       #:transparent #:mutable)
(struct silence  item ()            #:transparent #:mutable)
```

This isn't something I've ever used before, but you can make structs that inherit from one another. In this case, a `note?` is also an `item?`. You can create a new note like this:

```scheme
(note next length pitch)
```

Then you can use the functions `item-next`, `item-length`, and `note-pitch` to pull out the values. It's a nice combination all around. This way we can share the length between the three kinds of things we want to be able to play: notes, chords, and pitches.

In addition, we're going to need one additional struct:

```scheme
; Special item that should have length 0 that represents the start of a song
; This will be removed at the end of processing so the user should never see it

(struct start    item ()            #:transparent #:mutable)
```

As the comment says, I'm only using this because of how I'm building the linked lists. It will be removed before the list is returned.

So are we ready to parse the song yet? Well, not quite. First, we need to actually make sense of a few of the items. Specifically, key and time signatures, notes, and lengths. First, key signatures. Basically, these tell use the number of sharps or flats notes will have by default:

```scheme
; Key signature
(struct key
  (base     ; Base note for the key (C-B, ex: G)
   type     ; Type of key (major, minor, etc)
   sharps   ; List of notes that are sharp (C-B)
   flats    ; List of flats
   ) #:transparent #:mutable)

; Parse a key signature
(define (parse-key text)
  (match-define (list _ note type)
    (map 
     string->symbol
     (regexp-match #px"([A-G][#b]?)(|Maj|m|Min|Mix|Dor|Phr|Lyd|Loc)" text)))

  (when (eq? type '||) (set! type 'Maj))
  (when (eq? type 'm)  (set! type 'Min))

  (define-values (num-sharps num-flats)
    (case (string->symbol (format "~a~a" note type))
      [(C#Maj, AMin, G#Mix, D#Dor, E#Phr, F#Lyd, B#Loc) (values 7 0)]
      [(F#Maj, DMin, C#Mix, G#Dor, A#Phr, BLyd, E#Loc)  (values 6 0)]
      [(BMaj, GMin, F#Mix, C#Dor, D#Phr, ELyd, A#Loc)   (values 5 0)]
      [(EMaj, CMin, BMix, F#Dor, G#Phr, ALyd, D#Loc)    (values 4 0)]
      [(AMaj, FMin, EMix, BDor, C#Phr, DLyd, G#Loc)     (values 3 0)]
      [(DMaj, Min, AMix, EDor, F#Phr, GLyd, C#Loc)      (values 2 0)]
      [(GMaj, Min, DMix, ADor, BPhr, CLyd, F#Loc)       (values 1 0)]
      [(CMaj, Min, GMix, DDor, EPhr, FLyd, BLoc)        (values 0 0)]
      [(FMaj, Min, CMix, GDor, APhr, BbLyd, ELoc)       (values 0 1)]
      [(BbMaj, Min, FMix, CDor, DPhr, EbLyd, ALoc)      (values 0 2)]
      [(EbMaj, Min, BbMix, FDor, GPhr, AbLyd, DLoc)     (values 0 3)]
      [(AbMaj, Min, EbMix, BbDor, CPhr, DbLyd, GLoc)    (values 0 4)]
      [(DbMaj, BMin, AbMix, EbDor, FPhr, GbLyd, CLoc)   (values 0 5)]
      [(GbMaj, EMin, DbMix, AbDor, BbPhr, CbLyd, FLoc)  (values 0 6)]
      [(CbMaj, AMin, GbMix, DbDor, EbPhr, FbLyd, BbLoc) (values 0 7)]))

  (key note 
       type 
       (take '(F C G D A E B) num-sharps)
       (take '(B E A D G C F) num-flats)))
```

It's mostly only confusing because I went ahead and supported some of the more esoteric keys (such as [[wiki:Dorian mode|Dorian]]() and [[wiki:Lydian mode|Lydian]]() mode). The important part is that any valid combination with up to either seven sharps or flats can be returned. 

Next, we have the meter. This will normally be a fraction representing the number of beats per measure and how large a beat is. The only exception is that non-specified meters and `C` mean common time (4/4) and `C|` means cut time (2/2). 

```scheme
; Meter / time signature
(struct meter
  (beats    ; How many notes are in a measure
   1-beat   ; Which note is a beat (4 = quarter, so 1/n)
   ) #:transparent #:mutable)

; Parse a meter definition
(define (parse-meter text)
  (cond
    [(equal? text "none") (meter #f #f)]
    [(equal? text "C")    (meter 4 4)]
    [(equal? text "C|")   (meter "C|")]
    [else
     (apply meter (map string->number (string-split text "/")))]))
```

After that, the next two header fields are trivial to parse. The tempo (`Q:`) represents beats per minute and is just a number. Likewise, the default note length (`L:`) is a fraction representing the length to use on any notes without a specified duration and as a multiplier for those that do. For either case though, we can just trust Racket to parse the values for us:

```scheme
; Parse tempo information
(define (parse-tempo text)
  (string->number text))

; Parse length header information
(define (parse-length text)
  (string->number text))
```

The next two things to parse are the note pitches and the note/rest durations. First, the pitches. As I've mentioned in the previous post, a pitch is made up of three parts where the first and third are optional:


* accidental (optional) - sharps, flats, and naturals (^ / ^^ / _ / __ / =)
* pitch - a lower case or upper case letter, A-G (upper case is the higher of two octaves
* octave - an octave offset, apostrophes for higher octaves and commas for lower


The parser here is a little more complicated (and thus error prone), but still relatively straight forward:

```scheme
; Parse a note, taking into account the current key
(define (parse-pitch text)
  (match-define (list _ accidental note octave)
    (regexp-match #px"(^|^^|_|__|=)([A-Ga-g])([',]*)" text))

  (define accidental-w/key
    (or accidental
        (let ([note-name (string->symbol (string-upcase note))])
          (cond
            [(member note-name (key-sharps (current-key))) "^"]
            [(member note-name (key-flats  (current-key))) "_"]
            [else                                          ""]))))

  (define octave-offset
    (for/sum ([c (in-string octave)])
      (if (eq? c #\') 1 -1)))

  (+ 49
     (case (string->symbol accidental-w/key)
       [(|| |=|) 0] [(^) 1] [(^^) 2] [(_) -1] [(__) -2])
     (case (string->symbol note)
       [(c) -21] [(d) -19] [(e) -17] [(f) -16] [(g) -14] [(a) -12] [(b) -10]
       [(C) -9]  [(D) -7]  [(E) -5]  [(F) -4]  [(G) -2]  [(A) 0]   [(B) 2])
     (* 12 octave-offset)))
```

Finally, we have the note duration. This can follow a note or rest to use any duration other than the default. These are fractions with optional numbers. If the numbers aren't specified, a single slash (/) is equivalent to 1/2 and two slashes are a quarter: 1/4.

```scheme
; Parse a duration, taking into account the current note length and tempo
(define (parse-duration text)
  (match-define (list _ numer slashes denom)
    (regexp-match #px"(\\d*)(/*)(\\d*)" text))

  (* (cond
       [(and (equal? "" numer) (equal? "" denom))
        (/ 1 (* 2 (string-length slashes)))]
       [else
        (/ (or (and numer (string->number numer)) 1)
           (or (and denom (string->number denom)) 1))])
     (current-length)))
```

Okay, finally we're into the parsing. The function is a little long, but parsers tend to do that. First we want to set up a series of parameters. This sort of dynamic scoping (where variables will sometimes change but not always) is exactly what parameters were designed for.

```scheme
; Current parser state
(define current-key    (make-parameter #f))
(define current-length (make-parameter #f))
(define current-tempo  (make-parameter #f))
(define current-repeat (make-parameter #f))
(define current-item   (make-parameter #f))
```

Within the actual function, we'll start by setting these to a sensible value. This is to help clean up if we happen to run more than one song at a time:

```scheme
; Parse a song into a linked list of notes/chords/rests (see above)
(define (abc-parse/playback tokens)
  ; Reset parameters for this song
  (current-key    (parse-key    "CMaj"))
  (current-length (parse-length "1/8"))
  (current-tempo  (parse-tempo  "120"))
  (current-repeat #f)
  (current-item   #f)

  ...
```

After that, we're going to create that special start token I talked about before. This is because we're going to keep the current (technically previous) token around and we need an initial value:

```scheme
...
  ; Special token at the start makes the world go round, remove this later
  (define *start* (start #f 0))
  (current-repeat *start*)
  (current-item *start*)
  ...
```

Now, we'll read across the song body. Headers can appear either at the beginning of the song or inline, but there's really no difference between the two cases. The comments should be relatively straight forward (I hope):

```scheme
...
  ; Read the song body
  (let loop ([tokens tokens])
    (match tokens
      ; Ran out of tokens, force the end of the song
      ; Return the first token (which is the 'next' of the special start token)
      [(list)
       (item-next *start*)]
      ; Deal with headers (inline or not)
      [(list-rest (header text) tokens)
         (match-define (list _ key val)
           (regexp-match #px"([A-Z])\\s*\\:\\s*([^\n]*)\n?" text))

         (case (string->symbol key)
           [(K) (current-key    (parse-key val))]
           [(L) (current-length (parse-length val))]
           [(Q) (current-tempo  (parse-tempo val))])

         (loop tokens)]
      ; Ignore bars
      [(list-rest (or 'bar 'double-bar 'double-bar-start 'double-bar-end) tokens)
       (loop tokens)]
      ; Remember the current item as the start of a repeat block
      [(list-rest 'repeat-start tokens)
       (current-repeat (current-item))
       (loop tokens)]
      ; Add the start of the repeat block to the current item's nexts
      ; Note:The current item is the previous, so use the next
      ; The actual next item will get added as the second option
      [(list-rest 'repeat-end tokens)
       (add-next-to-current-item! (item-next (current-repeat)))
       (loop tokens)]
      ; Start/end repeat pairings do both
      [(list-rest 'repeat-end-start tokens)
       (add-next-to-current-item! (item-next (current-repeat)))
       (current-repeat (current-item))
       (loop tokens)]
      ; Notes with a set duration
      [(list-rest (pitch p) (duration d) tokens)
       (next-item-is! (note #f (parse-duration d) (parse-pitch p)))
       (loop tokens)]
      ; Notes without a duration
      [(list-rest (pitch p) tokens)
       (next-item-is! (note #f (parse-duration "1") (parse-pitch p)))
       (loop tokens)]
      ; Rests with a set duration
      [(list-rest 'rest (duration d) tokens)
       (next-item-is! (silence #f (parse-duration d)))
       (loop tokens)]
      ; Rests with standard duration
      [(list-rest 'rest tokens)
       (next-item-is! (silence #f (parse-duration "1")))
       (loop tokens)])))
```

In most of the cases, we use the function `next-item-is!` to add the newly created item as `item-next` to the `(current-item)`:

```scheme
; Add the new item to the current (see above) and update current item
(define (next-item-is! new-next)
  (add-next-to-current-item! new-next)
  (current-item new-next))
```

Adding the current item has a bunch of special cases because there are three different values that next can take:

```scheme
; Append a given item to the current item's next value
; If it was #f, this item is a singletone
; If it was a single item, make it a list and add to the end
; If it was a list, add it to the end
; (If the current item is #f, this function does nothing)
(define (add-next-to-current-item! new-next)
  (when (current-item)
    (cond
      [(list? (item-next (current-item)))
       (set-item-next! (current-item) (snoc (item-next (current-item)) new-next))]
      [(item-next (current-item))
       (set-item-next! (current-item) (list (item-next (current-item)) new-next))]
      [else
       (set-item-next! (current-item) new-next)])))
```

And that's really all there is to it. We already can parse relatively complicated songs. Here's a simple example:

```scheme
> (require "tokenizer.rkt")
> (abc-parse/playback
    (call-with-input-string
        "|abcd|:g2g/g/:|zcba||"
      abc-lex))

(note
 (note
  (note
   (note
    #0=(note
        (note (note (list #0# (silence (note 
                                        (note 
                                         (note #f 1/8 37) 
                                         1/8 39) 
                                        1/8 28) 
                                       1/8)) 
                    1/16 35) 
              1/16 35)
        1/4 35)
    1/8 30)
   1/8 28)
  1/8 39)
 1/8 37)
```

That looks a bit strange, but basically it means that it's a nested structure (the linked list we were trying to make) with an infinite recursive structure (the `#0=` defines a reference and `#0#` means that the reference goes there). This is how we're dealing with repeats. When we get to the playback, each time you see a list in a repeat, remove one from it. That way you'll go back to `#0=` the first time, but continue playing the second time. 

It's a bit dense right now, but next time it will all become clearer (since we'll have actual sounds!). Theoretically, it shouldn't take as long since I've already written probably 90% of the playback code. Unfortunately, there's a saying in Computer Science--probably others as well--that when you're 90% of the way done, you still have more than half the work to go. So it goes.

As always, I've uploaded my code to GitHub: <a href="https://github.com/jpverkamp/abc/">jpverkamp/abc</a>. Feel free to offer comments / suggestions, I always love to have them.
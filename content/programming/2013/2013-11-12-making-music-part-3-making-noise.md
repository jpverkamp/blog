---
title: 'Making music, part 3: Making noise'
date: 2013-11-12 14:00:25
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
[Last week]({{< ref "2013-11-07-making-music-part-2-taking-shape.md" >}}) we parsed some music. That post was in a bit of a hurry, so we had to leave off a fair few important pieces (like ties and slurs for one; chords for a rather bigger one). We'll get to them soon, but for now we want to actually get something playing back.

<!--more-->

The main part of the story this time around will be <a href="https://github.com/jbclements">John Clement's</a> <a href="https://github.com/jbclements/RSound/tree/master/">rsound </a>package for Racket. With the new package system (and an adequately new version of Racket), installation is rather straightforward:

```bash
raco pkg install rsound
```

This gives us a nice variety of methods for making music. For a quick overview, here's an older version of the documentation: <a href="http://planet.racket-lang.org/package-source/clements/rsound.plt/4/4/planet-docs/rsound/index.html">rsound docs</a>. I'm not sure where / if the new package manager has pre-built docs available, but installing it will build the documentation as well. Still, the API is essentially the same.

The first thing we need is to make a sound. We can use the `network` and `sine-wave` macros to generate a simple tone:

```scheme
(network ()
  [out (sine-wave 440)])
```

(440 Hz is perhaps the easiest tone on a piano keyboard to remember, it's the A above middle C.)

If we want to play that back, we can do so with `signal->rsound` to make a note and `play` to play it back:

```scheme
(play
 (signal->rsound
  44100
  (network ()
    [out (sine-wave 440)])))
```

44100 is the number of frames to generate. Given the default parameters, that will be a one second long sound. Go ahead and give that a whirl if you want something a bit painful. The default volume is... intense.

The last piece we need is the math that turns a piano key into a frequency. Luckily, the math has already been done for us:

{{< latex >}}f(n) = ( \sqrt[12]{2}\ )^{n-49} \cdot 440\ Hz{{< /latex >}}

Combine the previous code and that function and we have a nice way to make single pitches:

```scheme
(define (note->rsound 1/2s-above-c)
  (define 12th-root-of-2 (expt 2 (/ 1 12)))
  (define n (+ 1/2s-above-c 40))
  (define freq (* (expt 12th-root-of-2 (- n 49)) 440))
  (rs:network ()
              [out (rs:sine-wave freq)]))
```

You may have noticed the `rs:` prefix on rsound functions. That's because it exports at least one function (`silence`) that conflicts with what we've already written. So by using the `prefix-in` form of `require` way we have a namespace of sorts on the rsound functions:

```scheme
(require (prefix-in rs: rsound))
```

After single notes, there's a function `signal-+s` which we can use to add two signals together. This will let us build chords of those notes we were already making:

```scheme
(define (chord->rsound notes)
  (rs:signal-+s
   (for/list ([each (in-list notes)])
     (note->rsound each))))
```

Unfortunately, that doesn't quite work at the moment (since we don't have the parser working for chords yet), but we can still try it out:

```scheme
> (play (signal->rsound 44100 (chord->rsound '(40 44 47))))
```

With those being the notes on a standard piano corresponding to middle C and the E and G above it, that should be a nice C Major chord in all it's pure tone glory. It's ugly, but it's definitely a chord.

With that, all that's left is pulling apart a song. We'll go ahead and use our good friend `match` again, since we've already seen how well it deals with structs:

```scheme
(define (abc->rsound current-note)
  (define current-rsound
    (match current-note
      [(or #f '())
       (rs:silence 1)]
      [(note _ length pitch)
       (rs:signal->rsound (exact-floor (* length 44100)) (note->rsound pitch))]
      [(silence _ length)
       (rs:silence (exact-floor (* length 44100)))]))

  (define rest-rsound
    (match current-note
      [(or #f '())
       (rs:silence 1)]
      [(item (list-rest next-note rest-notes) _)
       (set-item-next! current-note rest-notes)
       (abc->rsound next-note)]
      [(item next-note _)
       (abc->rsound next-note)]))

  (rs:rs-append*
   (list current-rsound
         (rs:silence 10)
         rest-rsound)))
```

Hopefully that's pretty straight forward. We have three parts. In the first internal define, we're making a sound for the first note. It's either a note or silence, either way we create the correct number of frames, completely ignoring the `item-next` field (setting it to `_`).

In the second part, we ignore the first part and *only* look at the `item-next`. This lets us know if we have `#f` at the end of a song, and empty list if we've already played through a repeat enough times, a list of repeated options (which we need to advance with `set-item-next!`[^1], or finally a single note. In all cases but the first, we recursively generate that tone; if there's no `next`, we generate a single frame of silence (easier than special casing for the last part of the function).

Finally, we put it all together. I put another 10 frames of silence here as a completely randomly chosen break between notes. Without it, repeated notes tend to run together. With it, we get some nice spacing. I'm going to have to tune it a little bit, but for the moment it works great.

So now we can turn a song into an rsound, but how about playing it back? Easy:

```scheme
(define (abc-play-file filename)
  (rs:play
   (abc->rsound
    (abc-parse/playback
     (call-with-input-file filename abc-lex)))))
```

Here's a nice example:

{{< audio type="mp3" src="/embeds/2013/greensleeves.mp3" >}}

Yes, it's ~~a bit~~ really fuzzy. That's mostly because of the compression involved in making it an mp3. Also, the notes are pure sine waves. In reality, musical notes are a bit more complicated than that. We'll get to that soon, I hope.

How did I generate the file? Glad you asked. The rsound library pretty much does this for us with the `rs-write` function:

```scheme
(define (abc->wav abc-filename wav-filename)
  (rs:rs-write
   (abc->rsound
    (abc-parse/playback
     (call-with-input-file abc-filename abc-lex)))
   wav-filename))
```

For this particular file, I used <a href="http://audacity.sourceforge.net/">Audacity</a> to make it into an MP3, but that shouldn't strictly speaking be necessary.

And there you have it. We have audio playback. There's still a whole host of things to do, but I think this is pretty good progress.

As always, you can see the source code for this project on GitHub: <a href="https://github.com/jpverkamp/abc/">jpverkamp/abc</a>. I'd love to see some bug reports; I know there are some issues. :smile:

[^1]: yes, unfortunately this means songs can only be played once at the moment
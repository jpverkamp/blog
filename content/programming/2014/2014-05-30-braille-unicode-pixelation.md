---
title: Braille unicode pixelation
date: 2014-05-30 14:00:11
programming/languages:
- Racket
- Scheme
programming/topics:
- Graphics
- Unicode
---
What would you do if you were on a machine that had no higher level graphics, but you still wanted to display images?

<!--more-->

One option is [[wiki:ASCII art]]():

```
_____________
< Hello world >
 -------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```

[^1]

Another is using 'denser' characters (such as @/&amp;) for darker points and less dense characters (' or even a space) for lighter ones, such as the case with [AALib](http://aa-project.sourceforge.net/aalib/):

{{< figure src="/embeds/2014/AAlib-zebra1.png" >}}[^2]

But what if we want to get really exotic? Here's a <del>crazy</del> neat idea based on [a Python library](https://github.com/asciimoo/drawille/) that came up on [/r/programming](http://www.reddit.com/r/programming/comments/263opn/drawille_pixel_graphics_in_a_terminal_using/) a bit back: [[wiki:Braille|Braille pixel graphics]]().

Basically, we have a set of Unicode codepoints that are assigned to Braille (0x2800-0x28FF), known as [[wiki:Braille Patterns]](). With the extended set, there exists a character for every possible combination of up to 8 dots in a 2x4 grid. There's one main oddity, in that the dots aren't ordered in a purely row major or column major order. Instead, they're more like this:

{{< figure src="/embeds/2014/braille-dot-numbering.png" >}}[^3]

The reason for this is mostly historical. Originally, Braille characters had 6 dots. The additional two lowest dots were added later, and thus don't fit with the original numbering.

In any case, the above ordering gives us a way to encode a Braille character as a bitstring:

<pre>○● 14
●● 25
○○ 36
●○ 78
=
○●○●●○●○
12345678
=
01011010
=>
90 / #x5a
=>
#x285a</pre>

```scheme
> (integer->char #x285a)
#\⡚
```

So now we have a game plan: take the pixels of an image and treat each group of 2x4 pixels as a block. For each block, encode as binary using the Braille ordering. Convert that number to a Unicode code point and get the character. Loop over all of the blocks in the image and we should be good.

Something like this:

```scheme
; Convert a flomap into a dot matrix string, using Braille for the pixels
(define (flomap->braille fm #:threshold [threshold 0.75])
  ; Braille characters are two dots wide and four tall
  (define-values (width height) (flomap-size fm))
  (define b-width  (ceiling (/ width 2)))
  (define b-height (ceiling (/ height 4)))

  ; Return if the grayscale (simple average) at a point is greater than a threshold
  ; flomap-ref* is already 'safe' in that out of bounds pixels are always 0
  (define (bit x y)
    (define c (flomap-ref* fm x y))
    (define g (/ (flvector-sum c) (flvector-length c)))
    (> g threshold))

  ; Load each line directly to a string, join with newlines
  (string-join
   (for/list ([b-y (in-range b-height)])
     (list->string
      (for/list ([b-x (in-range b-width)])
        (integer->char
         ; The Braille unicode range is #x2800 - #x28FF, where each dot is one of 8 bits
         (+ #x2800
            ; Because Braille was originally only 6 dots, the order of bits is:
            ; 1 4
            ; 2 5
            ; 3 6
            ; 7 8
            (for/sum ([xΔ  (in-list '(0 0 0 1  1  1  0   1))]
                      [yΔ  (in-list '(0 1 2 0  1  2  3   3))]
                      [mul (in-list '(1 2 4 8 16 32 64 128))])
              (* mul (if (bit (+ (* 2 b-x) xΔ) (+ (* 4 b-y) yΔ)) 1 0))))))))
   "\n"))
```

That crazy line / `for/sum` right at the end does most of the work, actually doing the binary conversion. Basically, the `bit` function gets a thresholded pixel out of the image (using the fact that `flomap-ref*` actually does bounds checking for us, return 0 for out of bounds pixels). We use that and some bit shifting (the `mul` variable) to get an offset than add it to the #x2800 constant.

Other than that, we have some boilerplate to form a string. But that's all we need:

```scheme
> (display (flomap->braille (read-flomap "kitten.jpg") #:threshold 0.8))
```

<pre>⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⠟⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡗⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠘⠻⢾⡀⠀⣠⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠛⠛⠛⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠙⢿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠈⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣾⣦⣦⢀⡀⢀⢠⡀⢀⣀⢠⣴⣄⣀⣤⢀⢰⣟⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿</pre>

(Unfortunately, you do have to do some amount of hand tuning for the threshold...)

Or how about those entirely too cute mascots for a animated franchise:

```scheme
> (display (flomap->braille (read-flomap "minion.jpg") #:threshold 0.6))
```

{{< figure src="/embeds/2014/minion.txt.png" >}}

And that's all there is to it. It's wicked fast too (honestly, the actual printing is the slowest part by far). It might be interesting to actually hook this up as a video driver or the like and see if you could actually play a game.

Still, that's good for a day. As always, the code is on GitHub: [braille-images.rkt](https://github.com/jpverkamp/small-projects/blob/master/blog/braille-images.rkt). Enjoy!

[^1]: source: [[wiki:cowsay]]()
[^2]: source: [[wiki:File:AAlib-zebra.png|AALib]]()
[^3]: [[wiki:File:Braille8dotCellNumbering.svg|source]]()

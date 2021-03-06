---
title: "Wombat IDE - Assorted bug fixes (\u03BB\u200E mode fixed)"
date: 2012-03-09 04:55:48
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: wombat-ide-assorted-bug-fixes-lambda-mode-fixed
---
A few minor bug fixes first:

* Fixed the cursor jumping to the end of the document on saves. This was being caused by the code that automatically trimmed whitespace, which will still change the file on disk but won't change the actual open document.
* Apparently, there were some lingering issues with the undo/redo stack sometimes erasing the document. If this happens, you can always undo once more to get passed it, but I think I've tracked down why it was happening. If it happens again, please let me know.
* Fixed an error where closing documents through the InfoNode close event wouldn't actually remove them from memory.


<!--more-->

Also, the λ mode that I'd talked about [before]({{< ref "2012-02-24-wombat-ide-lambda-mode.md" >}}) has been fixed. Previously, it would work just fine if you stayed in either mode, but apparently changing from one to another with more than one λ/`lambda` in the document would break things.

Essentially, the code was calculating the position of all of the lambdas first and then replacing them. However, after the first, the shorter λ characters would through off the offset to the longer `lambda`, thus breaking the document.

Unfortunately, I don't actually write either `lambda`s often myself, much preferring the shorter forms of `define` and named `let`s, only using `lambda` in anonymous functions passed to `map` or `filter`. So I didn't catch this as soon as I should have. So it goes. It's a good reason that I should probably work in some more automated testing to make sure that fixes don't break things. :smile:

An example, before changing to λ mode:

```scheme
(define fact
  (lambda (n)
    (if (zero? n)
        1
        (* n (fact (- n 1))))))

(define tail-fact
  (lambda (n)
    (define ^
      (lambda (n a)
        (if (zero? n)
            a
            (^ (- n 1) (* n 1)))))
    (^ n 1)))
```

After switching to `lambda` mode:

```scheme
(define fact
  (λ (n)
    (if (zero? n)
        1
        (* n (fact (- n 1))))))

(define tail-fact
  (lambdλ    (define ^
      (lambda (n a)
        (if (zero? n)
            a
            (^ (- n 1) (* n 1)))))
    (^ n 1)))
```

Luckily, the fix was just a matter of slightly slower code that wouldn't find all the locations first but rather replaced each one in turn.

If you're curious why I didn't just do a find and replace on the text string, the issue is that's exactly what was causing the problems with the disappearing code that I mentioned in the second bullet above. Essentially, the undo/redo stack was seeing the document be cleared then the new code inserted on a `setText` call and this got saved to the undo/redo stack as two distinct elements. Unfortunate, but it really does make sense.

In any case, it's fixed now. Ah the joys of software development.

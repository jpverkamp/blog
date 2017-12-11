---
title: "Wombat IDE - Upload button and \u03BB\u200E"
date: 2012-02-17 04:55:54
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: wombat-ide-upload-button-and-lambda
---
Two new features that should prove to be pretty useful:

* Upload button
* λ‎ character


<!--more-->

The upload button shows up on the toolbar, right next to the new connect button:

{{< figure src="/embeds/2012/connect-upload.png" >}}

(The screen sharing button is on the left, the upload button is on the right.)

All that the upload button does is to connect to the upload server (the C211 software is called Tiro, but the button is not specific to that) by displaying a page in the user's default web browser. In addition, it will take the current file name and use that to set the URL, so for example having `a5.ss` open will open the submission page for `a5`, while `a6.ss` will submit to `a6`.

The second new feature is a λ character. Simple type Ctrl-L and the character will be inserted into the document like so:

```scheme
(define fact
  (λ (n)
    (define help
      (λ (n a)
        (if (zero? n)
            a
            (help (- n 1) (* n a)))))
    (help n 1)))
```

λ is completely identical to the more traditional lambda, defined by the following macro:

```scheme
(define-syntax \u03BB
  (syntax-rules ()
    [(\u03BB a ...) (lambda a ...)]))
```

(where `\u03BB` is the Unicode equivalent to λ)

I want to add a mode that will automatically switch between lambda and λ, but haven't had time to do so yet. I'm sure it won't be too difficult however.

If you want to switch over to the new versions of Wombat, you can get it <a title="Wombat Launcher Download" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>. You should have at least version 2.48.12.

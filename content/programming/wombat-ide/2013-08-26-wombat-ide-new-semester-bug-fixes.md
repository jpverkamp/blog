---
title: Wombat IDE - New semester / bug fixes
date: 2013-08-26 20:15:15
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
We're about to start up the Fall semester, so it seems like a good time to be updating Wombat for the new semester. With that, a whole slew of bugs have been squashed:

<!--more-->

Minor fixes:

* Issue [211](https://code.google.com/p/wombat-ide/issues/detail?id=211) \- fixed an issue in bracket matching for the first bracket after a line comment block
* Issue [220](https://code.google.com/p/wombat-ide/issues/detail?id=220) \- in find/replace, find starts at the cursor and wraps at the end of the document; replace automatically triggers find
* Issue [221](https://code.google.com/p/wombat-ide/issues/detail?id=221) \- when navigating through history you can use the down arrow at the end to clear the REPL
* Issue [222](https://code.google.com/p/wombat-ide/issues/detail?id=222) \- the CSV library is now correctly documented
* Issue [226](https://code.google.com/p/wombat-ide/issues/detail?id=226) \- the correct document is run even after closing a document and not clicking another
* Issue [230](https://code.google.com/p/wombat-ide/issues/detail?id=230) \- `(define x)` is now equivalent to `(define x (void))` rather than a syntax error
* Issue [231](https://code.google.com/p/wombat-ide/issues/detail?id=231) \- brackets in character literals and simple strings in the REPL no longer break execution (you can execute just `#\\)` now)
* Issue [233](https://code.google.com/p/wombat-ide/issues/detail?id=233) \- Wombat is no longer case sensitive by default; you can manually re-enable it with `(case-sensitive #f)`
* Issue [234](https://code.google.com/p/wombat-ide/issues/detail?id=234) \- Wombat should be called Wombat in the OSX 'force quit' dialog rather than Main
* Issue [236](https://code.google.com/p/wombat-ide/issues/detail?id=236) \- fixed a conflict between Lambda/Greek mode and the history panel

Slightly bigger fixes:

Issue <a href="https://code.google.com/p/wombat-ide/issues/detail?id=22">22</a> - It's been a long time coming (this was by far the oldest issue still open), but there's now an Emacs mode for Wombat. It's based on <a href="http://xnap-commons.sourceforge.net/xref/org/xnap/commons/gui/shortcut/EmacsKeyBindings.html">this project</a> from the XNap Commons (licensed LGPL). If anyone else is looking for basic Emacs keybindings for a Java project, this is a great place to start. Theoretically, everything defined in that project should work in any file or the REPL when Emacs mode is enabled (check the options menu), although it still needs some testing. Let me know if anything doesn't work.

Issue <a href="https://code.google.com/p/wombat-ide/issues/detail?id=229">229</a> - Essentially, this added a 'Greek mode' that acts like lambda mode, only for any Greek letter. This way you can do things like type sigma and get `σ`. As an added benefit, this takes advantage of Issue <a href="https://code.google.com/p/wombat-ide/issues/detail?id=233">233</a> (see above) to have upper and lower case Greek characters. So `Sigma` is `Σ` and `sigma` is `σ`.

That's it for the time being; if you have any more bugs, feel free to submit an issue to the <a href="https://code.google.com/p/wombat-ide/issues/list">bug tracker</a> or just <a href="mailto:wombat@jverkamp.com">email me</a> directly.
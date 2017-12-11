---
title: Wombat IDE - Defining define
date: 2011-09-13 04:55:12
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
First, minor bug fixes and reorganization:

* Fixed a problem with line separators that was causing automatic indentation to fail on Windows
* Re-factored save/load code to the text area
* Store a hash of the saved contents with each text area so that we can recognize files that don't need to be saved
* Add an option to disable confirmation on save before either running or exiting (if disabled, just automatically save in both cases)


<!--more-->

In addition, I've been having problems with the debugging procedures. Essentially if you used the short form of define, you wouldn't get a procedure name but the short name would.

```scheme
~ (define name
    (lambda (...)
      ...))

~ name
#

~ (define (name2 ...)
    ...)

~ name2
#
```

I'd really like to have the same behavior for both, so what did I do? I redefined define.

```scheme
(define-syntax define 
  (syntax-rules (lambda) 
    [(define name 
       (lambda (args ...) 
         bodies ...)) 
     ($define$ (name args ...) 
       bodies ...)] 
    [(define name 
       (lambda (args ... . dotted) 
         bodies ...)) 
     ($define$ (name args ... . dotted) 
       bodies ...)] 
    [(define name 
       (lambda arg 
         bodies ...)) 
     ($define$ (name . arg) 
       bodies ...)] 
    [(define stuff ...) 
     ($define$ stuff ...)])))
```

Probably not the best way to solve the problem, but it does work. I've done some stress testing to see if it breaks anything else, but for the moment it doesn't seem to do so.

The new version available is <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">r190</a>.
---
title: Wombat IDE - Options options everywhere
date: 2011-07-29 05:05:14
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: options-options-everywhere
---
From the beginning, I wanted Wombat to be configurable where it mattered, so I added a system that would be able to load and save options. This being a Scheme IDE, I wrote the options files in... what else? Scheme! Here's the default options.cfg file included with the current distribution of Wombat (r90). The code to read these options is defined using Scheme macros written partially in a hyrbid of Java and Scheme and can (at least theoretically) even be set during runtime by calling the cfg procedure in the REPL.

<!--more-->

```scheme
; Default dimensions of the main window
(cfg 'main.width 600)
(cfg 'main.height 800)

; Keybinding for evaluating the current file
; alternative (cfg scheme.run "control R")
(cfg 'scheme.run "F5")

; The Scheme backend to use.
; Use 'sisc to use the built in default
; Other options should be defined in schemes.cfg
;(cfg 'scheme 'petite)
(cfg 'scheme 'sisc)
```

One thing that I wanted to do (which you can see in the configuration file) was to allow for essentially plug-and-play backends. While <a title="Second Interpreter of Scheme Code" href="http://sisc-scheme.org/">SISC</a> would be the default Scheme and used to intially load the options, I wanted to be able to switch to any installed Scheme on the user's system (at least any that I had a plugin for). Here, you can see the option to switch to <a title="Petite Chez Scheme Homepage" href="http://www.scheme.com/petitechezscheme.html">Petite Chez Scheme</a> based on the paths found in schemes.cfg:

```scheme
(scheme 'petite
  "C:/Program Files (x86)/Chez Scheme Version 8.0/bin/i3nt/petite.exe"
  "C:/Program Files/Chez Scheme Version 8.0/bin/i3nt/petite.exe")
```

While not very portable, this would allow enterprising users to switch to any other Scheme they wanted.

Finally, there was a third options file that controlled the syntax highlighting and indentation.

```scheme
; Colors for different kinds of tokens, must be in Hex color codes starting with 0x
(color 'normal "Black")
(color 'comment "0x006600")
(color 'keyword "0x000099")
(color 'string "0xFF8C00")
(color 'bracket "Cyan")

; Keywords and how much to indent the next line after them.
(keyword "define" 2)
(keyword "lambda" 2)

(keyword "if" 4)
(keyword "cond" 2)
(keyword "and" 5)
(keyword "or" 4)

(keyword "+" 2)
(keyword "-" 2)
(keyword "*" 2)
(keyword "/" 2)
(keyword "add1" 6)
(keyword "sub1" 6)

(keyword "list" 6)
(keyword "cons" 6)
(keyword "car" 5)
(keyword "cdr" 5)
```

The colors can be either hex values or any name recognized by <a title="java.awt.Color API" href="http://docs.oracle.com/javase/1.4.2/docs/api/java/awt/Color.html">color</a>. Each keyword includes both a name (which will be highlighted) and an indentation level for subsequent nested lines. This way things like `if` line up nicely:

```scheme
(if (zero? n)
    1
    (* n (fact (- n 1))))
```

Finally, there are also menu options to automatically these configuration files into the editor and then to reload changes (such as new keywords) on the fly:

{{< figure src="/embeds/2011/Wombat-build-91.png" >}}

You can get the new build r91 <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.
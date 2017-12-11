---
title: Translate CSV to HTML
date: 2013-01-16 04:55:10
programming/languages:
- HTML
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- CSV
- Web Development
---
<a href="http://programmingpraxis.com/2013/01/15/translate-csv-to-html/" title="Translate CSV to HTML">Yesterday's post</a> from Programming Praxis asks us to write a function that will read content formatted as {{< wikipedia "comma-separated values" >}} and output the result as an HTML table. Their solution uses the <a href="http://programmingpraxis.com/essays/#text-file-databases" title="Text file database">text file database library</a> that they posted about (which is a neat concept, you should check it out), but I think I'm going to work out the solution more directly.

<!--more-->

To make the problem more interesting, I wanted to add a few additional constraints:


* The parsed must be able to handle quoted expressions that may themselves contain commas or escaped quotes (example: "to be, or not \"to be\"" should parse as a single item)
* Any expression that could be *read* as a Scheme expression should be
* All other expressions should be read as strings


So if we were to take this as a sample input file:

```css
this,is a,"test of awesome"
1,2,3.14
#<void>,"frog, \"neblins\"",#f
```

The output should be a list of lists like so:

```scheme
'((this "is a" "test of awesome")
  (1 2 3.14)
  ("#<void>" "frog, \"neblins\"" #f)))
```

Note how "is a" had to be parsed as a string because it was two objects, both quoted strings parsed correctly (including the escaped quotes and comma), and the numbers and *#f* all were converted into Scheme objects. Also, since *#<void>* isn't 'readable', it should be read as a string.

From there, we'll want to output that as HTML, but we'll get to that in a bit. If you'd like to follow along with the full code though, you can do so on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/csv-to-html.rkt" title="GitHub: csv to html source">csv to html source</a>

My basic avenue of attack is to use a {{< wikipedia "finite state machine" >}} to parse the input. I'm going to have four states:


* start -- when we're starting a line item
* string -- while we're reading a string
* string/escape -- immediately after an escape in a string
* normal -- any non-string line item


With these, we'll need to keep track of three additional things (all lists):


* lines -- all of the completed lines we've read thus far
* current-line -- the progress we've made on the current line
* current-block -- the progress we've made on the current line item


All three will start out empty. So our basic code is going to look something like this:

```scheme
; read csv content from the current input stream
; try to parse each value as a Scheme value, on fail return a string
; make sure to correctly handle quoted strings
(define (read-csv)
  (let loop ([lines '()]
             [current-line '()]
             [current-block '()]
             [mode 'start]) ; start, string, string/escape, or normal
    ...)
```

So far, so good. Although it does a whopping lot of nothing as of yet. Let's fix that.

First, we want to read the next character. Then we'll need to process it. The first case to consider will be if we're at the end of the file:

```scheme
...
(define next (read-char))
(cond
  ; eof, stop reading
  [(eof-object? next)
   (reverse (cons (reverse (cons (try-read (list->string (reverse current-block)))
                                 current-line))
                  lines))]
...
```

For the moment, ignore the *try-read* function. That will do the work of trying to parse a string as a Scheme object and falling back to a string if it fails. Other than that, one additional thing to note is that all three of the lists mentioned above are being built backwards (that's just the nature of {{< wikipedia "tail recursion" >}}; ask me why in the comments if you're curious).

That means when we're done with each block/line, we have to *reverse* it. You incur an *O(n)* cost, but compared to some of the other stuff we're doing, that'll be negligible. If you're really interested in performance, you'd probably want to read a line at a time into memory and split it using *substring*.

In any case, now that possibility is out of the way, the next to consider is whether we're in *string* mode or *normal* / non-string mode. That's actually probably the easiest state to deal with:

```scheme
...
; start in string or normal mode
[(eq? mode 'start)
 (loop lines current-line (cons next current-block) (if (eq? next #\") 'string 'normal))]
...
```

All we have to do is check for an opening quote.

Next, dealing with string mode. Basically, we have three options. Either we continue with normal characters in the string, we find an escape character, or we end the string.

```scheme
...
      ; look for escaped characters in string mode
      [(and (eq? mode 'string) (eq? next #\\))
       (loop lines current-line (cons next current-block) 'string/escape)]

      ; read next character in escape mode
      [(eq? mode 'string/escape)
       (loop lines current-line (cons next current-block) 'string)]

      ; end the string in string mode (the next character must be a comma or newline)
      ; todo: deal with \r\n newlines
      [(and (eq? mode 'string) (eq? next #\"))
       (define done-block (try-read (list->string (reverse (cons next current-block)))))
       (define next-next (read-char))
       (cond
         [(eq? next-next #\,)
          (loop lines (cons done-block current-line) '() 'start)]
         [(eq? next-next #\newline)
          (define done-line (reverse (cons done-block current-line)))
          (loop (cons done-line lines) '() '() 'start)]
         [else
          (error 'read-csv "Invalid string literal, missing comma or newline")])]
...
```

This is a bit more complicated, but only a bit. The interesting parts to note are that if we see an escape, we just skip over (buffering) the next character. That way, we can skip right past things like \". Technically, we could read ahead (like we have to do in the third part of this anyways) and skip the state entirely, but I think this way is cleaner.

To show the other way though, consider the third part where a string mode block ends. There are three possible endings here (each of which could be states, but I'm demonstrating both methods). Either you have a comma after the quote and you go on to another item on this line, you have a newline (I need to but haven't dealt with \r or \r\n {{< wikipedia "line endings" >}}. For now, this is Unix (including OS X) only.), or you have an error. One interesting thing to note: this system actually allows for multiline strings. So these two would be equivalent:

```css
"hello
world"

"hello\nworld"
```

Next, we have cases for the end of an item. These are basically the same as the string cases above, but I broke them out into their own cond cases this time.

```scheme
...
; end an item
[(and (eq? mode 'normal) (eq? next #\,))
 (define done-block (try-read (list->string (reverse current-block))))
 (loop lines (cons done-block current-line) '() 'start)]

; end a line
; todo: deal with \r\n
[(and (eq? mode 'normal) (eq? next #\newline))
 (define done-block (try-read (list->string (reverse current-block))))
 (define done-line (reverse (cons done-block current-line)))
 (loop (cons done-line lines) '() '() 'start)]
...
```

Like I said, this is the same as before.

Finally, we have the default case. If nothing else happens, just buffer the character and keep reading. This should happen most of the time. Note that *mode* (the FSM state) is preserved. This is important.

```scheme
...
; buffer all other characters
[else
 (loop lines current-line (cons next current-block) mode)])))
...
```

And there you have it. A fully functional CSV parser. You can try it out (although you'll need the definite for *try-read*, which I'll get to in a moment) like so:

```scheme
> (with-input-from-string
   "Beth,12.75,0,mfg
   Dan,8.50,10,sales
   Kathy,11.40,30,sales
   Mark,12.75,40,mfg
   Mary,7.50,20,mfg
   Susie,10.30,25,acctg"
   read-csv)
'((Beth 12.75 0 mfg) (Dan 8.5 10 sales)
  (Kathy 11.4 30 sales) (Mark 12.75 40 mfg)
  (Mary 7.5 20 mfg) (Susie 10.3 25 acctg))
```

Note how all of the names and positions were parsed as symbols. If you really wanted them as strings, you could just quote them:

```scheme
> (with-input-from-string
   "\"Beth\",12.75,0,mfg"
   read-csv)
'(("Beth" 12.75 0 mfg))
```

Now that I've showed that off sufficiently, what black magic is going on in that *try-read* function? Remember, the goal is to try to read the input as a single Scheme object. If that fails (for any reason) or if there is more than one object, just fall back and return the original string.

```scheme
; parse a block into a scheme object
; if that fails, just return the original string
(define (try-read block)
  (with-handlers ([exn? (lambda (err) block)])
    (with-input-from-string
     block
     (lambda ()
       (define result (read))
       (when (not (eof-object? (read)))
         (error 'try-read "unfinished"))
       result))))
```

This is actually the first time I've worked with Racket's {{< doc racket "exceptions" >}} and I have to say, they're actually pretty nice to work with. Just add an exception predicate (I used *exn?* to catch all of them) and say what that should return.

The last bit there, with the *(when (not (eof-object? ...)))* is to throw just such an exception if there's still more to read. I didn't have this originally, but that mean that something like this would happen:

```scheme
> (with-input-from-string
   "hello world"
   read-csv)
'(hello)
```

With the added code, you get a string as expected:

```scheme
> (with-input-from-string
   "hello world"
   read-csv)
'(("hello world"))
```

So that's all we need to parse the CSV files. What about the second half of that <a href="http://programmingpraxis.com/2013/01/15/translate-csv-to-html/" title="Translate CSV to HTML">original question</a> though? We still need to output an HTML table!

Well, actually that's by far the easier part. Just use *for* loops around *printf* statements.

```scheme
; write a list of lists to an html table
(define (csv->html csv)
  (with-output-to-string
   (lambda ()
     (printf "
| ~a |
|----|

```

Bam. Done.

And there you have it, the ability to read CSV files and write them back out as HTML tables. I think I may actually put this in to replace the (relatively new) <a href="http://blog.jverkamp.com/wombat-ide/c211-csv-api/" title="Wombat API: (c211 csv)">(c211 csv)</a> library in Wombat. It handles quoted strings much more nicely (or at all).

As a final aside, yes. I realize this could be written much more 'concisely' if you remove the constraints on quoted items and trying to convert to Scheme objects:

```scheme
(require racket/string)

(define (csv->html csv)
  (printf "
| ~s |
|----|

```

But where's the fun in that? :smile:

If you'd like to download the full code for today's post, you can do so on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/csv-to-html.rkt" title="GitHub: csv to html source">csv to html source</a>

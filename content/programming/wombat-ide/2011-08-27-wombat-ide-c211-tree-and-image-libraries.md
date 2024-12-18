---
title: Wombat IDE - C211 tree and image libraries
date: 2011-08-27 05:05:33
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
slug: c211-tree-and-image-libraries
---
To start off, I have a small list of bug fixes / minor improvements before I get to the real meat of what I've got for the day:

* Added ability to change font size
* Added a program icon (which doesn't seem to work on OSX, I should look into this)
* Added an IconManager to deal with all of the menu icons
* Added option to reset the Scheme environment if it gets broken for whatever reason
* Changed prompt from >>> to §, mostly because I just like the character (also a single character saves space)
* Fixed display, redirecting it to the REPL. Unfortunately `trace` still doesn't work
* Bound true to `#t` and false to `#f` to make input and output match
* Fix for a problem that would prevent Wombat from closing on OS X


<!--more-->

Now, a bigger change was actually getting the C211 libraries working in Wombat. Previously, they had been written in pure Scheme code, designed to run on [Chez Scheme][chez]. Unfortunately, some of that code, such as the code to load and save images was somewhat slower than I would like so I decided to rewrite the libraries in Java. That way, I could take advantage of all of the image types that Java can read/write without having to write adaptors for each myself. See below for the APIs for the image and tree libraries.

Overall, this has been a pretty major bump in version, we're up to r154 now. Download it <a title="Wombat Download Page" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/">here</a>.
## Image library
The C211 image library matches the old API while at the same time adding a few new features. Here's the API (Edit: The newest API can be found <a title="C211 Image API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm">here</a>):

* `(color r g b)` - creates a color with the given `r`, `g`, and `b` channels
* `(color? c)` - tests if `c` is a color
* `(color-equal? c1 c2)` - checks if two colors are the same
* `(color-ref c b)` - extracts the band `b` (one of the symbols `red`, `green`, or `blue`) from the color `c```
* `(image? i)` - tests if `i` is an image
* `(image-equal? i1 i1)` - tests if two images are equal (the same size and all pixels are `color-equal?`
* `(image-rows i)` - extract the number of rows in an image
* `(image-cols i)` - extract the number of columns in an image
* `(image-set! i r c c)` - sets the pixel at (`r`, `c`) in the image `i` to the color `v`
* `(read-image [filename])` - reads an image; if `filename` is not specified, prompt the user
* `(write-image i [filename])` - writes an image `i` to a file; if `filename` is not specified, prompt the user
* `(draw-image i)` - display the given image `i` on the screen
* `(image-map i p)` - map a function `p` of the form `color -> color` over the image
* `(make-image rs cs g)` - create a new image with `rs` rows and `cs` columns; if `g` is a color, use that; if `g` is a function of the form `r, c, rs, cs -> color` apply it at each possible row and column value``

In addition, the following colors have also been defined as constants: `black`, `darkgray`, `gray`, `lightgray`, `white`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `orange`, and `pink`.

Mainly, the only new features that the API exposes are making the filenames to `read-image` and `write-image` optional, allowing the user to choose an image with a standard file dialog.

As an example of what the image library is capable of, consider this code:

```scheme
(draw-image
  (make-image 500 500
    (lambda (rs cs r c)
      (color
        (div (* r 255) rs)
        (div (* c 255) cs)
        0))))
```

Save this code as `make-gradient.ss` and hit F5 to run it. Here's what you get:

{{< figure src="/embeds/2011/make-image.png" >}}

There are much more powerful things you can do with this that I'll probably post at some point, but for now I think you get the idea.
## Tree library
Edit: The newest C211 Tree Library API can be found <a title="C211 Tree API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-tree.htm">here</a>.

* `(tree v l r)` - creates a new tree with the given root value `v`, left subtree `l`, and right subtree `r`
* `(tree? tr)` - checks if an object is a tree
* `(leaf v)` - creates a leaf; an alias of `(tree v (empty-tree) (empty-tree))`
* `(leaf? tr)` - checks if a tree is a leaf
* `(empty-tree)` - creates an empty tree
* `(empty-tree? tr)` - checks if a tree is empty
* `(left-subtree tr)` - returns the left subtree of a given tree
* `(right-subtree tr)` - returns the right subtree of a given tree
* `(root-value tr)` - returns the value stored at the root value of the given tree
* `(draw-tree tr)` - draws a tree to the screen

Here's an example of `draw-tree`:

```scheme
(draw-tree
  (tree 8
  (tree 6
    (leaf 7)
    (empty-tree))
  (tree 5
    (tree 3
      (leaf 0)
      (leaf 9))
    (empty-tree))))
```

{{< figure src="/embeds/2011/draw-tree.png" >}}

One feature that I think turned out particularly well is how the tree will automatically scale with its window. This way you can shrink or grow the tree when you need to show certain properties or compare multiple trees:

{{< figure src="/embeds/2011/draw-tree-scaled.png" >}}

The only change between the previous tree API in <a title="Scheme Widget Library" href="http://www.scheme.com/chezscheme.html">SWL</a> and the new version is that the left and right subtrees of a tree must actually be trees. Previously, they could be any value, but do to a design consideration in the Java back-end of the trees, the underlying data structure was restricted. This will actually theoretically make it harder to write incorrect tree code as you can no longer mix tree and non-tree code. We'll see this semester if this is actually the case.
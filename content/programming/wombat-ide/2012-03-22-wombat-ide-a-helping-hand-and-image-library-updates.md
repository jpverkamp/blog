---
title: Wombat IDE - A helping hand and image library updates
date: 2012-03-22 04:55:53
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
Two interesting things to talk about this update. First, I have my first code contribution from someone else. I've been working with Graham during Peer Tutoring for C212 and when we were busy, we talked about Wombat. He seemed interesting in helping, so he worked out the new about dialog for Wombat. Now it has all of the different libraries and licenses that Wombat uses, along with a nice picture.

Many thanks! (And if anyone else wants to contribute, feel free. It's always nice to get a different viewpoint on things.)

<!--more-->

The second new features is a few new functions to add to the [image API]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}) (Edit: The most up to date C211 Image API can be found <a title="C211 Image API" href="http://www.cs.indiana.edu/cgi-pub/c211/wombat/docs/c211-image.htm">here</a>):

* `(color-equal? c1 c2)` - tests if two colors are equal
* `(image-equal? i1 i2)` - tests if two images are equal
* `(image->list i)` - converts an image into a flat list of colors, across each row then down columns
* `(list->image cols i)` - inverse of `image->list`

The first two were actually both in the original image API but somehow got lost in the shuffle of converting back to the mostly pure-Scheme versions. The latter two are for a final exam problem and seemed useful enough to add permanently.

Finally, the rectangles and ovals on `draw-tree` have been reversed to match the pre-Wombat version of the API. Essentially, this is so that any slides / screenshots from those days don't have to be redone (and it really wasn't a hard fix).
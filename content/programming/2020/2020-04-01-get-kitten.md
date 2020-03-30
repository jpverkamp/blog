---
title: Get kitten
date: 2020-04-01
programming/topics:
- Dotfiles
programming/languages:
- Bash
---
I upload a lot of images when testing for various things. And of course, I don't want to use any of my own images. So what would I do instead? 

Kittens!

```fish
$ get-kitten

Downloading a 640 x 480 kitten
Downloading to kitten-1.jpg

$ open kitten-1.jpg
```

{{< figure src="/embeds/2020/kitten-1.jpg" >}}

Perfect.

<!--more-->

Basically, wrap a `curl` to https://placekitten.com/ with some code to not overwrite the poor kittens and to be able to specify the sizes:

```bash
#!/bin/bash

width=${1:-640}
height=${2:-$(dc -e "$width 4 / 3 * p")}

echo "Downloading a $width x $height kitten"

i=1

while true
do
    filename="kitten-$i.jpg"
    if [ -f $filename ]; then
        echo "$filename already exists"
        ((i+=1))
        continue
    else 
        echo "Downloading to $filename"
        curl -s https://placekitten.com/$width/$height -o $filename
        break
    fi
done
```

MATH! KITTENS!

It doesn't actually work to run this in a loop, since they're cached per size. Unless of course you want piles of identical kittens. But it was fun to write anyways. 

[Source on github](https://github.com/jpverkamp/dotfiles/blob/master/bin/get-kitten)
---
title: gif shrinkage with ImageMagick
date: 2015-03-05
programming/topics:
- Dotfiles
- Graphics
- Open Source
- Unix
---
I have a gif collection now. :)

{{< figure src="/embeds/2015/dun-dun-dunnnnn.gif" >}}

<!--more-->

One problem with gifs is that they tend to be somewhat sizable. To keep that at least a little under control, I've added a quick script to my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) to trim all files passed on the command line to a maximum edge size of 256 pixels:

```bash
#!/bin/bash

tmpdir=`mktemp -d /tmp/shrink-gifs.XXXX`
echo "$tmpdir"

for file in "$@"
do
  echo "$file"
  convert "$file" -alpha on -channel rgba -coalesce -resize 256x256 -layers OptimizeFrame -colors 64 "$tmpdir/$file"
  mv "$tmpdir/$file" "$file"
done
```

Basically, I'm using the excellent <a href="http://www.imagemagick.org/">ImageMagick</a> software, specifically the `convert` utility. All of those flags are necessary since gifs have layers. This results in both a properly converted gif but also a somewhat optimized palette.

Also, we're using a temporary directory rather than using the in place version of `convert`: `mogrify`. For whatever reason, `mogrify` doesn't seem to work on gifs. So it goes.

As a side note, `identify` (another tool that comes with ImageMagick) is really useful. Give it an image and it will tell you how large it is, all on the command line.

This script (and all of my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}})) is available on GitHub: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/shrink-gifs">shrink-gifs</a>

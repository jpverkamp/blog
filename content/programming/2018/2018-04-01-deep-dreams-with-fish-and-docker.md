---
title: Deep Dreams with Fish and Docker
date: 2018-04-01
programming/languages:
- Fish
programming/topics:
- Docker
- Dotfiles
---
[DeepDream](https://github.com/google/deepdream) is a [research project](https://research.googleblog.com/2015/06/inceptionism-going-deeper-into-neural.html) originally from Google that gives you a look into how {{< wikipedia "neural networks" >}} see the world. They're fascinating, bizarre, and a lot of fun to play with. A bit of work getting them to work on your own machine though.

Luckily, GitHub user [saturnism](https://github.com/saturnism/deepdream-cli-docker) has put together a lovely Docker-based tool that will do just that for us: [deepdream-cli-docker](https://github.com/saturnism/deepdream-cli-docker). Unfortunately, the commands are still a bit long. Let's clean it up a bit and add the ability to dream about non-JPGs (animated GIFs especially!).

{{< figure src="/embeds/2018/dream-sorcery.gif" >}}

<!--more-->

# Base case: JPGs

First, we want the base case. How do we convert a {{< wikipedia "jpg" >}}?

```fish
cat $filename | docker run -i saturnism/deepdream-cli -l inception_4b/output > dream-$filename ^ /dev/null
```

That's easy enough. Put that as an alias and it works for just about any Bash-ish shell.

```fish
><> open hello-frame.jpg
```

{{< figure src="/embeds/2018/hello-frame.jpg" >}}

```fish
><> dream hello-frame.jpg

I'm dreaming of hello-frame.jpg...
Working in /tmp/dream.nJTQ
hello-frame.jpg has awoken

><> open dream-hello-frame.jpg
```

{{< figure src="/embeds/2018/dream-hello-frame.jpg" >}}

Let's go deeper.

```fish
><> begin
      for i in (seq 1 10)
            dream hello-frame.jpg
            mv dream-hello-frame.jpg hello-frame.jpg
        end
        mv hello-frame.jpg inception-dream-hello-frame.jpg
    end

I'm dreaming of hello-frame.jpg...
Working in /tmp/dream.hWOx
hello-frame.jpg has awoken
...
I'm dreaming of hello-frame.jpg...
Working in /tmp/dream.iA6i
hello-frame.jpg has awoken

><> open inception-dream-hello-frame.jpg
```

{{< figure src="/embeds/2018/inception-dream-hello-frame.jpg" >}}

# Non-JPGs: Convert and dream

Next, let's expand that a bit to any single frame, non-JPG format. [ImageMagick](https://www.imagemagick.org/script/index.php) to the rescue:

```fish
convert $filename $filename.jpg
cat $filename.jpg | docker run -i saturnism/deepdream-cli -l inception_4b/output > dream-$filename.jpg ^ /dev/null
convert dream-$filename.jpg dream-$filename
```

# Dream deeper: Converting GIFs frame by frame

Okay, let's get a bit more interesting now. What if want to apply a Deep Dream to an entire GIF one frame at a time:

```fish
mkdir src-frames dst-frames
convert $filename -coalesce src-frames/%04d.jpg

set -lx framecount (ls src-frames | wc -l)
for f in (ls src-frames/)
    cat src-frames/$f | docker run -i saturnism/deepdream-cli -l inception_4b/output > dst-frames/$f ^ /dev/null
    echo "$filename: Rendered $f (of $framecount)"
end

convert dst-frames/* -set delay 0 -strip -coalesce -layers Optimize dream-$filename
```

This one I particularly like. Essentially, we have three parts. Converting a GIF to JPG will automatically unpack each frame to its own image. We need the `-coalesce` option, otherwise transparent parts of frames (where they are just relying on the previous frame's color) will just end up with a solid color. The `%04d.jpg` makes sure that the frame filenames have leading zeros so they will sort properly.

Then, we convert each frame one at a time and put them all back together, optimizing as we go. Pretty cool that.

```fish
><> open hello.gif
```

{{< figure src="/embeds/2018/hello.gif" >}}

```fish
><> dream hello.gif

I'm dreaming of hello.gif...
Working in /tmp/dream.MrBg
hello.gif: Rendered 0000.jpg (of       51)
hello.gif: Rendered 0001.jpg (of       51)
hello.gif: Rendered 0002.jpg (of       51)
hello.gif: Rendered 0049.jpg (of       51)
hello.gif: Rendered 0050.jpg (of       51)
hello.gif: Rendered 0051.jpg (of       51)
hello.gif has awoken!

><> open dream-hello.gif
```

{{< figure src="/embeds/2018/dream-hello.gif" >}}

Finally, we want to wrap up everything. Specifically, we want:

- Allow multiple files to be converted at once
- Use a temporary folder and clean up when we're done
- Print out a bit more progress as we go

We can wrap this all up fairly cleanly:

```fish
for filename in $argv
    notify "I'm dreaming of $filename..."
    set -lx tmpdir (mktemp -d /tmp/dream.XXXX)
    cp $filename $tmpdir

    pushd $tmpdir
        echo "Working in $tmpdir"
        if test (string match -r ".gif" $filename)
            # GIF conversion
        else if test (string match -r ".jpg" $filename)
            # JPG conversion
        else
            # ANYTHING ELSE
        end
    popd

    mv $tmpdir/dream-$filename .
    rm -rf $tmpdir

    notify "$filename has awoken"
end
```

I like working with temporary directories with `mktemp`, it's handy. `notify` is another custom dotfile I have that will always echo, but on OSX will also display a notification using `osascript`'s `display notification`:

```bash
#!/bin/bash

echo "$@"
osascript -e "display notification \"$@\" with title \"CLI Notification\"" || true
```
Fun times.

{{< figure src="/embeds/2018/dream-canteven.gif" >}}

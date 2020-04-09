---
title: Command line AES with openssl (and tar)
date: 2020-04-09
programming/topics:
- Dotfiles
- Encryption
- AES
programming/languages:
- Bash
---
I had [a script](https://github.com/jpverkamp/dotfiles/blob/b708190/bin/aes) that would take a file and a passphrase and either encrypt it or, if already encrypted, decrypt it. It worked well enough and I got to play with the {{< doc python struct >}} library. But it was home grown--so not compatible with anything--and didn't properly validate anything. It worked well enough, but perhaps I could do something better.

<!--more-->

Enter [aes 2.0](https://github.com/jpverkamp/dotfiles/blob/7d53f95/bin/aes).

This time around, it's just a thin wrapper around [OpenSSL](https://www.openssl.org/), originally based on the commands in [https://www.tecmint.com/encrypt-decrypt-files-tar-openssl-linux/](this article). To encrypt a file:

```bash
dst=$src.aes
openssl enc -e -aes256 -in $src -out $dst && rm $src
```

To decrypt:

```bash
dst=${src::${#src}-4}
openssl enc -d -aes256 -in $src -out $dst && rm $src || (rm $dst; false)
```

And wrap that all up with a bit of magical filenames to [https://simpleprogrammer.com/when-doing-the-right-thing-is-wrong/](do the right thing)(but actually):

```bash
for src in "$@"
do
    if [[ "$src" == *.aes ]]
    then
        echo "Decrypting $src"
        dst=${src::${#src}-4}
        openssl enc -d -aes256 -in $src -out $dst && rm $src || (rm $dst; false)

    else
        echo "Encrypting $src"
        dst=$src.aes
        openssl enc -e -aes256 -in $src -out $dst && rm $src
    fi
done
```

And it works great:

{{< figure src="/embeds/2020/aes-file.gif" >}}

Excellent. 

But wait...

{{< figure src="/embeds/2020/theres-more.gif" >}}

There's more. 

```bash
if [[ "$src" == *.aesdir ]]
then
    echo "Decrypting directory $src"
    dst=${src::${#src}-7}
    (openssl enc -d -aes256 -in $src | tar xf -) && rm $src

elif [[ -d "$src" ]]
then
    echo "Encrypting directory $src"
    dst=$src.aesdir
    (tar -czf - $src | openssl enc -e -aes256 -out $dst) && rm -rf $src

...
```

Let's do directories! Basically, if it's given a directory instead of a file, tar it up then encrypt it (with a different extention). If you see that extension, decrypt it and untar it. 

{{< figure src="/embeds/2020/aes-directory.gif" >}}

Recordings generated via [Terminalizer](https://terminalizer.com/) with a wrapper. I'll write that up soon(tm). 

All in all, it's pretty handy. I'll have to move my files over at some point, but for now, onwards!
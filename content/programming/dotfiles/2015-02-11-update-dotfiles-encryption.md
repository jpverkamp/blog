---
title: update-dotfiles encryption
date: 2015-02-11
programming/topics:
- AES
- Dotfiles
- Open Source
- Unix
---
I do like having my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) on GitHub. For one, it means that they're always available when I set up a new machine. For two, others can see them and take whatever is interesting for their own dotfiles. But all that has a disadvantage: what if I want to store my SSH configs?

<!--more-->

Technically, they're not secret. I don't have my actual SSH keys in there. But I do have some names of machines and at least not having those on the GitHub means that the spiders trolling the repos have at least one more step before finding them. Especially those running on non-standard ports.

To that end, here's a quick script to AES encrypt / decrypt files with Python.

First, we want something that can turn any password into an AES key. Since they have to be an exact number of bits a hashing function works particularly well here:

```python
def get_key():
    if 'AESKEY' in os.environ:
        key = os.environ['AESKEY']
    else:
        key = getpass.getpass('AES passphrase: ')

    return hashlib.sha256(key.encode('utf-8')).digest()
```

(Yes, I should be using a [[wiki:Password-Based Key Derivation Function]](). So it goes.)

Next, the encryption function. We need to set up a random [[wiki:initialization vector]]().

Then, since the file might not be evenly divisible into blocks, we'll need to pad it. Since we want this to be able to deal with binary or other files, there's no guarantee that we can tell when a file has ended. So we'll use the `struct` library to store the file length as well. Given that we're storing the size as a 64-bit integer, we'll be able to store files up to 18.56 exabytes. Yeah, I think we'll be fine for a while.

Finally, we want to add a hash so we can verify that the file was not tampered with via <a href="https://crypto.stackexchange.com/questions/202/should-we-mac-then-encrypt-or-encrypt-then-mac">encrypt-then-MAC</a>. All together:

```python
def encrypt(file):

    key = get_key()

    iv = os.urandom(16)
    encryptor = AES.new(key, AES.MODE_CBC, IV = iv)

    with open(file, 'rb') as fin:
        content = fin.read()

    # Store the original file size as uint64 and pad to 16 bytes
    content = struct.pack('>Q', len(content)) + content
    content = content + (b'\0' * (16 - len(content) % 16))

    content = encryptor.encrypt(content)
    hash = hashlib.sha256(content).digest()

    content = base64.b64encode(iv + hash + content)

    outfile = file + '.aes'
    with open(outfile, 'wb') as fout:
        fout.write(content)
```

Straight forward.

Likewise, decryption pulls apart the parts of the file, checks the integrity with the hash, then decrypts:

```python
def decrypt(file):

    key = get_key()

    with open(file, 'r') as fin:
        content = fin.read()

    content = base64.b64decode(content)
    if len(content) < 32:
        print('Malformed content: not enough data')
        sys.exit(1)

    iv = content[:16]
    hash = content[16:48]
    content = content[48:]

    if hash != hashlib.sha256(content).digest():
        print('Failed hash check')
        sys.exit(1)

    decryptor = AES.new(key, AES.MODE_CBC, IV = iv)
    content = decryptor.decrypt(content)

    fileSize = struct.unpack('>Q', content[:8])[0]
    content = content[8:fileSize+8]

    outfile = file[:-4]
    with open(outfile, 'wb') as fout:
        fout.write(content)
```

Shiny. Now let's tweak the script that updates dotfiles to handle encrypted files:

Basically, the only code that changes is if the user choose `y` to replace a file. If that file ends with `.aes`, ask for the password and try to decrypt it.

```python
...

# If the file is encrypted, decrypt it
if path.endswith('.aes'):
    try:
        if not aes:
            aes = imp.load_source('aes', os.path.expanduser('~/.bin/aes'))

        if aes:
            print('{0} decrypting'.format(path))
            aes.decrypt(path)
            shutil.copymode(path, path[:-4])
            path = path[:-4]
    except:
        print('{0} cannot decrypt, aes does not exist'.format(path))

...
```

One caveat is that since the `aes` library is stored without the `py` suffix, we load it dynamically with the `imp` module. I love how that's possible (even easy) in Python.

And that's about it. I've moved my SSH configs over and vastly expended them with a number of servers that I work with on a daily basis. Also there's another level which allows for different environments (work or home) and operating systems (to deal with different keyboard standards).

Very cool.

If you'd like to see the full source for either piece, you can on GitHub:


* [aes](https://github.com/jpverkamp/dotfiles/blob/master/bin/aes)
* [update-dotfiles](https://github.com/jpverkamp/dotfiles/blob/master/bin/update-dotfiles)


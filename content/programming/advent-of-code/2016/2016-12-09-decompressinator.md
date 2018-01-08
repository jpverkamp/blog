---
title: "AoC 2016 Day 9: Decompressinator"
date: 2016-12-09
programming/languages:
- Python
programming/sources:
- Advent of Code
programming/topics:
- Compression
series:
- Advent of Code 2016
---
### Source: [Explosives in Cyberspace](http://adventofcode.com/2016/day/9)

> **Part 1:** A file is compressed by including compression markers of the form `(#x#)...` where the first number tells how many characters to copy and the second is how many times to copy them. So `A(2x3)HA!` becomes `AHAHAHA!`.

<!--more-->

For part 1, we could likely just expand the actual strings. But I'm guessing part 2 is going to do something crazy recursive. So let's just calculate the length directly.

```python
re_compressed_block = re.compile(r'\((?P<length>\d+)x(?P<count>\d+)\)')

def decompressed_length(content):
    index = 0
    output_length = 0

    while True:
        m = re_compressed_block.search(content, pos = index)
        if m:
            # Content before the current block
            output_length += m.start() - index

            # Expanded content
            length = int(m.group('length'))
            count = int(m.group('count'))

            output_length += length * count

            # Skip past this block for the next iteration
            index = m.end() + length
        else:
            break

    output_length += len(content) - index

    return output_length

if os.path.exists(args.input):
    with open(args.input, 'r') as fin:
        content = re.sub('\s+', '', fin.read())
else:
    content = args.input

print('v1:', decompressed_length(content, 1))
```

> **Part 2:** If a decompressed string contains a marker, decompress that as well. Repeat.

Called that.

```python
re_compressed_block = re.compile(r'\((?P<length>\d+)x(?P<count>\d+)\)')

def decompressed_length(content, version):
    index = 0
    output_length = 0

    while True:
        m = re_compressed_block.search(content, pos = index)
        if m:
            # Content before the current block
            output_length += m.start() - index

            # The current block, expand recursively for version 2
            length = int(m.group('length'))
            count = int(m.group('count'))

            if version == 1:
                output_length += length * count
            elif version == 2:
                block = content[m.end() : m.end() + length]
                expanded_block_length = decompressed_length(block, version = 2)
                output_length += expanded_block_length * count

            # Skip past this block for the next iteration
            index = m.end() + length
        else:
            break

    output_length += len(content) - index

    return output_length

print('v1:', decompressed_length(content, 1))
print('v2:', decompressed_length(content, 2))
```

My output for v2 was over 10 billion, so keeping that all in memory is unlikely to have ended well...

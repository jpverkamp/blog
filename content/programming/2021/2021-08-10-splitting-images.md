---
title: Splitting Images
date: 2021-08-10
programming/languages:
- Python
programming/topics:
- Graphics
---
I recently came across a problem where I had a single image with a transparent background containing multiple images that I wanted to split into their component parts. For example, split this:

{{< figure class="border" src="/embeds/2021/hi.png" >}}

Into these:

{{< figure class="border" src="/embeds/2021/hi_1.png" >}}
{{< figure class="border" src="/embeds/2021/hi_2.png" >}}
{{< figure class="border" src="/embeds/2021/hi_3.png" >}}
{{< figure class="border" src="/embeds/2021/hi_4.png" >}}
{{< figure class="border" src="/embeds/2021/hi_5.png" >}}

<!--more-->

My idea for an algorithm here is:

- Find any groups of columns that are entirely transparent pixels
    - Remove all columns with blank pixels, return the remaining columns between those groups
- Recursively repeat in those groups with rows
- If we didn't split to any new images, break the loop
- Otherwise, go back to the beginning (columns again)

First, split:

```python
def split(image, horizontal = True, min_size=None):
    print(f'splitting {image} {horizontal=}')

    pixels = image.load()
    width, height = image.size

    bounds = []
    start = 0

    for i in range(width if horizontal else height):
        # Found a transparent row/column
        if len({
            (pixels[i, j] if horizontal else pixels[j, i])[3]
            for j in range(height if horizontal else width)
        }) == 1:
            if start:
                bounds.append((start, i))
                start = None
        else:
            if not start:
                start = i

    # Ended with an image
    if start:
        bounds.append((start, i))

    for start, end in bounds:
        if min_size and end - start < min_size: continue

        chunk = image.copy().crop(
            [start, 0, end, height]
            if horizontal else
            [0, start, width, end]
        )
        yield chunk
```

This section amuses me somewhat:

```python
if len({
    (pixels[i, j] if horizontal else pixels[j, i])[3]
    for j in range(height if horizontal else width)
}) == 1:
```

In 'one line', it's going through an entire row/column and returning a set (`{...}`) of the alpha values (`[3]`) for each pixel. If all of the values are the same, split. 

Then we use `image.copy().crop(...)` to pull out new `PIL.Image` objects that contain the subsets of the images. 

Next, wrap that with the main loop:

```python
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--min-size', type=int, help='The minimize image size to split to')
    parser.add_argument('filenames', nargs='+', help='Image files to split')
    args = parser.parse_args()

    for filename in args.filenames:
        print(f'Splitting {filename}')
        images = [PIL.Image.open(filename).convert('RGBA')]

        while True:
            # Try to split horizontally than vertically
            new_images = list(
                image3
                for image1 in images
                for image2 in split(image1, True, min_size=args.min_size) 
                for image3 in split(image2, False, min_size=args.min_size)
            )
            
            # If we didn't generate any new images, we're done
            if len(new_images) == len(images):
                images = new_images
                break

            images = new_images

        if len(images) <= 1:
            continue
        
        name, ext = filename.split('/')[-1].rsplit('.', 1)

        for i, image in enumerate(images[1:], 1):
            filename = f'{name}_{i}.{ext}'
            print(f'Saving {filename}')
            image.save(filename)
```

In this case, we generate a `new_images` list by taking all current images and splitting them first horizontally, then vertically. Keep going until that list doesn't change. That would mean there's no way to split either way. After we have that, generate new filenames and split out the images. 

One note would that I'm `convert('RGBA')` on all images to internally represent them in a consistent format, so that the alpha channel always exists. That was a problem at first. 

```bash
$ python3 split.py --min-size 10 hi.png

Splitting hi.png
splitting <PIL.Image.Image image mode=RGBA size=800x600 at 0x10334A220> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=242x600 at 0x10356F880> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=26x600 at 0x10356F910> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=143x600 at 0x10356F8E0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=242x163 at 0x10356F9A0> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=229x163 at 0x103318CA0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=242x164 at 0x10356F9D0> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=101x164 at 0x10356F0A0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=39x164 at 0x103318CA0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=26x78 at 0x10356FA00> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=24x78 at 0x10356F8E0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=26x16 at 0x10356FA30> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=14x16 at 0x103318CA0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=143x326 at 0x10356FA60> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=141x326 at 0x10356F6D0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=229x161 at 0x10356F940> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=227x161 at 0x10334A250> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=101x162 at 0x10356FA90> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=99x162 at 0x10356FA30> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=39x16 at 0x10356FAC0> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=16x16 at 0x10334A220> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=39x56 at 0x10356FAF0> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=37x56 at 0x10356F9A0> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=24x76 at 0x10356FB20> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=22x76 at 0x10334A220> horizontal=False
splitting <PIL.Image.Image image mode=RGBA size=141x324 at 0x10356FB50> horizontal=True
splitting <PIL.Image.Image image mode=RGBA size=139x324 at 0x10356FA60> horizontal=False
Saving hi_1.png
Saving hi_2.png
Saving hi_3.png
Saving hi_4.png
Saving hi_5.png
```

Voila!

There is certainly some tuning I could do (output filename templates, detect background color, etc), but for the moment it works for what I needed. Onward!
---
title: Mandelbrot
date: 2015-09-14
programming/languages:
- Python
programming/topics:
- Fractals
- Graphics
---
Perhaps the best known fractal of all: the [[wiki:Mandelbrot set]]().

{{< figure src="/embeds/2015/mandelbrot_default_400x300_hot-and-cold.png" >}}

Since I was already working on Python code that would render an image given a function (for a future post), I figured that I might as well render fractals with it.

<!--more-->

The basic idea is simple. Use <a href="https://python-pillow.github.io/">pillow</a> (the successor <a href="http://www.pythonware.com/products/pil/">PIL</a>), create an empty image of a given size. Then, call a given function for each point in that image, passing the `x` and `y` coordinates of the function as parameters. Basically, the {{< doc racket "build-flomap*" >}} function I use all the time in Racket.

It turns out, that's actually really straight forward:

```python
def generate_image(width, height, generator):
    '''
    Generate an RGB image using a generator function.

    width, height -- the size of the generated image
    generator -- a function that takes (x, y) and returns (r, g, b)
    '''

    # Generate the data as a row-major list of (r, g, b)
    data = [generator(x, y) for y in range(height) for x in range(width)]

    # Pack that into a Pillow image and return it
    img = PIL.Image.new('RGB', (width, height))
    img.putdata(data)
    return img
```

I like that you can have multiple `for` statements in a generator like that. It's very similiar to the different forms of Racket's {{< doc racket "for" >}}[^1], but I always seem to forget that I can do that in Python.

One downside of this is that it's relatively slow (at least on the big multi-core machines we have now). Luckily, we can use the `<a href="https://docs.python.org/2/library/multiprocessing.html">multiprocessing</a>` module to speed things up:

```python
def generate_image(width, height, generator, threads = 1):
    '''
    Generate an RGB image using a generator function.

    width, height -- the size of the generated image
    generator -- a function that takes (x, y) and returns (r, g, b)
    threads -- if != 1, use multiprocessing to spawn this many processes
    '''

    # Generate the data as a row-major list of (r, g, b)
    if threads == 1:
        data = [generator(x, y) for y in range(height) for x in range(width)]
    else:
        pool = multiprocessing.Pool(threads)
        data = pool.starmap(generator, [(x, y) for y in range(height) for x in range(width)])

    # Pack that into a Pillow image and return it
    img = PIL.Image.new('RGB', (width, height))
    img.putdata(data)
    return img
```

By using `multiprocessing` rather than `threading`, we are actually spawning multiple Python processes, so we get a true multithreaded speedup. Since this program is almost entirely CPU bound, `threading` (with Python's [[wiki:global interpreter lock]]()) wouldn't actually be any faster.

An aside: Using `starmap` allows us to pass multiple parameters to the function we are mapping over. This was only introduced in Python 2.6 / 3.3, so make sure you have a sufficiently new version[^2].

With that, we can make some pretty pictures like I'm sure I've shown off before[^3].

```python
generate_image(
    400,
    300,
    lambda x, y: (
        (x * y) % 256,
        (x + y) % 256,
        max(x, y) % 256
    )
).save('sample.png')
```

{{< figure src="/embeds/2015/sample.png" >}}

Yes, I realize that's not the most Pythonic code in the world. And because the body of a Python `lambda` has to be an expression, you cannot write nearly as complicated functions as you could in Racket. It's perfectly valid though. :)

Okay, so we have a way to generate images, let's use it to generate Mandelbrot sets. The basic idea of the Mandelbrot set is surprisingly simple[^4]:

Given a complex number {{< inline-latex "\mathbb{C}" >}}, the [[wiki:complex|complex number]]() [[wiki:quadratic polynomial]]():

{{< latex >}}\mathbb{Z}_n+1 = \mathbb{Z}_n^2 + \mathbb{C}{{< /latex >}}

Either does or does not escape to infinity. If the result remains bounded as {{< inline-latex "n \to \infty" >}}, the number is part of the Mandelbrot set. If not, it's not. Because Python has built in support for complex numbers, this code is fairly elegant:

```python
def make_mandelbrot_generator(width, height, center, size, max_iterations = 256):
        '''
        A generator that makes generate_image compatible mandelbrot generators.

        width, height -- the size of the resulting image (used for scale)
        center -- the focus point of the image
        size -- the size of the larger dimension
        max_iterations -- the scale to check before exploding, used for coloring
        '''

        # Scale the size so that is the size of the larger dimension
        if width >= height:
            size_x = size
            size_y = size * height / width
        else:
            size_x = size * width / height
            size_y = size

        # Convert to a bounding box
        min_x = center[0] - size_x / 2
        max_x = center[0] + size_x / 2
        min_y = center[1] - size_y / 2
        max_y = center[1] + size_y / 2

        def generator(x, y):
            # Scale to the mandlebrot frame; convert to a complex number
            x = (x / width) * (max_x - min_x) + min_x
            y = (y / height) * (max_y - min_y) + min_y
            c = x + y * 1j

            # Iterate until we escape to infinity or run out of iterations
            # For our purposes, we can consider infinity = 2
            z = 0
            for iteration in range(max_iterations):
                z = z * z + c

                # Size is r of polar coordinates
                (r, phi) = cmath.polar(z)
                if r > 2:
                    break

            g = int(256 * iteration / max_iterations)
            return (g, g, g)

        return generator
```

I've chosen here to make a function that returns the actual color generator primarily so that we would have access to the `width` and `height` within the main function.

Amusingly, it's been proven that if the magnitude of {{< inline-latex "\mathbb{Z}_n" >}} crosses 2, it will go to infinity. Since `r` is the magnitude in the [[wiki:polar coordinate system]]() (`r`,`ϕ`), we can use that as an escape hatch and even as a basic way to color the output.

One side note: using the `multiprocessing` module, we have to be able to `<a href="https://docs.python.org/2/library/pickle.html">pickle</a>` any variables to the function called. Functions defined in the global scope can be pickled, but functions used directly as parameters to other functions cannot; don't ask me why.

So if `threads` is not 1, this does not work:

```python
generate_image(
    400,
    300,
    make_mandelbrot_generator(400, 300, (-0.5, 0), 3),
    threads = 4
)
```

But this does:

```python
generator = make_mandelbrot_generator(400, 300, (-0.5, 0), 3),
generate_image(400, 300, generator, threads = 4)
```

Weird.

Anyways, what do we get when we try it out?

{{< figure src="/embeds/2015/mandelbrot_default_400x300_grayscale.png" >}}

Beautiful[^5]!

We need some color. Let's introduce one more parameter to the `make_mandelbrot_generator` function: `coloring`. Basically, a function that takes in a number in the range `[0, 1]` (which we're already computing; that is `iteration / max_iterations`) and return an RGB color. That way, we can have some more interesting colorations.

For example, the grayscale coloring function from earlier:

```python
def grayscale(v):
    '''Simple grayscale value.'''

    g = int(256 * v)
    return (g, g, g)
```

Or how about instead, we render something in blue and red. Start at black, then fade up the blue channel, crossfade to red in the next third, and fade back to black in the last:

```python
def hot_and_cold(v):
    '''Scale from black to blue to red and back to black.'''

    r = g = b = 0

    if v < 1/3:
        v = 3 * v
        b = int(256 * v)
    elif v < 2/3:
        v = 3 * (v - 1/3)
        r = int(256 * v)
        b = int(256 * (1 - v))
    else:
        v = 3 * (v - 2/3)
        r = int(256 * (1 - v))

    return (r, g, b)
```

Let's render that one instead:

```python
generator = make_mandelbrot_generator(400, 300, (-0.5, 0), 3),
generate_image(400, 300, generator, threads = 4, coloring = hot_and_cold)
```

{{< figure src="/embeds/2015/mandelbrot_default_400x300_hot-and-cold.png" >}}

Excellent. We have a simple Mandelbrot generator. It's not exactly what I set out to do for this post (really only the `generate_image` function is), but I think it's pretty cool.

As a bonus round, I made something of a basic testing framework:

```python
THREAD_COUNT = max(1, multiprocessing.cpu_count() - 1)

SIZES = [
    (400, 300),
    (1920, 1080)
]

COLORINGS = [
    ('grayscale', grayscale),
    ('hot-and-cold', hot_and_cold),
]

IMAGES = [
    ('default', (-0.5, 0), 3),
    # http://www.nahee.com/Derbyshire/manguide.html
    ('seahorse-valley', (-0.75, 0.1), 0.05),
    ('triple-spiral-valley', (0.088, 0.654), 0.25),
    ('quad-spiral-valley', (0.274, 0.482), 0.005),
    ('double-scepter-valley', (-0.1, 0.8383), 0.005),
    ('mini-mandelbrot', (-1.75, 0), 0.1),

]

for width, height in SIZES:
    for image_name, center, size in IMAGES:
        for coloring_name, coloring in COLORINGS:
            filename = os.path.join('{width}x{height}', 'mandelbrot_{name}_{width}x{height}_{coloring}.png')
            filename = filename.format(
                name = image_name,
                width = width,
                height = height,
                coloring = coloring_name,
            )
            generator = make_mandelbrot_generator(width, height, center, size, coloring = coloring)

            start = time.time()
            img = generate_image(
                width,
                height,
                generator,
                threads = THREAD_COUNT
            )
            end = time.time()

            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            img.save(filename)

            print('{} generated in {} seconds with {} threads'.format(
                filename,
                end - start,
                THREAD_COUNT
            ))
```

`multiprocessing.cpu_count() - 1` means that I leave one processor for other work (I was having issues with my computer freazing, `multiprocessing` is good at that). Other than that, generate a bunch of images and shove them into directories by size.

Here are a few examples from <a href="http://www.nahee.com/Derbyshire/manguide.html">nahee.com</a>:

### Seahorse Valley<h3>

{{< figure src="/embeds/2015/mandelbrot_seahorse-valley_400x300_hot-and-cold.png" >}}

<h3>Double Scepter Valley

{{< figure src="/embeds/2015/mandelbrot_double-scepter-valley_400x300_hot-and-cold.png" >}}

### Triple Spiral Valley

{{< figure src="/embeds/2015/mandelbrot_triple-spiral-valley_400x300_hot-and-cold.png" >}}

### Quad Spiral Valley

{{< figure src="/embeds/2015/mandelbrot_quad-spiral-valley_400x300_hot-and-cold.png" >}}

### Mini Mandelbrot

{{< figure src="/embeds/2015/mandelbrot_mini-mandelbrot_400x300_hot-and-cold.png" >}}

Or how about one nice large one (right click, save as):

{{< figure src="/embeds/2015/mandelbrot_seahorse-valley_1920x1080_hot-and-cold.png" >}}

So much detail!

Enjoy!

[^1]: The <a href="http://www.call-cc.org/">chicken</a> or the <a href="https://wiki.python.org/moin/egg">egg</a>?
[^2]: Use Python 3. The more people that use it, the less we'll have issues with split-version libraries.
[^3]: [Generating omnichromatic images]({{< ref "2015-01-01-generating-omnichromatic-images.md" >}}) as an example
[^4]: or at least concise to explain
[^5]: Or at least elegant
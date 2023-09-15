---
title: 'Ludum Dare 46: Tetris Sand'
date: 2020-04-17 23:00:00
programming/languages:
- GScript
- Godot
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Games
series:
- Ludum Dare 46
---
It's [been a while]({{< ref "2014-08-24-sandbox-battle.md" >}}) since I've last done a [Ludum Dare](https://ldjam.com/). I felt the itch though, so let's do it again. 

> [Ludum Dare](https://ldjam.com/) is an online event where games are made from scratch in a weekend. Check us out every April and October!

The theme this time: *Keep it alive*

I don't know if I'll make it all the way through or actually finish a game. But I'm going to give it a try!

<!--more-->

{{< figure src="/embeds/2020/ludum-dare-46-planning.jpg" >}}

Basic idea: smoosh together Tetris and a Falling Sand style game. I know that's more or less what I did [last time](({{< ref "2014-08-24-sandbox-battle.md" >}})) (and [years before that](2009-11-28-sandbox-and-so-it-begins.md)), but it's fun! And something I know. 

Getting dynamic texture in Godot working from scratch proved to be interesting™. But I finally got something working:

```python
extends Sprite

# The image size can be changed for various blocks in the editor
export var IMAGE_SIZE = Vector2(800, 600)

const IMAGE_FORMAT = Image.FORMAT_RGBA8
var rng = RandomNumberGenerator.new()

var my_image
var my_texture

func _ready():
	# Resize the sprite to our given size
	region_rect = Rect2(0, 0, IMAGE_SIZE.x, IMAGE_SIZE.y)
	
	# Create the image we will actually draw to
	my_image = Image.new()
	my_image.create(IMAGE_SIZE.x, IMAGE_SIZE.y, false, IMAGE_FORMAT)
	
	# Create a texture that the image will render to and that we can use on this sprite
	my_texture = ImageTexture.new()
	my_texture.create_from_image(my_image)
	
	# Lock the image, this has to be done to draw to it
	my_image.lock()
	for _i in range(1000):
		my_image.set_pixel(
			rng.randi_range(0, IMAGE_SIZE.x - 1),
			rng.randi_range(0, IMAGE_SIZE.y - 1),
			Color(
				rng.randf(),
				rng.randf(),
				rng.randf()
			)
		)
	my_image.unlock()
	set_texture(my_texture)
```

The main gotcha was reading through the {{< doc godot "Image" >}} documentation and finally finding the {{< doc godot "Image.lock" >}} method. Without locking the image, you cannot modify it. Doh. 

So what do I have after a few hours? 

{{< figure src="/embeds/2020/ludum-dare-46-first-screenshot.png" >}}

Yeah. It's not much. But it renders and you can use your mouse to move it around. And you can play with it in a browser if you want!

(Click the link to open it, click and drag to move it around. That's really all it does...)

<iframe width="800" height="600" style="border: 1px solid black;" src="/embeds/games/ludum-dare/46/v0.1/launcher.html"></iframe>

The ability to compile that to [[wiki:WASM]]() and run it in a browser (even if it's a bit hefty at 20MB) out of the box is pretty awesome.

Tomorrow: 

- Make the tetris part work
- Make the falling sand part work
- ...
- Profit?
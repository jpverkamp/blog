---
title: "LD46: IT'S WORKING!"
date: 2020-04-18 23:00:00
programming/languages:
- GScript
- Godot
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Physics
- Games
series:
- Ludum Dare
- Ludum Dare 46
---
{{< figure src="/embeds/2020/its-working.gif" >}}

IT'S WORKING!

<video controls src="/embeds/2020/ludum-dare-46-its-working.mp4"></video>

The performance is **terrible** (sub 10 FPS on a pretty decent desktop and I want to try to run it in a browser...), but **it's working**.

<!--more-->

The core of it all comes down to the code that copies pixels from one `PixelEngine` (in each block) to another (the background of the entire game):

```python
# Stop the body from moving
body.set_mode(RigidBody2D.MODE_STATIC)

# Copy data from the block to the parent
var engine = body.get_node("PixelEngine")
var parent = get_parent().get_parent().get_node("PixelEngine")

for x in range(engine.WIDTH):
	for y in range(engine.HEIGHT):
		var target = body.global_position - Vector2(8, 8) + Vector2(x, y).rotated(engine.rotation)
		var tx = int(target.x)
		var ty = int(target.y)
		
		if parent.in_range(tx, ty):
			parent.data[tx][ty] = engine.data[x][y]
			parent.force_update = true
			
# Remove the block data
engine.queue_free()
engine.get_parent().get_node("Border").set_default_color(Color(1.0, 1.0, 1.0, 0.25))
```

I also added some borders and had them go mostly transparent when the block freezes, which works pretty well. It's not quite as squishy as before, since blocks completely lock (change to `MODE_STATIC`) rather than just giving up control. But it works. 

And hey, it's *almost* a game! I just need a bit of scoring and a few menus/screens and I could call it decent. But I can't very well stop there...

Todo:

- Scoring
- Main menu, game over + restart menu
- [Performance, performance, performance](https://www.youtube.com/watch?v=KMU0tzLwhbE)

Oh. When I was first working on the copy? Things got ...

{{< figure src="/embeds/2020/ludum-dare-46-things-got-weird.png" >}}

... weird. I later learned it was because of 'cloud' particles and an incorrect y bound on spawners. You can see the y=x line in that diagonal that should have clued me in, but I've been at this for a while. It was certainly an interesting first big attempt though.  
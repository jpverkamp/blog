---
title: "LD46: Score, Scaling, and BURNING! Oh my."
date: 2020-04-19 13:00:00
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
Got some sleep and BACK AT IT! 

<video controls src="/embeds/2020/ludum-dare-46-scaling.mp4"></video>

Big changes:

- We have scores now!
- And proper scaling (which also fixes the performance issue, at least on my machine, turns out 1/16 as many updates helps)
- Proper resetting

<!--more-->

# Scoring

The scoring isn't actually hard at all. I added a {{< doc godot Timer >}} and two {{< doc godot Label >}}s to `Main` and then had the timer fire this method off every quarter second or so:

```python
# Main.gd
func _on_Scores_timeout():
	var count = 0
	var highest = engine.HEIGHT
	
	for x in range(engine.WIDTH):
		for y in range(engine.HEIGHT):
			if engine.data[x][y] == engine.CELL.plant:
				count += 1
				highest = min(highest, y)
	
	score_count.text = "Plants: " + str(count)
	score_height.text = "Tallest: " + str(engine.HEIGHT - highest)
```

I'm going to use this such that if plants reaches 0, you lose and if the tallest gets tall enough, you win. I was going to make it so that filling the Tetris pieces also cost you the game, but I don't think I will any more.  

# Scaling

Scaling was actually not that much harder, although I hit a gotcha. I just added a new parameter to `PixelEngine`: `SCALE`. The image and texure are the same size, but I had to tweak a few other things:

```python
# PixelEngine.gd
func _ready():
	...

	# Create a texture that the image will render to and that we can use on this sprite
	my_texture = ImageTexture.new()
	my_texture.create_from_image(my_image)
	my_texture.flags &= ~ImageTexture.FLAG_FILTER
	my_texture.flags &= ~ImageTexture.FLAG_MIPMAPS

	...

	sprite.set_texture(my_texture)
	sprite.region_rect = Rect2(0, 0, WIDTH, HEIGHT)
	sprite.set_scale(SCALE * sprite.get_scale())
```

Turning off `FILTER` and `MIPMAPS` means that I get pixellated scaling (which I was having issues with previously) and setting scale (*but not the `region_rect`*) properly scales. Then I changed everything to 4x scale, which effectively gives me 16x as much capacity. And it looks nice and block still!

```python
# Tetromino.gd
...
var target = body.global_position - Vector2(8, 8) + Vector2(x, y).rotated(engine.rotation)
var tx = int(target.x) / parent.SCALE
var ty = int(target.y) / parent.SCALE

if parent.in_range(tx, ty) and parent.data[tx][ty] == parent.CELL.empty:
	parent.data[tx][ty] = engine.data[x][y]
	parent.force_update = true
...
```

I also had to modify the 'copy to the main `PixelEngine`' code to adjust for scale. While I did, I made it so that it only drops the contents if there's nothing there, since otherwise you keep overwriting things. 

# Resetting

This is more a design change than anything, but now if you fill the screen with Tetris blocks, you don't lose, instead the game will clear the blocks (but keep the particles). That way, the main goal is the plants, not the Tetris game. To do this, I added a new signal:

```python
# Tetromino.gd
signal on_reset

const RESET_THRESHOLD = 50

func _physics_process(delta):
	...

	# If we hit something, start a counter, if that goes long enough, lock the block
	if settled:
		stuck_time += delta
		var highest_body = INF
		
		if stuck_time > LOCK_TIME:
			...

			# If we're too high up, send a reset signal
			# Otherwise, lock this block and spawn a new one
			if highest_body < RESET_THRESHOLD:
				emit_signal("on_reset")
			else:
				set_physics_process(false)
				emit_signal("on_lock")
```

Then connect it:

```python
# Main.gd
func spawn():
	var child = Tetromino.instance()
	child.init_random()
	child.name = "Tetromino" + str(tetrominos.get_child_count() + 1)
	child.position = Vector2(80, 20)
	child.connect("on_lock", self, "spawn")
	child.connect("on_reset", self, "reset_blocks")
	tetrominos.add_child(child)
	
func reset_blocks():
	for tetromino in tetrominos.get_children():
		tetromino.queue_free()
		tetrominos.remove_child(tetromino)
	spawn()

func _ready():
	OS.window_size = Vector2(320, 640)

	reset_sand()
	reset_blocks()
```

And there we go. 

# Color variation

One tweak from [my 2009 version of Sandbox](2009-11-28-sandbox-and-so-it-begins.md) was color variation. That's easy enough to implement, so I went for it:

```python
# PixelEngine.gd

# Types that have slight color variations
const COLOR_VARIATION = 0.1
const VARIABLE_COLORS = [
	CELL.wall,
	CELL.sand,
	CELL.plant
]

func _process(_delta):
	# Render my data
	my_image.lock()
	for x in range(WIDTH):
		for y in range(HEIGHT):
			if updated[x][y] or force_update:
				var color = COLORS[data[x][y]]
				if data[x][y] in VARIABLE_COLORS:
					my_image.set_pixel(x, y, Color(
						color.r + COLOR_VARIATION * (randf() - 0.5),
						color.g + COLOR_VARIATION * (randf() - 0.5),
						color.b + COLOR_VARIATION * (randf() - 0.5)
					))
				else:
					my_image.set_pixel(x, y, color)
					
	my_image.unlock()
```

Check out the video, you can see it most obviously on the walls. 

# A demo

I don't include a demo with every post, since the compiled version is a bit large to host that many of them (in release mode still 13MB). But I've made enough changes that I think it's worth it this time. 

Instructions:

- Play with a keyboard
- Left and right move the block side to side
- Down and up speed up/slow down the block
- You can rotate with Z (left) and X (right)
- *debug* You can press ENTER to lock the current block
- *debug* You can press ESC to reset the blocks as if you've filled the screen

<iframe width="160" height="320" style="border: 1px solid black;" src="/embeds/games/ludum-dare/46/v0.2/launcher.html"></iframe>

# TODO

In rough order of priority:

- Main menu
- Game over menu
- Music
- Difficulty / options
	- Turn on/off spawn types
	- Make plants grow easier (allow 1-4 neighbors) or harder (exactly 1)
    - Two block mode (I accidently did this in testing, it was neat)
- Wall spawners
- New block types
    - Wax
    - Acid
    - Agent X
    - Fireworks
    - TNT
- Submit high scores


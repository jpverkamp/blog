---
title: 'LD46: Tetris is working! (sort of)'
slug: ludum-dare-46-tetris-sand
date: 2020-04-18 12:00:00
programming/languages:
- GScript
- Godot
programming/sources:
- Ludum Dare
programming/topics:
- Physics
- Games
series:
- Ludum Dare 46
---
Update! 

<video controls src="/embeds/2020/ludum-dare-46-tetris.mp4"></video>

I have basic blocks that fall by themselves and that I can move around with left/right on the keyboard. They will collide with each other and the walls/floor, and once they stick, a new block will spawn. 

<!--more-->

# Basic movement

The first thing to do is set up movement on the blocks. We'll give them a {{< doc godot KinematicBody2D >}} and a script to handle keyboard controls.

{{< figure src="/embeds/2020/ludum-dare-46-tetris-kinematic.png" >}}

The PixelEngine there is the falling sand block that I made in the [previous post]{{< ref "01-ludum-dare-46-tetris-sand.md" >}}. That just handles the UI and the falling sand, it's an animated sprite. 

Then movement via script:

```python
# Block.gd
func _physics_process(delta):
	# Keyboard controls
	if Input.is_action_pressed("ui_right"):
		velocity += IMPULSE

	if Input.is_action_pressed("ui_left"):
		velocity -= IMPULSE

	# Apply friction and gravity
	velocity *= DECAY
	velocity.y = FALLING
	
	# Move the block
	body.move_and_collide(velocity)
```

And that's it. It moves left and right and falls down. 

# Collisions

To collide, we need something to collide with:

{{< figure src="/embeds/2020/ludum-dare-46-tetris-walls.png" >}}

And that's actually it. No code. I didn't think I'd like that part of Godot... but it's really handy. 

Now the blocks fall down and can crash into walls. 

# Respawning

Now for the slightly tricky part. I want blocks to stop moving when they collide and then spawn a new block. Stopping them is actually pretty easy:

```python
func _physics_process(delta):
	...

	# Move the block
	var collision = body.move_and_collide(velocity)
	
	# If we hit something, start a counter, if that goes long enough, lock the block
	if collision:
		velocity = Vector2.ZERO
		stuck_time += delta
		if stuck_time > LOCK_TIME:
			set_physics_process(false)
	else:
		stuck_time = 0
```

Just tell Godot to stop the `_physics_process` calls to this object.

To respawn blocks, I'm going to use {{< doc godot signals >}}:

```python
# Block.gd
signal on_lock

func _physics_process(delta):
	...
	if collision:
		velocity = Vector2.ZERO
		stuck_time += delta
		if stuck_time > LOCK_TIME:
			set_physics_process(false)
			emit_signal("on_lock")
	else:
		stuck_time = 0

# Main.gd
extends Node2D

onready var Block = preload("res://scenes/Block.tscn")
onready var blocks = $Blocks

func _on_Block_on_lock():
	var new_block = Block.instance()
	new_block.name = "Block" + str(blocks.get_child_count() + 1)
	new_block.position = Vector2(80, 20)
	new_block.connect("on_lock", self, "_on_Block_on_lock")
	blocks.add_child(new_block)

	print('Spawned ' + new_block.name)
```

And... that's actually it. The `Main` scene/script is connected via UI for the first signal, but after that, whenever a `Block` fires the `on_lock` signal to `Main`, `Main` will create a new `Block` instance (with a unique name), set it to the top of the screen, and wire up the new signal.

It's really that easy.

Godot is nice.

Up next:

- Make the blocks into {{< wikipedia tetrominos >}}. 
- Work on the falling sand simulation
- Have the sand 'drop' into a shared simulation when the blocks lock (using the previous signal!)

This is fun!
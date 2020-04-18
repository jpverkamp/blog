---
title: 'LD46: Squishy squishy'
date: 2020-04-18 16:00:00
programming/languages:
- HTML
- JavaScript
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
It's so squish!

<video controls src="/embeds/2020/ludum-dare-46-squishy.mp4"></video>

That is not at all what I intended, but I kind of love it, so for the moment, it stays in. 

To get this far, I had a heck of a time trying to figure out Godot's physics engine, but I'm learning quickly!

<!--more-->

# Define the blocks

First, we have to figure out what the blocks look like. From Wikipedia:

{{< figure src="/embeds/2020/ludum-dare-46-shapes-wiki.png" >}}

So I have 7 shapes to define, each of which has four 'blocks' inside of it. So first I layed out a graphic:

{{< figure src="/embeds/2020/ludum-dare-46-tetris-shapes.jpg" >}}

Now I need to define how they relate in code. First, I was going to define what the neighbors of each was:

{{< figure src="/embeds/2020/ludum-dare-46-neighbors-1.jpg" >}}

In this case, that means that in an `I` block, `1` has top, right, bottom, left neighbors of `_` (none), `_`, `2`, `_` and so on. Seems verbose. So then I realized that I can calculate the neighbors myself. I just need to determine where they all are:

{{< figure src="/embeds/2020/ludum-dare-46-neighbors-2.jpg" >}}

That's much cleaner. It also includes the 'central point' of the shape that I will rotate around (which I don't end up using).

Turning that into code:

```python
# Tetromino.gd

# Define the shapes, values are the four coordinates and then a center point to rotate around
const SHAPES = {
	'I': [Vector2(0, 0), Vector2(0, 1), Vector2(0, 2), Vector2(0, 3), Vector2(0.5, 2.0)],
	'O': [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1), Vector2(1.0, 1.0)],
	'T': [Vector2(0, 0), Vector2(1, 0), Vector2(2, 0), Vector2(1, 1), Vector2(1.5, 0.5)],
	'J': [Vector2(1, 0), Vector2(1, 1), Vector2(1, 2), Vector2(0, 2), Vector2(1.5, 2.5)],
	'L': [Vector2(0, 0), Vector2(0, 1), Vector2(0, 2), Vector2(1, 2), Vector2(0.5, 2.5)],
	'S': [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(2, 0), Vector2(1.5, 0.5)],
	'Z': [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(2, 0), Vector2(1.5, 0.5)]
}
```

From there, the actual hard part. I have the 4 Blocks already created (in the [previous post]{{< ref "02-tetris-is-working.md" >}}), but I have to move them around and stick them together:

```python
# Tetromonio.gd

onready var bodies = [
	$"Block0/Body",
	$"Block1/Body",
	$"Block2/Body",
	$"Block3/Body"
]

# Helper functions to get the correct child nodes by index
func block(i):
	return get_node("Block" + str(i))
	
# Initialize a random shape
func init_random():
	var names = SHAPES.keys()
	var name = names[randi() % names.size()]
	init(name)

# Initialize the shape with one of the names
func init(shape):
	assert(shape in SHAPES)
	
	# Set positions
	for i in range(4):
		block(i).position = 16 * SHAPES[shape][i]
		
	# Get neighbors and create joints
	for i in range(4):
		for j in range(4):
			var xi = SHAPES[shape][i].x
			var yi = SHAPES[shape][i].y
			var xj = SHAPES[shape][j].x
			var yj = SHAPES[shape][j].y
			
			var bi = block(i)
			var bj = block(j)
			
			# Each only has to do one way, since we'll catch the other when bi  and bj swap
			var joined = false
			if xi + 1 == xj and yi == yj:
				bi.get_node("Body/PixelEngine").neighbors['right'] = bj
				joined = true
			elif xi - 1 == xj and yi == yj:
				bi.get_node("Body/PixelEngine").neighbors['left'] = bj
				joined = true
			elif xi == xj and yi + 1 == yj:
				bi.get_node("Body/PixelEngine").neighbors['bottom'] = bj
				joined = true
			elif xi == xj and yi - 1 == yj:
				bi.get_node("Body/PixelEngine").neighbors['top'] = bj
				joined = true
				
			# Only add joints one direction
			if joined and i < j:
				var midpoint = (bi.position + bj.position) / 2
				var pins = []
				
				if xi == xj:
					pins.append(midpoint + Vector2(0, 8))
					pins.append(midpoint + Vector2(0, -8))
				else:
					pins.append(midpoint + Vector2(8, 0))
					pins.append(midpoint + Vector2(-8, 0))
					
				for pin in pins:
					var joint = PinJoint2D.new()
					joint.position = pin

					add_child(joint)
					joint.node_a = joint.get_path_to(bi.get_node("Body"))
					joint.node_b = joint.get_path_to(bj.get_node("Body"))
```

I know right? 

It's some pretty wacky code. Except for the joints, it came together pretty quickly. The joints proved to be quite the headache though. First, I was using a {{< doc godot KinematicBody2D >}} for the block, which ... doesn't really work with joints at all? So I switched to {{< doc godot RigidBody2D >}}. But that means I have to change the physics system (more on that in a bit). Then I made the joints, but with only one pin, so they rotated all over the place. It turns out what I really want is to join each pair of blocks on the two corners touching. 

So, rewriting the input/physics engine. In a nutshell:

```python
# Tetromino.gd

func _physics_process(delta):
	# Keyboard controls
	for body in bodies:
		if Input.is_action_pressed("ui_right"):
			body.apply_central_impulse(IMPULSE)
		if Input.is_action_pressed("ui_left"):
			body.apply_central_impulse(-IMPULSE)
		if Input.is_action_pressed("ui_up"):
			body.apply_central_impulse(-0.1 * GRAVITY)
		if Input.is_action_pressed("ui_down"):
			body.apply_central_impulse(GRAVITY)
		if Input.is_action_pressed("ui_rotate_left"):
			body.apply_torque_impulse(-TORQUE)
		if Input.is_action_pressed("ui_rotate_right"):
			body.apply_torque_impulse(TORQUE)
		
	var settled = true
	for body in bodies:
		if not body.sleeping:
			settled = false
	
	# If we hit something, start a counter, if that goes long enough, lock the block
	if settled:
		velocity = Vector2.ZERO
		stuck_time += delta
		if stuck_time > LOCK_TIME:
			set_physics_process(false)
			emit_signal("on_lock")
			
	else:
		stuck_time = 0
```

I actually really like how {{< doc godot RigidBody2D >}}s work. I should play with those more. I do have to apply the forces to all of the 4 blocks, otherwise they start rotating like mad when you don't want them to (I mean, I do want them to, but not by themselves!). 

The `body.sleeping` actually works pretty well. Sometimes it gets stuck, but I can push that down the road a bit. I think I'll add a keybinding to Let It Go[^frozen] and move on to the next block without waiting. 

It... works? 

What we do end up getting though is amusingly squishy, which I love. I'm totally going to keep it for now.

<video controls src="/embeds/2020/ludum-dare-46-squishy-2.mp4"></video>

{{< figure src="/embeds/2020/my-squishy.gif" >}}

Anyways, off to a block, and then it's time to actually add some falling sand!

EDIT: I was working on adding a few keybindings (ESC restarts and ENTER forces you to the next tile) and this happened:

<video controls src="/embeds/2020/ludum-dare-46-oops.mp4"></video>

`is_action_**just**_pressed` y'all. That is all. 

[^frozen]: I finally got around to watching Frozen 2. The movie is insane, but I actually realy enjoy the music. Man it's stuck in my head. 
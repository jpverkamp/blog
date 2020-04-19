---
title: "LD46: I made a GAME!"
date: 2020-04-19 15:15:00
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
- Ludum Dare 46
---
I made a game y'all!

<video controls src="/embeds/2020/ludum-dare-46-i-made-a-game.mp4"></video>

Big changes:

- It's got a menu!
- And a demo mode!
- PLANTS GROW BY THEMSELVES!
- And win/lose screens!

<!--more-->

# Menu

I set up most of the menu in the Godot UI editor: 

{{< figure src="/embeds/2020/ludum-dare-46-menu-layout.png" >}}

One trick that took a while was having some issues with Z-indexing (I'm using that in the `PixelEngine`). All I had to do to fix it was put all the UI elements in a `CanvasLayer` (`Foreground`) and voila. 

Then a bit of code to hook things up:

```python
# Main.gd
func _on_play():
	get_tree().change_scene("res://scenes/Main.tscn")
	
func _on_options():
	$Foreground/Buttons.visible = false
	$Foreground/Options.visible = true
	$Foreground/StatusBox.visible = false
	
func _on_options_done():
	$Foreground/Buttons.visible = true
	$Foreground/Options.visible = false
	$Foreground/StatusBox.visible = true

func _on_quit():
	get_tree().quit()
```

Pretty cool. 

# Demo

To get demo mode working, I just added a `demo` variable to the `Main.gd` script and tweaked a few things (I'll talk about `return_to_menu` in a moment): 

```python
# Main.gd

func _on_Scores_timeout():
	...

	if count == 0:
		if demo:
			reset_sand()
		else:
			return_to_menu("All the plants died!\nYou lost.\n:(")

	elif highest <= TARGET:
		if demo:
			reset_sand()
		else:
			return_to_menu("You grew a plant to the top.\nYOU WIN!")

# Tetromino

# Keyboard controls
if get_parent().get_parent().demo:
	if randf() < 0.1:
		var impulse = IMPULSE * (randf() - 0.5)
		var torque = TORQUE * (randf() - 0.5)
		
		for body in bodies:
			body.apply_central_impulse(impulse)
			body.apply_torque_impulse(torque)
else:
	for body in bodies:
		if Input.is_action_pressed("ui_right"):
			body.apply_central_impulse(IMPULSE)
		...
```

# Plant growth

It was taking forever to grow plants with just water to help them grow, so I added the ability for them to grow by themselves:

```python
# PixelEngine.gd

# Try to react with neighboring particles
if current == CELL.plant:
	var hot_neighbors = count_neighbors_of(x, y, CELL.fire) + count_neighbors_of(x, y, CELL.lava)
	var empty_neighbors = count_neighbors_of(x, y, CELL.empty)
	var plant_neighbors = count_neighbors_of(x, y, CELL.plant)
	
	# Fire/lava ignite plants
	if randf() < hot_neighbors * BURN_CHANCE_PER_FIRE:
		data[x][y] = CELL.fire
		updated[x][y] = true
		
	# Plants try to grow
	elif empty_neighbors > 0 and plant_neighbors <= PLANT_GROWTH_LIMITER:
		for xi in range(x - 1, x + 2):
			for yi in range(y - 1, y + 2):
				if not in_range(xi, yi) or (xi == x and yi == y):
					continue
					
				if data[xi][yi] != CELL.empty:
					continue
					
				if randf() < PLANT_GROWTH_PER_EMPTY:
					data[xi][yi] = CELL.plant
					updated[xi][yi] = true
```

# Win/Lose

Last but not least, I updated the code to include win/lose screens (as seen in the `return_to_menu` function above). I did that so that I can go right back to the menu, but also display a message:

```python
# Main.gd
func return_to_menu(message):
	var menu = load("res://scenes/Menu.tscn").instance()
	menu.set_text(message)
	get_tree().get_root().add_child(menu)
	queue_free()
```

I can't directly use `get_tree().change_scene` here, since that doesn't let me pass along any state, but this works well enough. I may use that for options/difficulty settings before too long. 

# TODO

Next up: MUSIC! 

You need music to really sell a game. 

And hey, I already have a menu option for it. :D

If I have the time, after that I will work on:

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

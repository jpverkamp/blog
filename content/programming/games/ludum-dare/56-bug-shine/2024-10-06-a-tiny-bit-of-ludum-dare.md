---
title: 'Ludum Dare(ish) 56: BugShine'
date: 2024-10-07
programming/languages:
- Rust
programming/sources:
- Ludum Dare
programming/topics:
- Cellular Automata
- Games
series:
- Ludum Dare
---
[[Ludum Dare]]()? That's been a while!

I didn't actually enter the game jam. Honestly, I wasn't sure I was going to write anything. But I had a bit of an idea and spent a few hours only on Sunday hammering something out:

<video width=100% controls src="/embeds/games/ludum-dare/56/bugshine.mp4"></video>

Yeah, I did another cellular automata thing :smile:

It's not at all complete, but the basic idea is:

* Generate a random level
* See it with multiple players (colonies of bugs)
* Each bug will send out waves of 'shine', expanding their territory
* Take over the map to win

It's sort of got that?

I'm using Rust as I've been doing a lot recently. 

The main libraries are:

* [pixels](https://docs.rs/pixels/latest/pixels/) for the rendering; it gives me direct access to a pixel buffer, which is my favorite
* [winit](https://docs.rs/winit/latest/winit/) for windowing; this did require the feature `rwh_05` to be properly compatible with `pixels`, which took a minute to track down

Other than, that, it's straight custom code which you can see in it's entirety on [my github](https://github.com/jpverkamp/bug-shine). 

* [main.rs](https://github.com/jpverkamp/bug-shine/blob/main/src/main.rs) - creates the window and handles input
* [world.rs](https://github.com/jpverkamp/bug-shine/blob/main/src/world.rs) - runs the simulation mostly in an `update` function; with generation in `new`

I think that perhaps the only really interesting bit about the code is how the 'shine waves' work. Basically, I have a grid of the state of each cell, but I also have a `Vec` that tracks 'active' pixels. Those are the only ones that can update--which both helps performance and makes the simulation appear the way it does. 

Overall, a nice quick project. More than anything, it actually convinced me to try setting up something that can render pixel buffers on Rust. And with a (very minimal) GUI, too! Both things I've been meaning to learn. 

I probably won't do anything more with this code, but it's got the seeds of something more interesting. Keep an eye out. :smile:

Onward!

{{<figure src="/embeds/games/ludum-dare/56/bugshine.png">}}

<!--more-->
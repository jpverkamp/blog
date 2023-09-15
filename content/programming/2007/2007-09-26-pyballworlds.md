---
title: PyBallWorlds
date: 2007-09-26 04:55:18
programming/languages:
- Python
---
Back in the first quarter of my Freshman year at <a title="Rose-Hulman Institute of Technology" href="http://www.rose-hulman.edu/">Rose-Hulman</a>, we wrote a small Java program called BallWorlds. The idea was to teach us about objects and inheritance by asking us to make a 2d simulation of balls of various types bouncing around in an enclosed environment. There could be balls that bounced off each other, sticky balls that clumped together, balls that grew when they hit something, and really any combination there of. The sky was the limit. The idea so intrigued me that when I was playing with <a title="OpenGL" href="https://www.opengl.org/">OpenGL</a> (and specifically <a title="PyOpenGL" href="http://pyopengl.sourceforge.net/">PyOpenGL</a>), I decided to rewrite the same thing in Python.

<!--more-->

A little under 500 lines of code later, I present to you... PyBallWorlds:

{{< figure src="/embeds/2007/01-empty-screen.png" >}}

Yeah, I know. That's pretty boring. We need some balls! If you hit 1, you get randomly placed white balls that do *absolutely nothing*! Isn't computer science thrilling?

{{< figure src="/embeds/2007/02-three-white-balls.png" >}}

Okay, still pretty boring. How about you hit 2 instead. This time you'll get blue balls that bounce around the screen like mad! Of course, they don't interact with either each other or the white balls, but at least they bounce off of the walls. (Granted, a screenshot isn't exactly the most thrilling thing for something like this. That's why you should head down to the bottom of the post and download PyBallWorlds to try it for yourself!)

{{< figure src="/embeds/2007/03b-moving-around.png" >}}

Next (can you guess it?) you can hit 3. This will give you a pink ball that not only bounces around but now also interacts with the other balls. When it hits something (be it a white ball, blue ball, or the wall) it will bounce of with some (very) rough approximation of something not entirely unlike physics.

{{< figure src="/embeds/2007/04-pink-balls.png" >}}

Finally, you have number 4. That's my personal favorite. This one is the red ball--the sticky ball. Basically, whenever it hits something both the red ball and the one that it hit will stop right where they are and stick together. I was working on a way to have both balls stick and move together, but I figured that I can do that later and might as well upload this first.

{{< figure src="/embeds/2007/05-sticky-red-balls.png" >}}

That's all that I have implemented thus far, but I have a few more shots left to show you. First, you have to try just spamming a few dozen balls. Really you do. I'll wait.

Okay, not really. Here's when I did it:

{{< figure src="/embeds/2007/06-lots-of-balls.png" >}}

You can already see the red balls forming clumps when anything that runs into them stops in place. Actually it looks oddly organic, which intrigues me somewhat. I'm a fan of [[wiki:emergent behavior]]() like that.

Anyways, there's one final set of keyboard commands that you should know about. If you hit any of the arrow keys, you can rotate the cube in place. After all, it wouldn't be any fun to build these crazy semi-organic structures without being able to study them from every angle now would it?

{{< figure src="/embeds/2007/07-free-rotation.png" >}}

Anyways, that's all I have. Download it below and check it out. You'll need <a title="Python" href="http://www.python.org/">Python</a> and <a title="PyOpenGL" href="http://pyopengl.sourceforge.net/">PyOpenGL</a>.

Useful commands:

* 1 – Create a static (white) ball
* 2 – Create a moving (blue) ball
* 3 – Create a bouncing (pink) ball
* 4 – Create a sticky (red) ball
* C – Clear the screen
* Arrow keys – rotate the view
* Esc – Quit the program

**Download:** [PyBallWorlds.zip](/embeds/2007/PyBallWorlds.zip)

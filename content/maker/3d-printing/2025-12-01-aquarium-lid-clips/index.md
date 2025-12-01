---
title: Aquarium Lid Clips
date: 2025-12-01
---
Okay, here's another (wow, has it really been four years...)

We've been ~slowly~ acquiring fish tanks. In order to make custom lids which fit each tank and allow for growing plants in them, we need little clips which can hold the lid of the tank. Most of them, we get the right size for, but there's one tank which is a bit different.

Rather than the 5mm side walls all the rest have, this one has 4mm on the sides and back and 3mm on the front. 

But hey, I have a 3d printer. This is a great chance to put it to good use!

# The initial sketch

First, the initial sketch and notes on my desk:

![Initial sketch](sketch.png)

Having a whiteboard for a desk is really quite handy at times. 

Then, we move that over to [FreeCAD](https://www.freecad.org/). I've used it before, but never for anything at *all* complicated (which I suppose this isn't either). Remembering how in the world to use CAD programs takes a minute:

![Side view sketch with dimensions](dimensions.png)

Those orange dimensions there I'm particularly happy with, they're parameterized:

![The spreadsheet with parameters](params.png)

So I can change any number in the sheet (and assuming it actually works), the part will just change everything to match. Pretty cool, especially since I did end up needing a couple of different sizes for the different wall thicknesses. 

You might notice the `4.02 mm` for the middle number there. That's because the *actual* forumla is `1.005 * <<params>>.glass_thickness`. This gives the pieces just a little bit of room (half a percent) of tolerance to slide on. That percent is completely a guess, but seems to be working so far, so we'll take it. 

# Single clips

With the sketch done, all that was left was to extrude the parts in FreeCAD:

![The part extruded in FreeCAD](extruded.png)

Originally, I was going to put a fillet on each of the inside corners, mostly to look nice. But it seems you cannot parameterize those. And I couldn't get a curve based on the shape of the top surface to work. So for now, that will work. 

## Making corners

But that's not all. The harder(est?) part was that we wanted a clip for each corner. And I have *no* idea how to do that in FreeCAD. It should be possible to create a 3mm edge and a 4mm edge and place them both in a new par in FreeCAD, then add a new piece between them, but I just could *not* get that to work (yet). 

So instead, I jumped online to TinkerCAD, imported the two pieces, and just drew a piece between them. 

![The view in tinkercad making a corner](tinkercad.png)

It feels *so* hacky, but it works!

Even better? The best way I've found to print it? 

![Corner clip with supports](supports.png)

This piece is not very friendly to printing without supports. But they've proven easy enough to remove, so we'll go with it. 

And the final results?

![Final result of a corner clip](result.png)

It slides on perfectly and is exactly the right depth to hold the lid. 

3D printing is just so cool sometimes. 

(If you'd like to download the file, [here you go!](side-clip.FCStd))
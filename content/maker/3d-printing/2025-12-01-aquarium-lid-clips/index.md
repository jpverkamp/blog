---
title: Aquarium Lid Clips
date: 2025-12-01
---
Okay, here's another (wow, has it really been four years...)

We've been ~slowly~ acquiring fish tanks. In order to make custom lids which fit each tank and allow for growing plants in them, we need little clips which can hold the lid of the tank. Most of them, we get the right size for, but there's one tank which is a bit different.

Rather than the 5mm side walls all the rest have, this one has 4mm on the sides and back and 3mm on the front. 

But hey, I have a 3d printer. This is a great chance to put it to good use!

{{<toc>}}

## The initial sketch

First, the initial sketch and notes on my desk:

![Initial sketch](sketch.png)

Having a whiteboard for a desk is really quite handy at times. 

Then, we move that over to [FreeCAD](https://www.freecad.org/). I've used it before, but never for anything at *all* complicated (which I suppose this isn't either). Remembering how in the world to use CAD programs takes a minute:

![Side view sketch with dimensions](dimensions.png)

Those orange dimensions there I'm particularly happy with, they're parameterized:

![The spreadsheet with parameters](params.png)

So I can change any number in the sheet (and assuming it actually works), the part will just change everything to match. Pretty cool, especially since I did end up needing a couple of different sizes for the different wall thicknesses. 

You might notice the `4.02 mm` for the middle number there. That's because the *actual* forumla is `1.005 * <<params>>.glass_thickness`. This gives the pieces just a little bit of room (half a percent) of tolerance to slide on. That percent is completely a guess, but seems to be working so far, so we'll take it. 

## Single clips

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

## OpenSCAD

Okay, I couldn't leave well enough alone. Here are some versions that use OpenSCAD instead!

```scad
// How thick the glass you're fitting over is
glass_thickness = 4;
glass_tolerance = 0.05;

// How thick the lid is you're putting on top
lid_thickness = 5;

// How thick the plastic should be
piece_thickness = 2;

// How far the shelf extends inwards and then side to side
shelf_depth = 10;
shelf_width = 30;

module shelf(glass_thickness) {
    // Lip over the edge
    difference() {
        translate([0, 0, 0])
            cube([
                glass_thickness + 2 * piece_thickness,
                shelf_width,
                lid_thickness + 2 * piece_thickness
            ]);

        // Cut out for glass
        translate([piece_thickness, 0, 0])
            cube([
                glass_thickness,
                shelf_width,
                lid_thickness + piece_thickness
            ]);
    }
    
    // Shelf
    translate([
        glass_thickness + 2 * piece_thickness,
        0,
        piece_thickness
    ])
        cube([
            shelf_depth,
            shelf_width,
            piece_thickness
        ]);
}

shelf(glass_thickness * (1 + glass_tolerance));
```

![OpenSCAD version of the clip](openscad-clip.png)

And for the corner:

```scad
// How thick the glass you're fitting over is
// These can be different for two different sides
glass_thickness_a = 4;
glass_thickness_b = 4;
glass_tolerance = 0.05;

// How thick the lid is you're putting on top
lid_thickness = 5;

// How thick the plastic should be
piece_thickness = 2;

// How large the cutout in the corner should be 
corner_size = 20;

// How far the shelf extends inwards and then side to side
shelf_depth = 10;
shelf_width = 30;

module shelf(glass_thickness) {
    // Lip over the edge
    difference() {
        translate([0, 0, 0])
            cube([
                glass_thickness + 2 * piece_thickness,
                shelf_width,
                lid_thickness + 2 * piece_thickness
            ]);

        // Cut out for glass
        translate([piece_thickness, 0, 0])
            cube([
                glass_thickness,
                shelf_width,
                lid_thickness + piece_thickness
            ]);
    }
    
    // Shelf
    translate([
        glass_thickness + 2 * piece_thickness,
        0,
        piece_thickness
    ])
        cube([
            shelf_depth,
            shelf_width,
            piece_thickness
        ]);
}

translate([0, corner_size, 0])
    shelf(glass_thickness_a * (1 + glass_tolerance));

translate([corner_size + shelf_width, 0, 0])
    rotate([0, 0, 90]) shelf(glass_thickness_a * (1 + glass_tolerance));

difference() {
    translate([corner_size, corner_size, piece_thickness])
        cylinder(h=piece_thickness, r=shelf_width);
        
    translate([0, 0, piece_thickness])
        cube([corner_size, corner_size, piece_thickness]);
    
    // Going along each lip
    translate([-shelf_width, -shelf_width, piece_thickness])
        cube([shelf_width + glass_thickness_a + piece_thickness * 2, 3*shelf_width, piece_thickness]);

    translate([-shelf_width, -shelf_width, piece_thickness])
        cube([3*shelf_width, shelf_width + glass_thickness_b + piece_thickness * 2, piece_thickness]);
};
```

![OpenSCAN version of the corner clip](openscad-corner.png)

It's even curved! 

At this point, I already have the other version printed, so I'm not going to go back and make these as well... unless we get more fish tanks. :innocent:
---
title: Undergravel Filter
date: 2025-12-02
---
Four years / a day? What's really the difference. 

I was asked to design an [[wiki:undergravel filter]](). Let's do it.

{{<toc>}}

## Prototype

Here's the original prototype:

![Picture of the original design, made of paper](prototype.png)

Not much to go on. 

## Version 1

And here's where we ended up:

```scad
// Units
inch = 25.4;

// Requested dimensions (converted to mm)
box_x = 9 * inch;
box_y = 6 * inch;
box_z = 0.75 * inch;

// Piece thickness of walls and bottom (top?)
wall = 2;
bottom = 2;

// Size and space between centers for grid holes
hole_d = 2.5;
spacing = 10;

// Size of the larger tube hole in the corner
tube_hole_d = 18.4;

// --- Don't change anything below this line ---

// Derived cavity size
inner_x = box_x - 2 * wall;
inner_y = box_y - 2 * wall;
inner_z = box_z - bottom;

// Centered hole grid counts
nx = floor((inner_x - hole_d) / spacing) + 1;
ny = floor((inner_y - hole_d) / spacing) + 1;

// Offset to center hole grid
start_x = wall + (inner_x - (nx - 1) * spacing) / 2;
start_y = wall + (inner_y - (ny - 1) * spacing) / 2;

// Tube hole in the corner
tube_hole_x = start_x + spacing;
tube_hole_y = start_y + spacing;


difference() {
    // Outer box
    cube([box_x, box_y, box_z]);

    // Hollow interior (cut from top)
    translate([wall, wall, bottom])
        cube([inner_x, inner_y, inner_z + 0.01]);

    // Hole for the tube
    translate([tube_hole_x, tube_hole_y, -1])
        cylinder(h = inner_z + 2, d = tube_hole_d, $fn = 64);

    // Hole array through bottom
    for (i = [0:nx-1]) {
        for (j = [0:ny-1]) {
            x = start_x + i * spacing;
            y = start_y + j * spacing;

            // Skip grid hole if too near tube hole
            dist = sqrt( (x - tube_hole_x)*(x - tube_hole_x) +
                         (y - tube_hole_y)*(y - tube_hole_y) );

            if (dist - 1 > tube_hole_d/2) {
                translate([x, y, -1])
                    cylinder(h = bottom + 2, d = hole_d, $fn = 32);
            }
        }
    }
}
```

![Rendering of final design](rendering.png)

## Tube tolerance

One thing that did take a while to get close enough was the tolerance of the larger hole. It had to fit fairly accurately around a tube. Luckily, if you set a few minor changes:

```scad
box_x = 1.5 * inch;
box_y = 1.5 * inch;
box_z = 0.2 * inch;

tube_hole_d = 18.4;
```

![Picture showing prototypes for testing tolerance](testing-tolerance.png)

## Version 2

In the end, I actually ended up going a different route with that:

```scad
// Units
inch = 25.4;

// Requested dimensions (converted to mm)
box_x = 9 * inch;
box_y = 6 * inch;
box_z = 0.75 * inch;

// Piece thickness of walls and bottom (top?)
wall = 2;
bottom = 2;

// Size and space between centers for grid holes
hole_d = 2.5;
spacing = 10;

// Size of the larger tube hole in the corner
tube_hole_d = 18.4;
tube_coller_depth = 0.25 * inch;

// --- Don't change anything below this line ---

// Derived cavity size
inner_x = box_x - 2 * wall;
inner_y = box_y - 2 * wall;
inner_z = box_z - bottom;

// Centered hole grid counts
nx = floor((inner_x - hole_d) / spacing) + 1;
ny = floor((inner_y - hole_d) / spacing) + 1;

// Offset to center hole grid
start_x = wall + (inner_x - (nx - 1) * spacing) / 2;
start_y = wall + (inner_y - (ny - 1) * spacing) / 2;

// Tube hole in the corner
tube_hole_x = start_x + spacing;
tube_hole_y = start_y + spacing;

difference() {
    // Hollow cube
    union() {
        difference() {
            cube([box_x, box_y, box_z]);
            
            translate([wall, wall, bottom])
                cube([inner_x, inner_y, inner_z + 0.01]);
        }
        
        // Collar for the tube
        translate([tube_hole_x, tube_hole_y, 0])
            cylinder(h = tube_coller_depth + bottom, d = tube_hole_d + wall, $fn = 64);
    }

    // Hole for the tube
    translate([tube_hole_x, tube_hole_y, -1])
        cylinder(h = inner_z + 2, d = tube_hole_d, $fn = 64);

    // Hole array through bottom
    for (i = [0:nx-1]) {
        for (j = [0:ny-1]) {
            x = start_x + i * spacing;
            y = start_y + j * spacing;

            // Skip gri![alt text](image.png)d hole if too near tube hole
            dist = sqrt( (x - tube_hole_x)*(x - tube_hole_x) +
                         (y - tube_hole_y)*(y - tube_hole_y) );

            if (dist - 1 > tube_hole_d/2) {
                translate([x, y, -1])
                    cylinder(h = bottom + 2, d = hole_d, $fn = 32);
            }
        }
    }
}
```

![Addition of a collar to hold the tube in place](tube-collar.png)

And that was it, time for a full 9x6" print! Which is pretty close to the limits of what I can print (without a crazy angle). 

Unfortunately...

![Picture of version 1 of the final product with adhesion problems](adhesion.png)

I had my first bed adhesion problems in quite a while and even worse it was in the corner that really needed to be accurate or it wouldn't fit the air tube. 

So I cleaned off the plate (warm water and soap) and dropped the initial layer print speeds by about 1/3. Version 2? A perfect print!

![Picture of the version 2 of the final product, this time perfect](final-version.png)

About 3 hours and 100g of filament. None too shabby at all. 

(Now we'll just have to finish setting up the tank and see how it works!)

---
title: "Genuary: Triple Nested Loops"
date: 2021-01-08
programming/topics:
- Generative Art
- Procedural Content
- p5js
programming/languages:
- JavaScript
---
The fine people of [/r/generative](https://old.reddit.com/r/generative/) / [Genuary2021](https://genuary2021.github.io/) have a series of challenges for generative works for the month of January. I don't think I'm going to do all of them, but pick and choose. For example, the very first prompt is:

> `// TRIPLE NESTED LOOP`

My goal was to draw a grid of circles across the X/Y the image and nest them for the third dimension. To make it a little more interesting, I added a few different color modes. `seededRandom` is my personal favorite, that was interesting to get working. 

<!--more-->

{{< p5js width="600" height="420" >}}
let gui;
let params = {
  size: 50,
  sizeMin: 10,
  sizeMax: 400,
  bandWidth: 10,
  bandWidthMin: 1,
  colorMode: ['rgb', 'grayscale', 'random', 'seededRandom'],
};
let lastParams = undefined;

function naturalize(x, y) {
  let z = 0;
  while (true) {
    z += 1;
    if (x <= 0 && y <= 0) {
      return z;
    } else if (y == 0) {
      y = x - 1;
      x = 0;
    } else {
      x += 1;
      y -= 1
    }
  }
}

function setup() {
  createCanvas(400, 400);
  gui = createGuiPanel();
  gui.addObject(params);
  gui.setPosition(420, 0);

  background(0);
  noStroke();
}

function draw() {
  // If params haven't changed, don't redraw
  if (JSON.stringify(params) === JSON.stringify(lastParams)) {
    return;
  } else {
    lastParams = {
      ...params
    };
    background(0);
  }

  for (var i = 0; i < width; i += params.size) {
    for (var j = 0; j < height; j += params.size) {
      for (var k = params.size; k > 0; k -= params.bandWidth) {
        // Default is white circles
        let c = 255 * k / params.size
        
        // Just generate purely random colors
        if (params.colorMode === 'random') {
          c = [random(255), random(255), random(255)];
        } 
        
        // Generate random colors where the values are seeded by location
        // Only reseed on the outer band, so that circles are consistent
        if (params.colorMode === 'seededRandom') {
          if (k == params.size) {
            randomSeed(naturalize(i / params.size, j / params.size));
          }
          
          c = [random(255), random(255), random(255)];
        }
        
        // Generate color based on x/y/band 
        if (params.colorMode === 'rgb') {
          c = [
            255 * i / width,
            255 * j / height,
            255 * k / params.size,
          ];
        } 

        fill(c);
        circle(i + params.size / 2, j + params.size / 2, k);
      }
    }
  }
}
{{< /p5js >}}


[^pictogenesis]: I'll get back to this, I promised! 
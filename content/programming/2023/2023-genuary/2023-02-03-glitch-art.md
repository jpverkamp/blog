---
title: "Genuary 2023.03: Glitch art"
date: 2023-02-03
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- Colors
- HSL Color Space
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-03.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 3) Glitch Art

<!--more-->

Wikipedia: {{<wikipedia "Glitch Art">}}

This one took longer than I'd like to admit. The basic idea is that I want to take a region of the image, split into into red/green/blue channels and then offset the red left and the blue right. 

That's harder than I expected. I went through a bunch of direct `loadPixels` manipulation and a bunch of `tint` exploration, before realizing that it's easier than I was making it. Literally use the `blendMode(DIFFERENCE)` to remove the red, then `blendMode(ADD)` to put the red back. 

Good times. 

Note: this relies on https://picsum.photos/ so may take a moment to load. 

{{<p5js width="400" height="420">}}
let original;

function index(x, y, w, h, c) {
  return constrain(
    parseInt((y * w + x) * 4 + c),
    0,
    w * h * 4
  );
}

function preload() {
  console.log('Loading...');
  original = loadImage("https://picsum.photos/400");
  console.log("done");
}

function setup() {
  createCanvas(400, 400);
  frameRate(2);
  image(original, 0, 0);
}

function draw() {
  original.loadPixels();
  
  let maxOffset = 40;
  
  let x, y, w, h, offset;
  
  while (true) {
    let x1 = random(maxOffset, width - maxOffset);
    let x2 = random(maxOffset, width - maxOffset);
    let y1 = random(0, height);
    let y2 = random(0, height);

    x = min(x1, x2);
    w = max(x1, x2) - x;

    y = min(y1, y2);
    h = max(y1, y2) - y;

    offset = random(10, maxOffset);
  
    if (offset < w / 4) break;
  }
  
  let slice = original.get(x, y, w, h);
  
  // Remove red
  blendMode(DIFFERENCE);
  noStroke(); 
  fill(255, 0, 0, 255);
  rect(x - offset, y, w, h);
  
  // Add offset red
  blendMode(ADD);
  tint(255, 0, 0, 255);
  image(slice, x - offset, y);
  
  // Remove blue
  blendMode(DIFFERENCE);
  noStroke(); 
  fill(0, 0, 255, 255);
  rect(x + offset, y, w, h);
  
  // Add offset blue
  blendMode(ADD);
  tint(0, 0, 255, 255);
  image(slice, x + offset, y);
}
{{</p5js>}}

---
title: "Genuary 2023.30: Minimalism"
date: 2023-03-02
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-30.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 30) Minimalism

{{<p5js width="600" height="420">}}
let gui;
let params = {
  lineWidth: 10,
  minWidth: 50,
  maxWidth: 100, maxWidthMax: 400,
  minHeight: 50,
  maxHeight: 100, maxHeightMax: 400,
  colorChance: 0.1, colorChanceMin: 0, colorChanceMax: 1, colorChanceStep: 0.01,
}

let box;
let colors = [
  "red",
  "blue",
  "yellow",
]

function setup() {
  createCanvas(400, 400);
  
  box = {
    x: -params.lineWidth,
    y: -params.lineWidth,
    width: random(params.minWidth, params.maxWidth),
    height: random(params.minHeight, params.maxHeight),
  }

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  strokeWeight(params.lineWidth);
  stroke("black");
  
  if (random() < params.colorChance) {
    fill(random(colors));
  } else {
    fill("white");
  }
  
  rect(box.x, box.y, box.width, box.height);
  
  box.y += box.height;
  box.height = random(params.minHeight, params.maxHeight);
  
  if (box.y > height) {
    box.x += box.width;
    box.y = -params.lineWidth;
    box.width = random(params.minWidth, params.maxWidth);
    box.height = random(params.minHeight, params.maxHeight);
  }
  
  if (box.x > width) {
    noLoop();
  }
}
{{</p5js>}}

I did have a sketch before that that ended up getting a little un-minimal:

{{<p5js width="600" height="420">}}
let gui;
let params = {
  cycle: 10,
  refresh: 10,
  offset: 20,
  radius: 100,
}

let x, y;

function setup() {
  createCanvas(400, 400);
  
  x = random(200) + 100;
  y = random(200) + 100;

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  stroke("black");
  noFill();
  
  if (frameCount % (params.cycle * params.refresh) == 0) {
    background("white");
  }
  
  if (frameCount % params.cycle == 0) {
    x = random(200) + 100;
    y = random(200) + 100;
  }
  
  circle(
    x + params.offset * cos(frameCount / params.cycle),
    y + params.offset * sin(frameCount / params.cycle),
    params.radius,
  );
}
{{</p5js>}}

It's just circles! But yeah. 

{{< taxonomy-list "series" "Genuary 2023" >}}

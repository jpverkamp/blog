---
title: "Genuary 2023.11: Suprematism"
date: 2023-02-11
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-11.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 11) Suprematism

Wikipedia: [[wiki:Suprematism]]()

<!--more-->

Not entirely sure I hit this one. Or really what's going on here. But it's kind of neat looking. :smile: 

{{<p5js width="600" height="420">}}
let gui;
let params = {
  shapesPerColor: 4, shapesPerColorMin: 1, shapesPerColorMax: 10,
  minSize: 2, minSizeMin: 1, minSizeMax: 100, 
  maxSize: 20, maxSizeMin: 1, maxSizeMax: 100,
  pullForce: 0.3, pullForceMin: 0.0, pullForceMax: 5.0, pullForceStep: 0.01,
  pushForce: 3.0, pushForceMin: 0.0, pushForceMax: 5.0, pushForceStep: 0.01,
};

let colors = [
  "red",
  "gold",
  "black",
  "darkblue",
  "darkred",
  "tan",
  "brown",
  "gray",
];

let rects;

function setup() {
  createCanvas(400, 400);
  frameRate(30);
  rectMode(CENTER);
  
  rects = [];
  
  translate(createVector(200, 200));

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function addRects() {
  let c = random(colors);
  for (let si = 0; si < params.shapesPerColor; si++) {
    let x = 200 + random(-10, 10);
    let y = 200 + random(-10, 10);
    let w = random(params.minSize, params.maxSize);
    let h = random(params.minSize, params.maxSize);
    let r = TWO_PI * (random() * 0.01 - 0.005);
    
    rects.push([x, y, w, h, c, r]);
  }
}

function draw() {
  background(255);
  let color = random(colors);
  
  let movement = false;
  
  // Shapes try to pull together
  for (let i = 0; i < rects.length; i++) {
    let [xi, yi, wi, hi, _ci, _ri] = rects[i];
    
    let dx = 0.0;
    if (xi + wi / 2 < 200) dx = 1.0;
    if (xi - wi / 2 > 200) dx = -1.0;
    
    let dy = 0.0;
    if (yi + hi / 2 < 200) dy = 1.0;
    if (yi - hi / 2 > 200) dy = -1.0;
    
    rects[i][0] += 0.1 * dx * params.pullForce * random();
    rects[i][1] += 0.1 * dy * params.pullForce * random();
  }
  
  // Shapes try to push apart
  for (let i = 0; i < rects.length; i++) {
    for (let j = 0; j < rects.length; j++) {
      if (i == j) continue;
      
      let [xi, yi, wi, hi, _ci, _ri] = rects[i];
      let [xj, yj, wj, hj, _cj, _rj] = rects[j];
      
      let dx = abs(xi - xj);
      let dy = abs(yi - yj);
      
      let offset_x = (wi + wj) / 2 - dx;
      let offset_y = (hi + hj) / 2 - dy;
      
      let x_is_fine = offset_x < 5;
      let y_is_fine = offset_y < 5;
      
      let x_or_y, ij_min, ij_max;
      
      let do_x = offset_x > offset_y;
      if (random() < 0.5) do_x = !do_x;
      
      if (do_x && x_is_fine) continue;
      if (!do_x && y_is_fine) continue;
      
      if (do_x) { // which to move
        x_or_y = 0;
        [ij_min, ij_max] = (xi < xj) ? [i, j] : [j, i];
      } else {
        x_or_y = 1;
        [ij_min, ij_max] = (yi < yj) ? [i, j] : [j, i];
      }
      
      rects[ij_min][x_or_y] -= params.pushForce * random();
      rects[ij_max][x_or_y] += params.pushForce * random();
      
      movement = true;
    }
  }
  
  if (!movement) {
    addRects()
  }

  for (let i = 0; i < rects.length; i++) {
    let [xi, yi, wi, hi, _ci, _ri] = rects[i];

    if (
        (xi + wi / 2 < 0)
        || (xi - wi / 2 > width)
        || (yi + hi / 2 < 0)
        || (yi + hi / 2 > height)
    ) {
      rects.splice(i, 1);
      i--;
    }
  }

  // Emergency backup: remove any more than 1000 oldest first
  while (rects.length > 1000) rects.shift();
  
  for (let [x, y, w, h, c, r] of rects) {
    push();
    {
      translate(x, y);
      rotate(r);

      fill(c);
      rect(0, 0, w, h);
    }
    pop();
  } 
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

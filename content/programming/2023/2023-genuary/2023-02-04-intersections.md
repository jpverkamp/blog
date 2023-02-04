---
title: "Genuary 2023.04: Intersections"
date: 2023-02-04
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 4) Intersections

<!--more-->

This actually came about a lot from the previous one. I was working with `blendMode` and found that `ADD` is a good way to draw intersections. So we have:

{{<p5js width="400" height="420">}}
function setup() {
  createCanvas(400, 400);
  rectMode(CENTER);
  noStroke();
}

function draw() {
  push();
  {
    translate(200, 200);
    rotate(TWO_PI / random(360));
    
    // Set up a modulo every N seconds (the div in blockCount)
    let secondCount = parseInt(frameCount / 60);
    let blockCount = parseInt(secondCount / 5);
    
    // Every other block, swap blend mode
    blendMode({
      0: DIFFERENCE,
      1: ADD
    }[blockCount % 2]);
    
    // Each block out (or each two) move down in scale
    let scaleScale = {
      0: 1.0,
      1: 1.0,
      2: 0.8,
      3: 0.8,
      4: 0.6,
      5: 0.6,
      6: 0.4,
      7: 0.4,
    }[blockCount % 8];
    
    scale(scaleScale * (random() - 0.5));

    fill(
      random(255),
      random(255),
      random(255),
    )
    rect(0, 0, 400, 400);
  }
  pop();
}
{{</p5js>}}


{{< taxonomy-list "series" "Genuary 2023" >}}

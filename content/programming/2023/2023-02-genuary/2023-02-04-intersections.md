---
title: "Genuary 2023.04: Intersections"
date: 2023-02-04
draft: True
programming/languages:
- JavaScript
programming/topics:
- Procedural
series:
- Genuary 2023
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

{{< taxonomy-list "series" "Genuary 2023" >}}

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
    blendMode(ADD);
    translate(200, 200);
    rotate(TWO_PI / random(360));
    scale(random(100) / 100.0 - 0.5);

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

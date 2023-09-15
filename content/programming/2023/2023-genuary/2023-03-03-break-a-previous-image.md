---
title: "Genuary 2023.31: Break a previous image"
date: 2023-03-03
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-31.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.

Let's do it!

## 31) Deliberately break one of your previous images, take one of your previous works and ruin it. Alternatively, remix one of your previous works.

<!--more-->

Ouch. 

Based on [[Genuary 2023.19: Black and white]]()

Still kinda cool looking. 

{{<p5js width="400" height="420">}}
function setup() {
  createCanvas(400, 400);
  background(255);
  rectMode(CENTER);

  stroke(255);
  fill(0);
}

function draw() {
  translate(200, 200);
  
  if (frameCount % 100 == 0) {
    push();
    translate(random(10), random(10));
  }
  
  rotate((frameCount % 360) * TWO_PI / 360.0);
  scale(cos(frameCount / 100.0));
  
  rect(0, 0, 200, 200);
  
  if (frameCount % 100 == 0) {
    pop();
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

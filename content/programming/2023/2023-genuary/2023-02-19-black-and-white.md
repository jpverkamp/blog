---
title: "Genuary 2023.19: Black and white"
date: 2023-02-19
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-19.png
---
[Genuary](https://genuary.art/)! 

## 19) Black and white

<!--more-->

Something absolutely tiny (code wise) but still cool. 

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
  
  rotate((frameCount % 360) * TWO_PI / 360.0);
  scale(cos(frameCount / 100.0));
  
  rect(0, 0, 200, 200);
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

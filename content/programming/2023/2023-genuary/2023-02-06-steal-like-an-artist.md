---
title: "Genuary 2023.06: Steal like an artist"
date: 2023-02-06
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-06.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 6) Steal Like An Artist

<!--more-->

Cool. Let's do the [picsum](https://picsum.photos/) thing again and then randomly draw some nice curvy brush strokes over it. 

Now with parameterization!

{{<p5js width="600" height="420">}}
let gui;
let params = {
  iterationCount: 100, iterationCountMin: 1,
  maximumDistance: 10.0, maximumDistanceMax: 100.0,
  brush: 3, brushMin: 1, brushMax: 10,
};

let original;

function preload() {
  console.log('Loading...');
  original = loadImage("https://picsum.photos/400");
  console.log("done");
}

function setup() {
  createCanvas(400, 400);

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  for (let i = 0; i < params.iterationCount; i++) {
    drawOne();
  }
}

function drawOne() {
  let points = [];
  points.push(createVector(
    random(width),
    random(height)
  ));
  
  for (let i = 1; i <= 4; i++) {
    points.push(p5.Vector.add(
      points[points.length - 1],
      p5.Vector.random2D().mult(random() * params.maximumDistance)
    ));
  }
  
  let r = 0, g = 0, b = 0;
  
  for (let p of points) {
    let c = original.get(parseInt(p.x), parseInt(p.y));
    r += c[0];
    g += c[1];
    b += c[2];
  }
  
  r /= points.length;
  g /= points.length;
  b /= points.length;
  
  strokeWeight(params.brush);
  stroke(
    parseInt(r),
    parseInt(g),
    parseInt(b),
    255
  );
  noFill();
  
  curve(
    points[0].x, points[0].y,
    points[1].x, points[1].y,
    points[2].x, points[2].y,
    points[3].x, points[3].y
  );
}
{{</p5js>}}



{{< taxonomy-list "series" "Genuary 2023" >}}

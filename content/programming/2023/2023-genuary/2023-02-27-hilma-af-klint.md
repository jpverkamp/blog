---
title: "Genuary 2023.27: In the style of Hilma Af Klint"
date: 2023-02-27
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-27.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 27) In the style of [[wiki:Hilma Af Klint]]()

<!--more-->

Based on [Svanen](https://arthur.io/art/hilma-af-klint/svanen-the-swan-no-17-group-ix-series-suw). 

{{<p5js width="600" height="420">}}
let gui;
let params = {
  wiggle: 0, wiggleMax: 10,
  randomColors: false,
  smokeSize: 10, smokeSizeMin: 0, smokeSizeMax: 400,
}

let COLORS = [
  "black",
  "white",
  "blue",
  "yellow",
  "red",
  "green",
  "magenta",
  "cyan",
  "gray",
];

function setup() {
  createCanvas(400, 400);
  frameRate(10);

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  if (params.randomColors) {
    background(random(COLORS))
  } else {
    background("red");
  }
  
  function wiggle() {
    return random(params.wiggle) - params.wiggle / 2;
  }
  
  function myArc(color, left, size) {
    noStroke();
    
    if (params.randomColors) {
      fill(random(COLORS))
    } else {
      fill(color);
    }
    
    arc(
      200 + wiggle(),
      200 + wiggle(),
      size + wiggle(),
      size + wiggle(), 
      TWO_PI*(left ? 1 : 3)/4,
      TWO_PI*(left ? 3 : 1)/4,
      PIE
    );
  }
  
  myArc("white",  true,  300);
  myArc("black",  true,  200);
  myArc("blue",   false, 300);
  myArc("yellow", false, 200);
  myArc("red",    false, 100);
  
  noStroke();
  
  if (params.randomColors) {
    fill(random(COLORS))
  } else {
    fill("black");
  }
  triangle(
    200 + wiggle(), 190 + wiggle(), 
    205 + wiggle(), 200 + wiggle(), 
    200 + wiggle(), 200 + wiggle()
  );
  
  if (params.randomColors) {
    fill(random(COLORS))
  } else {
    fill("red");
  }
  triangle(
    200 + wiggle(), 190 + wiggle(), 
    195 + wiggle(), 200 + wiggle(), 
    200 + wiggle(), 200 + wiggle()
  );
  
  noStroke();
  if (params.smokeSize > 0) {
    for (let x = 0; x < width; x += params.smokeSize) {
      for (let y = 0; y < height; y += params.smokeSize) {
        let a = 256 * noise(x / width, y / height, frameCount / 10.0);
        fill(255, 255, 255, a);
        rect(x, y, params.smokeSize, params.smokeSize);
      }
    }
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

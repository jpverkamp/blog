---
title: "Genuary 2023.21: Persian Carpet"
date: 2023-02-21
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2023
cover: /embeds/2023/genuary-21.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 21) Persian carpet

Wikipedia: {{<wikipedia "Persian carpet">}}

<!--more-->

Yeah... this one got away from me. I ended up making some *very vaguely* Persian rug style trees. I mostly ran out of time to dig deeper into this one. I think it's neat though. 

{{<p5js width="400" height="420">}}
class Tree {
  constructor(x, y, a, r, trunkColor, flowerColor) {
    this.x = x;
    this.y = y;
    this.a = a;
    this.r = r;
    this.trunkColor = trunkColor;
    this.flowerColor = flowerColor;
    this.growing = true;
    this.flowering = false;
    this.children = [];
    
          
    let [fr, fg, fb] = this.flowerColor;
    fr += random(10) - 5;
    fg += random(10) - 5;
    fb += random(10) - 5;
    this.flowerColor = [fr, fg, fb];
  }
  
  update() {
    if (this.growing) {
      let r = this.r / 4 * random();
      let a = this.a + (random() - 0.5) / 10.0

      this.x += r * cos(a);
      this.y += r * sin(a);

      if (random() < 0.025) {
        this.growing = false;

        if (this.r < 10) {
          this.flowering = true;
        } else {
          // branches
          for (let aDelta of [TWO_PI * 1/8, -TWO_PI * 1/8]) {
            this.children.push(new Tree(
              this.x,
              this.y,
              this.a + random() * aDelta,
              this.r * 0.8,
              this.trunkColor,
              this.flowerColor
            ));
          }
        }      
      }
    }

    for (let child of this.children) child.update();
  }
  
  draw() {
    if(!this.flowering) {      
      noStroke();
      
      let [r, g, b] = this.trunkColor;
      r += random(10) - 5;
      g += random(10) - 5;
      b += random(10) - 5;
      fill([r, g, b]);
      
      circle(this.x, this.y, this.r);
    }
    
    for (let child of this.children) child.draw();
  }
  
  drawFlowers() {
    if (this.flowering) {
      stack(() => {
        translate(this.x, this.y);
        for (let i = 0; i < 6; i++) {
          rotate(TWO_PI / 6);
          stroke("black");
          fill(this.flowerColor);
          circle(0, this.r, 2 * this.r);
        }
        fill("black");
        circle(0, 0, this.r);
      });
    }
    
    for (let child of this.children) child.drawFlowers();
  }
}

let trees;

function setup() {
  createCanvas(400, 400);
  
  trees = [];
  
  trees.push(new Tree(
    100,
    400,
    TWO_PI * 3/4,
    20,
    [230, 160, 100],
    [230, 180, 180],
  ));
  
  trees.push(new Tree(
    200,
    400,
    TWO_PI * 3/4,
    20,
    [150, 75, 0],
    [100, 150, 100],
  ));  
  
  trees.push(new Tree(
    300,
    400,
    TWO_PI * 3/4,
    20,
    [255, 180, 180],
    [240, 230, 220],
  ));
  
  background(0);
}

function draw() {
  for (let tree of trees) {
    tree.update();
  }
  
  for (let tree of trees) {
    tree.draw();
  } 
  
  for (let tree of trees) {
    tree.drawFlowers();
  } 
}

function stack(thunk) {
  push();
  thunk();
  pop();
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

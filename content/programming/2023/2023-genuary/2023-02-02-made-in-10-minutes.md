---
title: "Genuary 2023.02: Made in 10 minutes"
date: 2023-02-02
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- Trigonometry
- Time
- Clocks
- p5js
series:
- Genuary 2023
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 2) Made in 10 minutes

<!--more-->

I made a clock.

{{<p5js width="400" height="420">}}
function setup() {
    createCanvas(400, 400);
}

function draw() {
    background(0);

    // Border
    rectMode(CENTER);
    for (let i = 0; i < 24; i++) {
        let a = i * TWO_PI / 24;
        let x = width / 2 + width / 4 * cos(a);
        let y = height / 2 + width / 4 * sin(a);

        fill(
          255 * noise(frameCount / 100.0, i / 24.0, 1),
          255 * noise(frameCount / 100.0, i / 24.0, 2),
          255 * noise(frameCount / 100.0, i / 24.0, 3)
        );
        rect(x, y, 50, 50);
    } 

    push();
    {
      rectMode(CORNER);
      translate(200, 200);
      fill(255);

      // Hour hand
      push();
      {
        rotate(PI + ((TWO_PI * hour()) % 12) / 12);
        rect(0, 0, 4, 40);
      }
      pop();

      // Minute hand
      push();
      {
        rotate(PI + (TWO_PI * minute()) / 60);
        rect(0, 0, 3, 60);
      }
      pop();

      // Second hand
      push();
      {
        rotate(PI + (TWO_PI * second()) / 60);
        rect(0, 0, 2, 80);
      }
      pop();
    }
    pop();
}
{{</p5js>}}

The background uses some simple noise to cycle through interesting colors. 

Not thrilled with the seam on the right hand side... but 10 minutes :shrug:

{{< taxonomy-list "series" "Genuary 2023" >}}

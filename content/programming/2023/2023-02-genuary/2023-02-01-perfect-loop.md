---
title: "Genuary 2023.01: Perfect loop"
date: 2023-02-01
programming/languages:
- JavaScript
programming/topics:
- Procedural
- Perfect Loops
- Animated
series:
- Genuary 2023
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

{{< taxonomy-list "series" "Genuary 2023" >}}

## 1) Perfect loop / Infinite loop / endless GIFs

<!--more-->

For this one, really anything that uses trig functions of the frame count will work. Trig functions are great at cycling. :smile: 

Ergo:

```javascript
function frame_cycle(C) {
  return cos(map(frameCount % C, 0, C, -1.0, 1.0));
}
```

Let's use that to cycle through colors, rotations, and translations:

{{<p5js width="400" height="420">}}
function frame_cycle(C) {
  return cos(map(frameCount % C, 0, C, -1.0, 1.0));
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSL);
}

function draw() {
  fill(360 * frame_cycle(90), 100, 50, 1);

  push();
  translate(width / 2, height / 2);
  rotate(360 * frame_cycle(180));
  scale(frame_cycle(15));

  rect(0, 0, width / 4, height / 4);
  pop();
}
{{</p5js>}}

And away we go. Is it perfect? Absolutely not. Is it generated and fun to watch? Absolute!

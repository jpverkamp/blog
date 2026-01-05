---
title: "Genuary 2026.02: Twelve principles of animation "
date: 2026-01-02
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.02.png
---
## 2) Twelve principles of animation 

[[wiki:Twelve principles of animation]]()

* Stretch and shrink
* Anticipation
* Staging
* Direct animation
* Complementary
* Accelerate and decelerate
* Arcs
* Secondary action
* Synchronization
* Exaggeration
* Solid drawing
* Attractive

That ... is a lot. And I'm not *really* an animator. But let's see what we can do!

<!--more-->

{{<p5js width="600" height="420">}}
let gui;
let params = {
  stretchAndShrink: false,
  anticipation: false,
  staging: false,
  directAnimation: false,
  complementary: false,
  accelerateAndDecelerate: false,
  arcs: false,
  secondaryAction: false,
  synchronization: false,
  exaggeration: false,
  solidDrawing: false,
  attractive: false,
};

function frameCycle(cycleLength, offset) {
  let t = ((frameCount + (offset || 0)) % cycleLength) / cycleLength;
  return t < 0.5 ? t * 2 : 2 - t * 2;
}

function setup() {
  createCanvas(400, 400);
  background("white");

  gui = createGuiPanel('params');
  gui.addObject(params);
  gui.setPosition(420, 0);
}

function draw() {
  stroke("white");
  fill(0);

  let arcPhase = frameCycle(60);
  let groundPhase = 1 - arcPhase;

  let xPhase = frameCycle(600);
  let yPhase = arcPhase;
  
  // Accelerate / Decelerate. as we're going left/right
  if (params.accelerateAndDecelerate) {
    let cycle = frameCount % 600;
    let goingRight = cycle < 300;

    if (goingRight) {
      xPhase = pow(xPhase, 0.5);   // speed up
    } else {
      xPhase = pow(xPhase, 2.0);   // slow down
    }
  }

  let x = xPhase * width;
  let y = height * 3 / 4 - (height / 2) * yPhase;

  // Arcs (horizontal sway)
  if (params.arcs) {
    x += sin(yPhase * PI) * 40;
  }

  let baseRadius = width / 6;
  let w = baseRadius;
  let h = baseRadius;

  // Stretch & Squash (ground contact)
  if (params.stretchAndShrink) {
    let squashiness = 1 + 0.6 * pow(groundPhase, 4);
    w *= squashiness;
    h /= squashiness;
    y += (baseRadius - h) * 0.5;
  }
  
  // Anticipation (hang time at top, exaggerated drop)
  if (params.anticipation) {
    // invert easing so it slows near the top
    let t = 1 - arcPhase;
    let eased = 1 - pow(t, 3);   // slow at top, fast downward
    y = height * 3 / 4 - (height / 2) * eased;
  }

  // Exaggeration
  if (params.exaggeration) {
    w *= 1.4;
    h *= 0.6;
  }

  // Solid Drawing (fake volume via outline weight)
  if (params.solidDrawing) {
    background("white");
    fill("white");
    stroke("white");
  } else {
    fill("black");
    stroke("white");
  }

  // Staging (center bias)
  if (params.staging) {
    x = width / 2;
  }

  // Direct Animation (mouse-driven influence)
  // I'm already keyframing, so I just took it literally :)
  if (params.directAnimation) {
    let mx = (mouseX - width / 2) * 0.1;
    let my = (mouseY - height / 2) * 0.1;

    x += mx;
    y += my;
  }

  // Secondary Action (small orbiting detail)
  if (params.secondaryAction) {
    let sx = x + cos(frameCount / 20) * w * 1.4;
    let sy = y + sin(frameCount / 20) * h * 1.4;
    ellipse(sx, sy, w * 0.25, h * 0.25);
  }

  // Synchronization (bounce timing matches squash)
  if (params.synchronization) {
    // sync horizontal + vertical timing
    let syncFactor = sin(frameCount / 10); // smooth oscillation
    w *= 1 + 0.3 * syncFactor;
    h /= 1 + 0.3 * syncFactor;

    // adjust y to stay grounded
    y += (baseRadius - h) * 0.5;
  }


  // Attractive (subtle harmonic proportions)
  // 'cause the golden ratio is attractive or something
  // What do you want from me? There are *12* of these on day 2...
  if (params.attractive) {
    let ratio = 1.618;
    if (w > h) {
      h = w / ratio;
    } else {
      w = h / ratio;
    }
  }

  ellipse(x, y, w, h);
  
  if (params.complementary) {
    ellipse(x, height - y, w, h);
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2026" >}}

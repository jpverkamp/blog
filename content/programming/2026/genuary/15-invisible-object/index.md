---
title: "Genuary 2026.15: Invisible Object"
date: "2026-01-15"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.15.png
---
> Create an invisible object where only the shadows can be seen.

Noise that pushes a bunch of particles around on the screen. There is 1 (or more) 'shadows' on the screen that push the dust away. 

If the shadow runs off the screen it will come back in a bit from the opposite edge. 

Settings:

* `dustCount` is how much dust
* `dustSpeed` is a multiplier for how fast the dust goes per frame
* `dustDieOff` is how much dust disappears each frame
* `onlyEdgeDust` sets dust to only spawn on the edges, rather than anywhere (has some weird visual artifacts when the dust is a nearly horizontal / vertical)
* `rainbowDust` makes the dust far more colorful
* `windScale` is the scale of the noise, 1 will wiggle a lot more, 5 is closer to straight lines and slow changes
* `fade` will leave trails by fading the screen; turning this off is interesting since the shadow will be much more subtle
* `shadowCount` is how many shadows there are
* `shadowForce` is how strongly they repel dust
* `shadowWindIndependent` means the shadow doesn't always move with the particles
* `shadowEdge` will show where the shadow shape actually is
* `shadowsMove` will allow the shadows to move / stop them

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  dustCount: 5000, dustCountMin: 0, dustCountMax: 10000,
  dustSpeed: 5, dustSpeedMin: 1, dustSpeedMax: 10, dustSpeedStep: 0.1,
  dustDieOff: 0.001, dustDieOffMin: 0, dustDieOffMax: 1, dustDieOffStep: 0.001,
  onlyEdgeDust: true,
  rainbowDust: true,
  windScale: 3, windScaleMin: 0, windScaleMax: 5,
  fade: true,
  shadowCount: 1, shadowCountMin: 0, shadowCountMax: 5,
  shadowForce: 2, shadowForceMin: 0, shadowForceMax: 5,
  shadowWindIndependent: true,
  shadowEdge: false,
  shadowsMove: true,
  
};

let dusts = [];
let shadows = [];

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
  
  background("black");
}

function draw() {
  while (dusts.length > params.dustCount) dusts.shift();
  while (dusts.length < params.dustCount) {
    let d = {
      type: 'dust',
      x: floor(random() * width),
      y: floor(random() * height),
      h: floor(random() * 360),
    };
    
    if (params.onlyEdgeDust) {
      let zero_x = random() < 0.5;
      let zero_min = random() < 0.5;

      if (zero_x && zero_min) d.x = 0;
      if (zero_x && !zero_min) d.x = width;
      if (!zero_x && zero_min) d.y = 0;
      if (!zero_x && !zero_min) d.y = height;
    }
    
    dusts.push(d);
  }
  
  while (shadows.length > params.shadowCount) shadows.shift();
  while (shadows.length < params.shadowCount) {
    shadows.push({
      type: 'shadow',
      x: floor(width / 4 + random() * width / 2),
      y: floor(height / 4 + random() * height / 2),
      d: floor(random() * 10) + 100,
    })
  }
  
  // Apply all forces at the given point
  function applyForces(p, speed) {
    let z = 0;
    if (params.shadowWindIndependent && p.type == 'shadow') {
      z += 1337.1;
    }
    
    let nf = frameCount / (10 ** params.windScale);
    let nx = p.x / width / (10 ** params.windScale);
    let ny = p.x / height / (10 ** params.windScale);
    
    let windX = noise(nf, nx, z) - noise(nf, nx, z + 10.1);
    let windY = noise(nf, ny, z + 20.2) - noise(nf, ny, z + 30.3);

    p.x += windX * speed;
    p.y += windY * speed;
    
    for (let s of shadows) {
      if (p === s) continue;

      let dx = p.x - s.x;
      let dy = p.y - s.y;
      let d = sqrt(dx * dx + dy * dy);

      if (d < 0.0001) continue;

      let r = s.d / 2;

      if (d >= r && d <= 2 * r) {
        let t = (d - r) / r;
        let strength = pow(1 - t, 3);

        let f = params.shadowForce * strength * speed;

        p.x += (dx / d) * f;
        p.y += (dy / d) * f;
      }
    }

  }
  
  // Update shadows
  if (params.shadowsMove) {
    for (let s of shadows) {
      applyForces(s, 1);
      
      let r = s.d / 2;
      
      if (s.x < -2 * r) { 
        s.x = width + r;
        s.y = height / 2 + floor(random() * height / 4);
      }
      if (s.x > width + 2 * r) {
        s.x = -r;
        s.y = height / 2 + floor(random() * height / 4);
      } 
      if (s.y < -2 * r) {
        s.y = height + r;
        s.x = width / 2 + floor(random() * width / 4);
      }
      if (s.y > height + 2 * r) {
        s.y = -r;
        s.x = width / 2 + floor(random() * width / 4);
      }
    }
  }
  
  // Update dusts
  for (let p of dusts) {
    applyForces(p, params.dustSpeed);
  }
  
  // Remove dust that has drifted off screen
  dusts = dusts.filter((p) => {
    if (p.x < 0 || p.x >= width || p.y < 0 || p.y >= height) {
      return false;
    }
    
    if (shadows.some((s) => {
      let dx = p.x - s.x;
      let dy = p.y - s.y;
      let r = s.d / 2;
      
      return dx * dx + dy * dy < r * r;
    })) {
      return false;
    }
    
    if (random() < params.dustDieOff) {
      return false;
    }
    
    return true;
  });
  
  if (params.shadowEdge) {
    stroke("white")
    noFill();
    for (let s of shadows) {
      circle(s.x, s.y, s.d);
    }
  }
  
  for (let p of dusts) {
    if (params.rainbowDust) {
      stroke(p.h, 100, 100);
    } else {
      stroke(35, 20 + random() * 40, 75 + random() * 40);
    }

    // For some reason point works on editor.p5js but not here? 
    circle(p.x, p.y, 1); 
  }
  
  if (params.fade) {
    noStroke();
    fill(0, 0, 0, 4);
    rect(0, 0, width, height);
  }
}
{{</p5js>}}

Here are some fun ones I've found.

## Examples

## Brownian motion

[Not rainbow, high die off, low wind scale.](?dustDieOff=0.814&onlyEdgeDust=false&rainbowDust=false&windScale=0&shadowForce=3)

![](brownian.png)

## Weakly interacting

[High speed, shadow force 0](?dustSpeed=10&dustDieOff=0.007&onlyEdgeDust=false&windScale=5&shadowForce=0)

![](wimp.png)    

## Gradient

[Only edge, die off 0.05.](?dustSpeed=10&dustDieOff=0.007&rainbowDust=false&windScale=5&shadowForce=3)

![](gradiant.png)

There's that artifact along the top I was talking about. 

## Texture

High speed, low (but non 0) die off, wind scale of 0, no shadows. 

Gives a path of each texture. Man it looks weird to watch it wiggle. 

![](texture.png)

{{< taxonomy-list "series" "Genuary 2026" >}}

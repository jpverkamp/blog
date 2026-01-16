---
title: "Genuary 2026.16: Order vs Disorder"
date: "2026-01-16"
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
series:
- Genuary 2026
cover: gen26.16.png
---
> Order vs Disorder

So I have two kinds of agents: Order, which always moves in straight lines and Chaos which... doesn't!

Settings:

* `updateRate` is how fast it runs
* `minAgentCount` will spawn agents until you reach this number
* `maxAgentCount` will kill off agents until you're under this number
* `dieOfOldAge` will kill off old agents
* `maxAge` is the longest an agent can last
* `agentRatio` of 0 is all order and 1 is all chaos
* `spawnRate` is how often an agent will spawn a new agent (of the same kind)
* `resetPercent` is how much of the screen can be full before resetting
* `pauseOnReset` will pause on a reset to allow downloading! (change any setting include this one to unpause)

<!--more-->

{{<p5js width="600" height="500">}}
let gui;
let params = {
  updateRate: 10, updateRateMin: 1, updateRateMax: 100,
  minAgentCount: 5, minAgentCountMin: 1, minAgentCountMax: 100,
  maxAgentCount: 100, maxAgentCountMin: 1, maxAgentCountMax: 100,
  dieOfOldAge: true,
  maxAge: 100, maxAgeMin: 0, maxAgeMax: 1000,
  agentRatio: 0.75, agentRatioMin: 0, agentRatioMax: 1, agentRatioStep: 0.01,
  spawnRate: 0.01, spawnRateMin: 0, spawnRateMax: 1, spawnRateStep: 0.01,
  resetPercent: 0.2, resetPercentMin: 0, resetPercentMax: 1, resetPercentStep: 0.01,
  pauseOnReset: false,
};

let lastParams;
let agents = [];
let points = new Set();
let clearNextFrame = false;
let paused = false;

const pKey = (p) => `${p.x},${p.y}`;
const pointsHas = (p) => points.has(pKey(p));
const pointsAdd = (p) => points.add(pKey(p));

const randomD = () => {
  const r = Math.floor(Math.random() * 4);
  return [
    { x:  1, y:  0 },
    { x: -1, y:  0 },
    { x:  0, y:  1 },
    { x:  0, y: -1 },
  ][r];
};

const cw = (d) => ({ x: d.y, y: -d.x });
const ccw = (d) => ({ x: -d.y, y: d.x });
const randomTurn = (d) => {
  if (random() < 0.5) {
    return cw(d);
  } else {
    return ccw(d);
  }
}

const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y });

class OrderAgent {
  constructor(p, d, h) {
    this.age = 0;
    this.alive = true;
    this.p = p;
    this.d = d;
    this.h = h || random(360);
  }
  
  static random() {
    return new OrderAgent(
      {
        x: floor(random(width)),
        y: floor(random(height)),
      },
      randomD(),
    );
  }
  
  update() {
    this.age += 1;
    this.p = add(this.p, this.d);
    
    if (random() < params.spawnRate) {
      let newD = randomTurn(this.d);
      let newP = add(this.p, newD);
      if (!pointsHas(newP)) {
        let c = new OrderAgent(newP, newD, this.h);
        agents.push(c);
      }
    }
    
    if (this.p.x < 0 || this.p.x >= width || this.p.y < 0 || this.p.y >= height) {
      this.alive = false;
    }

    if (pointsHas(this.p)) {
      this.alive = false;
    } else {
      pointsAdd(this.p);
    }
  }
  
  draw() {
    noStroke();
    fill(this.h, 100, 100);
    rect(this.p.x, this.p.y, 1, 1);
  }
}

class ChaosAgent {
  constructor(p, d, h) {
    this.age = 0;
    this.alive = true;
    this.p = p;
    this.d = d;
    this.h = h || random(360);
  }
  
  static random() {
    return new ChaosAgent(
      {
        x: floor(random(width)),
        y: floor(random(height)),
      },
      randomD(),
    );
  }
  
  update() {
    this.age += 1;
    this.p = add(this.p, this.d);
    
    // Hacks lol
    for (let i = 0; i < 10; i++) {
      this.d = randomD();
      let nextP = add(this.p, this.d);
      if (!pointsHas(nextP)) {
        break;
      }
    }    

    if (random() < params.spawnRate) {
      let newD = randomTurn(this.d);
      let newP = add(this.p, newD);
      if (!pointsHas(newP)) {
        let c = new ChaosAgent(newP, newD);
        agents.push(c);
      }
    }
    
    if (this.p.x < 0 || this.p.x >= width || this.p.y < 0 || this.p.y >= height) {
      this.alive = false;
    }

    if (pointsHas(this.p)) {
      this.alive = false;
    } else {
      pointsAdd(this.p);
    }
  }
  
  draw() {
    noStroke();
    fill(this.h, 100, 100);
    rect(this.p.x, this.p.y, 1, 1);
  }
}

function setup() {
  createCanvas(400, 400);
  colorMode(HSB, 360, 100, 100, 100);
  
  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);
  
  background("black");
}

function draw() {
  if (lastParams == undefined || Object.keys(params).some(k => params[k] !== lastParams[k])) {
    agents = [];
    points = new Set();
    lastParams = {...params};
    clearNextFrame = true;
    paused = false;
  }
  
  if (params.pauseOnReset && paused) {
    return;
  }

  if (clearNextFrame) {
    background("black");
    clearNextFrame = false;
  }

  while (agents.length > params.maxAgentCount) agents.shift();
  while (agents.length < params.minAgentCount) {
    if (random() < params.agentRatio) {
      agents.push(ChaosAgent.random());
    } else {
      agents.push(OrderAgent.random());
    }
    
  }
  
  for (let i = 0; i < params.updateRate; i++) {
    agents.forEach((a) => a.update());
    agents = agents.filter((a) => a.alive && (!params.dieOfOldAge || a.age < params.maxAge));
    agents.forEach((a) => a.draw());
  }
  
  if (points.size > params.resetPercent * width * height) {
    agents = [];
    points = new Set();
    clearNextFrame = true;
    
    if (params.pauseOnReset) {
      paused = true;
    }
  }
}
{{</p5js>}}

## Examples

It's fun to push this to all order:

![](all-order.png)

Or all chaos:

![](all-chaos.png)

{{< taxonomy-list "series" "Genuary 2026" >}}

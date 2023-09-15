---
title: "Genuary 2023.05: Debug view"
date: 2023-02-05
programming/languages:
- JavaScript
programming/topics:
- Generative Art
- Procedural Content
- p5js
- Cellular Automata
- Generative Art
- Procedural Content Content
series:
- Genuary 2023
cover: /embeds/2023/genuary-05.png
---
[Genuary](https://genuary.art/)! 

Spend a month making one beautiful thing per day, given a bunch of prompts. A month late, but as they say, 'the second best time is now'.  

Let's do it!

## 5) Debug view

I like [[wiki:Boids]](). Here are some Boids with debug vectors drawn showing the three forces acting on them (red to stay away from one another, green to move in the same direction as their friends, blue to move towards the center of their friends). 

Use the 'toggle clear' button to clear the screen between each frames to see the simulation versus not to get some twisty spaghetti 'art'. :smile:

Also, the forces for each are randomized each time. Click 'reload' to get new random values. 

{{<p5js width="600" height="460">}}
let gui;
let params = {
  count: 100,
  countMin: 10,
  countMax: 1000,
  maxSpeed: 3.0,
  maxSpeedMin: 0.0,
  maxSpeedMax: 10.0,
  maxSpeedStep: 0.1,

  visionDistance: 50.0,
  visionDistanceMin: 1.0,
  visionDistanceMax: 400.0,

  noiseForce: 1.0,
  noiseForceMin: 0.0,
  noiseForceMax: 2.0,
  noiseForceStep: 0.1,
  wallAvoidanceForce: 1.0,
  wallAvoidanceForceMin: 0.0,
  wallAvoidanceForceMax: 2.0,
  wallAvoidanceForceStep: 0.1,
  separationForce: 1.0,
  separationForceMin: 0.0,
  separationForceMax: 2.0,
  separationForceStep: 0.1,
  alignmentForce: 1.0,
  alignmentForceMin: 0.0,
  alignmentForceMax: 2.0,
  alignmentForceStep: 0.1,
  cohesionForce: 1.0,
  cohesionForceMin: 0.0,
  cohesionForceMax: 2.0,
  cohesionForceStep: 0.1,

  debug: true,
  drawBackground: true,
};

let boids;

class Boid {
  constructor(p) {
    this.position =
      p ||
      createVector(
        params.visionDistance + random(width - params.visionDistance * 2),
        params.visionDistance + random(height - params.visionDistance * 2)
      );
    this.velocity = p5.Vector.random2D().mult(params.maxSpeed * random());
  }

  update() {
    // Apply noise
    this.velocity.add(p5.Vector.random2D().mult(params.noiseForce));

    // Avoid the walls
    if (this.position.x < params.visionDistance) {
      this.velocity.x += params.wallAvoidanceForce;
    }
    if (this.position.x > width - params.visionDistance) {
      this.velocity.x -= params.wallAvoidanceForce;
    }
    if (this.position.y < params.visionDistance) {
      this.velocity.y += params.wallAvoidanceForce;
    }
    if (this.position.y > height - params.visionDistance) {
      this.velocity.y -= params.wallAvoidanceForce;
    }

    // Actual BOID forces
    this.separation_force = createVector(0, 0);
    this.alignment_force = createVector(0, 0);
    this.cohesion_force = createVector(0, 0);

    // Calculate average of local neighborhood
    this.friend_count = 0;
    this.friend_position = createVector(0, 0);
    this.friend_velocity = createVector(0, 0);

    // Check all boids, ignore those not close enough
    for (let other of boids) {
      if (this == other) continue;

      let v = p5.Vector.sub(other.position, this.position).normalize();
      let d = v.mag();
      if (d > params.visionDistance) continue;

      // Add separation force
      this.separation_force.add(
        p5.Vector.mult(v, -1 * d / params.visionDistance * params.separationForce)
      );

      // Alignment and cohesion
      this.friend_count += 1;
      this.friend_position.add(other.position);
      this.friend_velocity.add(other.velocity);
    }

    this.velocity.add(p5.Vector.mult(this.separation_force, 0.1));

    if (this.friend_count > 0) {
      // Alignment force, move towards local heading
      this.friend_velocity.mult(1 / this.friend_count);
      this.alignment_force = p5.Vector.mult(
        this.friend_velocity,
        params.alignmentForce
      );
      this.velocity.add(p5.Vector.mult(this.alignment_force, 0.1));

      // Cohesion force, move towards center of local group
      this.friend_position.mult(1 / this.friend_count);
      this.cohesion_force = p5.Vector.mult(
        p5.Vector.sub(this.friend_position, this.position).normalize(),
        params.cohesionForce
      );
      this.velocity.add(p5.Vector.mult(this.cohesion_force, 0.1));
    }

    // Clamp to maximum speed
    if (this.velocity.mag() > params.maxSpeed) {
      this.velocity = this.velocity.normalize().mult(params.maxSpeed);
    }

    // Update position based on current velocity
    this.position = this.position.add(this.velocity);

    if (this.position.x < 0) {
      this.position.x = 0;
      this.velocity.x = abs(this.velocity.x);
    }

    if (this.position.x > width) {
      this.position.x = width;
      this.velocity.x = -1 * abs(this.velocity.x);
    }

    if (this.position.y < 0) {
      this.position.y = 0;
      this.velocity.y = abs(this.velocity.y);
    }

    if (this.position.y > width) {
      this.position.y = height;
      this.velocity.y = -1 * abs(this.velocity.y);
    }
  }

  draw() {
    stroke(0);
    circle(this.position.x, this.position.y, 5);

    if (params.debug) {
      stroke(255, 0, 0);
      line(
        this.position.x,
        this.position.y,
        this.position.x + 10.0 * this.separation_force.x,
        this.position.y + 10.0 * this.separation_force.y
      );

      stroke(0, 255, 0);
      line(
        this.position.x,
        this.position.y,
        this.position.x + 10.0 * this.alignment_force.x,
        this.position.y + 10.0 * this.alignment_force.y
      );

      stroke(0, 0, 255);
      line(
        this.position.x,
        this.position.y,
        this.position.x + 10.0 * this.cohesion_force.x,
        this.position.y + 10.0 * this.cohesion_force.y
      );
    }
  }
}

function setup() {
  params.noiseForce = random() / 5.0;
  params.wallAvoidanceForce = random() / 5.0;
  params.separationForce = random() / 5.0;
  params.alignmentForce = random() / 5.0;
  params.cohesionForce = random() / 5.0;

  createCanvas(400, 400);

  boids = [];
  for (let i = 0; i < params.count; i++) {
    boids.push(new Boid());
  }

  gui = createGuiPanel("params");
  gui.addObject(params);
  gui.setPosition(420, 0);

  background(255);
}

function draw() {
  if (params.drawBackground) {
    background(255);
  }

  for (let boid of boids) {
    boid.update();
  }

  for (let boid of boids) {
    boid.draw();
  }
}
{{</p5js>}}

{{< taxonomy-list "series" "Genuary 2023" >}}

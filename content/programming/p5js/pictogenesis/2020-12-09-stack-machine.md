---
title: "Pictogenesis: Stack Machine"
date: 2020-12-09
series:
- Pictogenesis
programming/topics:
- Cellular Automata
- Generative Art
- Procedural Content
- p5js
programming/languages:
- JavaScript
---
Okay, enough with [register machines]({{< ref "2020-11-24-register-machine" >}}). Let's make something new. This time, a stack based machine!

Rather than keeping it's memory in a series of memory cells, there will be a single stack of values. All functions can `pop` values from the top of the stack or `push` them back on. I will add the ability to `read` the X/Y value and directly `write` R/G/B, but you can't write to the former or read from the latter, so you can't use them as registers. Let's see what that looks like!

<!--more-->

The first thing I want to do is add a handful of new instructions that don't really make as much sense in the register machine, but do in a stack context:

```javascript
const stackInstructions = instructions.concat([
  // Functions to read/write X/Y/R/G/B (also on the stack)
  {name: "readX", function: function() { return this.x;}},
  {name: "readY", function: function() { return this.y;}},
  {name: "writeR", function: function(v) { this.r = v; }},
  {name: "writeG", function: function(v) { this.g = v; }},
  {name: "writeB", function: function(v) { this.b = v; }},

  // Duplicate the top element of the stack
  {
    name: "dup",
    function: function(x) {
      this.stack.push(x);
      this.stack.push(x);
    }
  },
]);
```

Here I'm actually getting a bit more tricky. I can't use the `() => ...` syntax, because `this` behaves differently than when using the `function` syntax (even with apply). Specifically, with an arrow function, `this` is still set to the context the function was defined in. But now, I can actually pass `this` in and mess with variables on that object:

```javascript
var result = command.function.apply(this, args);
```

Doing this, I'm passing the `this` of the `run` function into the `function()` in the `instructions` object as `this`. That's one of the things that Javascript both does well and can really bite if you get too fancy (which I'm often guilty of).

That's most of it, so let's check out the demo!

{{< p5js-tab "sketch.js" >}}
let gui;
let params = {
  genomeSize: 30,
  genomeSizeMin: 10,
  genomeSizeMax: 1000,
  modeCall: ["keep", "clamp", "wrap"],
  modeEnd: ["clamp", "wrap"],
  renderPerFrame: 100,
  renderPerFrameMax: 1000,
  noise: 10,
  noiseMin: 0.01,
  noiseMax: 100,
  noiseStep: 0.01,
};

let g, p;
let rendering = true,
  renderingX = 0,
  renderingY = 0;
let code;

function resetRendering() {
  background(0);
  rendering = false;
  renderingX = 0;
  renderingY = 0;
}

function updateP(kls) {
  if (kls) {
    p = new kls(g);
  } else {
    p = new p.constructor(g);
  }
  code.value(p.toString());
  resetRendering();
  rendering = true;
}

// Helper function to index an array by a real number
gendex = (arr, id) => arr[int(arr.length * id)];

function setup() {
  createCanvas(400, 400);
  gui = createGuiPanel();
  gui.addObject(params);
  gui.setPosition(420, 0);

  background(0);

  g = new Genome(params.genomeSize);
  p = new StackMachine(g);

  let divMachine = createDiv("machines");
  
  divMachine.child(createButton("stack").mousePressed(() => {
    g = new Genome(params.genomeSize);
    updateP(StackMachine);
  }));

  let divMutations = createDiv("mutations");

  divMutations.child(createButton("point").mousePressed(() => {
    g.mutatePoint();
    updateP();
  }));

  divMutations.child(createButton("insert").mousePressed(() => {
    g.mutateInsertion();
    updateP();
  }));

  divMutations.child(createButton("delete").mousePressed(() => {
    g.mutateDeletion();
    updateP();
  }));

  divMutations.child(createButton("duplicate").mousePressed(() => {
    g.mutateDuplication();
    updateP();
  }));

  let divControl = createDiv("control");

  divControl.child(createButton("rerender").mousePressed(() => {
    resetRendering();
    rendering = true;
  }));

  let block = createElement('div');
  code = createElement('textarea');
  code.style('width', '400px');
  code.style('height', '400px');
  code.value(p.toString());
  block.child(code);
}

function draw() {
  if (rendering) {
    let f = (v) => v;
    if (params.modeEnd === "clamp") {
      f = (v) => constrain(v, 0, 1);
    } else if (params.modeEnd === "wrap") {
      f = (v) => v % 1.0;
    }

    for (var i = 0; i < params.renderPerFrame; i++) {
      let c = p.run(1.0 * renderingX / width, 1.0 * renderingY / height);
      c = c.map((el) => int(255 * f(el)));

      fill(c);
      noStroke();
      rect(renderingX, renderingY, 1, 1);

      renderingX++;
      if (renderingX >= width) {
        renderingX = 0;
        renderingY++;
      }
      if (renderingY >= height) {
        rendering = false;
      }
    }
  }
}
{{< /p5js-tab >}}

{{< p5js-tab "ops.js" >}}
const instructions = [
  // Basic math
  {name: "id", function: (x) => x},
  {name: "add", function: (x, y) => x + y},
  {name: "sub", function: (x, y) => x - y},
  {name: "mul", function: (x, y) => x * y},
  {name: "div", function: (x, y) => x / y},
  {name: "mod", function: (x, y) => x % y},
  {name: "max", function: (x, y) => Math.max(x, y)},
  {name: "min", function: (x, y) => Math.min(x, y)},
  {name: "abs", function: (x) => Math.abs(x)},
  {name: "inv", function: (x) => 1 / x},
  {name: "invsub", function: (x) => 1 - x},
  {name: "neg", function: (x) => -x},
  {name: "sin", function: (x) => Math.sin(x)},
  {name: "exp", function: (x) => Math.exp(x)},
  {name: "log", function: (x) => Math.log(x)},
  {name: "sqrt", function: (x) => Math.sqrt(x)},
  
  // Polar coordinate conversions
  {name: "polR", function: (x, y) => Math.sqrt(x * x + y * y)},
  {name: "polT", function: (x, y) => Math.atan2(x, y)},
  
  // Constants
  {name: "ZERO", function: () => 0},
  {name: "ONE", function: () => 1},
  
  // Conditionals
  {name: "zero?", function: (c, t, f) => c === 0 ? t : f},
  {name: "equal?", function: (a, b, t, f) => a === b ? t : f},
  {name: "gt?", function: (a, b, t, f) => a > b ? t : f},
  
  // Perlin noise
  {name: "noise1", function: (x) => noise(params.noise * x)},
  {name: "noise2", function: (x, y) => noise(params.noise * x, params.noise * y)},
];

const stackInstructions = instructions.concat([
  // Functions to read/write X/Y/R/G/B (also on the stack)
  {name: "readX", function: function() { return this.x;}},
  {name: "readY", function: function() { return this.y;}},
  {name: "writeR", function: function(v) { this.r = v; }},
  {name: "writeG", function: function(v) { this.g = v; }},
  {name: "writeB", function: function(v) { this.b = v; }},

  // Duplicate the top element of the stack
  {
    name: "dup",
    function: function(x) {
      this.stack.push(x);
      this.stack.push(x);
    }
  },
]);
{{< /p5js-tab >}}

{{< p5js-tab "stack.js" >}}
class StackMachine {
  constructor(genome) {
    this.program = [];
    for (var i = 0; i < genome.data.length;) {
      this.program.push(gendex(stackInstructions, genome.data[i++]));
    }
  }

  // Push x,y; pop r,g,b (if they weren't written)
  run(x, y) {
    // Store x/y/r/g/b on object for read/write
    this.x = x;
    this.y = y;

    this.stack = [];
    this.r = undefined;
    this.g = undefined;
    this.b = undefined;

    this.stack.push(x);
    this.stack.push(y);

    for (var command of this.program) {
      // Collect parameters by popping
      var args = [];
      while (args.length < command.function.length) {
        args.push(this.stack.pop() || 0);
      }

      // If we get a result, push it back onto the stack
      var result = command.function.apply(this, args);
      if (result !== undefined) {
        if (params.modeCall === "clamp") {
          result = constrain(result, 0, 1);
        } else if (params.modeCall == "wrap") {
          result = result % 1.0;
        }
        this.stack.push(result);
      }
    }

    return [
      this.r === undefined ? this.stack.pop() : this.r,
      this.g === undefined ? this.stack.pop() : this.g,
      this.b === undefined ? this.stack.pop() : this.b,
    ];
  }

  toString() {
    return this.program.map((cmd) => cmd.name).join('\n');
  }
}
{{< /p5js-tab >}}

{{< p5js-tab "genome.js" >}}
class Genome {
  constructor(length) {
    length = length || 10;
    this.data = [];
    while (this.data.length < length) {
      this.data.push(random());
    }
  }

  // Apply up to one of each kind of mutation to this genome
  mutate() {
    var index;

    if (random() < params.mutationRate_point) mutatePoint();
    if (random() < params.mutationRate_insertion) mutateInsertion();
    if (random() < params.mutationRate_deletion) mutateDeletion();
    if (random() < params.mutationRate_duplication) mutateDuplication();
  }

  mutatePoint() {
    var index = Math.floor(random() * this.data.length);
    this.data[index] = random();
  }

  mutateInsertion() {
    var index = Math.floor(random() * this.data.length);
    this.data.splice(index, 0, random());
  }


  mutateDeletion() {
    var index = Math.floor(random() * this.data.length);
    this.data.splice(index, 1);
  }


  mutateDuplication() {
    var index = Math.floor(random() * this.data.length);
    this.data.splice(index, 0, this.data[index]);
  }

  crossover(other) {
    var child = new Genome();
    var thisIndex = Math.floor(random() * this.data.length);
    var otherIndex = Math.floor(random() * other.data.length);

    child.data = this.data.slice(0, thisIndex).concat(other.data.slice(otherIndex));
    return child;
  }
}
{{< /p5js-tab >}}

{{< p5js width="600" height="900" >}}{{< /p5js >}}

Unfortunately, about the coolest image I got in my testing was this:

{{< figure src="/embeds/2020/pictogenesis-stack-curtains.png" >}}

Since most of the stack functions pop two variables, they are almost always grabbing `0` (when the stack is empty) and breaking things. So it goes. It was still interesting to write up.

I think next I'll work on transpiling this ([like I did for registers]({{< ref "2020-12-03-transpiling" >}})). And then on to some other type of function! {{< wikipedia "S-expressions" >}}? {{< wikipedia "Neural networks" >}}? Who knows!
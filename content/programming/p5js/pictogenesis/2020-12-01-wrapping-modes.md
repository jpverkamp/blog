---
title: "Pictogenesis: Wrapping Modes"
date: 2020-12-01
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
Now that I've got [register machines]({{< ref "2020-11-24-register-machine" >}}) working, one of the next ideas I had was to implement different wrapping modes. Currently, as it stands, `X` and `Y` are passed into the machine as floating point numbers from [0, 1] across the image and output is expected to be [0, 1] for each of `R`, `G`, and `B`. Any values that end up outside of that range, we truncate down to that range. But some of our mathematical functions (multiplication, exponentiation, negation, etc) tend to generate numbers way out of this range. But they don't have to!

<!--more-->

Specifically, I'm going to modify this to give a choice of options: 

* `keep`: The value is preserved, nothing is done
* `wrap`: The integer part of values is removed (1.37 -> 0.37, -1.37 -> 0.37)
* `clamp`: The old behavior: values less than 0 become 0, values greater than 1 become 1

Any one of these options can be applied either step by step or only at the end of the entire run (although `keep` at the end of the function doesn't make overmuch sense).

How to implement that? 

Per step: 

```javascript
// Run each command in the program
for (var command of this.program) {
    // Collect input registers (all but the first)
    let args = [];
    for (var param of command.params.slice(1)) {
        args.push(registers[param] || 0);
    }

    // Run the function, store in the first param
    var result = command.function.apply(this, args);
    result = isNaN(result) ? 0 : result;
    if (params.modeCall === "clamp") {
        result = constrain(result, 0, 1);
    } else if (params.modeCall == "wrap") {
        result = result % 1.0;
    }

    if (params.readonlyXY && (command.params[0] == 'X' || command.params[0] == 'Y')) {
    // Do nothing, trying to write to x/y
    } else {
        registers[command.params[0]] = result;
    }
}
```

It's pretty nice that modulus (`%`) does precisely what we need here!

```javascript
function draw() {
    if (rendering) {
        let f = (v) => v;
        if (params.modeCall === "clamp") {
            f = (v) => constrain(v, 0, 1);
        } else if (params.modeEnd === "wrap") {
            f = (v) => v % 1.0;
        }

        for (var i = 0; i < params.renderPerFrame; i++) {
            let c = p.run(1.0 * renderingX / width, 1.0 * renderingY / height);
            c = c.map((el) => int(255 * f(el)));

            ...
        }
    }
}
```

Check it out:

```javascript
function setup() {
  createCanvas(400, 400);
  gui = createGuiPanel();
  gui.addObject(params);
  gui.setPosition(420, 0);

  background(0);

  g = new Genome(params.genomeSize);
  p = new RegisterMachine(g);

  let block = createElement('div');
  code = createElement('textarea');
  code.style('width', '400px');
  code.style('height', '400px');
  code.value(p.toString());
}

function draw() {
  if (rendering) {
    for (var i = 0; i < params.renderPerFrame; i++) {
      let c = p.run(1.0 * renderingX / width, 1.0 * renderingY / height);
      c = c.map((el) => int(255 * constrain(el, 0, 1)));

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
```

Here's a big example of how this can work. The program

```
polT x b t1
sqrt g t0
mul g t0 b
polT t1 t0 x
abs t1 r
polR g y y
sqrt t0 t0
invsub t1 y
add r x x
```

With `modeCall: clamp, modeEnd: clamp` or `modeCall: keep, modeEnd: clamp`: 

{{< figure src="/embeds/2020/pictogenesis-register-clamp-clamp.png" >}}

With `modeCall: clamp, modeEnd: wrap`: 

{{< figure src="/embeds/2020/pictogenesis-register-clamp-wrap.png" >}}

With `modeCall: wrap, modeEnd: clamp`: 

{{< figure src="/embeds/2020/pictogenesis-register-wrap-clamp.png" >}}

Neat!

Here's the interactive one to play with:

{{< p5js width="600" height="900" >}}
let gui;
let params = {
  registerCount: 7,
  registerCountMin: 5, // x, y, ..., r, g, b
  registerCountMax: 30,
  genomeSize: 30,
  genomeSizeMin: 10,
  genomeSizeMax: 1000,
  modeCall: ["keep", "clamp", "wrap"],
  modeEnd: ["clamp", "wrap"],
  readonlyXY: true,
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
  p = new RegisterMachine(g);

  let divMachine = createDiv("machines");
  
  divMachine.child(createButton("registers").mousePressed(() => {
    g = new Genome(params.genomeSize);
    updateP(RegisterMachine);
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

  createButton("rerender").mousePressed(() => {
    resetRendering();
    rendering = true;
  });

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

class RegisterMachine {
  constructor(genome) {
    // Low registers are input, high output, middle are temporary
    let registers = ['x', 'y', 'r', 'g', 'b'];
    while (registers.length < params.registerCount) {
      registers.splice(2, 0, 't' + (registers.length - 5));
    }

    // Pull off one command for instruction and then as many args as needed
    this.program = [];
    for (var i = 0; i < genome.data.length;) {
      // Copy the instruction to add params
      let instruction = {
        ...gendex(instructions, genome.data[i++])
      };
      instruction.params = []
      for (var j = 0; j < instruction.function.length + 1; j++) {
        instruction.params.push(gendex(registers, genome.data[i++]));
      }
      this.program.push(instruction);
    }
  }

  run(x, y) {
    let registers = {
      x: x,
      y: y,
      r: 0,
      g: 0,
      b: 0
    };

    // Run each command in the program
    for (var command of this.program) {
      // Collect input registers (all but the first)
      let args = [];
      for (var param of command.params.slice(1)) {
        args.push(registers[param] || 0);
      }

      // Run the function, store in the first param
      var result = command.function.apply(this, args);
      result = isNaN(result) ? 0 : result;
      if (params.modeCall === "clamp") {
        result = constrain(result, 0, 1);
      } else if (params.modeCall == "wrap") {
        result = result % 1.0;
      }

      if (params.readonlyXY && (command.params[0] == 'x' || command.params[0] == 'y')) {
        // Do nothing, trying to write to x/y
      } else {
        registers[command.params[0]] = result;
      }
    }

    // Return the color from the r/g/b registers
    return [
      registers.r,
      registers.g,
      registers.b
    ];
  }

  toString() {
    return this.program.map((cmd) => cmd.name + ' ' + cmd.params.join(' ')).join('\n');
  }
}
{{< /p5js >}}
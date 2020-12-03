---
title: "Pictogenesis: Register Machine"
date: 2020-11-24
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
Okay. First [Pictogeneis]({{< ref "2020-11-23-the-idea" >}}) machine: a register based machine. Today we're going to create a very small language with a small number of registers that can read from the outside world, write colors, and act as temporary variables. 

Something like this:

```asm
gt? t0 b y x r
add g y x
abs b x
inv t0 g
add r g x
sub t0 b r
mul x r b
abs y x
```

{{< figure src="/embeds/2020/pictogenesis-register-1.png" >}}

In each case, the first argument is the output and the rest are inputs. So:

```
# gt? t0 b y x r
if (b > y) {
    t0 = x;
} else {
    t0 = r;
}
 
# add g y x
g = y + x

# abs b x
b = |x|
...
```

Where `x` and `y` are the input point x and y mapped to the range [0, 1]; `r`, `g`, `b` are the output colors in the same range and `t{n}` are temporary registers just used during the program. 

<!--more-->

First up, let's decide on some instructions for the language: 

```javascript
const instructions = [
  // Basic math
  {name: "id", function: (x) => x},
  {name: "add", function: (x, y) => x + y},
  {name: "sub", function: (x, y) => x - y},
  {name: "mul", function: (x, y) => x * y},
  {name: "div", function: (x, y) => x / y},
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
  {name: "clamp", function: (x) => constrain(x, 0, 1)},
  {name: "ceilfloor", function: (x) => x > 0.5 ? 1.0 : 0.0},

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
  {name: "gt.5?", function: (c, t, f) => c > 0.5 ? t : f},
  {name: "xgt.5?", function: function(t, f) { return this.x > 0.5 ? t : f; }},
  {name: "ygt.5?", function: function(t, f) { return this.y > 0.5 ? t : f; }},
];
```

I started with just basic `add`, `sub`, `mul`, `div`, but then it sort of grew from there. Every function I expect will be able to take a small number of paramaters (even zero) and output one value. For the most part, we can use Lambda functions to create nice inline functions, but in a few cases, I expanded to use the full `function` syntax, I'll get back to why in a bit. 

Next, let's take a genome (from [the first post]({{< ref "2020-11-23-the-idea" >}})) and turn it into a program:

```javascript
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
  ...
}
```

As we're assembling the program (really more disassembling I guess), we'll eat one real number for the opcode and then figure out how many parameters we need (`function.length` gives the arity of a function in JavaScript) and pull those off as well. 

Now, how do we run it? 

```javascript
class RegisterMachine {
  ...
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
      if (params.clampPerStep) result = constrain(result, 0, 1);

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
}
```

We'll initialize the registers and then run through each command. There are a few variables that I made for tweaking parameters that come up here:

* clampPerStep: Every register we write is clamped to the range [0, 1]
* readonlyXY: The registers `x` and `y` cannot be written to, only read from

Once we've run the entire program, output the colors. I'll get to the wrapper in a bit. 

Finally, we have a nice string representation for debugging:

```javascript
toString() {
  return this.program.map((cmd) => cmd.name + ' ' + cmd.params.join(' ')).join('\n');
}
```

That's what prints what I shared up at the top of the post. 

Okay, so what's the wrapper that actually turns this into code?

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

Originally I had the entire thing drawing in `setup`, but this code is ... slow. I'll work on that at some point, but we're doing very inefficient interpretation. Maybe I can compile it to JavaScript at some point. That'd be neat! 

So that's all we need for this, let's p5js it!

{{< p5js width="600" height="900" >}}
let gui;
let params = {
  registerCount: 7,
  registerCountMin: 5, // x, y, ..., r, g, b
  registerCountMax: 30,
  genomeSize: 30,
  genomeSizeMin: 10,
  genomeSizeMax: 1000,
  clampPerStap: false,
  readonlyXY: true,
  renderPerFrame: 100,
  renderPerFrameMax: 1000,
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

const instructions = [
  // Basic math
  {name: "id", function: (x) => x},
  {name: "add", function: (x, y) => x + y},
  {name: "sub", function: (x, y) => x - y},
  {name: "mul", function: (x, y) => x * y},
  {name: "div", function: (x, y) => x / y},
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
  {name: "clamp", function: (x) => constrain(x, 0, 1)},
  {name: "ceilfloor", function: (x) => x > 0.5 ? 1.0 : 0.0},

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
  {name: "gt.5?", function: (c, t, f) => c > 0.5 ? t : f},
  {name: "xgt.5?", function: function(t, f) { return this.x > 0.5 ? t : f; }},
  {name: "ygt.5?", function: function(t, f) { return this.y > 0.5 ? t : f; }},
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
      if (params.clampPerStep) result = constrain(result, 0, 1);

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
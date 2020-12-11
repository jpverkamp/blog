---
title: "Pictogenesis: Stack Transpiling"
date: 2020-12-11
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
Much like [transpiling register machines]({{< ref "2020-12-03-transpiling" >}}), now we have a chance to transpile [stack machines]({{< ref "2020-12-09-stack-machine" >}}). Unfortunately, it doesn't actually speed up the code nearly so much (the stack is just not as effective of a memory structure in this case), but it's still an interesting bit of code. 

In this case, we turn something like this:

```asm
invsub
polT
writeG
id
neg
zero?
sin
invsub
ZERO
inv
```

Into this:

```javascript
function(X, Y) {
  this.x = X;
  this.y = Y;

  this.stack = [];
  this.r = undefined;
  this.g = undefined;
  this.b = undefined;

  this.stack.push(X);
  this.stack.push(Y);

  var arg0 = 0;
  var arg1 = 0;
  var arg2 = 0;
  var result = 0;

  // invsub
  arg0 = this.stack.pop() || 0;
  result = 1 - arg0;
  result = result % 1.0;
  this.stack.push(result);

  // polT
  arg0 = this.stack.pop() || 0;
  arg1 = this.stack.pop() || 0;
  result = Math.atan2(arg0, arg1);
  result = result % 1.0;
  this.stack.push(result);

  // writeG
  arg0 = this.stack.pop() || 0;
  this.g = arg0;

  // id
  arg0 = this.stack.pop() || 0;
  result = arg0;
  result = result % 1.0;
  this.stack.push(result);

  // neg
  arg0 = this.stack.pop() || 0;
  result = -arg0;
  result = result % 1.0;
  this.stack.push(result);

  // zero?
  arg0 = this.stack.pop() || 0;
  arg1 = this.stack.pop() || 0;
  arg2 = this.stack.pop() || 0;
  result = arg0 === 0 ? arg1 : arg2;
  result = result % 1.0;
  this.stack.push(result);

  // sin
  arg0 = this.stack.pop() || 0;
  result = Math.sin(arg0);
  result = result % 1.0;
  this.stack.push(result);

  // invsub
  arg0 = this.stack.pop() || 0;
  result = 1 - arg0;
  result = result % 1.0;
  this.stack.push(result);

  // ZERO
  result = 0;
  result = result % 1.0;
  this.stack.push(result);

  // inv
  arg0 = this.stack.pop() || 0;
  result = 1 / arg0;
  result = result % 1.0;
  this.stack.push(result);


  return [
    this.r === undefined ? this.stack.pop() || 0 : this.r,
    this.g === undefined ? this.stack.pop() || 0 : this.g,
    this.b === undefined ? this.stack.pop() || 0 : this.b,
  ];
}
```

<!--more-->

The code is not actually that much different for transpiling:

```javascript
transpile() {
    let patterns = [
      /^\((.*?)\) => (.*?)$/,
      /^function\((.*?)\) ({.*?})$/,
    ]

    let code = [
        `
this.run = function(X, Y) {
this.x = X;
this.y = Y;

this.stack = [];
this.r = undefined;
this.g = undefined;
this.b = undefined;

this.stack.push(X);
this.stack.push(Y);
`];
  
  // Find the maximum arity of any function
  var maxLength = 0;
  for (var command of this.program) {
    maxLength = Math.max(maxLength, command.function.length);
  }
  for (var i = 0; i < maxLength; i++) {
    code.push(`  var arg${i} = 0;`)
  }
  code.push(`  var result = 0;`)
  code.push('');

  for (command of this.program) {
    let f = command.function.toString();
    for (var pattern of patterns) {
      // Match each kind of function
      let parts = f.match(pattern);
      if (parts) {
        code.push(`  // ${command.name}`);

        // Pop the number of parameters we need
        for (var i = 0; i < command.function.length; i++) {
          code.push(`  arg${i} = this.stack.pop() || 0;`)
        }

        // Add the code
        var line = `  result = ${parts[2]};`;
        var noResult = false;
        if (parts[2].includes('{')) {
          if (parts[2].includes('return')) {
            line = parts[2].replace('return', 'result = ');
          } else {
            line = parts[2];
            noResult = true;
          } 
          line = '  ' + line.replace(/^{|}$/g, '').trim();
        }
        
        if (parts[1]) {
          parts[1].split(',').map((el, i) => {
            line = line.replaceAll(
              new RegExp("\\b" + el.trim() + "\\b", "g"),
              `arg${i}`
            );
          });
        }
        code.push(line);
        
        if (!noResult) {
          if (params.modeCall === "clamp") {
            code.push(`  result = result < 0 ? 0.0 : (result > 1 : 1.0);`);
          } else if (params.modeCall == "wrap") {
            code.push(`  result = result % 1.0;`);
          }
          code.push(`  this.stack.push(result);`);
        }
        code.push('');
      }
    }
  }

  code.push(`
return [
  this.r === undefined ? this.stack.pop() || 0 : this.r,
  this.g === undefined ? this.stack.pop() || 0 : this.g,
  this.b === undefined ? this.stack.pop() || 0 : this.b,
];
`);
  
  code.push('}');
  code = code.join('\n');
  eval(code);
}
```

It's a bit more complicated, because we have to deal with a few functions that `return` and some that don't. That's the bit in the middle with the `noResult` variable. If you don't do that, you end up pushing the previous result, which can have some interesting (but non desirable) results. 

Demo!

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

  divControl.child(createButton("transpile").mousePressed(() => {
    p.transpile();
    code.value(p.run.toString());
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
      this.r === undefined ? this.stack.pop() || 0 : this.r,
      this.g === undefined ? this.stack.pop() || 0 : this.g,
      this.b === undefined ? this.stack.pop() || 0 : this.b,
    ];
  }

  transpile() {
      let patterns = [
        /^\((.*?)\) => (.*?)$/,
        /^function\((.*?)\) ({.*?})$/,
      ]

      let code = [
          `
this.run = function(X, Y) {
  this.x = X;
  this.y = Y;

  this.stack = [];
  this.r = undefined;
  this.g = undefined;
  this.b = undefined;

  this.stack.push(X);
  this.stack.push(Y);
`];
    
    // Find the maximum arity of any function
    var maxLength = 0;
    for (var command of this.program) {
      maxLength = Math.max(maxLength, command.function.length);
    }
    for (var i = 0; i < maxLength; i++) {
      code.push(`  var arg${i} = 0;`)
    }
    code.push(`  var result = 0;`)
    code.push('');

    for (command of this.program) {
      let f = command.function.toString();
      for (var pattern of patterns) {
        // Match each kind of function
        let parts = f.match(pattern);
        if (parts) {
          code.push(`  // ${command.name}`);

          // Pop the number of parameters we need
          for (var i = 0; i < command.function.length; i++) {
            code.push(`  arg${i} = this.stack.pop() || 0;`)
          }

          // Add the code
          var line = `  result = ${parts[2]};`;
          var noResult = false;
          if (parts[2].includes('{')) {
            if (parts[2].includes('return')) {
              line = parts[2].replace('return', 'result = ');
            } else {
              line = parts[2];
              noResult = true;
            } 
            line = '  ' + line.replace(/^{|}$/g, '').trim();
          }
          
          if (parts[1]) {
            parts[1].split(',').map((el, i) => {
              line = line.replaceAll(
                new RegExp("\\b" + el.trim() + "\\b", "g"),
                `arg${i}`
              );
            });
          }
          code.push(line);
          
          if (!noResult) {
            if (params.modeCall === "clamp") {
              code.push(`  result = result < 0 ? 0.0 : (result > 1 : 1.0);`);
            } else if (params.modeCall == "wrap") {
              code.push(`  result = result % 1.0;`);
            }
            code.push(`  this.stack.push(result);`);
          }
          code.push('');
        }
      }
    }

    code.push(`
  return [
    this.r === undefined ? this.stack.pop() || 0 : this.r,
    this.g === undefined ? this.stack.pop() || 0 : this.g,
    this.b === undefined ? this.stack.pop() || 0 : this.b,
  ];
`);
    
    code.push('}');
    code = code.join('\n');
    eval(code);
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

I've actually gotten a few much cooler images from stack machines now:

{{< figure src="/embeds/2020/pictogenesis-molten.png" >}}

{{< figure src="/embeds/2020/pictogenesis-muscle.png" >}}

So they're in the running! It would be interesting to take the genome for one machine and directly convert it to the other. I expect there will be no relation at all, but still interesting.
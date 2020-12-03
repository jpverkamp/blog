---
title: "Pictogenesis: Transpiling"
date: 2020-12-03
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
Okay. That is *slow*... Let's make it faster!

So the main problem we have is that we're interpreting the code. For every single pixel, for every line of code, we're doing a few housekeeping things and making at least one function call. For a 400x400 image with just 10 lines of code, that's 1.6M function calls. Like I said, *slow*.

So let's make it faster!

My first idea? {{< wikipedia "Transpile" >}} it to Javascript!

<!--more-->

Specifically, my goal is to turn this:

```asm
ZERO B
ONE B
max B T0 Y
abs B G
add B B X
inv Y T0
abs T1 T1
polR Y T1 G
sqrt G B
max G X X
```

Into this:

```javascript
function(X, Y) {
  var T1,T0,R,G,B;
  T1 = T0 = R = G = B = 0;
  B = 0;
  B = 1;
  B = Math.max(T0, Y);
  B = Math.abs(G);
  B = B + X;
  // Y = 1 / T0;
  T1 = Math.abs(T1);
  // Y = Math.sqrt(T1 * T1 + G * G);
  G = Math.sqrt(B);
  G = Math.max(X, X);
  return [R, G, B];
}
```

Let's do it!

So, for better or for worse, our code is stored as functions. But one thing that JavaScript does is give us access to the source code for functions with `toString()`!

```javascript
const instructions = [
  // Basic math
  {name: "id", function: (x) => x},
  {name: "add", function: (x, y) => x + y},
  {name: "sub", function: (x, y) => x - y},
  ...
];

>> instructions[1].function.toString();
"(x, y) => x + y"
```

We can then 'parse' that with a {{< wikipedia "regular expression" >}}:

```javascript
>> instructions[1].function.toString().match(/^\((.*?)\) => (.*?)$/)
Array(3) [
  "(x, y) => x + y",
  "x, y",
  "x + y"
]
```

Now that is interesting. We have a list of parameters and the actual code. But how do we match that to the registers (in our first machine)? Well, for each parameter in the 'function' (x and y in this example), we need to map those to the registers in the assembled code:

```javascript
let f = command.function.toString();
let out = command.params[0];
let parts = f.match(pattern);

// Directly convert it to code
var line = `  ${out} = ${parts[2]};`;

// We have parameters, replace those in the code
if (parts[1]) {
  parts[1].split(',').map((el, i) => {
    line = line.replaceAll(
      new RegExp("\\b" + el.trim() + "\\b", "g"),
      command.params[i + 1]
    );
  });
}
```

This also adds the `out` variable as a prefix.

In this case, `\b` is fixing the first problem I ran into: what if you're calling functions that use the letters of variable names. For example, `max` has an `x` in it. But `\b` is a special character that means 'word boundry'. It doesn't match anything by itself, but it does mean that the variable has to be an entire 'word', not part of one. 

So now we've gone from `add t1 x y` to `t1 = x + y`. Or does it?

Well, there's actually another bug here. If I have the same variable in the function definition (`add(x, y)`) and the registers (`x` and `y` are registers), then they can collide in weird ways. I thought about doing two passes, writing to temporary variables that wouldn't collide, but in the end, I just ended up using case. Registers are all named with capital letters, while the functions in `instructions` use lower case. In that way `x` and `X` are different. 

So for a full function (including parsing functions that have the `function(x,y) { ... }` syntax), [wrapping modes]({{< ref "2020-12-01-wrapping-modes" >}}), and `readonlyXY`:

```javascript
transpile() {
  let patterns = [
    /^\((.*?)\) => (.*?)$/,
    /^function\((.*?)\) {(.*?)}$/,
  ]

  let registers = ['X', 'Y', 'R', 'G', 'B'];
  while (registers.length < params.registerCount) {
    registers.splice(2, 0, 'T' + (registers.length - 5));
  }
  registers = registers.slice(2);
  let code = [
    'this.run = function(X, Y) {',
    '  var ' + registers.join(',') + ';',
    '  ' + registers.join(' = ') + ' = 0;'
  ];

  for (var command of this.program) {
    let f = command.function.toString();
    for (var pattern of patterns) {
      let out = command.params[0];

      // Match each kind of function
      let parts = f.match(pattern);
      if (parts) {
        // Directly convert it to code
        var line = `  ${out} = ${parts[2]};`;
        
        // We have parameters, replace those in the code
        if (parts[1]) {
          parts[1].split(',').map((el, i) => {
            line = line.replaceAll(
              new RegExp("\\b" + el.trim() + "\\b", "g"),
              command.params[i + 1]
            );
          });
        }
        
        // When x/y are readonly, comment out the line
        // Otherwise, apply any end of call functions
        if (params.readonlyXY && (out == 'X' || out == 'Y')) {
          code.push('  // ' + line.trim());
        } else {
          code.push(line);
          if (params.modeCall == "clamp") {
            code.push(`  ${out} = ${out} < 0 ? 0 : (${out} > 1 ? 1 : ${out});`);
          } else if (params.modeCall == "wrap") {
            code.push(`  ${out} %= 1.0;`);
          }
        }
      }
    }
  }
  code.push('  return [R, G, B];')
  code.push('}');
  code = code.join('\n');

  eval(code);
}
```

And yup. At the end I use `eval`. It's [evil](https://www.google.com/search?&q=eval+is+evil) afterall. :D But it works perfectly well here, so ONWARDS! Once I transpile, I replace the previous `run` function. 

And man is it faster. Several times faster.

I haven't actually timed it, but try it out, you can see it for yourself (try setting the `genomeSize` to 1000, that really crawls in the old model):

(Note: Click `register` to generate a new image, and then `transpile` to transpile and re-render it.)

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
    let registers = ['X', 'Y', 'R', 'G', 'B'];
    while (registers.length < params.registerCount) {
      registers.splice(2, 0, 'T' + (registers.length - 5));
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

  run(X, Y) {
    let registers = {
      X: X,
      Y: Y,
      R: 0,
      G: 0,
      B: 0
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

      if (params.readonlyXY && (command.params[0] == 'X' || command.params[0] == 'Y')) {
        // Do nothing, trying to write to x/y
      } else {
        registers[command.params[0]] = result;
      }
    }

    // Return the color from the r/g/b registers
    return [
      registers.R,
      registers.G,
      registers.B
    ];
  }

  transpile() {
    let patterns = [
      /^\((.*?)\) => (.*?)$/,
      /^function\((.*?)\) {(.*?)}$/,
    ]

    let registers = ['X', 'Y', 'R', 'G', 'B'];
    while (registers.length < params.registerCount) {
      registers.splice(2, 0, 'T' + (registers.length - 5));
    }
    registers = registers.slice(2);
    let code = [
      'this.run = function(X, Y) {',
      '  var ' + registers.join(',') + ';',
      '  ' + registers.join(' = ') + ' = 0;'
    ];

    for (var command of this.program) {
      let f = command.function.toString();
      for (var pattern of patterns) {
        let out = command.params[0];

        // Match each kind of function
        let parts = f.match(pattern);
        if (parts) {
          // Directly convert it to code
          var line = `  ${out} = ${parts[2]};`;
          
          // We have parameters, replace those in the code
          if (parts[1]) {
            parts[1].split(',').map((el, i) => {
              line = line.replaceAll(
                new RegExp("\\b" + el.trim() + "\\b", "g"),
                command.params[i + 1]
              );
            });
          }
          
          // When x/y are readonly, comment out the line
          // Otherwise, apply any end of call functions
          if (params.readonlyXY && (out == 'X' || out == 'Y')) {
            code.push('  // ' + line.trim());
          } else {
            code.push(line);
            if (params.modeCall == "clamp") {
              code.push(`  ${out} = ${out} < 0 ? 0 : (${out} > 1 ? 1 : ${out});`);
            } else if (params.modeCall == "wrap") {
              code.push(`  ${out} %= 1.0;`);
            }
          }
        }
      }
    }
    code.push('  return [R, G, B];')
    code.push('}');
    code = code.join('\n');

    eval(code);
  }

  toString() {
    return this.program.map((cmd) => cmd.name + ' ' + cmd.params.join(' ')).join('\n');
  }
}
{{< /p5js >}}

While I was testing it, I came up with these images:

{{< figure src="/embeds/2020/pictogenesis-awesome-noise.png" >}}
{{< figure src="/embeds/2020/pictogenesis-awesome-noise2.png" >}}

Adding `noise` was a good choice! And you can get some really complicated images with 1000 gene programs... now that you can actually run them in a reasonable span of time. 
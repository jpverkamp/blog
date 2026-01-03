---
title: "Runelang: Evaluation"
date: 2022-07-16
programming/languages:
- Javascript
programming/topics:
- Small Scripts
- Generative Art
- Procedural Content
series:
- Runelang in the Browser
---
As they say, life is what happens when you're making other plans. But I'm back, so let's talk some more about [Runelang](/series/runelang-in-the-browser/). In the interest of not dragging on months without finishing, we're going to go ahead and push through the rest of the project. Onward!

<!--more-->

So far, we've [[Runelang: Language Specification|described the language]](), [[Runelang: The Lexer|wrote a lexer]](), and parsed both [[Runelang: The Parser (Part 1)|nodes, parameters, and lists]]() and [[Runelang: The Parser (Part 2: Expressions)|more complicated expressions, literals, and an expression sublanguage]](). 

Next up? Evaluation!

To do that, we need a few things:

* An environment (so we can handle variables passed to function calls, along with a top level `define` syntax)

* `evaluate*` functions for each kind of object we might have parsed (group, terminal, node, stacker, literal, list, ... you get the idea)

## Table of Contents

{{% toc %}}

## The environment

The goal of the environment is to properly handle [[wiki:lexical scope]](). If we have code like this:

```text
define test(x) {
  radial(scale: 1/8) [
    text(x)
    for x in 1..x
  ]
}

rune {
  test(5)
}
```

It should *work*. We should be able to take `5`, assign it to `x` when we call `test`, and then within the radial, assign an inner `x` the values 1 up to `x = 5`.

So to do that, we're going to store a series of objects, each of which can store their own data (as a map), and a pointer to the parent. If you `get` / lookup a value, look in the current environment. So long as you don't find it, ask the parent, then it's parent, and so on. Likewise, if you set a variable, start at the current scope and move up the ladder to set a value. That's why the `for x in 1..x` works. The outermost `x` is being written to, but the `x=5` passed into `test` isn't modified. 

To make this all work:

```javascript
class Environment {
  constructor(parent = null) {
    this.parent = parent
    this.data = {}
  }

  set(key, value) {
    this.data[key] = value
  }

  get(key) {
    if (key in this.data) {
      return this.data[key]
    }

    if (this.parent) {
      return this.parent.get(key)
    }
  }

  extend() {
    return new Environment(this)
  }
}
```

Not much, but it does what we need!

## The root of evaluation

Okay, now that's out of the way, let's start with the base evaluation function `evaluate`:

```javascript
export default function evaluate(node, environment = null, asNext = false) {
  let id = IDGenerator.next().value

  // Construct base environment
  if (environment === null) {
    log.debug("Building base environment")
    environment = new Environment()
    for (let type in GLOBALS) {
      for (let name in GLOBALS[type]) {
        log.debug(`Loading global ${type}.${name}:\n---\n${GLOBALS[type][name].toString()}\n---`)
        environment.set(name, { type, value: new Callable(GLOBALS[type][name]) })
        log.debug("Resulting callable:", environment.get(name))
      }
    }
    environment = environment.extend()
    log.debug("Finished building base environment")
  }

  if (node === undefined || node === null) return null

  // We've already evaluated this node (for example as a .next)
  if (node.evaluated && !asNext) {
    log.debug("Skipping evaluation, already evaluated", node)
    return null
  } else {
    let formatNode = (node) => {
      return JSON.stringify(node, (k, v) => (["body"].includes(k) ? "<removed>" : v))
    }

    let formatEnvironment = (environment) => {
      if (environment.parent === null) {
        return `<GLOBAL>`
      } else {
        return `<${JSON.stringify(environment.data)} extends ${formatEnvironment(environment.parent)}>`
      }
    }

    log.info(`[${id}] Evaluating ${formatNode(node)} in ${formatEnvironment(environment)}`, node)
  }

  let result

  // Evaluate a node group by evaluating each and concating results
  if (node.type === "group") {
    result = evaluateGroup(node, environment)
  }

  // Define a new callable in the environment
  else if (node.type === "define") {
    result = evaluateDefine(node, environment)
  }

  // Get the value for a node type
  else if (node.type === "node") {
    result = evaluateNode(node, environment)
  }

  // A parameter list
  else if (node.type === "params") {
    result = evaluateParams(node, environment)
  }

  // An expression
  else if (node.type === "expression") {
    result = evaluateExpression(node, environment)
  }

  // Different kinds of lists
  else if (node.type === "list") {
    result = evaluateList(node, environment)
  }

  // Get the value for a parameter list
  else {
    log.error("Runtime error, unknown node type to evaluate", node, node)
  }

  log.info(`[${id}] Returning: ${result}`)
  return result
}
```

A few things this does:

* Construct the base environment by defining all of the functions that are in the `GLOBALS` array (see the next section)

* Evaluate each node in turn. This is a bit tricky, since we have the syntax like this: `scale(0.9) circle`. That should be equivalent to `scale(0.9) { circle }`, so we want to evaluate the `circle` as a child of `scale` and then *not again* as the next node in the list. That's what the `node.evaluate && !asNext` chunk does. 

* Debugging. That's what `IDGenerator` is. In essence, it's a JavaScript generator function that will return the next integer so we can keep track of each invocation when recurring. 

* Dispatch to specific functions, such as `evaluateGroup` etc. We'll come back to those.

## Globals

As a quick aside, a discussion about how globals are handled. You can see the full code for them [here](https://github.com/jpverkamp/runelang/blob/07c8fbb2cb9ef52114447d5e366dbcb172ad20dd/runelang/constants.js), but the idea is something like this:

```javascript
const GLOBALS = {
  // Terminals do not have any children, they just generate content
  terminal: {
    line: (min = 0, max = 1) => `<line x1="0" y1="${100.0 * min}" x2="0" y2="${100.0 * max}" />`,
    circle: () => '<circle cx="0" cy="0" r="100" />',
    ...
  },
  // Modifiers take a child and apply their changes to them
  modifier: {
    ...
    scale: (x, y) => (child) => `<g data-source="scale(${y ? [x, y] : x})" transform="scale(${x}, ${y ? y : x})">${child.eval()}</g>`,
    fill: (color) => (child) => `<g data-source="fill(${color})" fill="${color}">${child.eval()}</g>`,
    ...
  }, 
    // Stackers apply to a list of children and organize them in various ways
  stacker: {
    stack: () => (children) => `<g data-source="stack()">${children.join(" ")}</g>`,
    radial:
      (scale = 1, offset = 1, rotate = false) =>
      (children) => {
        let points = onCircle(children.length)
        let nodes = []
        for (let i = 0; i < children.length; i++) {
          let [x, y] = points[i]
          x *= offset
          y *= offset

          let transforms = [`translate(${x}, ${y})`, `scale(${scale})`]
          if (rotate) {
            transforms.push(`rotate(${(360.0 * i) / children.length})`)
          }

          nodes.push(`<g data-source="radial(${scale}, ${offset}, ${rotate})" data-child="${i}" transform="${transforms.join(" ")}">${children[i]}</g>`)
        }
        return `<g data-source="radial(${scale}, ${offset}, ${rotate})">${nodes.join(" ")}</g>`
      },
      ...
  },
```

For each of the different kind of functions, you will have a different kind of inline function.

For terminals (with no children), they can take arbitrary parameters and render that to SVG. So `line(0.5)` becomes a line from `0,0` to `50,0` (everything assumes a unit circle of 100 so the numbers don't end up too tiny too fast), `circle` becomes a unit circle. 

For modifiers, you have base parameters (the same as terminals) first, then you have a single child node that you're modifying. So something like `scale(0.9) circle` would pass `0.9` as `x` and `circle` as the child node. It will render some wrapper (usually) and then evaluate the child in turn. 

For stackers, you do the same thing, but this time with a list of children (either literal or with one of the list constructors). Either way, the contents of the child nodes will already have been evaluated at this point, but you can wrap them with all sorts of interesting things. For example, in the `radial` above which will arrange the list of child nodes in a circle. 

If you want any more complicated behavior, this is where you'd put it, but as I've mentioned before, if you just want to combine this primitives, you can do so with defines. 

## Turning globals (and other things) into callable objects

But these functions alone aren't enough, we need a bit more magic to make them 'callable':

```javascript
class Callable {
  constructor(f) {
    if (f === undefined) return

    this.f = f
    this.defaults = []

    let match = f.toString().match(/\((.*?)\)/)
    if (match === null) {
      log.error(`could not find params in ${f.toString()}`, null, f)
    }

    for (let arg of match[1].split(",")) {
      if (arg.includes("=")) {
        let [key, def] = arg.split("=")
        this.defaults.push([key.trim(), def.trim()])
      } else {
        this.defaults.push([arg.trim(), undefined])
      }
    }
  }

  call(params, environment) {
    // this.defaults comes from the definition of the function

    // params comes from the call
    //    params might contain zero, one, or both of args and kwargs
    //    params duplicates args in both args and kwargs, if it's in both it's passed as a kwarg

    // argsToCall is what we'll send to the internal function with apply

    let args = params?.args
    let kwargs = params?.kwargs

    let passedArgsCount = 0
    if (args) passedArgsCount += args.length
    if (kwargs) passedArgsCount -= Object.keys(kwargs).length

    let argsToCall = []
    for (let i = 0; i < this.defaults.length; i++) {
      let [name, defaultValue] = this.defaults[i]

      // Try to get each value from args, kwargs, then default

      if (args && i < passedArgsCount) {
        if (kwargs && args[i].asName && args[i].asName in kwargs) {
          argsToCall.push(evaluate(kwargs[args[i].asName], environment))
        } else {
          argsToCall.push(evaluate(args[i], environment))
        }
      } else if (kwargs && name in kwargs) {
        argsToCall.push(evaluate(kwargs[name], environment))
      } else {
        argsToCall.push(defaultValue)
      }
    }
    return this.f.apply(this, argsToCall)
  }
}
```

First, when we construct it, we're going to dynamically pull in the parameter list. This really should be something that has a better way to do it built into JavaScript, but for better or for worse, we're literally going to turn the function into a string of the original code (with `toString` and use regex to parse the first parameter list, parsing that (looking for defaults)). It's ugly, but it works. 

After that, the `call` function will take in any parameters plus the current environment and then use any defaults from above to fill in args that are missing before finally calling `this.f.apply` to actually call the wrapped function.

This is... more complicated than I wish it was, but at least the user never really needs to use it. Just me!

## Evaluating groups

Okay, first we have `groups`. These are just collections of nodes that are being grouped together. For example, if you want something like `scale(0.9) { circle star }`, you want both the `circle` and the `star` to be scaled, so you'll evaluate the two as a group. 

```javascript
function evaluateGroup(node, environment) {
  let children = []
  for (let child of node.nodes) {
    let result = evaluate(child, environment)
    if (result !== null) children.push(result)
  }
  return children.join("")
}
```

## Evaluating nodes

Next up, the three types of nodes: terminals, modifiers, and stackers. They all work closely together, but there are a few differences to be mindful of.

So first the dispatcher:

```javascript
function evaluateNode(node, environment) {
  /* Special case for includes */
  // TODO: Better error handling
  if (node.identifier.text === "include") {
    let path = evaluate(node.params.args[0], environment)
    return include(path, environment)
  }

  let object = environment.get(node.identifier.text)
  if (!object) {
    log.error(`object ${node.identifier.text} is not defined`, node)
  }

  if (object.type === "terminal") {
    return evaluateTerminalNode(object, node, environment)
  } else if (object.type == "modifier") {
    return evaluateModifierNode(object, node, environment)
  } else if (object.type == "stacker") {
    return evaluateStackerNode(object, node, environment)
  } else if (object.type == "group") {
    return evaluateGroup(object, environment)
  } else {
    log.error("unknown object type", node, object)
  }
}
```

This also handles the one special case I have: `include` which only really works locally, but can include other files. Other than that, we'll just go for one of the kinds we have below (or group, which we've already mentioned). 

### Terminal nodes

In this case, it's just a straight function evaluation of the `callable` as defined above / in the globals.  

```javascript
function evaluateTerminalNode(object, node, environment) {
  if (node.body) {
    log.error("terminal should not have a body", node)
  }

  if (node.group) {
    log.error("terminal should not have a group", node)
  }

  return object.value.call(node.params, environment)
}
```

### Modifier nodes

Here we want to find and pass along a child node. This could either be a literal child or group (if we have the `{}` syntax) or just the next node in line if we don't. A modifier always has a child though. 

```javascript

function evaluateModifierNode(object, node, environment) {
  // If we have a group evaluate it as child, otherwise take the next node
  let child = null,
    asNext = false
  if (node.body) {
    if (node.body.type !== "group") {
      log.error("modifiers can only modify groups", node)
    }

    child = node.body
  } else if (node.next) {
    child = node.next
    asNext = true
    node.next.evaluated = true
  } else {
    log.error("modifiers must have a following group or node", node)
  }

  child.eval = (env = null) => evaluate(child, env || environment, asNext)

  return object.value.call(node.params, environment)(child)
}
```

In the end, we have the nested functions as I mentioned in globals. The first level is handled by the callable, but that will return the inner function that takes just the child. 

So for this:

```javascript
scale: (x, y) => (child) => `<g data-source="scale(${y ? [x, y] : x})" transform="scale(${x}, ${y ? y : x})">${child.eval()}</g>`,
```

The callable will parse the `(x, y)` and that's what `object.value.call` will handle and return the second function: `(child) => ...`. I hope that's clear? 

### Stacker nodes 

These work basically the same way as modifiers, except they can't have a implicit child node, they always have to be given a list of some sort:

```javascript
function evaluateStackerNode(object, node, environment) {
  // Stackers apply to the following list
  if (!node.list || node.body) {
    log.error("stackers can only modify lists", node)
  }

  let children = evaluate(node.list, environment)
  return object.value.call(node.params, environment)(children)
}
```

They still use the nested function approach though, this time passing first the `call` parameters and the list of `children`. 

## Evaluating lists

Okay, nodes are done, next up is the three kinds of lists: literal lists, for lists, and times lists. Each of them has slightly different behavior.

```javascript
function evaluateList(node, environment) {
  if (node.mode === "literal") {
    let result = []
    for (let childNode of node.nodes) {
      result.push(evaluate(childNode, environment))
    }
    return result
  } else if (node.mode === "for") {
    if (node.variable.type !== "identifier") {
      log.error(`for-list variable must be an identifier, got ${node.variable}`, node)
    }

    let variable = node.variable.text
    let iterable = evaluate(node.expression, environment)
    let forEnvironment = environment.extend()

    log.debug(`In for-loop, iterable is ${iterable}`, node)

    let result = []
    for (let eachValue of iterable) {
      log.debug(`In for-loop, setting ${variable} to ${eachValue}`, node)
      forEnvironment.set(variable, eachValue)
      result.push(evaluate(node.body, forEnvironment))
    }
    return result
  } else if (node.mode === "times") {
    let times = evaluate(node.expression, environment)
    if (typeof times !== "number") {
      log.error(`times-list must be a number, got ${times}`, node)
    }

    let result = []
    for (var i = 0; i < times; i++) {
      result.push(evaluate(node.body, environment))
    }
    return result
  } else {
    log.error(`unknown list mode ${node.mode}`, node)
  }
}
```

The literal list is basically the same thing as a `group`, but the difference comes in what you can pass them to. `groups` can be passed to `modifiers` (or used directly), while `lists` are passed to `stackers`. I'm not sure if the distinction is 100% necessary, but it did make it easier to reason about. 

For `for` lists we're going to extend the environment, since in each case, we're going to define a new variable, scoped just to the evaluation of the list. To do that, we'll evaluate the range-like object (see `expressions` below) and assign each value in turn as the `variable` and then evaluate the `node` with that value. 

For the `times` list, we do the same (evaluating the same body many times), but this time without a new variable/environment. Mostly useful for copying the same thing a few times without having to ignore a `for` loop and constructing a range every time. 

## Evaluating expressions

Now here's one of the big (and honestly more alien) bits of the code: expressions. Really, it's a language within a language, since at this point, we have an [[wiki:Reverse Polish Notation|RPN]]() expression to evaluate. 

```javascript
function evaluateExpression(node, environment) {
  log.debug(`Evaluating RPN`, node, node.rpn)

  let stack = []
  for (let el of node.rpn) {
    log.debug(`In RPN: Current stack`, node, { el, stack })

    if (el.type === "literal") {
      stack.push(el.value)
    } else if (el.type === "operator") {
      if (stack.length < 2) {
        log.error(`In RPN: tried to evaluate ${el} but needed two parameters`, node, { el, stack })
      }

      let right = stack.pop()
      let left = stack.pop()
      let f = EVAL_OPERATORS[el.value].f
      stack.push(f(left, right))
    } else if (el.type === "variable") {
      let key = el.value
      let value = environment.get(el.value)

      if (value !== undefined && value !== null) {
        stack.push(value)
      } else {
        log.error(`In RPN: failed to evaluate variable ${key} not defined`, node, { el, stack })
      }
    } else if (el.type === "function") {
      let args = []
      for (var i = 0; i < el.arity; i++) {
        args.unshift(stack.pop())
      }
      let result = el.value.apply(null, args)
      stack.push(result)
    } else {
      log.error(`In RPN: unknown type ${el}`, node, { el, stack })
    }
  }

  if (stack.length !== 1) {
    log.error(`In RPN: expressions must result in exactly one value, got ${stack}`, node, { el, stack })
  }

  return stack[0]
}
```

Really, the wikipedia article above does a good job explaining what's going on here, but the basic idea is this: we either have a literal--which we push onto a stack--or a function with a known arity. For functions, we pull as many params as we need off the stack, apply the function, and then push the result back onto the stack. 

Really, most of the work here was done in parsing, but we do have a few built in operators in the same [constants.js](https://github.com/jpverkamp/runelang/blob/07c8fbb2cb9ef52114447d5e366dbcb172ad20dd/runelang/constants.js) function mentioned earlier. Specifically, things like `chooseOne` and `chooseMany` can take 1 or 2 parameters respectively. And you can easily add more functions here to do all sorts of things. Randomness? Loading external data? External API access? Who knows!

## Evaluating defines

Okay, last, but certainly not least, we have `evaluateDefine`. This is a special syntax that lets you define your very own `terminal` or `modifier`. Unfortunately, I haven't yet figured out how to define custom `stackers` yet, but we'll see if we can yet. 

```javascript
function evaluateDefine(node, environment) {
  let name = node.identifier.text
  if (environment.get(name)) {
    log.error(`unable to redefine ${name}`, node.location, node)
  }

  let defaults = []
  if (node.params) {
    for (var i = 0; i < node.params.args.length; i++) {
      let name = node.params.args[i].asName
      if (!name) {
        log.error(`Unable to define ${name}, missing a name in args`, node.location, node)
      }

      // This will be undefined if no default is set, this is fine
      let def = evaluate(node.params.kwargs[name], environment)
      defaults.push([name, def])
    }
  }

  let definedFunction

  if (node.mode === "terminal") {
    // Create the new function for the callable object
    definedFunction = (...args) => {
      // Bind passed variables into the local environment
      let definedEnvironment = environment.extend()
      for (let i = 0; i < defaults.length; i++) {
        let [key, def] = defaults[i]
        let value = args[i]
        if (value === undefined) value = def
        definedEnvironment.set(key, value)
      }

      // Call the body (a single group) with those args/kwargs
      return evaluate(node.body, definedEnvironment)
    }
  } else if (node.mode === "modifier") {
    // Create the new function for the callable object
    definedFunction =
      (...args) =>
      (child) => {
        // Bind passed variables into the local environment
        let definedEnvironment = environment.extend()
        for (let i = 0; i < defaults.length; i++) {
          let [key, def] = defaults[i]
          let value = args[i]
          if (value === undefined) value = def
          definedEnvironment.set(key, value)
        }

        definedEnvironment.set(node.child, child)

        // Call the body (a single group) with those args/kwargs
        return evaluate(node.body, definedEnvironment)
      }
  } else if (node.mode === "stacker") {
    throw "define stacker not implemented"
  } else {
    log.error(`unknown define mode ${node.mode}`, node.location, node)
  }

  log.awesome(`Created a new function ${name} of type ${node.mode} with defaults = ${defaults}`, node)

  let callable = new Callable()
  callable.defaults = defaults
  callable.f = definedFunction

  let obj = { type: node.mode, value: callable }

  environment.set(name, obj)
}
```

Essentially, we have to:

* Evaluate the parameters that we're being passed in parens

* Figure out what kind of node we're defining based on if we have a group or list (or neither) following it

* Define a custom function that will take in the parameters from above and return something that can be passed to `Callable` and work like the native functions we have

* Extend the current environment with the newly defined function (you can actually define local functions within other functions and it will work as it 'should')

It's a neat bit of code if I do say so myself!

## Summary

And... that's it. It's a bit of a long writeup and I probably could have gone into more detail, but I hope anything I missed in the writeup was in the comments or the code and anything I missed there... well [let me know](mailto:blog@jverkamp.com). Always happy to chat!

## Demo

[[wiki:Vegvísir]](). 

It's something that I always wanted to do with my older [[A DSL for rendering magic circles and runes|rune DSL]]() but couldn't make work. Now I did!

(Fully functional, give it a try and see what you can make!)

{{<html>}}
<script defer type="module">
import { render } from '/embeds/runelang/runelang/main.js'
import logging from '/embeds/runelang/lib/logging.js'

const log = logging.get("system")

let elInput = document.querySelector('[data-input]')
let elOutput = document.querySelector('[data-output]')
let elLog = document.querySelector('[data-log]')

elInput.value = `
define bar { translate(x: 0.5) rotate(0.25) line }
define fork(n) {
  translate(x: 0.5) rotate(0.25) {
    line
    linear [
      rotate(0.25) translate(y: -0.5) scale(0.5) line
      times n
    ]
  }
}

rune stroke(weight: 5) scale(0.75) {
  radial(offset: 0) [
    # N
    stack [
      line
      linear(scale: 0.25, min: 0.75) [
        bar
        bar
        bar
        fork(3)
      ]
    ]

    # NE
    stack [
      line
      linear(scale: 0.25, min: 0.5) [
        scale(0.5) {
          arc(-1/4, 1/4)
          fill("black") stack [
            { translate(-0.5) scale(0.1) circle }
            { translate( 0.5) scale(0.1) circle }
          ]
        }
        scale(0.75) translate(y: 1.6) arc(1/3, 2/3)
        fork(3)
      ]
    ]

    # E
    stack [
      line
      linear(scale: 0.25, min: 0.5) [
        group { translate(y: -0.25) scale(0.5) arc(-1/4, 1/4) }
        bar
        group { translate(y: 0.25) scale(0.5) arc(1/4, -1/4) }
        fork(3)
      ]
    ]

    # SE
    stack [
      line
      linear(scale: 0.25, min: 0.75) [
        bar
        bar
        bar
        fork(3)
      ]
    ]

    # S
    stack [
      line
      linear(scale: 0.25, min: 0.75) [
        group { 
          scale(x: 2) fork(3) 
          
          translate(x: -0.8) scale(0.25) line
          translate(x: -1, y: 0.8) scale(0.25) bar
          translate(x: -1, y: 1) scale(0.25) bar
          
          translate(x: 0.8) scale(0.25) line
          translate(x:  1, y: 0.8) scale(0.25) bar
          translate(x:  1, y: 1) scale(0.25) bar
        }
        group { scale(x: 1, y: 0.75) fork(3) }
        group { scale(0.5) bar }
      ]
    ]

    # SW
    stack [
      line
      linear(scale: 0.25, min: 0.5) [
        group { translate(y: -0.5) scale(0.5) arc(-1/4, 1/4) }
        bar
        group { scale(x: 1, y: 2) fork(3) }
        group { scale(0.5) bar }
        group { scale(0.5) bar }
        group {}
      ]
    ]

    # W
    stack [
      line
      translate(y: 0.9) scale(x: 0.5, y: 0.25) fork(5)
    ]

    # NW
    stack [
      line
      linear(scale: 0.25, min: 0.50) [
        scale(0.5) { translate(y: -0.25) arc(-1/4, 1/4) }
        group { scale(x: 2, y: 2) fork(3) }
        group { translate(y: -0.25) bar }
        group { translate(y: -0.25) scale(0.25) fill("none") circle }
      ]
    ]
  ]

  scale(0.15) circle
}
`

logging.register((msg) => {
   let node = document.createElement('li')
   node.innerText = msg
   elLog.prepend(node)
})

logging.setMode('ERROR')

function doRender() {
  elLog.innerHTML = ''
  let input = elInput.value

  try {
      let svg = render(input)
      elOutput.innerHTML = svg
      log.awesome('IT WORKED!')
   } catch (exception) {
      console.log(exception)
   }
}

function debounce(f, timeout = 500) {
   let timer
   return (...args) => {
         clearTimeout(timer)
         timer = setTimeout(() => f.apply(this, args), timeout)
   }
}

document.addEventListener('keyup', debounce(doRender))
doRender()
</script>

<style>
   textarea[data-input],
   div[data-output] {
      width: 80%;
      height: 600px;
      padding: 1em;
   }

   td {
      width: 45%;
      vertical-align: top;
   }
</style>

<h3>Output</h3>
<div data-output></div>

<h3>Source</h3>
<textarea data-input></textarea>

<h3>Log (most recent messages first):</h2>
<ul data-log></ul>
{{</html>}}

## Next steps

I think that's enough for this code for now and I'm looking forward to other things, but there are two things that I still want to try: 

* a better looking stand alone editor for Runelang (that still runs in a browser) rather than the semi hacky demo above

* a full CLI release with examples so you can download and run it yourself

Look for these soon! (At the very least hopefully not months more...)

---
title: "Runelang: A Bind Rune Generator"
date: 2022-08-25
programming/languages:
- Javascript
programming/topics:
- Small Scripts
programming/topics:
- Generative Art
- Procedural Content
series:
- Runelang in the Browser
---
Continuing with my [Runelang in the Browser](/series/runelang-in-the-browser/) series, I had the idea to automatically generate runes. So basically reversing the parsing step, rather than to take what I've written and make it look good, to write something that Runelang can parse--and still look good. 

In a nutshell, I want to write a series of functions that can recursively call one another to render runes:

- `generate_bind_rune`
  - *n* times `generate_bind_rune_arm`
    - *m* times generate bars, circles, and other decrations
    - add a fork at the end

<!--more-->

## Generate Bind Rune

I'll follow up with a few other styles, but for this first one, here's what we have:

```javascript
function generate_rune() {
  stdlib()
  block("rune {")
  choose(generate_bind_rune)
  end_block("}")
}

function generate_bind_rune() {
  block("stroke(weight: 5) scale(0.75) {")
  block("radial(offset: 0) [")
  {
    for (let i = 0; i < random_int(2, 4) * 2; i++) {
      generate_bind_rune_arm()
    }
  }

  end_block("]")
  end_block("}")
}

function generate_bind_rune_arm() {
  block("stack [")
  line("line")
  block("linear(scale: 0.25, min: 0.5) [")
  {
    for (let i = 0; i < random_int(2, 5); i++) {
      choose(
        // cross bar
        8,
        () => line("bar"),
        // half circle in
        2,
        () => line("group { translate(y: -0.25) scale(0.5) arc(-1/4, 1/4) }"),
        // half circle out
        2,
        () => line("group { translate(y: 0.25) scale(0.5) arc(1/4, -1/4) }"),
        // full circle
        1,
        () => line('scale(0.25) fill("none") circle'),
        // two dots
        1,
        () => {
          block('fill("black") stack [')
          line("{ translate(-0.5) scale(0.1) circle }")
          line("{ translate(0.5) scale(0.1) circle }")
          end_block("]")
        }
      )
    }
    line(`fork(${random_int(3, 5)})`)
  }
  end_block("]")
  end_block("]")
}

// main
generate_rune()
```

Fairly straight forward to start with, if you assume that all of those helper functions do what you expect them to do:

* `block`: starts an indented block (can be nested)
* `end_block`: ends the indentation of a previous block
* `line`: outputs a properly indented line of text
* `choose`: random choose and output one of many options, with optional weights
* `random_float` and `random_int`: wrap `random` to generate random numbers with given bounds

So let's go through each of those.

## Indentation levels: `block` and `end_block`

```javascript
const INDENTATION_STRING = "  "
let INDENTATION_LEVEL = 0

function block(text) {
  line(text)
  INDENTATION_LEVEL++
}

function end_block(text) {
  INDENTATION_LEVEL--
  line(text)
}
```

All this does is keep track of a global (I know) indentation level, incrementing it when we see a `block` and decrementing it when we see an `end_block`. You do have to make sure to do that in the proper order, otherwise you'll end up with the end block as part of the block (Python style) rather than as being at the level of the opening. 

## Single lines: `line`

Next, rendering single lines to the right level:

```javascript
function line(text) {
  console.log(INDENTATION_STRING.repeat(INDENTATION_LEVEL) + text)
}
```

Not much there.

## Weighty choices: `choose`

```javascript

function choose(...options) {
  let weights = []
  let total_options = 1

  for (let i = 0; i < options.length; i++) {
    if (Number.isInteger(options[i])) {
      weights.push([options[i], options[i + 1]])
      total_options += options[i]
      i += 1
    } else {
      weights.push([1, options[i]])
      total_options += 1
    }
  }

  let value = random_int(0, total_options - 1)
  for (let [weight, option] of weights) {
    if (value <= weight) {
      if (option instanceof Function) {
        return option()
      } else {
        return option
      }
    } else {
      value -= weight
    }
  }
  console.error("out of range choice)")
}
```

This is an interesting function, in large part because the arguments are so dynamic. You can specify any number of children to randomly choose between, along with optional weights. So you could have:

```text
// Randomly choose between a, b, and c
choose('a', 'b', 'c')

// Randomly choose between a, b, and c with each twice as likely as the next
choose(4, 'a', 2, 'b', 'c')

// Randomly choose a function with hello() twice as likely
function hello() {}
function world() {}
choose(2, hello, world)
```

It's a bit persnickity if you want to randomly choose numeric values. Technically you can, but you always have to specify the weight. I think it's probably best if you don't though. 

## Random numbers

And finally, wrappers for random numbers:

```javascript
function random_float(min, max) {
  min ||= 0.0
  max ||= 1.0

  return Math.random() * (max - min) + min
}

function random_int(min, max) {
  if (!max) {
    max = min
    min = 0
  }

  return Math.floor(Math.random() * (1 + max - min)) + min
}
```

## Demo

Demo time!

{{<html>}}
<script defer type="module">
import { render } from '/embeds/runelang/runelang/main.js'
import logging from '/embeds/runelang/lib/logging.js'

const log = logging.get("system")

let elInput = document.querySelector('[data-input]')
let elOutput = document.querySelector('[data-output]')
let elLog = document.querySelector('[data-log]')

elInput.value = `
`

const INDENTATION_STRING = "  "
let INDENTATION_LEVEL = 0

function stdlib() {
  console.log(`
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
  `)
}

function block(text) {
  line(text)
  INDENTATION_LEVEL++
}

function end_block(text) {
  INDENTATION_LEVEL--
  line(text)
}

function random_float(min, max) {
  min ||= 0.0
  max ||= 1.0

  return Math.random() * (max - min) + min
}

function random_int(min, max) {
  if (!max) {
    max = min
    min = 0
  }

  return Math.floor(Math.random() * (1 + max - min)) + min
}

function choose(...options) {
  let weights = []
  let total_options = 1

  for (let i = 0; i < options.length; i++) {
    if (Number.isInteger(options[i])) {
      weights.push([options[i], options[i + 1]])
      total_options += options[i]
      i += 1
    } else {
      weights.push([1, options[i]])
      total_options += 1
    }
  }

  let value = random_int(0, total_options - 1)
  for (let [weight, option] of weights) {
    if (value <= weight) {
      if (option instanceof Function) {
        return option()
      } else {
        return option
      }
    } else {
      value -= weight
    }
  }
  console.error("out of range choice)")
}

function line(text) {
  console.log(INDENTATION_STRING.repeat(INDENTATION_LEVEL) + text)
}

function generate_rune() {
  stdlib()
  block("rune {")
  choose(generate_bind_rune)
  end_block("}")
}

function generate_bind_rune() {
  block("stroke(weight: 5) scale(0.75) {")
  block("radial(offset: 0) [")
  {
    for (let i = 0; i < random_int(2, 4) * 2; i++) {
      generate_bind_rune_arm()
    }
  }

  end_block("]")
  end_block("}")
}

function generate_bind_rune_arm() {
  block("stack [")
  line("line")
  block("linear(scale: 0.25, min: 0.5) [")
  {
    for (let i = 0; i < random_int(2, 5); i++) {
      choose(
        // cross bar
        8,
        () => line("bar"),
        // half circle in
        2,
        () => line("group { translate(y: -0.25) scale(0.5) arc(-1/4, 1/4) }"),
        // half circle out
        2,
        () => line("group { translate(y: 0.25) scale(0.5) arc(1/4, -1/4) }"),
        // full circle
        1,
        () => line('scale(0.25) fill("none") circle'),
        // two dots
        1,
        () => {
          block('fill("black") stack [')
          line("{ translate(-0.5) scale(0.1) circle }")
          line("{ translate(0.5) scale(0.1) circle }")
          end_block("]")
        }
      )
    }
    line(`fork(${random_int(3, 5)})`)
  }
  end_block("]")
  end_block("]")
}

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

function doGenerate() {
    let buffer = []
    const old_log = console.log
    {
        console.log = (line) => buffer.push(line)
        generate_rune()
    }
    console.log = old_log

    elInput.value = buffer.join("\n")
    doRender()
}

document.addEventListener('keyup', debounce(doRender))
document.querySelector('button[data-generate="bind-rune"]').addEventListener('click', (event) => {
    event.preventDefault()
    doGenerate()
})

doGenerate()
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

<button data-generate="bind-rune">Generate random Bind Rune</button>

<h3>Log (most recent messages first):</h2>
<ul data-log></ul>
{{</html>}}
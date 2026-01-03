---
title: "Runelang: A Summoning Circle Generator"
date: 2022-08-29
programming/languages:
- Javascript
programming/topics:
- Small Scripts
- Generative Art
- Procedural Content
series:
- Runelang in the Browser
---
Last time we had [[Runelang: A Bind Rune Generator]](). This time, let's make 'summoning circles'. Basically, we want to make a circle with stars and other circles inscribed and around the borders with various 'mystic' text in the mix. Something like this:

- `generate_summoning_circle`
  - random chance of boder
  - random chance of one or more inscribed stars
  - random chance of recurring on the border (calling `generate_summoning_circle` again)
  - random chance of recurring in the middle

<!--more-->

## Generate Bind Rune

Codewise, I only have one (relatively complicated) function this time:

```javascript
function generate_summoning_circle(depth, options) {
  let LANGUAGES = ["GREEK_UPPER", "ASTROLOGICAL", "RUNIC"]

  options ||= {}
  depth ||= 0
  block("group {")

  let border_text_chance = options["border_text_chance"] || 0.5
  let star_chance = depth == 0 ? 1.0 : options["star_chance"] || 0.5
  let second_star_chance = depth == 0 ? 1.0 : options["second_star_chance"] || 0.5
  let border_recur_chance = options["border_recur_chance"] || 0.5 ** depth
  let inner_recur_chance = options["inner_recur_chance"] || 0.5 ** depth
  let inner_text_chance = options["inner_text_chance"] || 0.5 // if not inner recur

  // Border
  if (random_float() < border_text_chance) {
    line(`doubleTextCircle(${choose(...LANGUAGES)})`)
  } else {
    line("double(0.1) circle")
  }

  // Stars
  if (random_float() < star_chance) {
    let points = [5, 7, 11, 13][random_int(0, 3)]
    line(`star(${points})`)

    if (random_float() < second_star_chance) {
      let points = [5, 7, 11, 13][random_int(0, 3)]
      line(`invert star(${points})`)
    }
  }

  // Outer circles
  if (random_float() < border_recur_chance) {
    let points = [5, 7, 11, 13][random_int(0, 3)]
    if (depth <= random_int(1, 3)) {
      block("radial(scale: 1/4) [")
      for (let i = 0; i < points; i++) {
        generate_summoning_circle(depth + 1)
      }
      end_block("]")
    }
  }

  // Inscribed circles
  if (random_float() < inner_recur_chance) {
    block("scale(0.5) {")
    generate_summoning_circle(depth + 1)
    end_block("}")
  } else if (random_float() < inner_text_chance) {
    line(`text(chooseOne(${choose(...LANGUAGES)}))`)
  }

  end_block("}")
}
```

Most of it's in the comments and configuration variables, but the idea for each part is `random_float() < ***_chance`, randomly choosing which features to draw. And then in 'outer circles' and 'inscribed circles', you have the recursive calls to `generate_summoning_circle`. You do have to be careful with those chances. If they're too high, you'll recur an awfully long way down and end up bringing your browser to a screaming halt. But until then, it's all good. :D 


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

define doubleTextCircle(set) {
  double(0.1) circle
  stroke(weight: 1, color:"none") fill("black") invert text(chooseOne(set))
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

function generate_rune(f) {
  stdlib()
  block("rune scale(0.8) {")
  if (f instanceof Function) {
    f()
  } else {
    choose(generate_bind_rune, generate_summoning_circle)
  }
  end_block("}")
}

function generate_summoning_circle(depth, options) {
  let LANGUAGES = ["GREEK_UPPER", "ASTROLOGICAL", "RUNIC"]

  options ||= {}
  depth ||= 0
  block("group {")

  let border_text_chance = options["border_text_chance"] || 0.5
  let star_chance = depth == 0 ? 1.0 : options["star_chance"] || 0.5
  let second_star_chance = depth == 0 ? 1.0 : options["second_star_chance"] || 0.5
  let border_recur_chance = options["border_recur_chance"] || 0.5 ** depth
  let inner_recur_chance = options["inner_recur_chance"] || 0.5 ** depth
  let inner_text_chance = options["inner_text_chance"] || 0.5 // if not inner recur

  // Border
  if (random_float() < border_text_chance) {
    line(`doubleTextCircle(${choose(...LANGUAGES)})`)
  } else {
    line("double(0.1) circle")
  }

  // Stars
  if (random_float() < star_chance) {
    let points = [5, 7, 11, 13][random_int(0, 3)]
    line(`star(${points})`)

    if (random_float() < second_star_chance) {
      let points = [5, 7, 11, 13][random_int(0, 3)]
      line(`invert star(${points})`)
    }
  }

  // Outer circles
  if (random_float() < border_recur_chance) {
    let points = [5, 7, 11, 13][random_int(0, 3)]
    if (depth <= random_int(1, 3)) {
      block("radial(scale: 1/4) [")
      for (let i = 0; i < points; i++) {
        generate_summoning_circle(depth + 1)
      }
      end_block("]")
    }
  }

  // Inscribed circles
  if (random_float() < inner_recur_chance) {
    block("scale(0.5) {")
    generate_summoning_circle(depth + 1)
    end_block("}")
  } else if (random_float() < inner_text_chance) {
    line(`text(chooseOne(${choose(...LANGUAGES)}))`)
  }

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

function doGenerate(f) {
    let buffer = []
    const old_log = console.log
    {
        console.log = (line) => buffer.push(line)
        f()
    }
    console.log = old_log

    elInput.value = buffer.join("\n")
    doRender()
}

document.addEventListener('keyup', debounce(doRender))

document.querySelectorAll('button[data-generate]').forEach(el => el.addEventListener('click', (event) => {
    event.preventDefault()

    if (event.target.dataset.generate === 'bind') {
      doGenerate(() => generate_rune(generate_bind_rune))
    } else if (event.target.dataset.generate === 'circle') {
      doGenerate(() => generate_rune(generate_summoning_circle))
    } else {
      doGenerate(generate_rune)
    }
}))

doGenerate(() => generate_rune(generate_summoning_circle))
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

<div>
  <button data-generate="rune">Random (either)</button>
  <button data-generate="bind">Bind Rune</button>
  <button data-generate="circle">Summoning Circle</button>
</div>

<h3>Log (most recent messages first):</h2>
<ul data-log></ul>
{{</html>}}
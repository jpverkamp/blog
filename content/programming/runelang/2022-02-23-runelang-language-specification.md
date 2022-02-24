---
title: "Runelang: Language Specification"
date: 2022-02-23
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
[Previously]({{<ref "2021-01-26-rune-dsl">}}), I wrote a post about making a DSL in Ruby that could render magic circles/runes. It worked pretty well. I could turn things like this:

```ruby
rune do
    scale 0.9 do 
        circle
        polygon 7
        star 14, 3
        star 7, 2
        children 7, scale: 1/8r, offset: 1 do |i|
            circle
            invert do
                text (0x2641 + i).chr Encoding::UTF_8
            end
        end
    end
    scale 0.15 do
        translate x: -2 do circle; moon 0.45 end
        circle
        translate x: 2 do circle; moon 0.55 end
    end
end
```

Into this:

<img src="/embeds/2022/old-astrology-and-moons.svg" />

But... I decided to completely rewrite it. Now it's an entirely separate language:

{{<html>}}
<script defer type="module">
import { render } from '/embeds/2022/runelang/runelang/main.js'
import logging from '/embeds/2022/runelang/lib/logging.js'

const log = logging.get("system")

let elInput = document.querySelector('[data-input]')
let elOutput = document.querySelector('[data-output]')
let elLog = document.querySelector('[data-log]')

elInput.value = `
define offsetmoon(x, phase) {
  translate(x: x) {
    circle
    fill("black") moon(phase)
  }
}

rune {
  scale(0.9) {
    circle
    polygon(7)
    star(14, 3)
    star(7, 2)

    radial(scale: 1/8, rotate: true) [
      circle
      invert character(0x2640 + i) 
      for i in 1..7
    ]
  }

  scale(0.15) stroke(2) {
    circle
    offsetmoon(-2,  0.55)
    offsetmoon( 2, -0.55)
  }
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

<!--more-->

My main reasons for doing this? 

1. It's written in JavaScript, so I can run it in the browser!

   Why yes. The example above is *live*. Try it out. See what you can make. 

   Pretty cool, no?

2. It lets me play with a full compiler stack: lexer, parser, evaluator/code generator

## Language specification

So, for this first post, what does the final language specification look like?

* Tokens
  * Numeric literals integers: `1`, decimal: `2.3`, rational/fractions: `4/5`, negatives (any of the previous): `-7`, hexadecimal: `0xDEADBEEF`, angles: `30deg` / `1rad`
  * String literals: `"hello world"`, includes escape sequences
  * Booleans: `true`/`false`
  * Identifiers: start with a letter, include letters, numbers, dashes, or underscores
  * Operators: `+` `-` `*` `/`, also `..` for making ranges

* Types of groups
  * Parameter groups, bound by `()`, including both positional (`args`) and named (`kwargs`) parameters 
    * When defining, `kwargs` represent the default values
    * When calling, `kwargs` represent the value passed to that parameter
    * In `params`, you can use `expressions` which are a large subset of mathematical expressions with proper operator precedence 
  
  * Function groups, bound by `{}` contain zero or more nodes that will be evaluated as a single group and that can be passed to `modifiers` (see below)

  * Lists, bound by `[]` represent zero or more nodes, can be evaluated similarly to Python `generators`, and can be passed to `stackers` (see below)

    Lists can have three different forms:

    * `[ NODE* ]` a static list of items
    * `[ NODE* for VARIABLE in ITERABLE ]` acts like a python generator, assigning each value in `ITERABLE` in turn to `VARIABLE` than evaluating each `NODE`
    * `[ NODE* times NUMBER ]` a shortcut/alternative for writing `[ ... for i in 0..NUMBER ]`, although it does not bind `i` (or anything) to the counter

    Both the 2nd and 3rd case above can use the full `expression` language for the `ITERABLE` / `NUMBER`

  * Each node (see below) can have params, a list, and a group, each optional and in that order. If no group is specified for a node that expects one, the next node will be used instead. 

    This means that `scale(0.9) circle` is equivalent to `scale(0.9) { circle }`

* Types of builtins
  * Terminals: represents a single shape, can take `params` but not a `list` or `group`
    * `line(min: 0, max: 1)` - a line from the center (0) upwards (1)
    * `circle` - a unit circle
    * `polygon(n: 5)` - an n-sided polygon
    * `star(n: 5, m: 2)` - a star with n points, skipping to the mth point each time, the 'normal' five pointed star has `m=2`, a polygon is a star with `m=1`
    * `character(c, scale: 1)` - a single character from it's Unicode codepoint, so for example `character(0x03B1)` = α, scale modifies font size
    * `text(s, scale: 1)` - a string, scale modified font size
    * `textCircle(s, scale: 1, outward: true)` - a string rendered onto a circle, outward modifies if the text is upright at the top of the circle or inverted
    * `textStar(n: 5, m: 2, s: "", scale: 1)` - a string rendered onto a star path
    * `arc(min: 0, max: 1)` - an arc around a circle ranging from 0 at the top, clockwise around to 1 as a full circle (can use angle literals as well)
    * `moon(phase)` - a moon ranging from 0 as new moon to 0.5 as full, back to 1 as a new moon again

  * Modifiers: modifier a single child or a group, can take `params` and a `group` but not a `list`; if no group is specified will apply to the next node instead
    * `rune` - the base of all shapes
    * `group` - a 'null' operator, used for grouping in `lists`
    * `scale(x, y)` - scale children on the x/y axis; if only one argument is supplied use it for both x and y, a scale of 1 is the identity
    * `fill(color)` - change the fill color for all children, can be any SVG compatible color (names or hex strings)
    * `stroke(weight, color)` - change the stroke weight/color, if either param is not supplied, it will be skipped rather than using a default
    * `invert` - rotate by 180 degrees
    * `double(scale)` - draw the child node twice with the second scaled by scale, most useful for double circles like: `double(0.9) circle`
    * `translate(x: 0, y: 0)` - offset by x/y coordinates where 1 is the unit circle
    * `rotate(a)` - rotate by an angle where 0 is no rotation, 1/4 is a quarter circle (clockwise), 1/2 is 180 degrees, 1 is a full circle
    * `skew(x, y)` - skew by angles on the x and y axis, angles defined as above

  * Stackers:
    * `stack` - the base stacker if you just want to stack children without doing anything to them, mostly equivalent to a `group`
    * `radial(scale: 1, offset: 1, rotate: false)` - place children around a circle with the first at the top and going clockwise, evenly spaced; `scale` will apply to each child, `offset` is 0 at the center of the circle to 1 at the edge, if `rotate` is `true`, each shape will be rotated to point 'outwards', otherwise they'll all stay upwards relative to the `radial` node
    * `linear(scale: 1, min: 0, max: 1)` - place children in a line from `min` (default 0 is the middle of the circle) to `max` (default 1 is the top of the circle), `scale` acts like above

* `define` - a special form that allows you to define new elements, a `group` is always required, but what it does depends on the form
  * `define NAME ( PARAMS ) { BODY }` defines a new `terminal`
  * `define NAME ( PARAMS ) ( CHILD_PARAM ) { BODY }` defines a new `modifier` and will bind the children (either one node or a group) to `CHILD_PARAM` in the call, that param list must be exactly one `arg`, no `kwarg`
  * `define NAME ( PARAMS ) [ LIST_PARAM ] { BODY }` like above, defines a new `stacker` (warning: currently not implemented)

And... that's it! 

Yeah... I know that's a ridiculous block of text. And that's only the first of it! Next up:

* Lexing
* Parsing
* Evaluating: generating basic `SVGs`
* Evaluating: allowing basic infix expression with operator precedence 
* Adding functions to the `expression` language
* Adding `define`
* Adding `import`

If you'd like to see the source or even help contribute, take a look here: [jpverkamp/runelang](https://github.com/jpverkamp/runelang) 

That's well ahead of where this post is (it's already doing everything above, except `import` doesn't work in the browser). One thing I really need to do is write tests. That link may always be ahead. So ... spoilers I guess? 

All posts (as I write them): 

{{< taxonomy-list "series" "Runelang in the Browser" >}}
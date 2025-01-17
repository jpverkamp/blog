---
title: "Runelang: The Lexer"
date: 2022-02-24
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
Let's [[wiki:Lexical_analysis|LEX]]()!

So this is actually one of the easier parts of a programming language. In this case, we need to turn the raw text of a program into a sequence of tokens / lexemes that will be easier to parse. In this case, we want to:

* Remove all whitespace and comments
* Store the row and column with the token to make debugging easier

So let's do it!

<!--more-->

First, the definition of all tokens that we need to be able to deal with:

```javascript
const TOKEN_PATTERNS = [
  /^[\(\)\[\]\{\}]/,          // Brackets
  /^,/,                       // Commas
  /^:/,                       // Colons
  /^(false|true)/,            // Booleans
  /^0x[0-9a-fA-F]+/,          // Hexadecimal literals
  /^\-?\d+\/\d+/,             // Fractions
  /^\-?\d+\.\d+/,             // Decimals
  /^\-?\d+(deg|rad)/,         // Angles with units
  /^\-?\d+/,                  // Integers
  /^[a-zA-Z][a-zA-Z0-9_-]*/,  // Words
  /^(\.\.|\+|\-|\/|\*)/,      // Operators
  /^"([^\\"]|\\.)*"/,         // Strings (with escaping)
]
```

For the most part, they're all unique. Brackets (`()[]{}`) are all treated as their own thing, since those will define `params`, `lists`, and `groups` (respectively, see [my previous post]({{<ref "1 - Language Specification">}})). `,` is a token that should only be used in `params`, but does break up tokens in that case. Likewise `:` is only used in `kwargs` during `param` parsing. They we have literal booleans. After that, we start getting slightly more interesting, with numbers!

* Hexadecimal literals: `0x__`
* Fractions: `_/_`
* Decimals: `_._`
* Angles: `_deg` and `_rad`
* Integers: `_`

These are the main case where we have to parse in order, since if we parse integers before fractions (for example), it will parse as `integer, operator(/), integer` (which would mostly be fine) instead of what we want. Likewise with angles. 

After that, we have `words`, which are basically any name. They have to start with a letter, but then can have alphanumerics, underscores, and dashes. This is before `operators` so that `a-b` is a `word`, not `word(a), operator(-), word(b)`. 

Operators are used in `expressions`, these will be parts of mathematical expressions. The main interesting one here is `..` making ranges. 

And finally, strings. We allow double quoted strings with arbitrary escape sequences. A string is a pair of double quotes around any character, where `\"` will not be counted as the end. 

And that's actually it! Let's use that to turn a raw string into a sequence of tokens:

```javascript
import logging from "../lib/logging.js"
const log = logging.get("lexer")

import { TOKEN_PATTERNS } from "./constants.js"

export default function lex(text) {
  let row = 0, col = 0
  let tokens = []

  while (text.length > 0) {
    let match

    // Match against comments
    match = text.match(/^\#.*\n/)
    if (match !== null) {
      row += 1
      text = text.substring(match[0].length)
      continue
    }

    // Try to match against known tokens
    let matched = false
    for (let token_pattern of TOKEN_PATTERNS) {
      let match = text.match(token_pattern)
      if (match === null) continue

      let token = match[0]
      let chars = token.length

      tokens.push({ row, col, token })
      row += chars
      text = text.substring(chars)

      matched = true
      break
    }
    if (matched) continue

    // Try to match against a newline
    if (text[0] === "\n") {
      row = 0
      col += 1
      text = text.substring(1)
      continue
    }

    // Try to match against other whitespace
    match = text.match(/^\s+/)
    if (match !== null) {
      let chars = match[0].length

      row += chars
      text = text.substring(chars)
      continue
    }

    // Error case, no idea what's at the beginning
    let context = text.substring(0, 10).replace(/\n/g, "\\n")
    if (text.length > 10) context += "..."
    log.error("Lex Error, unknown token at", row, ":", col, ":", context, "")
  }

  return tokens
}
```

I'll admit, making substrings all the time is potentially a performance problem. I don't know if `substring` makes a copy in Javascript. I know that if we were working in `Java` (with immutable strings by default), this wouldn't be a problem at all. Given the size of strings that we've used so far now though... it's still not a problem. Fast enough and it's functional!

Here's a demo!

{{<html>}}
<script defer type="module">
import lex from '/embeds/runelang/runelang/lexer.js'
import logging from '/embeds/runelang/lib/logging.js'

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

function doLex() {
  elLog.innerHTML = ''
  let input = elInput.value

  try {
      let output = lex(input).map(JSON.stringify).join("\n")
      elOutput.value = output
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

document.addEventListener('keyup', debounce(doLex))
doLex()
</script>

<style>
   textarea[data-input],
   textarea[data-output] {
      width: 80%;
      height: 600px;
      padding: 1em;
   }

   td {
      width: 45%;
      vertical-align: top;
   }
</style>

<h3>Source</h3>
<textarea data-input></textarea>

<h3>Lexed</h3>
<textarea readonly data-output></textarea>

<h3>Log (most recent messages first):</h2>
<ul data-log></ul>
{{</html>}}

Onward!

As before, here's the current source: [jpverkamp/runelang](https://github.com/jpverkamp/runelang) 

And here is the entire series (as I write them): 

{{< taxonomy-list "series" "Runelang in the Browser" >}}
---
title: "Runelang: The Parser (Part 2: Expressions)"
date: 2022-03-18
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
[[Runelang: The Parser (Part 1)|Earlier this week]](), we started parsing, getting through groups, nodes, params, and lists. A pretty good start, but it also leaves out two very powerful things (expressions and defines), one of which we absolutely do need to start actually evaluating things: expressions. Since we use them in every param, we pretty much need to know how to parse them, so let's do it!

<!--more-->

## Parsing expressions

My goals for expressions are:

* A variety of literal values (integers, decimals, fractions, hex/binary literals, angles, strings)
* Simple [[wiki:infix]]() style expressions: `a + b`, rather than `(+ a b)` or `a b +`
* [[wiki:Operator precedence]](): `a + b * c` should be evaluated as `a + (b * c)` rather than `(a + b) * c`
* `()` for grouping when you want to override precedence (so `(a + b) * c` does what it should)
* Built in functions (`sin(x)`)

This isn't really something that works directly with our current [[wiki:recursive descent parser]](), but we can switch modes (while parsing an expression) to instead use the [[wiki:Shunting-Yard Algorithm]](). It's designed for exactly this sort of thing and does pretty well. 

It doesn't directly evaluate the expressions, but what it does is parse them into a list that is in [[wiki:Reverse Polish Notation]]() form. The advantage of that is RPN is unambiguous and doesn't have to deal with precedence--you just evaluate the list of expressions left to right. So by using the Shunting-Yard to deal with precedence now, we're hopefully making the expression evaluation easier. Let's do it!

First, the entire code:

```javascript
function parseExpression() {
  let token = tokens[0]
  log.debug("parseExpression", token)

  if (tokens.length === 0) {
    log.error("unable to parse expression, got EOF")
  }

  // Parse using the [Shunting-Yard algorithm](https://en.wikipedia.org/wiki/Shunting-yard_algorithm)
  let output = []
  let operator_stack = []

  // Loop through tokens until we hit a token that can't be part of the expression
  while (tokens.length > 0) {
    let token = tokens.shift()
    let text = token.token

    // Literal string
    if (text[0] === '"') {
      output.push({ type: "literal", mode: "string", value: text.substring(1, text.length - 1), token })
    }
    // A parameter list
    else if (operator_stack.includes("(") && text === ",") {
    }
    // A constant
    else if (text in EVAL_CONSTANTS) {
      output.push({ type: "literal", mode: "constant", value: EVAL_CONSTANTS[text], token })
    }
    // A predefined function
    else if (text in EVAL_FUNCTIONS) {
      operator_stack.push(text)
    }
    // Some kind of number
    else if (text.match(/^\-?[0-9]/)) {
      // Rational numbers/fractions
      // TODO: Divided by zero error
      if (text.match(/\//)) {
        let [num, den] = text.split("/")
        let value = (1.0 * parseInt(num)) / parseInt(den)

        output.push({ type: "literal", mode: "number", value, token })
      }
      // Decimal
      else if (text.match(/\./)) {
        output.push({ type: "literal", mode: "number", value: parseFloat(text), token })
      }
      // Hexadecimal
      else if (text.match(/^0x/)) {
        output.push({ type: "literal", mode: "number", value: parseInt(text.substring(2), 16) })
      }
      // Degrees (stored internally angles 0-1 for a circle)
      else if (text.match(/\-?\d+deg/)) {
        output.push({ type: "literal", mode: "number", unit: "degrees", value: parseInt(text.substring(0, text.length - 3)) / 360, token })
      }
      // Radians (stored internally angles 0-1 for a circle)
      else if (text.match(/\-?\d+rad/)) {
        output.push({ type: "literal", mode: "number", unit: "radians", value: parseInt(text.substring(0, text.length - 3)) / (2 * Math.PI), token })
      }
      // Anything else should be an integer
      else {
        output.push({ type: "literal", mode: "number", value: parseInt(text), token })
      }
    }
    // Parens, either a function call or grouping
    else if (text == "(") {
      operator_stack.push("(")
    }
    // Closing parens
    else if (text == ")") {
      if (operator_stack.includes("(")) {
        while (true) {
          let token = operator_stack.pop()
          if (token === "(") {
            break
          } else {
            output.push(token)
          }
        }

        if (operator_stack.length > 0) {
          let maybeFunction = operator_stack.pop()
          if (maybeFunction in EVAL_FUNCTIONS) {
            let f = EVAL_FUNCTIONS[maybeFunction]
            let arity = f
              .toString()
              .match(/\(.*?\)/)[0]
              .split(",").length

            output.push({ type: "function", value: f, arity, token })
          } else {
            operator_stack.push(maybeFunction)
          }
        }
      } else {
        // No ( on the stack means this is finishing the expression
        tokens.unshift(token)
        break
      }
    }
    // An operator
    // https://en.wikipedia.org/wiki/Shunting-yard_algorithm
    else if (text in EVAL_OPERATORS) {
      let precedence = EVAL_OPERATORS[text].precedence
      log.debug(`Working on operator`, token, { text, precedence })

      while (operator_stack.length > 0) {
        let stack_operator = operator_stack[operator_stack.length - 1]
        if (stack_operator == "(") break

        let stack_precedence = EVAL_OPERATORS[stack_operator].precedence

        log.debug(`Continuing operator`, token, { stack_operator, stack_precedence })

        if (stack_precedence < precedence) {
          log.debug(`Done popping`, token, { stack_precedence, precedence })
          break
        }

        output.push({ type: "operator", value: operator_stack.pop() })
      }
      operator_stack.push(text)
    }
    // A variable
    else if (text[0].match(/[a-zA-Z]/) && !EVAL_KEYWORDS.includes(text)) {
      output.push({ type: "variable", value: text, token })
    }
    // Anything else means that we're done parsing the expression
    // Remember to put the token back!
    else {
      tokens.unshift(token)
      break
    }
  }
  log.debug(`Done parsing expression`, token, { output, operator_stack })

  // After we exit the list, any remaining operators get added to the stack
  while (operator_stack.length > 0) {
    output.push({ type: "operator", value: operator_stack.pop() })
  }

  // Construct the result value
  let result = { type: "expression", rpn: output, token }

  // Special case: if the expression was a single identifier
  // It's probably being used as a variable name in a param/kwarg, store an alias for this
  if (output.length === 1 && output[0].type === "variable") {
    result.asName = output[0].value
  }

  return result
}
```

It's a bit much, so let's break it apart!

### Literals

The first case is any of our various sorts of literals:

* integers like 0, 5, -10
* decimals like 3.14, -0.7
* rationals/fractions like 1/2, 1/7, -3/2
* hexadecimal literals like: 0xFF (primarily used for [[wiki:Unicode code points]]())
* angles in degrees or radians (30deg, 1rad), TODO: I need to combine these with decimals and fractions
* strings like "hello world"
* constants like `true` and `false`
* predefined functions like `chooseOne` (choose one item from a list)

Most of the parsing methods of those are pretty straight forward (thus, literals):

```javascript
...
// Literal string
if (text[0] === '"') {
  output.push({ type: "literal", mode: "string", value: text.substring(1, text.length - 1), token })
}
// A parameter list
else if (operator_stack.includes("(") && text === ",") {
}
// A constant
else if (text in EVAL_CONSTANTS) {
  output.push({ type: "literal", mode: "constant", value: EVAL_CONSTANTS[text], token })
}
// A predefined function
else if (text in EVAL_FUNCTIONS) {
  operator_stack.push(text)
}
// Some kind of number
else if (text.match(/^\-?[0-9]/)) {
  // Rational numbers/fractions
  // TODO: Divided by zero error
  if (text.match(/\//)) {
    let [num, den] = text.split("/")
    let value = (1.0 * parseInt(num)) / parseInt(den)

    output.push({ type: "literal", mode: "number", value, token })
  }
  // Decimal
  else if (text.match(/\./)) {
    output.push({ type: "literal", mode: "number", value: parseFloat(text), token })
  }
  // Hexadecimal
  else if (text.match(/^0x/)) {
    output.push({ type: "literal", mode: "number", value: parseInt(text.substring(2), 16) })
  }
  // Degrees (stored internally angles 0-1 for a circle)
  else if (text.match(/\-?\d+deg/)) {
    output.push({ type: "literal", mode: "number", unit: "degrees", value: parseInt(text.substring(0, text.length - 3)) / 360, token })
  }
  // Radians (stored internally angles 0-1 for a circle)
  else if (text.match(/\-?\d+rad/)) {
    output.push({ type: "literal", mode: "number", unit: "radians", value: parseInt(text.substring(0, text.length - 3)) / (2 * Math.PI), token })
  }
  // Anything else should be an integer
  else {
    output.push({ type: "literal", mode: "number", value: parseInt(text), token })
  }
}
...
```

The main complication is that we have to make sure this is in the right order. For example, if we try to parse integers before angles, we'll never see the `deg` / `rad` and things will get confusing. 

## Operators

The next step is a core part of the Shunting-Yard algorithm: operators:

```javascript
...
// An operator
// https://en.wikipedia.org/wiki/Shunting-yard_algorithm
else if (text in EVAL_OPERATORS) {
  let precedence = EVAL_OPERATORS[text].precedence
  log.debug(`Working on operator`, token, { text, precedence })

  while (operator_stack.length > 0) {
    let stack_operator = operator_stack[operator_stack.length - 1]
    if (stack_operator == "(") break

    let stack_precedence = EVAL_OPERATORS[stack_operator].precedence

    log.debug(`Continuing operator`, token, { stack_operator, stack_precedence })

    if (stack_precedence < precedence) {
      log.debug(`Done popping`, token, { stack_precedence, precedence })
      break
    }

    output.push({ type: "operator", value: operator_stack.pop() })
  }
  operator_stack.push(text)
}
...
```

This is a pretty direct implementation of the Shunting-Yard algorithm. Every operator has an associated precedence. Whenever we see an operator with higher precedence, that means that any currently on the operator stack need to be evaluated 'first', so they get pushed to output. Any with higher precedence needs to be done later, so stays on the stack. 

There's also another complication when you run into a `)`:

```javascript
...
// Closing parens
else if (text == ")") {
  if (operator_stack.includes("(")) {
    while (true) {
      let token = operator_stack.pop()
      if (token === "(") {
        break
      } else {
        output.push(token)
      }
    }

    if (operator_stack.length > 0) {
      let maybeFunction = operator_stack.pop()
      if (maybeFunction in EVAL_FUNCTIONS) {
        let f = EVAL_FUNCTIONS[maybeFunction]
        let arity = f
          .toString()
          .match(/\(.*?\)/)[0]
          .split(",").length

        output.push({ type: "function", value: f, arity, token })
      } else {
        operator_stack.push(maybeFunction)
      }
    }
  } else {
    // No ( on the stack means this is finishing the expression
    tokens.unshift(token)
    break
  }
}
...
```

If we see a `)`, it could either be closing an internal paren (in which case we're staying in expression mode) or closing the parameter list (for example) in which case w're done with the expression. What we do next is a much hackier method of making sure that we can parse any [[wiki:arity]]() of function with the function's `toString` method. This is... hacky. But it works and I don't believe there's a better way to evaluate this in Javascript. 

## Back to the top

And that's the majority of how we parse expressions. It took a while to get the detail right (and I really should be writing more (any) test cases), but it does work great now. Try it in the demo:

{{<html>}}
<script defer type="module">
import lex from '/embeds/runelang/runelang/lexer.js'
import parse from '/embeds/runelang/runelang/parser.js'
import logging from '/embeds/runelang/lib/logging.js'

const log = logging.get("system")

let elInput = document.querySelector('[data-input]')
let elOutput = document.querySelector('[data-output]')
let elLog = document.querySelector('[data-log]')

elInput.value = `
testExpressions(
  a: 1 + 2 * 3,
  b: sin(x),
  c: 1..2,
  d: "test"
)
`

logging.register((msg) => {
   let node = document.createElement('li')
   node.innerText = msg
   elLog.prepend(node)
})

logging.setMode('ERROR')

function doParse() {
  elLog.innerHTML = ''
  let input = elInput.value

  try {
      let lexed = lex(input)
      let parsed = parse(lexed)
      elOutput.value = JSON.stringify(parsed, null, 2)
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

document.addEventListener('keyup', debounce(doParse))
doParse()
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

<h3>Parsed</h3>
<textarea readonly data-output></textarea>

<h3>Log (most recent messages first):</h2>
<ul data-log></ul>
{{</html>}}

## Conclusion

As before, here's the current source: [jpverkamp/runelang](https://github.com/jpverkamp/runelang) 

And here is the entire series (as I write them): 

{{< taxonomy-list "series" "Runelang in the Browser" >}}
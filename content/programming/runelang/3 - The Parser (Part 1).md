---
title: "Runelang: The Parser (Part 1)"
date: 2022-03-15
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
I'm still here! And less sick now. 

Last time(s), we {{<crosslink text="described" title="Runelang: Language Specification">}} and {{<crosslink text="lexed" title="Runelang: The Lexer">}}) Runelang! This time around, let's take the lexed tokens and go one step further and parse them!

So, how do we go about this? With a {{<wikipedia "recursive descent parser">}}! 

* Start with a list/stream of tokens
* Using the first *k* (in a {{<wikipedia "LL(k) parser">}}) elements of the list, identify which sort of object we are parsing (a `group` / `identifier` / `literal` / `expression` / etc)
* Call a parsing function for that object type (`parseGroup` etc) that will:
    * Recursively parse the given object type (this may in turn call more parse functions)
    * Advance the token stream 'consuming' any tokens used in this group so the new 'first' element is the next object

<!--more-->

## Initialization and parsing groups

Okay, let's just get to the code. The outermost object that we're always going to be parsing is a `group`, which is a sequence of other objects grouped by `{...}`. In fact, I'm actually going to add an implicit group around whatever code you type. So if you have something like `rune { circle }`, the actual parser will see `{ rune { circle } }`, so we know we can always parse a group first. 

Code:

```javascript
export default function parse(tokens) {
  function parseGroup(terminator = "}") {
    let token = tokens.shift()
    log.debug("parseGroup", token)

    let nodes = []

    while (true) {
      if (tokens.length === 0) {
        console.log(token)
        log.error("unterminated group", token)
      }

      if (tokens[0].token === "}") {
        tokens.shift()
        return { type: "group", nodes, token }
      }

      if (tokens[0].token === "define") {
        nodes.push(parseDefine())
      } else {
        nodes.push(parseNode())
      }

      if (nodes.length >= 2) {
        nodes[nodes.length - 2].next = nodes[nodes.length - 1]
      }
    }
  }

  // Implicitly add a group
  tokens.unshift({ token: "{", row: 0, col: 0 })
  tokens.push({ token: "}", row: 0, col: 0 })

  return parseGroup()
}
```

Okay, what does that mean? Well, let's go through the parts:

* ```javascript
  let token = tokens.shift()
  ```

  Consumes the first `{` and marks that as the `token` where the group starts (for debugging purposes)

* ```javascript
  let nodes = []

  while (true) {
    if (tokens.length === 0) {
      console.log(token)
      log.error("unterminated group", token)
    }

    if (tokens[0].token === "}") {
      tokens.shift()
      return { type: "group", nodes, token }
    }

    ...
  }
  ```

  Keep consuming tokens until one of two things happens:

  * If we hit the end of teh file, report a parse error
  * If we hit a `}`, that's the end of the group, consume the `}` with `tokens.shift` and return the group along with any nodes we've parsed (next)

* ```javascript
  while (true) {
    ...

    if (tokens[0].token === "define") {
      nodes.push(parseDefine())
    } else {
      nodes.push(parseNode())
    }

    if (nodes.length >= 2) {
      nodes[nodes.length - 2].next = nodes[nodes.length - 1]
    }
  ```

  Finally, we parse either a normal node (with `parseNode`) or the special `define` syntax(s) (we'll come back to defines later). A `node` in this case is basically a function call (with a few different forms). You can have terminals with no arguments or children like `circle`, parameters like `star(5, 2)`, nodes (`modifiers`) that apply to a child group like `double circle` and `rotate(0.25) { star(5, 2) }`, or even `stackers` that apply specifically to lists, a la `radial(scale: 0.5) [ circle times 5 ]`. 

  The last bit of code there (assigning a value to `.next`) looks a bit strange, but essentially what we're doing is making a data structure that is a hybrid between an {{<wikipedia "abstract syntax tree">}} and a {{<wikipedia "linked list">}}. Each node is normally placed in a tree, but one thing that I wanted was to be able to treat `{...}` as implicit whenever I could. So instead of something like `double { circle }`, which would easily be parsed as a `Node<double>` with a child `Group<Node<circle>>`. 
  
  But I want to be able to write `double circle` and have it work the same way. To do that, each time I parse a node in a single group, if it's at least the second, I add a `.next` link that shows what the next node would be. That will cause some complications when running (for example: making sure I don't evaluate the `.next` node as a child and then again at the top level). 

So, we have the entire `parseGroup` function. Not at all that bad! But it depends on `parseDefine` and `parseNode`, so that's what's next!

## Parsing nodes (function calls)

As mentioned above, a `node` is basically a function call. It can have up to 4 parts, depending on which kind of `node` it is. All but the `identifier` are optional, but if present, they have to be in this order:

* An `identifier` which represents the name of the `terminal` / `modifier` / `stacker` that we're going to be applying
* A `(`, which signifies the start of a parameter list (either positional or key/value args); all three kinds of nodes can have this 
* A `[`, which signifies the start of a `list` child, only stackers should have these (but we'll deal with that at runtime)
* A `{`, which signifies the start of a `group` of children, which is primarily for `modifiers` (although they can also use the `.next` described above, but only *if no group is present here*)

```javascript
function parseNode() {
  let token = tokens[0]
  log.debug("parseNode", token)

  let identifier = parseIdentifier()
  let params = null,
    list = null,
    body = null

  // Nodes have an identifier and then optionally a param list, list body, and group body (in that order)

  if (tokens.length > 0 && tokens[0].token == "(") {
    params = parseParams()
  }

  if (tokens.length > 0 && tokens[0].token == "[") {
    list = parseList()
  }

  if (tokens.length > 0 && tokens[0].token == "{") {
    body = parseGroup()
  }

  let result = { type: "node", identifier, token }

  if (params !== null) result.params = params
  if (list !== null) result.list = list
  if (body !== null) result.body = body

  return result
}
```

Not so bad! And we're already getting into the recursive part, since `parseGroup` can call `parseNode`, which then can immediately (after the `identifier`) have another `parseGroup` to deal with. That's what you'd see in something like `double { circle }`:

* An implicit `parseGroup`
  * `parseNode` on `double { circle }`
    * `identifier` gets value `double`
    * `parseGroup` on `{ circle }`
      * `parseNode` on `circle }`
        * `identifier` gets value `circle`
        * No opening `([{`, so return the `Node<circle>`
    * Parse the closing `}`, so return `Group<Node<circle>>`
  * Parsed a `group`, so done parsing the node, got `Node<double, group: <Group<Node<circle>>>>`
* Done parsing

I don't know about you, but I think that's pretty cool!

So we already have `parseGroup`, but now we're missing `parseParams` and `parseList`, both of which are a bit trickier. Let's start with params.

## Parsing parameters

Okay, a parameter list. For this, I've chosen a syntax that looks like this: `(x, y: 5)`, which can be overloaded depending on if you're defining arguments (in a `define`) or calling a `node` (see above). But there are always a few rules:

* Starts with `(`, ends with `)`
* May contain 0, 1, or more params; params will be delimited by a comma: `,`
* Positional params will come first, these will either be a single variable name (for definitions) or an expression (for calls, see `parseExpression`)
* After 0 or more positional params, keyword params (kwargs) will come next, these will always have a name (an `identifier`), a colon `:`, and an expression for their value
* No positional params can occur after the first keyword param
* No param can be both a positional and keyword param (with the same `identifier`)

Why yes, it does look a lot like Python. I've written a *lot* of Python :D. 

So, let's make that (overly (properly?) commented) code:

```javascript
function parseParams() {
  // Consume the leading (
  let token = tokens.shift()
  log.debug("parseParams", token)

  let args = []
  let kwargs = {}

  // Start by parsing args (not kwargs) until we see a kwarg (with a `:`)
  let parsingKwargs = false
  while (true) {
    // Failure state: no closing )
    if (tokens.length === 0) {
      log.error("unterminated params", token, { expected: ")", got: "EOF" })
    }
    // End state: closing ), consume it and return the parsed params
    else if (tokens[0].token === ")") {
      tokens.shift()
      return { type: "params", args, kwargs, token }
    }

    // Parse the first part of the expression:
    // * When in a define, this should always be a single name
    // * When in a call as an arg, this can be a name or a complicated expression
    // * When in a kwarg, this is always a name
    let identifier = parseExpression()

    // Failure states: ran out of input or we've started parsing kwargs and got a , (should be a :)
    if (tokens.length === 0) {
      log.error("unterminated params, expected , or : got EOF", token)
    } else if (parsingKwargs && tokens[0].token === ",") {
      log.error("args cannot come after kwargs", token, { expected: ";", got: "," })
    }

    // If the next token is a : switch to kwargs mode and parse the value of the key/value pair
    if (tokens[0].token === ":") {
      tokens.shift()
      parsingKwargs = true

      // This is where we check the above case that for kwargs the left side of the `:` must just be a name
      // .asName is populated by `parseExpression`, when it returns a single identifier it will be filled
      if (!identifier.asName) {
        log.error("kwargs key must be an identifier", token, { expected: "identifer", got: token })
      }

      // Parsing kwargs and ran out of input
      if (tokens.length === 0) {
        log.error("missing kwargs body", key)
      }

      // Parsing the value
      let value = parseExpression()

      // Cannot have duplicate values in kwargs (we'll check that there are no duplicates in args at runtime)
      if (identifier.asName in kwargs) {
        log.error("duplicate kwarg", token, { name: identifier.asName })
      }

      // All kwargs are also positional `args`, store the new arg in both places here
      args.push(identifier)
      kwargs[identifier.asName] = value
    }
    // A regular arg, not a kwarg, just store it
    else {
      args.push(identifier)
    }

    // If the next argument is a `,` we're still parsing the list
    // If it's ) we'll catch the end of the list at the top of the loop
    // If it's anything else, we have malformed input (this previously caused an infinite loop)
    if (tokens[0].token === ",") {
      tokens.shift()
    } else if (tokens[0].token === ")") {
      continue
    } else {
      log.error("badly formed parameters", token, { expected: [",", ")"], got: tokens[0] })
    }
  }
}
```

Okay, we've got groups, nodes, and parameters, next up will be lists!

## Parsing lists

Okay, we have the concept of `stackers`, where you can take a list of items and spread them in a line or around a circle (or just on top of one another, but that's already done by a group). But what would be nice would be if we didn't have to manually define all of the nodes. For example, if we want a series of stars in a circle, you could do:

```text
rotate(0.0) translate(1.0) scale(0.5) star(2)
rotate(0.2) translate(1.0) scale(0.5) star(3)
rotate(0.4) translate(1.0) scale(0.5) star(4)
rotate(0.6) translate(1.0) scale(0.5) star(5)
rotate(0.8) translate(1.0) scale(0.5) star(6)
```

But I'd much rather write:

```text
radial(scale: 0.5) [
  star(n)
  for n in 2..6
]
```

Especially since we can get *much* more complicated than that with what we're putting in the nested expression. 

So to do that, I want to be able to define three different list constructors, two based directly on Python (list literals and `for` lists, which are list generators) and another that's more specific to what I'm doing (`times` lists):

| mode | syntax | example |
|------|--------|---------|
| literal | `[ <nodes:node>* ]` | `[circle star { circle star }]` |
| for | `[ <nodes:node>* for <variable:identifier> in <expression:iterable> ]` | `[star(n) for n in 2..6]` |
| times | `[ <nodes:node>* times <variable:integer> ]` | `[star(5) times 3]` |

In each case, the initial list of children can be made of either nodes or groups. We can use the `.next` syntax here, so this will mostly be to distinguish `[circle star ...]` from `[{circle star} ...]` where in the first case we have two children: a `circle` and a `star` and in the second, we have only one: a `circle` with a `star` overlaid on it. 

So, how do we parse that?

```javascript
function parseList() {
  // Consume the opening [
  let token = tokens.shift()
  log.debug("parseList", token)

  let nodes = []

  // Lists can be:
  // literal-list:    [ <nodes:node>* ]
  // for-list:        [ <nodes:node>* for <variable:identifier> in <expression:iterable> ]
  // times-list:      [ <nodes:node>* times <variable:integer> ]

  while (true) {
    // Error state: never saw a closing ]
    if (tokens.length === 0) {
      log.error("unterminated list", token)
    }

    // Saw a ] before seeing for or times (see below), this must have been a literal list
    if (tokens[0].token === "]") {
      tokens.shift()
      return { type: "list", mode: "literal", nodes, token }
    }

    // If we see the `for` keyword, then we're parsing a `for` special form
    // [ <nodes:node>* for <variable:identifier> in <expression:iterable> ]
    if (tokens[0].token === "for") {
      // Consume the for and parse what the variable we're looping over is
      tokens.shift()
      let variable = parseIdentifier()

      // Error states: no more input or no 'in' keyword after the variable name
      if (tokens.length === 0) {
        log.error("unterminated for-list", token)
      } else if (tokens[0].token !== "in") {
        log.error("invalid for-list", token, { expected: "in", got: tokens[0] })
      }
      tokens.shift() // in

      // The expression should return any iterable object (we're fuzzy on times)
      // We only check this at runtime, for now, just parse an expression
      let expression = parseExpression()

      // The for list is done, make sure that we have a closing ]
      if (tokens.length === 0) {
        log.error("unterminated for-list", token)
      } else if (tokens[0].token != "]") {
        log.error("unterminated for-list", token, { expected: "]", got: tokens[0] })
      }

      // Consume the closing ] and return the `list` with mode `for`
      tokens.shift()
      return { type: "list", mode: "for", body: { type: "group", nodes }, variable, expression, token }
    }

    // If we see the `times` keyword, then we're parsing the `times` special form
    // [ <nodes:node>* times <variable:integer> ]
    if (tokens[0].token === "times") {
      // Consume the times
      tokens.shift()

      // Parse an expression, this should evaluate to a numeric value but we'll deal with that at runtime
      let expression = parseExpression()

      // That's everything for a times list, so make sure we have a closing ]
      if (tokens.length === 0) {
        log.error("unterminated times-list", token)
      } else if (tokens[0].token != "]") {
        log.error("unterminated times-list", token, { expected: "]", got: tokens[0] })
      }

      // Consume the closing ] and return the `times` `list`
      tokens.shift()
      return { type: "list", mode: "times", body: { type: "group", nodes }, expression, token }
    }

    // Otherwise we don't know what kind of list it is yet
    // But for all three cases, we will build up more nodes or groups
    // The next token ({, define, or anything else) defines what sort of child we're parsing next
    if (tokens[0].token === "{") {
      nodes.push(parseGroup())
    } else if (tokens[0].token === "define") {
      nodes.push(parseDefine())
    } else {
      nodes.push(parseNode())
    }

    // As we do in groups, apply the `.next` parameter
    if (nodes.length >= 2) {
      nodes[nodes.length - 2].next = nodes[nodes.length - 1]
    }
  }
}
```

I think the main oddity here is that while we know we're parsing a list, we don't actually know which kind (literal/for/times) we're parsing until we see either the `for` or `times` keyword. We don't have to have a state machine though, because in both cases there's an exact (known) number of children after those nodes: `for` has 3 more things to parse after the `for`, times has 1. 

Here again, we have the recursion. We're relying only on the previously defined `parseGroup` / `parseDefine` / `parseNode` for objects in the list. Pretty cool!

## Demo

Okay. That's a lot of parsing... so far we can parse groups, nodes, parameters, and lists. That leaves two big ones: expressions and defines. I think each of those is complicated enough to give their own post, so we'll be back for that. Keep posted! 

But for now, a demo of parsing!

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
rune { 
  radial(scale: 0.5) [
    star(n)
    for n in 2..6
  ]
}
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
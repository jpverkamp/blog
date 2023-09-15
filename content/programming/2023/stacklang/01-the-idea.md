---
title: "StackLang Part I: The Idea"
date: '2023-04-14 23:00:00'
programming/languages:
- Rust
- StackLang
programming/topics:
- Assemblers
- Compilers
- Memory
- Data Structures
- Stacks
- Virtual Machines
series:
- StackLang
---
I enjoy writing programming languages. [[A 'Tiny' virtual machine in Racket|Example: Tiny]](). Let’s do that again. 

This time, StackLang:

```text
{
  @[n fact]
  1
  { n 1 - $fact fact n * }
  N 1 <= if
} @fact

5 $fact fact writeln
```

Bit of gibberish there, I suppose, but the goal is to write everything in a postfix/stack based model. So `n 1 - $fact fact n *` is equivalent to `fact(fact, n - 1) * n` in a more traditional language. 

Over the next few posts, I hope to write up where I am thus far and what’s next. 

<!--more-->

---

Posts in this series:

{{< taxonomy-list "series" "StackLang" >}}

This post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)


## Literals
You have to start somewhere!

First, literals I support or intend to support:

* Numbers: a Lisp/Scheme style {{<wikipedia "numeric tower">}}: integers, rational numbers, floats, and complex numbers
* Strings: double quoted; I intend to include multi line strings but I’m not sure if I want to support that with normal strings, backticks (JavaScript style), or triple quoted (Python style)
* Booleans: true and false

### The Numeric Tower

As in many Schemes, numbers form a ‘numeric tower’ of increasing complexity. When any mathematical operation is performed, numeric values will be automatically implicitly coerced to the same type. So adding a rational and float will result in a float, for example. 

To convert the other way (and possibly truncate values) must be done explicitly. 

## Identifiers and Named Indexes
I’m currently going Scheme style with identifiers. If you want to name a variant `is-awesome?`, go for it. The only exceptions are:

1. Brackets. `{}` define blocks, `[]` define lists, and `()` are for grouping. None of these can be used in an identifier. 
2. Dots, `.`. I intend to allow struct fields and implemented methods to use dot syntax directly. See {{[structs](#structs)}} for more information. So not dots in identifiers. 
3. Special prefixes; these symbols have a special meaning when attached to the beginning of an identifier (so they’re allowed in identifiers but not as the prefix): 
	* `@` names the top value of the stack, so `@n` lets you write `n` later to push whatever value is ‘at’ `n`, no matter how far down the stack
	* `!` writes to a named variable, so `5 !n` is equivalent to `n = 5`; you can just use the same name again (and shadow the previous one)
	* `$` lets you pass a block as a value rather than applying it, I’ll demonstrate this later

Other than that, most anything goes. Whitespace, brackets, and dots act as delimiters. Anything that can be parsed as a different sort of literal will be. 

## Blocks
Blocks are the building blocks (heh) of more complicated control structures. Every block will be delimited by `{}`, have a two part arity: in and out (see below), and then have as many other expressions as needed. 

Here are some example blocks:

```text
# Add 2 to the top value of the stack
{ 2 + }

# Duplicate the top value of the stack
{ @n !2 n n }

# Test if a number is even or odd
{ @n “even” “odd” n 2 % 0 == if }
```

### Arity

Since all functions use the same stack, arity in is the number of variables that are available from the call site (and will be removed by calling the block). As an example, most mathematical functions have an arity in of 2. `if` has an arity in of 3 (true, false, and condition). Literals can be thought of as having an arity in of 0. 

Likewise, arity out is how many more values should be on the stack after execution. So mathematical expressions have arity out of 1 as do literals. `writeln` has an arity out of 0; it doesn’t output anything. 

### Implicit Arity

When possible, the arity of a block will be automatically calculated. So, `{ 2 + }` has an implicit arity of 1 to 1. It will read one value, (add 2 to it), and return one value. If an arity cannot be determined though, you can (and must) specify it explicitly. 

### Explicit arity

To explicitly specify the arity, the first 1 or 2 expressions of the the block are used with `@` for arity in and `!` for arity out:

* `@n` specifies an arity in of 1 and assigns the name `n`
* `@[a b c]` specified an arity in of 3 and assigns the names `a`, `b`, and `c`. In this case `c` will be the current top of the stack with `b` beneath it and`a` beneath that
* `@2` specifies an arity in of 2 without naming any variables 
* If only arity out is specified explicitly, arity in is assumed to be 0
* `!n` specifies an output arity of 1 from the named value `n` rather than the top of the stack
* `![a b c]` specifies an output arity of 3 from the named variables, `a` pushed first and `c` last
* `!2` specifies an arity out of 2 from the top of the stack
* If only arity in is specified explicitly, arity out is assumed to be 1

### Extra data

It’s entirely possible to work with more data on the stack than the output arity. When that happens, any extra values are dropped and the arity out values will end up at the new top of the stack. 

So this block:

```text
{
  @n
  “Hello” 42 “times”
  n
}
```

Will take in one value, push three values on top of it (Hello, 42, and times), the push a copy of whatever original value was in `n`. It will then drop the original `n`, the three pushed values, and move the copy of `n` to the stack and return control. 

### Naming blocks

A block is not directly evaluated, but rather placed on the stack, as would any other value. You can then name it with `@`, once again, the same as any other value. So this code creates the ‘function’ `add2` out of a block:

```text
{
  @n
  2 n + 
} @add2
```

At any future point, whenever you reference a block by name, it will be automatically applied, so:

```text
10 add2 # 12
```

Alternatively, you can directly `apply` a block with the built in of that same name. So if you for some reason wanted to, the following are equivalent:

```text
# Directly adding 5 + 7
5 7 +

# Creating an unnamed add7 block and applying it
5 { @n 7 n + } apply
```

### Passing a block to another block

This does raise the more ‘functional’ question of what do you do if you want to pass a block to another block. This is what the prefix `$` is for:

```text
{ @[n f] n f f } do-twice

10 $add2 do-twice # passed add2 as f, result is 12
```

### Explicit recursion

Being able to pass a block to itself allows for recursion. For example, to recursively define the factorial function, you could do:

```text
{
	@[n fact]
  1
  { @n n 1 - $fact fact n * }
  n 1 <= if
} @fact

5 $fact fact # 120
```

I’m still working on a better syntax for that. Options are `5 fact.recur` and `$block @fact` within the block. 

## Control flow
There are currently only two control flow structures that I have added, although I will likely add more: `if` and `loop`. 

`if` takes 3 variables: the value or block if true, value or block if false, and conditional. As mentioned, the value or block for true or false can be either. If it’s a block, the one that is not chosen will not be evaluated (to, for example, prevent infinite recursion in the `factorial` example above. 

Each of the blocks (and the literals, although this comes for free) should have the same arity. 

`loop` takes a block and an iterable or number. If it’s an iterable, it will call the block once with each value of the iterable. If a number, it will count up from 0 to n-1. So, for example, you could implement factorial like this:

```text
{
  @n
  1 { 1 + * } n loop
} @fact
```
 
This will start with 1 and then from 0 to n-1 take the number, add 1 to it, and multiply the current top of the stack by it. This loop body has an implicit arity in of 2 and arity out of 1. The arity of the loop block can be anything, but not having out be 1 less than in can cause odd side effects (that will be dropped when the enclosing block returns). 

## Structs
Currently all values are simple single values you can store on the stack. But you can do also define custom structs with custom methods like this:

```text
[ x y ] @Point

{
  @[self other]
  self.x other.x +
  self.y other.y +
  Point
} Point.add

2 3 Point @p1
4 5 Point @p2
P2 p1.add 
# [6 7]
```

The dot syntax can also act on a non-named value on top of the stack if there’s nothing before the dot:

```text
2 3 Point 
4 5 Point
.add # [6 7]
```

In this case, the `.add` is being called on the Point `[4, 5]` with `[2, 3]` as other, which may be counter intuitive, so naming is probably the more common approach. 

## That's all for now

Okay, that's more than enough to get going with, next up... lexing!
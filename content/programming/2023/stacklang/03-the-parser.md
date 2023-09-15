---
title: "StackLang Part III: The Parser"
date: '2023-04-24 00:01:00'
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
StackLang, part 3: parsing. This is going to be the most complicated one thus far! Onward.  

<!--more-->

---

Posts in this series:

{{< taxonomy-list "series" "StackLang" >}}

This post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## Types

Okay, things are getting more interesting. Let's start where I generally do, with the types. In this case, I'm going to split things to a few levels. 

### `Expression` - the AST itself

Starting at the top level, we have expressions. These are the actual AST and represent one level of the eventual parse tree:

```rust
/// An expression is a single unit of a program, part of the AST
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Expression {
    /// An identifier/variable, used to lookup a named value or global
    Identifier(String),
    /// A literal value
    Literal(Value),

    /// A function definition, generally delimited with {}
    Block(Vec<Expression>),
    /// A list of values, generally delimited with []
    List(Vec<Expression>),
    /// A group of values, generally delimited with (), currently used only for clean code
    Group(Vec<Expression>),

    /// An @ prefixed expression, used to name values on the stack
    /// If followed by [], an @list is multiple names
    At(Box<Expression>),
    /// A ! prefixed expression, used to set values by name
    Bang(Box<Expression>),
    /// A $ prefixed expression, used to pass to the stack (only really needed for blocks)
    Dollar(Box<Expression>),
}
```

It's actually for the most part simpler than a lot of ASTs, since (like S-Expression based languages) we really don't have much complicated syntax. In this case, there are broadly three groups:

* Single tokens: literal values (like `42`, `"Hello world"`, etc; [we'll get there](#values)) and identifiers (anything else)
* Groups of subexpressions (these could probably have been one expression with a node that stores which type it is but I found this better since they work differently):
  * Blocks, defined with `{}`, essentially function definitions, important since these will have their own arity
  * Lists, defined with `[]`, currently only used in list naming `@[a b c]`
  * Groups, defined with `()`, implicitly used for the 'main' block, but can be used to group code mostly for visual appeal, because of the stack nature, doesn't actually modify control flow or introduce scopes
* Prefixed expressions:
  * `@` expressions, for naming values; the expression should be a single identifier, a list of identifiers, or an integer (arity in), but that isn't a parse time check yet
  * `!` expressions, for setting values by name or setting arity out; should be a single identifier or integer (arity)
  * `$` expressions, for passing blocks as a parameter rather than applying them

One interesting bit is the implementation of `Display` for `Expression`:

```rust

macro_rules! write_children {
    ($f:ident $prefix:literal $children:ident $suffix:literal) => {{
        let mut s = String::new();
        s.push($prefix);
        for (i, child) in $children.iter().enumerate() {
            s.push_str(&format!("{}", child));
            if i != $children.len() - 1 {
                s.push(' ');
            }
        }
        s.push($suffix);
        write!($f, "{}", s)
    }};
}

impl Display for Expression {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Expression::Identifier(id) => write!(f, "{}", id),
            Expression::Literal(value) => write!(f, "{}", value),
            Expression::Block(children) => write_children! {f '{' children '}'},
            Expression::List(children) => write_children! {f '[' children ']'},
            Expression::Group(children) => write_children! {f '(' children ')'},
            Expression::At(expr) => write!(f, "@{}", expr),
            Expression::Bang(expr) => write!(f, "!{}", expr),
            Expression::Dollar(expr) => write!(f, "${}", expr),
        }
    }
}
```

It should be possible to round trip this: `Display`ed code should be readable. Mostly the goal is to display expressions without using up quite so much screen real estate. Don't have tests for that though.

### `Value` - values on the stack + literals

Okay, we have expressions, but we're missing `Value`. That's any `Value` that can actually be stored on the stack, but is also used for literals.

```rust
/// A value is a literal value that has been evaluated.
#[derive(Clone, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Value {
    Number(Number),
    String(String),
    Boolean(bool),
    Block {
        arity_in: usize,
        arity_out: usize,
        expression: Box<Expression>,
    },
}

impl Display for Value {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}",
            match self {
                Value::Number(v) => v.to_string(),
                Value::String(v) => v.to_string().trim_matches('"').to_string(),
                Value::Boolean(v) => v.to_string(),
                Value::Block {
                    arity_in,
                    arity_out,
                    ..
                } => format!("{{{}->{}}}", arity_in, arity_out),
            }
        )
    }
}
```

Numbers are further distinguished ([see below](#numbers)). Otherwise, it's strings, booleans, or blocks. Blocks shouldn't show up in the parser, they're when Values are used as values on the stack, but they're defined here anyways. 

### `Number` - the numeric tower

The [[wiki:numeric tower]]().

```rust
/// The numeric tower
#[derive(Copy, Clone, Debug)]
pub enum Number {
    Integer(i64),
    // Rational(i64, i64),
    Float(f64),
    // Complex(f64, f64),
}
```

So... I haven't actually written `Rational` or `Complex` values yet! But I'm getting there. 

I do want to implement the various mathematical traits for numbers on these values though, so let's give that a try:

```rust
macro_rules! do_op {
    ($trait:ty, $f:ident, $op:tt) => {
        impl $trait for Number {
            type Output = Number;

            fn $f(self, rhs: Self) -> Self::Output {
                let (a, b) = Number::coerce(self, rhs);
                match (a, b) {
                    (Number::Integer(av), Number::Integer(bv)) => Number::Integer(av $op bv),
                    (Number::Float(av), Number::Float(bv)) => Number::Float(av $op bv),
                    _ => unreachable!(),
                }
            }
        }
    };
}

do_op!(Add, add, +);
do_op!(Sub, sub, -);
do_op!(Mul, mul, *);
do_op!(Div, div, /);
do_op!(Rem, rem, %);

impl PartialEq for Number {
    fn eq(&self, other: &Self) -> bool {
        let (a, b) = Number::coerce(*self, *other);
        match (a, b) {
            (Number::Integer(av), Number::Integer(bv)) => av == bv,
            (Number::Float(av), Number::Float(bv)) => av == bv,
            _ => unreachable!(),
        }
    }
}

impl Eq for Number {}

impl PartialOrd for Number {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        let (a, b) = Number::coerce(*self, *other);
        match (a, b) {
            (Number::Integer(av), Number::Integer(bv)) => av.partial_cmp(&bv),
            (Number::Float(av), Number::Float(bv)) => av.partial_cmp(&bv),
            _ => unreachable!(),
        }
    }
}
```

I don't know if this will actually work for `Rational` / `Complex`. We'll figure that out. 

I think that what I'm going to have to do is to create a new `Rational` struct and then implement `Number::Rational` as `Rational(Rational)` (or something less confusing). That way, I can implement `Add` etc manually on that type and everything else will just work (tm). 

We'll see. 

### Future work: type constructors / macros

One problem that I've been running into a bit is code like this:

```rust
#[test]
fn test_integer() {
    let input = tokenize("123".as_bytes());
    let output = parse(input);
    assert_eq!(
        output,
        Expression::Group(vec![Expression::Literal(Value::Number(Number::Integer(
            123
        )))])
    );
}
```

Having a `Group` of one `Literal`, which is a `Number`, specifically an `Integer` is... annoying. At the very least, being able to write `Literal::make_integer(123)` would be nice. 

Or alternatively, with macros: `group!{integer!(123)}`. 

Or perhaps a single macro: `expr!{ group(integer(123)) }`. But at that point, we're re-writing the parser. We'll see. 

## Parsing

Okay. That's fun, but a worthwhile framework. Now that we have that, I'm going to have to start actually parsing things, probably with a `pub fn parse(tokens: Vec<Token>) -> Expression` function. But to do that, I think that I want to split it into two helper functions:

* 
    ```
    fn parse_one(tokens: &[Token]) -> (Expression, &[Token])
    ```
    
    given a slice of `Token`, consume enough to parse one expression and return the remaining slice of `Token`

* 
    ```rust
    fn parse_until(tokens: &[Token], ending: Option<String>) -> (Vec<Expression>, &[Token])
    ```

    given a slice of `Token` and an `ending`, parse until we see the `ending` character; this is for parsing block etc expressions until you reach the `}` / `]` / `)`

    `ending` is `Option` for the `main` block (that doesn't have a delimiter); in that case, parse until the end of the `Token` slice

### `parse_until` - for blocks of code

Since the latter is actually easier (and depends on `parse_one`), let's start with that:

```rust
// A helper to parse a list of expressions until a given ending token
// If ending is not set, parse until end of stream
fn parse_until(tokens: &[Token], ending: Option<String>) -> (Vec<Expression>, &[Token]) {
    let mut tokens = tokens;
    let mut expressions = vec![];

    while !tokens.is_empty() && Some(tokens[0].token.clone()) != ending {
        let (expression, next_tokens) = parse_one(tokens);
        expressions.push(expression);
        tokens = next_tokens;
    }

    if !tokens.is_empty() && Some(tokens[0].token.clone()) == ending {
        (expressions, &tokens[1..])
    } else {
        (expressions, tokens)
    }
}
```

That really is it. For each token (until we hit the ending), `parse_one` and collect them. If we hit the ending (or end of slice), we're done. 

Return the sub slice--this advances the tokens that we've already consumed, so we can start from where we left off. This is something I really like about Rust. Slices are a window (+ reference) into a section of memory, so it's cheap to get a sub slice, rather than copying `Vec` around. 

### `parse_one` - for single expressions

This is the much more interesting one. 

```rust
// A helper to parse a single expression from the current position in the token stream
fn parse_one(tokens: &[Token]) -> (Expression, &[Token]) {
    if tokens[0].token == "@" {
        // @ expressions prefix the next value (naming)
        let (next, tokens) = parse_one(&tokens[1..]);
        (Expression::At(Box::new(next)), tokens)
    } else if tokens[0].token == "!" {
        // ! expressions prefix the next value (assignment)
        let (next, tokens) = parse_one(&tokens[1..]);
        (Expression::Bang(Box::new(next)), tokens)
    } else if tokens[0].token == "$" {
        // $ expressions allow pushing a block to the stack
        let (next, tokens) = parse_one(&tokens[1..]);
        (Expression::Dollar(Box::new(next)), tokens)
    } else if tokens[0].token == "{" {
        // { expressions are blocks
        let (children, tokens) = parse_until(&tokens[1..], Some(String::from("}")));
        (Expression::Block(children), tokens)
    } else if tokens[0].token == "[" {
        // [ expressions are lists
        let (children, tokens) = parse_until(&tokens[1..], Some(String::from("]")));
        (Expression::List(children), tokens)
    } else if tokens[0].token == "(" {
        // ( expressions are groups
        let (children, tokens) = parse_until(&tokens[1..], Some(String::from(")")));
        (Expression::Group(children), tokens)
    } else {
        // Try to parse each literal value, if none match assume it's an identifier
        if let Some(v) = tokens[0].token.parse::<i64>().ok() {
            (
                Expression::Literal(Value::Number(Number::Integer(v))),
                &tokens[1..],
            )
        } else if let Some(v) = tokens[0].token.parse::<f64>().ok() {
            (
                Expression::Literal(Value::Number(Number::Float(v))),
                &tokens[1..],
            )
        } else if tokens[0].token.starts_with("\"") {
            (
                Expression::Literal(Value::String(
                    tokens[0].token.trim_matches('"').to_string(),
                )),
                &tokens[1..],
            )
        } else if tokens[0].token == "true" || tokens[0].token == "false" {
            (
                Expression::Literal(Value::Boolean(tokens[0].token == "true")),
                &tokens[1..],
            )
        } else {
            (
                Expression::Identifier(tokens[0].token.clone()),
                &tokens[1..],
            )
        }
    }
}
```

A bit more complicated. Similar to the same breakdown of the [`Value` struct](#values), we have three parts (albeit in reverse order): prefixed expressions, nested expressions, and literals. 

For prefixed expressions, they're all the same:

```rust
if tokens[0].token == "@" {
    // @ expressions prefix the next value (naming)
    let (next, tokens) = parse_one(&tokens[1..]);
    (Expression::At(Box::new(next)), tokens)
}
```

Take and consume the `@`, `parse_one` the expression it's prefixing, and return the new `Expression:At` plus the next `tokens` (from the subexpression).

For subexpressions, likewise, we're the same (and this is why we have `parse_until` as a separate function):

```rust
if tokens[0].token == "{" {
    // { expressions are blocks
    let (children, tokens) = parse_until(&tokens[1..], Some(String::from("}")));
    (Expression::Block(children), tokens)
}
```

`parse_until` the matching delimiter and return the new `Expression::Block` and the point in `tokens` after that. 

And finally, literals. These are a bit more interesting, but another reason that I'm really liking Rust. The `parse` function will try to parse the given token into whatever type we give it (using that type's `FromStr` trait). If it can, use `if let Some(v)` to unpack it and return. If not, fall through to the next case.

```rust
if let Some(v) = tokens[0].token.parse::<i64>().ok() {
    (
        Expression::Literal(Value::Number(Number::Integer(v))),
        &tokens[1..],
    )
}
```

All without exceptions! I like it. 

### Starting the parser

And that's it. Now just tie it together:

```rust
/// Parses a vector of tokens into a vector of expressions.
pub fn parse(tokens: Vec<Token>) -> Expression {
    log::debug!("parse({:?})", tokens);

    // A helper to parse a single expression from the current position in the token stream
    fn parse_one(tokens: &[Token]) -> (Expression, &[Token]) {
        // ... 
    }

    // A helper to parse a list of expressions until a given ending token
    // If ending is not set, parse until end of stream
    fn parse_until(tokens: &[Token], ending: Option<String>) -> (Vec<Expression>, &[Token]) {
        // ...
    }

    // Parse the entire stream
    // TODO: This should be an exception if the stream is not empty after this
    Expression::Group(parse_until(tokens.as_slice(), None).0)
}
```

## Testing

As before, I'm actually writing some unit tests! Thank you Github Co-Pilot. 

```rust
#[cfg(test)]
mod test {
    use crate::lexer::tokenize;
    use crate::numbers::Number;
    use crate::parser::parse;
    use crate::types::{Expression, Value};

    #[test]
    fn test_integer() {
        let input = tokenize("123".as_bytes());
        let output = parse(input);
        assert_eq!(
            output,
            Expression::Group(vec![Expression::Literal(Value::Number(Number::Integer(
                123
            )))])
        );
    }

    // ...

    #[test]
    fn test_factorial() {
        let input = tokenize(
            "
{
  @[n fact]
  1
  { @0 n 1 - $fact fact n * }
  n 1 < if
} @fact

5 $fact fact writeln"
                .as_bytes(),
        );
        let output = parse(input);
        assert_eq!(
            output,
            Expression::Group(vec![
                Expression::Block(vec![
                    Expression::At(Box::new(Expression::List(vec![
                        Expression::Identifier(String::from("n")),
                        Expression::Identifier(String::from("fact")),
                    ]))),
                    Expression::Literal(Value::Number(Number::Integer(1))),
                    Expression::Block(vec![
                        Expression::At(Box::new(Expression::Literal(Value::Number(
                            Number::Integer(0)
                        )),)),
                        Expression::Identifier(String::from("n")),
                        Expression::Literal(Value::Number(Number::Integer(1))),
                        Expression::Identifier(String::from("-")),
                        Expression::Dollar(Box::new(Expression::Identifier(String::from("fact")))),
                        Expression::Identifier(String::from("fact")),
                        Expression::Identifier(String::from("n")),
                        Expression::Identifier(String::from("*")),
                    ]),
                    Expression::Identifier(String::from("n")),
                    Expression::Literal(Value::Number(Number::Integer(1))),
                    Expression::Identifier(String::from("<")),
                    Expression::Identifier(String::from("if")),
                ]),
                Expression::At(Box::new(Expression::Identifier(String::from("fact")))),
                Expression::Literal(Value::Number(Number::Integer(5))),
                Expression::Dollar(Box::new(Expression::Identifier(String::from("fact")))),
                Expression::Identifier(String::from("fact")),
                Expression::Identifier(String::from("writeln")),
            ])
        );
    }
}
```

Writing that by hand would be a *pain*. But Co-Pilot doesn't mind!

## What's next?

Onward!

Next up, I'm planning to:

* Type checking:
  * Automatically determine the `arity` of blocks when possible
  * Automatically determine specific types of expressions (including blocks)
* Numeric tower:
  * Implement rationals/complex numbers at the parser level + in any interpreter / compiler I have at that point
  * Implement automatic numeric coercion--if you try to add an integer to a complex number, the result should be a complex number
* Interpreters:
  * An AST-walking interpreter, directly evaluating the AST
  * A bytecode interpreter/compiler, evaluating at a lower level (I'm not sure how much this would gain, the AST is already fairly low level)
* Compilers:
  * Compile to C (and then pass to GCC/Clang) to compile that
  * Compile to WASM; since it's also stack based, this should be interesting
  * Compile to x86/ARM assembly


---
title: "StackLang Part IV: An Interpreter"
date: '2023-05-01 23:00:00'
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
StackLang, part 4: an interpreter. Here we go again! 

This time, the goal is to actually get code running

<!--more-->

---

Posts in this series:

{{< taxonomy-list "series" "StackLang" >}}

This post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## The main function

Okay, let's start this off. Here's the entire structure:

```rust
use crate::arity::calculate_arity;
use crate::numbers::Number;
use crate::stack::Stack;
use crate::types::{Expression, Value};

/// Evaluates a vector of expressions
/// This does not actually return anything, but instead mutates the stack
#[allow(dead_code)]
pub fn evaluate(ast: Expression) {
    log::debug!("evaluate({})", ast);

    // ...

    // Internal eval function, carries the stack with it and mutates it
    fn eval(node: Expression, stack: &mut Stack) {
        log::info!("eval({node}, {stack})");

        // Handle running a block
        fn eval_block(
            stack: &mut Stack,
            arity_in: usize,
            expression: Box<Expression>,
            arity_out: usize,
        ) {
            // ...
        }

        // Cloned for debug printing
        match node.clone() {
            Expression::Identifier(id) => {
                // ...
            }
        };
    }

    // At the top level, create the stack and evaluate each expression
    let mut stack = Stack::new();
    eval(ast, &mut stack);
}
```

So we have a basic evaluation function. It's going to set up a [stack](#the-stack-type) that will handle the data and then evaluate an AST node. Each node knows how to evaluate itself (given this function), with blocks being the most complicated of them and [having their own function](#evaluating-blocks). 

## The `Stack` type

So, what is a stack? 

In this case (in theory) it's a linear sequence of values in memory. Some of those values can be accessed by names. That's the complicated bit: if we're accessing a value by name, it could be at the current level *or it could be at a previous level*. 

So let's use this as our `struct`:

```rust
/// A stack in the context of the VM
///
/// This will actually have a stack of data, and a map of names to stack indices
/// These are also nested by block; when a new block is entered, a new stack is created
#[derive(Debug, Clone, Default)]
pub struct Stack {
    // The values on the stack
    data: Vec<Value>,
    // A mapping of names to indices in the data
    names: HashMap<String, usize>,
    // The parent of this stack for name lookups
    parent: Option<Rc<Stack>>,
}
```

Then, implementation:

```rust
impl Stack {
    /// Creates a new top level stack
    pub fn new() -> Self {
        Stack::default()
    }

    /// Creates a new stack with the current stack as its parent
    ///
    /// n is the number of values to pop from the parent stack and push onto this one
    pub fn extend(&mut self, n: usize) -> Self {
        let mut values = vec![];
        for _ in 0..n {
            values.push(self.pop().unwrap());
        }
        values.reverse();

        Stack {
            data: values,
            names: HashMap::new(),
            parent: Some(Rc::new(self.clone())),
        }
    }

    /// Pushes a value onto the stack
    pub fn push(&mut self, value: Value) {
        self.data.push(value);
    }

    /// Pops a value off the stack
    ///
    /// TODO: Handle popping a named value
    pub fn pop(&mut self) -> Option<Value> {
        self.data.pop()
    }

    /// Assign a new name to the top value on the stack
    ///
    /// A single stack can have multiple names for the same value
    pub fn name(&mut self, name: String) {
        self.names.insert(name, self.data.len() - 1);
    }

    /// Assigns a new name to the top N values of the stack (from bottom to top)
    ///
    /// If the stack is [8, 6, 7, 5], name_many("A", "B") would result in [8, 6, 7@A, 5@B]
    pub fn name_many(&mut self, names: Vec<String>) {
        for (i, name) in names.iter().enumerate() {
            self.names
                .insert(name.clone(), self.data.len() - names.len() + i);
        }
    }

    /// Get a named value from this stack (including the parent) if it exists
    ///
    /// If this stack doesn't have it, check the parent
    pub fn get_named(&self, name: String) -> Option<Value> {
        log::debug!("get_named({}) from {}", name, self);

        if self.names.contains_key(&name) {
            Some(self.data[self.names[&name]].clone())
        } else if self.parent.is_some() {
            self.parent.as_ref().unwrap().get_named(name)
        } else {
            None
        }
    }
}
```

Among those:

* `extend` is for making a new nested stack level
* `push` / `pop` are the standard stack functions
* `name` will assign a name to the top of the stack (with `@n`)
* `name_many` will assign many names (with `@[a b c]`)
* `get_named` will look up a value by name, looking in this scope and then any previous scope

Works pretty well for me!

## Evaluating values

### Literal values

These are easy. Just push them onto the stack:

```rust
// Literal values are just pushed onto the stack
Expression::Literal(value) => stack.push(value.clone()),
```

### `at` (`@`) expressions

These have three interesting cases:

* single values
* list names
* integer naming expressions (for setting arity, doesn't actually do anything)

```rust
// @ expressions name the top value on the stack
// @[] expressions name multiple values
Expression::At(subnode) => {
    match subnode.as_ref() {
        // Specifying input arity, ignore
        Expression::Literal(Value::Number(Number::Integer(_))) => {}
        // Naming the top of the stack
        Expression::Identifier(name) => {
            stack.name(name.clone());
        }
        // Naming several values at once on top of the stack
        Expression::List(exprs) => {
            let mut names = vec![];
            for expr in exprs {
                match expr {
                    Expression::Identifier(name) => names.push(name.clone()),
                    _ => panic!("Invalid @ expression, @[list] must contain only names, got {:?}", node)
                }
            }
            stack.name_many(names.clone())
        }
        _ => panic!(
            "Invalid @ expression, must be @name or @[list], got {:?}",
            node
        ),
    }
}
```

### `bang` (`!`) expressions

I've ... not actually implemented these yet. 

```rust
// ! expressions set (or update) the value of named expressions
Expression::Bang(subnode) => {
    match subnode.as_ref() {
        // Output expression, ignore
        Expression::Literal(Value::Number(Number::Integer(_))) => {}

        // Write to a named variable
        Expression::Identifier(_name) => todo!(),

        // Anything else doesn't currently make sense
        _ => panic!("Invalid ! expression, must be !# or !name, got {:?}", node),
    }
}
```

So far, everything is more functional and doesn't need them. We'll have to see if this is something we actually need. 

### Identifier expressions and built ins

So this one is certainly longer. We'll start with the built ins, since anything that isn't a built in will instead by a lookup by name. 

```rust
// Identifiers are globals are named expressions
// TODO: Extract globals into their own module
Expression::Identifier(id) => {
    match id.as_str() {
        // Built in numeric functions
        "+" => numeric_binop!(stack, |a, b| { a + b }),
        "-" => numeric_binop!(stack, |a, b| { a - b }),
        "*" => numeric_binop!(stack, |a, b| { a * b }),
        "/" => numeric_binop!(stack, |a, b| { a / b }),
        "%" => numeric_binop!(stack, |a, b| { a % b }),
        // Built in comparisons
        "<" => comparison_binop!(stack, |a, b| { a < b }),
        "<=" => comparison_binop!(stack, |a, b| { a <= b }),
        "=" => comparison_binop!(stack, |a, b| { a == b }),
        ">=" => comparison_binop!(stack, |a, b| { a >= b }),
        ">" => comparison_binop!(stack, |a, b| { a > b }),
        // Convert a value to an int if possible
        "int" => {
            let value = stack.pop().unwrap();
            match value {
                Value::String(s) => {
                    stack.push(Value::Number(Number::Integer(s.parse().unwrap())))
                }
                Value::Number(n) => stack.push(Value::Number(n.to_integer())),
                _ => panic!("int cannot, got {}", value),
            }
        }
        // Apply a block to the stack
        "apply" => {
            let block = stack.pop().unwrap();
            match block {
                Value::Block {
                    arity_in,
                    arity_out,
                    expression,
                } => {
                    eval_block(stack, arity_in, expression, arity_out);
                }
                _ => panic!("apply expects a block, got {}", block),
            }
        }
        // Read a line from stdin as a string
        "read" => {
            let mut input = String::new();
            match std::io::stdin().read_line(&mut input) {
                Ok(_) => {
                    stack.push(Value::String(input.trim_end_matches('\n').to_string()));
                }
                Err(e) => {
                    panic!("failed to read from stdin: {e}");
                }
            };
        }
        // Pop and write a value to stdout
        "write" => {
            print!("{}", stack.pop().unwrap());
        }
        // Pop and write a value to stdout with a newline
        "writeln" => {
            println!("{}", stack.pop().unwrap());
        }
        // Write a newline
        "newline" => {
            println!();
        }
        // Loop over an iterable, expects a block and an iterable
        "loop" => {
            let iterable = stack.pop().unwrap();
            let block = stack.pop().unwrap();

            match iterable {
                Value::Number(Number::Integer(n)) => {
                    if n < 0 {
                        panic!("numeric loops must have a positive integer, got {}", n);
                    }

                    for i in 0..n {
                        stack.push(Value::Number(Number::Integer(i)));
                        match block.clone() {
                            // Blocks get evaluated lazily (now)
                            Value::Block { arity_in, arity_out, expression } => {
                                eval_block(stack, arity_in, expression, arity_out);
                            },
                            // Loops must have a block
                            _ => panic!("loop must have a block, got {}", block),
                        }
                    }
                },
                Value::String(s) => {
                    for c in s.chars() {
                        stack.push(Value::String(c.to_string()));
                        match block.clone() {
                            Value::Block { arity_in, arity_out, expression } => {
                                eval_block(stack, arity_in, expression, arity_out);
                            },
                            _ => panic!("loop must have a block, got {}", block),
                        }
                    }
                },
                _ => panic!("loop must have an iterable (currently an integer or string), got {}", iterable),
            };
        }
        // If statement, expects two blocks or literals and a conditional (must be boolean)
        "if" => {
            let condition = stack.pop().unwrap();
            let false_branch = stack.pop().unwrap();
            let true_branch = stack.pop().unwrap();

            log::debug!(
                "if condition: {}, true: {}, false: {}",
                condition,
                true_branch,
                false_branch
            );

            let branch = match condition {
                Value::Boolean(value) => {
                    if value {
                        true_branch
                    } else {
                        false_branch
                    }
                }
                _ => panic!("if condition must be a boolean, got {}", condition),
            };

            log::debug!("if selected: {}", branch);

            match branch {
                // Blocks get evaluated lazily (now)
                Value::Block {
                    arity_in,
                    arity_out,
                    expression,
                } => {
                    eval_block(stack, arity_in, expression, arity_out);
                }
                // All literal values just get directly pushed
                _ => {
                    stack.push(branch);
                }
            }
        }
        name => {
            if let Some(value) = stack.get_named(String::from(name)) {
                if let Value::Block {
                    arity_in,
                    arity_out,
                    expression,
                } = value
                {
                    eval_block(stack, arity_in, expression, arity_out);
                } else {
                    stack.push(value);
                }
            } else {
                panic!("Unknown identifier {:?}", name);
            }
        }
    }
}
```

Because we have the `stack` and the `eval` function, we can directly implement these. The most interesting ones are the ones that have blocks, such as `if` expressions. That's why we need [`eval_block`](#evaluating-blocks). 

Other than that, we're looking up values by name (at the end). One thing that we're going to have to do here is determine if it's a block ([`eval_block` it](#evaluating-blocks)) or a value (push it). 

### Binops and coercion

One more, we have a few macros you've probably seen (with `+` etc) that is designed to automatically convert the values to the same type before applying them:

```rust
/// A helper macro to generate functions that operate on two integers and floats
macro_rules! numeric_binop {
    ($stack:expr, $f:expr) => {{
        // TODO: Check we have enough values
        let b = $stack.pop().unwrap();
        let a = $stack.pop().unwrap();

        match (a.clone(), b.clone()) {
            (Value::Number(a), Value::Number(b)) => {
                $stack.push(Value::Number($f(a, b)));
            }
            _ => panic!(
                "cannot perform numeric operation on non-numeric values, got {} and {}",
                a, b
            ),
        };
    }};
}

/// A helper macro to generate functions that operate on two integers and floats
macro_rules! comparison_binop {
    ($stack:expr, $f:expr) => {{
        // TODO: Check we have enough values
        let b = $stack.pop().unwrap();
        let a = $stack.pop().unwrap();

        match (a.clone(), b.clone()) {
            (Value::Number(a), Value::Number(b)) => {
                $stack.push(Value::Boolean($f(a, b)));
            }
            // TODO: Handle other types
            _ => panic!(
                "cannot perform comparison operation on non-numeric values, got {} and {}",
                a, b
            ),
        };
    }};
}
```

Having that in a macro so that all of the functions use the same code without duplicating it is pretty cool, not going to lie. 

And that's all there is, except:

### Evaluating blocks

All this actually has to do is pushing a new stack:

```rust
// Handle running a block
fn eval_block(
    stack: &mut Stack,
    arity_in: usize,
    expression: Box<Expression>,
    arity_out: usize,
) {
    // Extend the stack with arity_in values
    let mut substack = stack.extend(arity_in);
    log::debug!("substack: {}", substack);

    // Evaluate the block with that new stack context
    eval(expression.as_ref().clone(), &mut substack);
    log::debug!("substack after eval: {}", substack);

    // Copy arity_out values to return, drop the rest of the substack
    // TODO: should this be a stack method?
    let mut results = vec![];
    for _ in 0..arity_out {
        results.push(substack.pop().unwrap())
    }
    results.reverse();

    for result in results {
        stack.push(result);
    }
}
```

When we call, we extend with the `arity_in` values. When we return, instead we will copy `arity_out` values from the top of the current level and move it down a level. Having these as nested values is... not great memory efficiency wise, but I suppose it will work for the time being. 

## Trying it out

So. How does it work?

```text
# factorial.stack
{
  @n
  1
  { @0 n 1 - fact n * }
  n 1 < if
} @fact

5 fact writeln
```

Running it:

```bash
┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ cargo run -- --file examples/factorial.stack

    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running `target/debug/stacklang --file examples/factorial.stack`
120
```

That's pretty cool. With debugging (only `info`, `debug` is so chatty) on:

```bash
┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ RUST_LOG=info cargo run -- --file examples/factorial.stack

    Finished dev [unoptimized + debuginfo] target(s) in 0.09s
     Running `target/debug/stacklang --file examples/factorial.stack`
 INFO  stacklang > Tokens: { @ n 1 { @ 0 n 1 - fact n * } n 1 < if } @ fact 5 fact writeln
 INFO  stacklang > AST:
Group(
    [
        Block(
            [
                At(
                    Identifier(
                        "n",
                    ),
                ),
                Literal(
                    Number(
                        Integer(
                            1,
                        ),
                    ),
                ),
                Block(
                    [
                        At(
                            Literal(
                                Number(
                                    Integer(
                                        0,
                                    ),
                                ),
                            ),
                        ),
                        Identifier(
                            "n",
                        ),
                        Literal(
                            Number(
                                Integer(
                                    1,
                                ),
                            ),
                        ),
                        Identifier(
                            "-",
                        ),
                        Identifier(
                            "fact",
                        ),
                        Identifier(
                            "n",
                        ),
                        Identifier(
                            "*",
                        ),
                    ],
                ),
                Identifier(
                    "n",
                ),
                Literal(
                    Number(
                        Integer(
                            1,
                        ),
                    ),
                ),
                Identifier(
                    "<",
                ),
                Identifier(
                    "if",
                ),
            ],
        ),
        At(
            Identifier(
                "fact",
            ),
        ),
        Literal(
            Number(
                Integer(
                    5,
                ),
            ),
        ),
        Identifier(
            "fact",
        ),
        Identifier(
            "writeln",
        ),
    ],
)
 INFO  stacklang::vm > eval(({@n 1 {@0 n 1 - fact n *} n 1 < if} @fact 5 fact writeln), [])
 INFO  stacklang::vm > eval({@n 1 {@0 n 1 - fact n *} n 1 < if}, [])
 INFO  stacklang::vm > eval(@fact, [{1->1}])
 INFO  stacklang::vm > eval(5, [{1->1}@fact])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact 5])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n 1 {0->1} 5])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n 1 {0->1} 5 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n 1 {0->1} false])
 INFO  stacklang::vm > eval((@0 n 1 - fact n *), [{1->1}@fact] : [5@n] : [])
 INFO  stacklang::vm > eval(@0, [{1->1}@fact] : [5@n] : [])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [5])
 INFO  stacklang::vm > eval(-, [{1->1}@fact] : [5@n] : [5 1])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact] : [5@n] : [4])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5@n] : [] : [4])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5@n] : [] : [4])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n] : [] : [4@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n 1 {0->1} 4])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n] : [] : [4@n 1 {0->1} 4 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n] : [] : [4@n 1 {0->1} false])
 INFO  stacklang::vm > eval((@0 n 1 - fact n *), [{1->1}@fact] : [5@n] : [] : [4@n] : [])
 INFO  stacklang::vm > eval(@0, [{1->1}@fact] : [5@n] : [] : [4@n] : [])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [4])
 INFO  stacklang::vm > eval(-, [{1->1}@fact] : [5@n] : [] : [4@n] : [4 1])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact] : [5@n] : [] : [4@n] : [3])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n 1 {0->1} 3])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n 1 {0->1} 3 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n 1 {0->1} false])
 INFO  stacklang::vm > eval((@0 n 1 - fact n *), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [])
 INFO  stacklang::vm > eval(@0, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [3])
 INFO  stacklang::vm > eval(-, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [3 1])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [2])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n 1 {0->1} 2])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n 1 {0->1} 2 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n 1 {0->1} false])
 INFO  stacklang::vm > eval((@0 n 1 - fact n *), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [])
 INFO  stacklang::vm > eval(@0, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [2])
 INFO  stacklang::vm > eval(-, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [2 1])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [1])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n 1 {0->1} 1])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n 1 {0->1} 1 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n 1 {0->1} false])
 INFO  stacklang::vm > eval((@0 n 1 - fact n *), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [])
 INFO  stacklang::vm > eval(@0, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [1])
 INFO  stacklang::vm > eval(-, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [1 1])
 INFO  stacklang::vm > eval(fact, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [0])
 INFO  stacklang::vm > eval((@n 1 {@0 n 1 - fact n *} n 1 < if), [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0])
 INFO  stacklang::vm > eval(@n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n])
 INFO  stacklang::vm > eval({@0 n 1 - fact n *}, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n 1 {0->1}])
 INFO  stacklang::vm > eval(1, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n 1 {0->1} 0])
 INFO  stacklang::vm > eval(<, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n 1 {0->1} 0 1])
 INFO  stacklang::vm > eval(if, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [] : [0@n 1 {0->1} true])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [1])
 INFO  stacklang::vm > eval(*, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [] : [1@n] : [1 1])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [1])
 INFO  stacklang::vm > eval(*, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [] : [2@n] : [1 2])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [2])
 INFO  stacklang::vm > eval(*, [{1->1}@fact] : [5@n] : [] : [4@n] : [] : [3@n] : [2 3])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [] : [4@n] : [6])
 INFO  stacklang::vm > eval(*, [{1->1}@fact] : [5@n] : [] : [4@n] : [6 4])
 INFO  stacklang::vm > eval(n, [{1->1}@fact] : [5@n] : [24])
 INFO  stacklang::vm > eval(*, [{1->1}@fact] : [5@n] : [24 5])
 INFO  stacklang::vm > eval(writeln, [{1->1}@fact 120])
120
```

It's so fun to see that working. 

## Mandelbrot

Now, let's stress test it. 

Here's one of the most complicated functions I've written so far: rendering the [[wiki:Mandelbrot set]]() to a [[wiki:PPM file]](). 

```text
# Set image dimensions and maximum number of iterations
128 @width
128 @height
16 @max_iterations

# Set the range of complex numbers to visualize
-2.0 @min_real
1.0 @max_real
-1.0 @min_imag
1.0 @max_imag

# Calculate the step sizes for the real and imaginary parts
max_real min_real - width / @real_step
max_imag min_imag - height / @imag_step

{
  @[ar ai br bi] !2
  ar br * ai bi * - 
  ar bi * ai br * +
} @cmul

{
  @[ar ai br bi] !2
  ar br +
  ai bi +
} @cadd

{
  @[r i]
  r i * r i * +
} @cmag2

{ 
  @[px py max_iter]
  
  {
    @[zx zy i iter] 
    
    0
    {
      @0 !1
      i
      { 
        @0 !1
        zx zy zx zy cmul px py cadd
        i 1 +
        $iter iter
      }
      zx zy cmag2 4.0 > if
    } 
    i max_iter = if

  } @iter

  px py 1 $iter iter
} @mandelbrot

# Write the PPM header
"P3" writeln
width writeln
height writeln
"255" writeln

# Loop through image rows (y) and columns (x)
{
    @y
    {
        @x

        # Calculate the current complex number (real + imag * i)
        x real_step * min_real + @real
        y imag_step * min_imag + @imag

        # Calculate the number of iterations for the current complex number
        real imag max_iterations mandelbrot @iterations

        # Scale the number of iterations to a color value (assuming grayscale)
        1.0 iterations * max_iterations / 255 * int @color

        # Write the color value to the PPM file (red, green, blue)
        color write " " write
        color write " " write
        color write " " write
    } width loop
    newline
} height loop
```

There are some interesting things in there, IMO. In particular, we're not (yet) using complex numbers, since I haven't implemented that directly. But with multiple arity, we can do it 'easily'. Represent a complex number as two numbers on the stack. So `cmul` (complex multiplication) takes four parameters (a and b, real and imaginary) and returns two (real and imaginary of the result). 

Other than that, we have a three way `if` in the `@mandelbrot` set (which could be implemented better), a nested `loop` for rendering and some color conversion. 

And that's it. We can write PPM files! 

```bash 
┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ time cargo run --release -- --file examples/mandelbrot.stack > output/mandelbrot-128x128@16.ppm

    Finished release [optimized] target(s) in 0.09s
     Running `target/release/stacklang --file examples/mandelbrot.stack`
cargo run --release -- --file examples/mandelbrot.stack >   3.37s user 0.10s system 93% cpu 3.721 total

┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ convert output/mandelbrot-128x128@16.ppm output/mandelbrot-128x128@16.png
```

3 seconds is... kind of slow for 128x128. But with an initial interpreter, not bad!

![Mandelbrot fractal at 128x128 with 16 max iterations](/embeds/2023/mandelbrot-128x128@16.png)

Let's go 8x as large with twice the iterations:

```bash
┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ head -n 4 examples/mandelbrot.stack

# Set image dimensions and maximum number of iterations
512 @width
256 @height
32 @max_iterations

┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ time cargo run --release -- --file examples/mandelbrot.stack > output/mandelbrot-512x256@32.ppm

    Finished release [optimized] target(s) in 0.09s
     Running `target/release/stacklang --file examples/mandelbrot.stack`
cargo run --release -- --file examples/mandelbrot.stack >   44.38s user 0.87s system 93% cpu 48.471 total
```

![Mandelbrot fractal at 512x128 with 32 max iterations](/embeds/2023/mandelbrot-512x256@32.png)

It does seem to mostly be based on the complex math and number of iterations:

```bash
┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ head -n 4 examples/mandelbrot.stack

# Set image dimensions and maximum number of iterations
512 @width
256 @height
8 @max_iterations

┌ ^_^ jp@Mercury {git main} ~/Projects/stacklang
└ time cargo run --release -- --file examples/mandelbrot.stack > output/mandelbrot-512x256@8.ppm

    Finished release [optimized] target(s) in 0.10s
     Running `target/release/stacklang --file examples/mandelbrot.stack`
cargo run --release -- --file examples/mandelbrot.stack >   18.30s user 0.29s system 91% cpu 20.239 total
```

I'm going to have to check that out again when we get complex numbers. 

![Mandelbrot fractal at 512x128 with 8 max iterations](/embeds/2023/mandelbrot-512x256@8.png)

It's pretty cool looking though. 

## Next steps

And that's it for today. It's so cool just seeing something like this working...

What's next? Mostly from last time. 

Next up, I'm planning to:

* Type checking:
  * Automatically determine the `arity` of blocks when possible
  * Automatically determine specific types of expressions (including blocks)
* Numeric tower:
  * Implement rationals/complex numbers at the parser level + in any interpreter / compiler I have at that point
  * Implement automatic numeric coercion--if you try to add an integer to a complex number, the result should be a complex number
* Interpreters:
  * A bytecode interpreter/compiler, evaluating at a lower level (I'm not sure how much this would gain, the AST is already fairly low level)
* Compilers:
  * Compile to C (and then pass to GCC/Clang) to compile that
  * Compile to WASM; since it's also stack based, this should be interesting
  * Compile to x86/ARM assembly

Probably the C-compiler, but there's a lot to do here. 
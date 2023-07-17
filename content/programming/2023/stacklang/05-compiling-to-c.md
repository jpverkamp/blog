---
title: "StackLang Part V: Compiling to C"
date: '2023-07-12 12:00:00'
programming/languages:
- C
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
It's been a bit, but I hope it's worth it. StackLang, part 5: compiling to C!

<!--more-->

---

Posts in this series:

{{< taxonomy-list "series" "StackLang" >}}

This post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## The goal

So previously, I {{<crosslink text="wrote an interpreter" title="StackLang Part IV: An Interpreter">}} that can run StackLang programs. It works well enough and is great for hacking on features, but on the other hand:

* It's pretty slow. Generating a 1024x768x8 Mandelbrot image takes ~2m15s even in release mode with the VM vs 2s in the initial compiler. No, that's not a typo. 
* It redoes the lex + parse + run on each run, versus building a binary that just runs
* The compiled executable is a bit larger (2.5MB vs 50kB; yes I know that's not much either way)
* I just want to write a compiler!

## The target

So the next question: what do we want to compile to? 

* Assembly (x86 / ARM); directly compile without other tools (although an assembler is probably still necessary), best low level control
* A compiler backend (LLVM); something I've been meaning to learn
* Another language (C / Rust); leverage a lower level compiler for the final compilation steps
* WASM; compiles to the web, it's stack based, so theoretically fits the language well

All together... I think that any of those would be interesting, but semi-randomly I think that I'm going to try compiling to C and using [Clang](https://clang.llvm.org/) behind that (which in turn ends up using LLVM, although not directly). 

## Code generation

Okay, first things first. I want to write a function `compile(ast: Expression) -> String`. It should generate C code which then can be written to file (or stdout, whichever). 

To start with, something like this:

```rust
/// Compile the AST into C code
pub fn compile(ast: Expression) -> String {
    let mut lines = vec![];

    lines.push(include_str!("../compile_c_includes/header.c").to_string());
    lines.push(include_str!("../compile_c_includes/types.c").to_string());
    lines.push(include_str!("../compile_c_includes/globals.c").to_string());
    lines.push(include_str!("../compile_c_includes/coerce.c").to_string());
    
    /// Helper function to compile a specific block to be output later
    fn compile_block(
        arity: (usize, usize),
        body: &Vec<Expression>,
        blocks: &mut Vec<Vec<String>>,
    ) -> usize {
        ...
    }

    /// Compile a single expression into strings
    fn compile_expr(
        expr: Expression,
        blocks: &mut Vec<Vec<String>>
    ) -> Vec<String> {
        ...
    }

    // Compile the top level expression
    let mut blocks = vec![];
    match ast {
        Expression::Group(body) => {
            compile_block((0, 0), &body, &mut blocks);
        }
        _ => panic!("Unexpected top level expression: {:?}", ast),
    }

    // Forward declare all blocks
    ...

    // Generate block functions
    ...

    // Add the main function that setups up the initial stack
    // and calls the top level block (block_0)
    lines.push(include_str!("../compile_c_includes/main.c").to_string());

    // Put it all together
    lines.join("\n")
}
```

So there are a few things going on here:

* We're generating a `vec` of `lines` that will be combined at the end
* The main compile function has two helper functions:
  * `compile_block` will take a block of code (`{ ... }`) and compile it into a C function, calling `compile_expr` once for each subexpression
  * `compile_expr` will compile a single expression, be it a literal, variable, name, lookup, or whatever (if it's a `block`, call `compile_block`)
* It's possible to add static C code to `lines` with `include_str!`:
  * `header.c` has the includes and a number of `#define` constants
  * `types.c` defines the `Value` type (a {{<wikipedia "tagged union">}} struct)
  * `globals.c` stores global variables (the `stack` and `frame`)
  * `coerce.c` contains a function to automatically cast numbers when necessary (adding an integer + float should result in a float for example)
  * `main.c` defines the `int main(int, char*)` function; sets up memory 

## Static C code

First, let's talk about all of the static C code that I'm including in every program, no matter the content. 

### `header.c`

```c
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TAG_NUMBER 0
#define TAG_NUMBER_INTEGER 1
#define TAG_NUMBER_RATIONAL 2
#define TAG_NUMBER_FLOAT 3
#define TAG_NUMBER_COMPLEX 4

#define TAG_STRING 16
#define TAG_BOOLEAN 17
#define TAG_BLOCK 18
```

Essentially, this is where I pull in headers (for boolean types, converting to/from ints, and doing some string I/O) + define the tags for types (see [`types.c`](#typesc)). 

### `types.c`

```c

// Values on the stack
typedef struct
{
    uint8_t type;
    union
    {
        int64_t as_integer;
        double as_float;

        char *as_string;
        bool as_boolean;
        void *as_block;
    };
} Value;
```

As mentioned, this is a {{<wikipedia "tagged union">}} for all `values`. It stores the `type` (one of the constants from [`header.c`](#headerc)) and the data. But because I'm using a union, all of the values are stored in the same memory--you have to make sure to read it as the right kind of data. It will always take as much memory as the largest of the values (`int64_t` and `double` are each 8 bytes), which can be wasteful, but such is life. 

One interesting one in particular is the `void *as_block`. This is a function pointer to another `block_#` (we haven't defined them yet) stored as a value. 

### `globals.c`

```c
// The stack holding all values
Value *stack;
Value *stack_ptr;

// Frames holding the stack pointer for each block
Value **frames;
Value **frame_ptr;
```

This stores two arrays which I'll allocate in [`main.c`](#mainc). They're not dynamic at this point. 

Specifically, `stack` points to base of the entire stack of values while `stack_ptr` points to the current top of the `stack` and will be incremented when pushing and decremented when popping. 

`frames` stores an array of pointers to the `stack` pointer (yay `**`) which is updated whenever a new scope is introduced (when invoking a `block`), so that I know how many values to pop from `stack_ptr` on return. Likewise, `frame_ptr` is the current top of that stack. 

It's... certainly an interesting way to do it, but I think it works well enough. 

### `coerce.c`

```c

// Convert two values to have the same type by upgrading if necessary
void coerce(Value *a, Value *b)
{
    if (a->type == b->type)
    {
        return;
    }

    if (a->type == TAG_NUMBER_INTEGER && b->type == TAG_NUMBER_FLOAT)
    {
        a->type = TAG_NUMBER_FLOAT;
        a->as_float = (double)a->as_integer;
    }

    if (a->type == TAG_NUMBER_FLOAT && b->type == TAG_NUMBER_INTEGER)
    {
        b->type = TAG_NUMBER_FLOAT;
        b->as_float = (double)b->as_integer;
    }
}
```

As mentioned, this is the function to automatically convert ints/floats when doing math on mixed types. So far, I don't have the rest of the numeric tower I'm planning and I may eventually make manual casting required instead of this, but for the moment, this works pretty well. 

I did, for a while, have a rather subtle bug here that did all sorts of interesting things. The last (contentful) line was `b->as_float = (double)a->as_integer;`. So I ended up copying `a` over `b`, but only if `a` was a float and `b` an int. That took a while to find... I need better tests. :smile:

### `main.c`

And finally, the main function!

```c
int main(int argc, char *argv[])
{
    // The stack holding all values
    stack = malloc(10240 * sizeof(Value));
    stack_ptr = stack;

    // Frames holding the stack pointer for each block
    frames = malloc(10240 * sizeof(Value **));
    frame_ptr = frames;

    block_0(NULL);

    return 0;
}
```

So right now, I'm just allocating two flat arrays of ~90kB each (10240 * (1 byte for the tag and 8 bytes for the value union)). I'll probably make that dynamic at some point, but so far as making this work, it works well. 

Then we call `block_0` (I'll get to the `NULL` when talking [names](#named-variables)) and finally (if we make it this far) `return` success. Voila!

## `compile_block`

Okay, let's actually talk about compilation. I'm going to start with `compile_block`. This function call `compile_expr` to actually compile each expression, but it also has to do a few more things:

* Calculate (or be given) the `arity` of the expression: how many values it will consume from the stack and how many it will push back on
* Store the frame pointer--this will be offset by `arity_in` (which effectively consumes those values)
* Compile the expressions
* Handle popping 'extra' values off the stack so only `arity_out` values are left after the stored `frame_ptr` when we're done

Like this:

```rust
    /// Helper function to compile a specific block to be output later
    fn compile_block(
        arity: (usize, usize),
        body: &Vec<Expression>,
        blocks: &mut Vec<Vec<String>>,
    ) -> usize {
        log::debug!("compile_block({arity:?}, {body:?})");

        let index = blocks.len();
        blocks.push(vec![]); // Throwaway vec to hold the index
        let mut lines = vec![];

        let (arity_in, arity_out) = arity;

        lines.push(format!(
            "    // block: {}",
            body.iter()
                .map(|ex| ex.to_string())
                .collect::<Vec<String>>()
                .join(" ")
        ));
        lines.push(format!("\n    // Store the current stack pointer with arity_in={arity_in}"));
        lines.push(format!("    *(++frame_ptr) = (stack_ptr - {arity_in});\n"));

        // Compile the block itself
        for expr in body {
            for line in compile_expr(expr.clone(), blocks) {
                lines.push(line);
            }
        }

        // Pop the block off the stack
        lines.push(format!("    // Pop the block off the stack, preserving arity_out={arity_out} values"));
        lines.push(format!("    Value* return_ptr = (stack_ptr - {arity_out});"));
        lines.push(format!("    stack_ptr =  *(frame_ptr--);"));
        for _ in 0..arity_out {
            lines.push(format!("    *(++stack_ptr) = *(++return_ptr);"));
        }

        blocks[index] = lines;
        index
    }
```

One thing that I've been making sure I do is generating comments in the C code. In a perfect world, these are never going to get looked at, since we're going to immediately compile this C code to assembly/machine code. But in a practical world, knowing what code I'm generating is kind of important...

One thing to note is that all blocks have a single variable: `names`. This one is a {{<wikipedia "linked list">}} of `name` -> `stack_ptr` associations that we've stored. Because it's passed as a parameter to the `block_#(...)` call, when we return, it 'forgets' all `names` bound in this block or child blocks. I'll get more into that in [the names section](#named-variables). 

This is also the first time seeing code like this:

```c
*(++frame_ptr) = (stack_ptr - {arity_in});
```

Essentially, `frame_ptr` is a pointer to a value in the `frames` array. `++frame_ptr` is a pre-increment, so it's saying advance the `frame_ptr` to the next available value in the array *before* evaluating the rest of the code. `*(++frame_ptr)` then unwraps one level (so rather than a frame, it's a `stack` value), which we then store the current `stack_ptr` offset by `arity_in` (essentially saying we're going to pop that many values throughout this function). 

Likewise, at the end:

```c
Value* return_ptr = (stack_ptr - {arity_out});
stack_ptr =  *(frame_ptr--);
*(++stack_ptr) = *(++return_ptr); // ... repeat arity_out times
```

This will use `arity_out` to determine how many values from the top of the stack (`stack_ptr`) we want to return. If it's 0, we just won't copy any values. But if it's 3 (for example), we'll start returning from the 3rd from the top of the stack. 

Next, move the `stack_ptr` to the `frame_ptr`. Because it's `frame_ptr--`, we will take the top one and then only after we're done, decrement it to pop this `frame`. This `frame_ptr` starts without `arity_in`

Then `*(++stack_ptr) = *(++return_ptr);` will be called once for each of arity_in. That says: 'set the next value on the stack to the next value to return. 

It... makes sense to me? Perhaps a diagram will help. Let's show a few examples. 

In the first example, let's show what would happen when calling `dup` function that will pop 1 value and return 2:

```text
# Initial state
stack: A B C
           └ `stack_ptr`

# Call dup, generate a new frame pointer
# The `stack_ptr` contains the value passed to the function
# The `frame_ptr` does not, since it's treating it as those values will be popped
stack: A B C
         │ └ `stack_ptr`
         └ `frame_ptr`

# Dup runs, duplicating the C
stack: A B C C
         │   └ `stack_ptr`
         └ `frame_ptr`

# Preparing for return, 1) `return_ptr` needs to have two values to return
stack: A B C C
         │ │ └ `stack_ptr`
         │ └ `return_ptr`
         └ `frame_ptr`

# 2) The `stack_ptr` is moved to `frame_ptr - 1` (since we increment before copying)
stack: A B C C
       │ │ └ `return_ptr`
       │ └ `frame_ptr`
       └ `stack_ptr`

# Now (twice because of `arity_out`), we copy the value at `return_ptr` to `stack_ptr` and increment
# After the first copy:
stack: A C C C
         │ └ `return_ptr`
         └ `frame_ptr` + `stack_ptr`

# After the second copy:
stack: A C C C
         │ │ └ `return_ptr`
         │ └ `stack_ptr`
         └ `frame_ptr`


# Finally, we return; because `stack_ptr` is where the stack
# will be on returning from the function; the last `C` (`return_ptr`)
# is effectively ignored / not able to be referenced any more
```

Hopefully that helps? 

And that's all we have for `compile_block`. Now the real fun(tm), `compile_expr`:

## `compile_expr`

In a nutshell, we have this:

```rust
    /// Compile a single expression into strings
    fn compile_expr(expr: Expression, blocks: &mut Vec<Vec<String>>) -> Vec<String> {
        log::debug!("compile_expr({expr})");

        let mut lines = vec![];
        lines.push(format!("    // {expr}")); // TODO: Flag for verbose mode

        match expr {
            Expression::Identifier(id) => {
                ...
            },
            ...
        }

        lines
    }
```

Where `match expr` will generate code for each possible expression (see the sections below). Two interesting bits:

* `blocks: &mut Vec<Vec<String>>` - this stores the blocks as we compile; since we can have `blocks` in `exprs`, we need to thread this through for when we see more blocks
* `-> Vec<String>` - we return a `Vec` so that we can return 0, 1, or more lines; if an expression doesn't generate code, it should return 0. Most will return more than 1: a comment + the actual generated code

So let's go through the generation!

### Expression::Identifier

```rust
Expression::Identifier(id) => {
    match id.as_str() {
        // Built in numeric functions
        "+" => numeric_binop!(lines, "+"),
        "-" => numeric_binop!(lines, "-"),
        "*" => numeric_binop!(lines, "*"),
        "/" => numeric_binop!(lines, "/"),
        "%" => numeric_binop!(lines, "%"),

        // Built in numeric comparisons
        "<" => numeric_compare!(lines, "<"),
        "<=" => numeric_compare!(lines, "<="),
        "=" => numeric_compare!(lines, "=="),
        "!=" => numeric_compare!(lines, "!="),
        ">=" => numeric_compare!(lines, ">="),
        ">" => numeric_compare!(lines, ">"),

        // Built ins
        "read" => lines.push(include_str!("../compile_c_includes/builtins/read.c").to_string()),
        "write" => lines.push(include_str!("../compile_c_includes/builtins/write.c").to_string()),
        "writeln" => {
            lines.push(include_str!("../compile_c_includes/builtins/write.c").to_string());
            lines.push("printf(\"\\n\");".to_string());
        },
        "newline" => lines.push("printf(\"\\n\");".to_string()),
        "loop" => lines.push(include_str!("../compile_c_includes/builtins/loop.c").to_string()),
        "if" => lines.push(include_str!("../compile_c_includes/builtins/if.c").to_string()),
        "to_float" => lines.push(include_str!("../compile_c_includes/builtins/to_float.c").to_string()),
        "to_int" => lines.push(include_str!("../compile_c_includes/builtins/to_int.c").to_string()),

        // Attempt to lookup in names table
        id => {
            let id = sanitize_name(id);
            lines.push(format!(
                "
{{
Value* v = lookup(names, NAME_{id});
if (v->type == TAG_BLOCK) {{
void *f = v->as_block;
((void (*)(Name*))f)(names);
}} else {{
*(++stack_ptr) = *v;
}}
}}
    "
            ));
        }
    }
}
```

So there are threeish categories here: 

* builtins numeric functions generated by macro
* builtin functions included as C files
* variable lookups

For numeric functions, we do much like we did in the VM version:

```rust
/// A helper macro to generate functions that operate on two integers and floats
macro_rules! numeric_binop {
    ($lines:expr, $op:literal) => {{
        let op = stringify!($op).to_string().trim_matches('"').to_string();

        $lines.push(format!("
    {{
        Value *b = stack_ptr--;
        Value *a = stack_ptr--;
        coerce(a, b);
        
        if (a->type == TAG_NUMBER_INTEGER) {{
            Value result = {{.type=TAG_NUMBER_INTEGER, .as_integer=a->as_integer {op} b->as_integer}};
            *(++stack_ptr) = result;
        }} else if (a->type == TAG_NUMBER_FLOAT) {{
            Value result = {{.type=TAG_NUMBER_FLOAT, .as_float=a->as_float {op} b->as_float}};
            *(++stack_ptr) = result;
        }}
    }}
"));
    }};
}
```

It's got fun `{{ double brackets }}` because otherwise those are template variables (which I do use for `op`), but other than that, all we do is:
* pop two values with `Value *b = stack_ptr--` (gets the value and then decrements the pointer)
* [`coerce`](#coercec)
* perform the function, creating a new value
* push the new value onto the stack with `*(++stack_ptr) = result;`

`numeric_compare` is much the same, except instead we create a new `TAG_BOOLEAN` value. 

The next case is the builtins. Those are just including C code, which you can see in the repo [github:jpverkamp/stacklang:compile_c_includes/builtins](https://github.com/jpverkamp/stacklang/tree/main/compile_c_includes/builtins). 

For example, `if` includes `builtins/if.c`:

```rust
{
    Value cond = *(stack_ptr--);
    Value if_false = *(stack_ptr--);
    Value if_true = *(stack_ptr--);

    if (cond.type != TAG_BOOLEAN)
    {
        printf("Error: if condition must be a boolean\n");
        exit(1);
    }

    Value v = (cond.as_boolean ? if_true : if_false);

    if (v.type == TAG_BLOCK)
    {
        void *f = v.as_block;
        ((void (*)(Name *))f)(names);
    }
    else
    {
        *(++stack_ptr) = v;
    }
}
```

Oh that `((void (*)(Name *))f)(names);` line... Essentially, that's taking the `as_block`, which has to be stored as an arbitrary (`void*`) pointer and then casts it to a function pointer of the proper type (take a `Name*` and return nothing), which is then called with the [`names` linked list](#named-variables). 

Finally, if the `Identifier` isn't a builtin function, assume it's a variable and look it up:

```rust
                    lines.push(format!(
                        "
{{
    Value* v = lookup(names, NAME_{id});
    if (v->type == TAG_BLOCK) {{
        void *f = v->as_block;
        ((void (*)(Name*))f)(names);
    }} else {{
        *(++stack_ptr) = *v;
    }}
}}
            "
                    ));
```

Then, if it's not a `block`, push that variable's `Value` onto the stack as always. But if it is a `block`, then we need to call it, as we did in `if` above. 

So that's a lot. :smile:

### Expression::Literal

Literals are much easier. 

```rust
Expression::Literal(value) => {
    let (tag, field, value) = match value {
        // TODO: additional numeric tyhpes
        Value::Number(Number::Integer(v)) => {
            ("TAG_NUMBER_INTEGER", "integer", v.to_string())
        }
        Value::Number(Number::Float(v)) => ("TAG_NUMBER_FLOAT", "float", v.to_string()),
        Value::String(v) => ("TAG_STRING", "string", format!("{v:?}")),
        Value::Boolean(v) => ("TAG_BOOLEAN", "boolean", format!("{v:?}")),
        Value::Block { .. } => panic!("Blocks should be compiled separately"),
    };

    lines.push(format!(
        "
{{
Value v = {{.type={tag}, .as_{field}={value}}};
*(++stack_ptr) = v;
}}
"
    ));
}
```

For each type of literal, determine what the tag should be and generate the necessary code for it. Then push it onto the stack. 

There shouldn't be direct `block` literals at the moment. `panic!`

### Expression::Block

```rust
Expression::Block(ref body) => {
    let arity = calculate_arity(&expr)
        .expect(format!("Unable to calculate arity for block: {:?}", expr).as_str());
    let index = compile_block(arity, body, blocks);
    lines.push(format!(
        "
{{
Value v = {{.type=TAG_BLOCK, .as_block=(void*)block_{index}}};
*(++stack_ptr) = v;
}}
"
    ));
}
```

This one is straight forward (mostly because the code is in [`compile_block`](#compile_block)). We do calculate the arity ahead of time (I'm not sure why anymore--I think because we have the `expr` here and only the body in `calculate_block`?), but then we just compile the block, get the new index for this block, and push a `Value::Block` onto the stack containing a pointer to the new function. 

Pretty cool how that just works. 

### Expression::List 

`todo!()`

I haven't actually implemented list expressions yet, but I also haven't written any code that needs them yet!

### Expression::Group

Groups are defined with `( ... )` (or there is an implicit one at the top level). All they are is a sequence of expressions, but this is exactly why we have the function return an arbitrary number of lines:

```rust
Expression::Group(exprs) => {
    for expr in exprs {
        for line in compile_expr(expr, blocks) {
            lines.push(line);
        }
    }
}
```

### Expression:At

Here's a more interesting case. At expressions are implicitly tied into [naming](#named-variables), so we'll get into it more there. But for now, assume we have a function `bind` in our C code that takes `names`, a `NAME_{id}` constant, and a pointer to the stack and binds the name to that stack location. 

Then, there are two three cases:
* `@a` for single `Identifier` binding 
* `@[a b c]` for `List` binding of multiple variables at once
* `@5` for arity clauses, these just shouldn't generate code

```rust
Expression::At(expr) => {
    match expr.as_ref() {
        Expression::Identifier(id) => {
            let id = sanitize_name(id);
            lines.push(format!(
                "
{{
    Value *p = stack_ptr;
    names = bind(names, NAME_{id}, p);
}}
"
            ));
        }
        Expression::List(id_exprs) => {
            let id_count = id_exprs.len();
            for (i, id_expr) in id_exprs.iter().enumerate() {
                match id_expr {
                    Expression::Identifier(id) => {
                        let id = sanitize_name(id);
                        
                        lines.push(format!(
                            "
{{ 
    Value *p = (stack_ptr - {id_count} + {i} + 1);
    names = bind(names, NAME_{id}, p);
}}
"
                        ));
                    }
                    _ => panic!("Unexpected @ expression when compiling: {}", expr),
                }
            }
        }
        Expression::Literal(Value::Number(Number::Integer(_))) => {} // ignore numeric @ expressions
        _ => panic!("Unexpected @ expression when compiling: {}", expr),
    }
}
```

### Expression::Bang

These are eventually going to be for writing to named variables, but I'm not currently using them much. What we do have though is `arity_out` expressions, which have a numeric field, a la `!1`. We don't want to generate code for them, but do need to handle them:

```rust
Expression::Bang(v) => {
    match v.as_ref() {
        Expression::Literal(Value::Number(Number::Integer(_))) => {}, // Used only for arity out expressions
        _ => todo!(),
    }
}
```

### Expression::Dollar

`$` expressions are essentially a simpler form of variable lookups. They always have an `Identifier` and they always push the value on the stack, even if it's a block. Essentially, this is to allow passing blocks to other blocks. It does make the code simpler though:

```rust
Expression::Dollar(expr) => match expr.as_ref() {
    Expression::Identifier(id) => {
        lines.push(format!(
            "
{{
    Value* v = lookup(names, NAME_{id});
    *(++stack_ptr) = *v;
}}
"
        ));
    }
    _ => panic!("Unexpected $ expression when compiling: {}", expr),
}
```

## Generating block code

Okay, that's all well and good, but remember back in [the original code](#code-generation) when I said I still have to forward declare and generate all blocks? Well, now we have the `blocks`, so let's do that!

First:

```rust
// Forward declare all blocks
lines.push("\n// Forward declare all blocks".to_string());
for (i, _) in blocks.iter().enumerate() {
    lines.push(format!("void block_{i}(Name *block_names);", i = i).to_string());
}
```

This comes up because each `block` can theoretically call any other block in any order. Because of how C compilers work, you can't call a function defined after you (by default), so what we're doing here is just naming all of the `block_#` functions we're going to generate to make the compiler happy. 

And then the code gen:

```rust
// Generate block functions
lines.push("\n// Actual block definitions".to_string());
for (i, block) in blocks.iter().enumerate() {
    lines.push(format!("void block_{i}(Name *block_names) {{").to_string());
    lines.push(format!("    if (block_names != NULL) block_names->boundary = true;").to_string());
    lines.push(format!("    Name* names = block_names;").to_string());

    lines.push(block.join("\n"));

    lines.push("    // Free names bound in this block".to_string());
    lines.push("    
while (names != NULL && block_names != names) {
    Name *next = names->prev;
    free(names);
    names = next;
}
    ".to_string());
    lines.push("}".to_string());
}
```

A lot of that has to do with how we actually deal with [named variables](#named-variables), which we're almost to, I promise. In a nutshell though, we take in `block_names` as a pointer to where in the `names` linked list the block started at. We then copy `names` which will be incremented as we evaluate this block (in `At` expressions). At the end of the block, if there are any values between (if we bound any names), we free the memory those names used, since the calling function will no longer be able to see them. 

It's not how I originally did it, see the [first version of named variables](#original-code), but it does work! 

## Named variables

Okay, enough is enough. Let's actually talk about `names`. 

As mentioned in [the previous section](#generating-block-code), we have one more data structure: `names`. This one, rather than a static array, is actually a linked list. Each name will be added to the end of this list, with the `name` and `stack_ptr` it refers to. To lookup, we'll start at the end of this list and iterate backwards until we find `name`. If we bound a variable multiple times, the last bound (so the closest in scope) will be seen first. 

It's pretty elegant, IMO. Here's the code:

```c
// Names linked list
typedef struct Name Name;
struct Name
{
    bool boundary;
    uint8_t name;
    Value *value;
    Name *prev;
};

Name *bind(Name *names, uint8_t name, Value *value)
{
    Name *new_name = malloc(sizeof(Name));
    if (new_name == NULL)
    {
        printf("Out of memory");
        exit(1);
    }

    new_name->boundary = false;
    new_name->name = name;
    new_name->value = value;
    new_name->prev = names;
    return new_name;
}

// Lookup a value on the stack by name
Value *lookup(Name *names, uint8_t name)
{
    while (names != NULL)
    {
        if (names->name == name)
        {
            return names->value;
        }
        names = names->prev;
    }

    printf("Name not found: %d", name);
    exit(1);
}
```

Yes, it's a bit weird that we don't store `next`, but we don't need it. Just `prev` to look back from the end of the list. And if we ever go all the way back, `prev` will be `NULL` and we know the variable isn't defined (so error out). 

One last interesting field is `new_name->boundary`. This is set when a `block` is called and essentially all it does is allow us to print a distinction between `names` in different `block_#` for [debug mode](#debug-mode). 

With that, `bind` will `malloc` the memory for the new node, fill it out, and return the new end of list. `lookup` (as mentioned) will start at the current end of the list and go back until we either find the `name` or run out of `names`. 

I do store all `name` as `uint8_t`, which does require collecting all of the names at the start of the `compile` function:

### Collecting names

```rust
/// Collect the names used so we can assign each an integer value
fn collect_names(ast: &Expression) -> HashMap<String, usize> {
    let mut names = HashMap::new();

    fn collect_names_expr(expr: &Expression, names: &mut HashMap<String, usize>) {
        match expr {
            Expression::Identifier(_)
            | Expression::Literal(_)
            | Expression::Bang(_)
            | Expression::Dollar(_) => {
                // Do nothing, no names possible
            }
            Expression::List(_) => todo!(),
            Expression::Block(exprs) => {
                for expr in exprs {
                    collect_names_expr(expr, names);
                }
            }
            Expression::Group(exprs) => {
                for expr in exprs {
                    collect_names_expr(expr, names);
                }
            }
            Expression::At(expr) => {
                match expr.as_ref() {
                    Expression::Identifier(id) => {
                        let id = sanitize_name(id);
                        if !names.contains_key(&id) {
                            log::debug!("Adding name: {} @ {}", id, names.len());
                            names.insert(id.clone(), names.len());
                        }
                    }
                    Expression::List(id_exprs) => {
                        for id_expr in id_exprs {
                            match id_expr {
                                Expression::Identifier(id) => {
                                    let id = sanitize_name(id);
                                    if !names.contains_key(&id) {
                                        log::debug!("Adding name: {} @ {}", id, names.len());
                                        names.insert(id.clone(), names.len());
                                    }
                                }
                                _ => panic!(
                                    "Unexpected @ expression when collecting names: {}",
                                    expr
                                ),
                            }
                        }
                    }
                    Expression::Literal(Value::Number(Number::Integer(_))) => {} // ignore numeric @ expressions
                    _ => panic!("Unexpected @ expression when collecting names: {}", expr),
                }
            }
        }
    }

    collect_names_expr(ast, &mut names);
    names
}
```

This just iterates through the function, looking for anything that is used in an `At` expression recursively and makes a unique set of them. It then can generate a define for each:

```rust
let names = collect_names(&ast);
log::debug!("collected names: {:?}", names);

for (name, index) in names.iter() {
    lines.push(format!("#define NAME_{name} {index}"));
}
```

Not so bad. 

### Original idea

As a quick aside, this isn't the first iteration of variable naming I wrote. Originally (and it works in *most* cases), the [`types.c`](#typesc) definition looked like this:

```c
// Values on the stack
typedef struct
{
    uint8_t type;
    union
    {
        int64_t as_integer;
        double as_float;

        char *as_string;
        bool as_boolean;
        void *as_block;
    };

    uint8_t name_count;
    uint8_t names[4];
    // TODO: more than 4 names
} Value;
```

In essence, this would store up to 4 `names` with each value on the stack. This would end up using up that extra memory even if a value was never named, but that's not actually where the bug crept in: because names were always bound on the stack and never removed, when you called a child `block` that used the same names as a parent `block`, weird things(tm) could happen. 

This... took a while to trace down before finally settling on the linked list version above. 

## Adding it to the `main` function

Okay, we have all of the code now! So let's add it to my `main.rs`. Because we have two possible branches now, along with setting up logging and [debug mode](#debug-mode), it's worth pushing out into a new function:

```rust
use clap::*;
use log;
use std::{io::BufReader, env};

mod debug;

mod numbers;
mod stack;
mod types;

mod arity;
mod compile_c;
mod lexer;
mod parser;
mod vm;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(short, long)]
    file: String,

    #[arg(short, long)]
    compile: bool,

    #[arg(short, long)]
    debug: bool, 
}

fn main() {
    pretty_env_logger::init();
    let args = Args::parse();

    let file = std::fs::File::open(args.file).unwrap();
    let tokens = lexer::tokenize(BufReader::new(file));

    log::info!(
        "Tokens: {}",
        tokens
            .iter()
            .map(|token| token.token.clone())
            .collect::<Vec<String>>()
            .join(" ")
    );

    let ast = parser::parse(tokens);
    log::info!("AST:\n{:#?}", ast);

    if args.compile {
        let c_code = compile_c::compile(ast);
        println!("{}", c_code);
    } else {
        vm::evaluate(ast);
    }
}
```

[clap](https://docs.rs/clap/latest/clap/) is pretty cool!

Essentially, we read args, load the specified file, always tokenize, always generate an AST, and then based on the `compile` flag, either run it with the VM or compile it to C. 

That's pretty shiny. 

## Debug mode

One bit missing though, debug mode!

There were essentially three options I had here:

* Thread a `debug_mode` flag through all of the other functions
* Set an environment variable based on the command line flag (if specified)
* Create a crate with `debug::ENABLED` 

The third appealed to me... with `ENABLED` being a `static mut bool`. The only problem with that... is that it's `unsafe`:

```rust
// main.rs
fn main() {
    pretty_env_logger::init();
    let args = Args::parse();

    // Debug flag override envs variable
    if args.debug {
        unsafe {
            debug::ENABLED = true;
        }
    } else {
        match env::var("STACKLANG_DEBUG") {
            Ok(s) if s.to_lowercase() == "true" => unsafe {
                debug::ENABLED = true;
            },
            _ => {},
        }
    }
    unsafe {
        env::set_var("RUST_LOG", "trace");
        if debug::ENABLED {
            log::debug!("Debug mode enabled");
        }
    }

    ...
}

// compile_c.rs
/// Compile the AST into C code
pub fn compile(ast: Expression) -> String {
    ...

    unsafe {
        if debug::ENABLED {
            lines.push("char* get_name(int index) {".to_string());
            for (name, index) in names.iter() {
                lines.push(format!("    if (index == {index}) {{ return \"{name}\"; }}"));
            }
            lines.push("    return \"<unknown>\";".to_string());
            lines.push("}".to_string());
        }
    }

    ...
}
```

I'm ... not thrilled with that. There has to be a better way to do it, but I've not found it yet. And it works. For now!

## Justfile

So now I can run with the `--file` flag to specify file, `--compile` to enable compilation mode (which actually only generates C code), and `--debug` to enable [debug mode](#debug-mode). But that's... a lot. So I made a [Justfile](https://github.com/casey/just):

```text
both name:
    just example {{ name }}
    just example {{ name }} compile=true

example name compile="false" debug="false":
    just example{{ if compile != "false" { "-compile" } else { "-run" } }}{{ if debug != "false" { "-debug" } else { "" } }} {{name}}

example-run name:
    time cargo run --release -- --file examples/{{name}}.stack

example-compile name:
    cargo run --release -- --file examples/{{name}}.stack --compile > output/{{name}}.c
    clang -Ofast output/{{name}}.c -o output/{{name}}
    time output/{{name}}

example-run-debug name:
    cargo run -- --debug --file examples/{{name}}.stack

example-compile-debug name:
    cargo run -- --debug --file examples/{{name}}.stack --compile > output/{{name}}.c
    clang output/{{name}}.c -o output/{{name}}
    output/{{name}}
```

Now I can run my code examples (with timing! and automatic clang!) with `just example`:

```bash
$ just example fibonacci-acc

just example-run fibonacci-acc
time cargo run --release -- --file examples/fibonacci-acc.stack
   Compiling stacklang v0.1.0 (/Users/jp/Projects/stacklang)
    Finished release [optimized] target(s) in 3.76s
     Running `target/release/stacklang --file examples/fibonacci-acc.stack`
12586269025

real	0m4.037s
user	0m0.048s
sys	0m0.047s

$ just example fibonacci-acc compile=true

just example-compile fibonacci-acc
cargo run --release -- --file examples/fibonacci-acc.stack --compile > output/fibonacci-acc.c
    Finished release [optimized] target(s) in 0.05s
     Running `target/release/stacklang --file examples/fibonacci-acc.stack --compile`
clang -Ofast output/fibonacci-acc.c -o output/fibonacci-acc
time output/fibonacci-acc
12586269025

real	0m0.097s
user	0m0.001s
sys	0m0.001s
```

Pretty cool. 

And if I just want to compare VM vs compiler (as I did quite a lot while tracking down bugs):

```bash
$ just both fibonacci-acc

just example fibonacci-acc
just example-run fibonacci-acc
time cargo run --release -- --file examples/fibonacci-acc.stack
    Finished release [optimized] target(s) in 0.08s
     Running `target/release/stacklang --file examples/fibonacci-acc.stack`
12586269025

real	0m0.327s
user	0m0.044s
sys	0m0.036s
just example fibonacci-acc compile=true
just example-compile fibonacci-acc
cargo run --release -- --file examples/fibonacci-acc.stack --compile > output/fibonacci-acc.c
    Finished release [optimized] target(s) in 0.02s
     Running `target/release/stacklang --file examples/fibonacci-acc.stack --compile`
clang -Ofast output/fibonacci-acc.c -o output/fibonacci-acc
time output/fibonacci-acc
12586269025

real	0m0.035s
user	0m0.000s
sys	0m0.001s
```

Shiny. 

## Mandelbrot timing

As mentioned (and shown [above](#justfile)), the C compiler is *fast* compared to the VM. Here's a real example. Generating a 1024x768x8 Mandelbrot image. 

```bash
$ echo -e "1024\n768\n8\n" | just example mandelbrot-read | convert - output/mandelbrot-vm.png

just example-run mandelbrot-read
time cargo run --release -- --file examples/mandelbrot-read.stack
    Finished release [optimized] target(s) in 0.15s
     Running `target/release/stacklang --file examples/mandelbrot-read.stack`
                                                                                                                                       real	2m16.413s
user	1m59.204s
sys	0m2.758s

$ echo -e "1024\n768\n8\n" | just example mandelbrot-read compile=true | convert - output/mandelbrot-compile.png

just example-compile mandelbrot-read
cargo run --release -- --file examples/mandelbrot-read.stack --compile > output/mandelbrot-read.c
    Finished release [optimized] target(s) in 0.02s
     Running `target/release/stacklang --file examples/mandelbrot-read.stack --compile`
clang -Ofast output/mandelbrot-read.c -o output/mandelbrot-read
time output/mandelbrot-read

real	0m2.145s
user	0m2.062s
```

Yes. You read that write. From 2m16s down to 2s. Not too bad! :smile:

## Next steps

I know it's been a while, but I hope it was worth it. Like last time, it's so cool just seeing something like this working...

So what's next? 

* Type checking:
  * Automatically determine specific types of expressions (including blocks)
  * Automatically determine the `arity` of blocks when possible
* Numeric tower:
  * Implement rationals/complex numbers at the parser level + in any interpreter / compiler I have at that point
* Interpreters:
  * A bytecode interpreter/compiler, evaluating at a lower level (I'm not sure how much this would gain, the AST is already fairly low level)
* Compilers:
  * Compile to WASM; since it's also stack based, this should be interesting
  * Compile to x86/ARM assembly

I think I want to work more on types next, possibly doing away with manual coercion. We'll see. 

Onwards, once again!
---
title: "StackLang Part VIII: Compiler Stacks"
date: '2023-08-11 23:59:00'
programming/languages:
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
Let's continue [[StackLang Part VII: New CLI and Datatypes]]() and implement ~~lists~~ stacks in the compiler!

{{< taxonomy-list "series" "StackLang" >}}

In this post:

{{<toc>}}


Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## Implementing stacks

### Adding C code

To implement stacks in the compiler, the first thing that we're going to need is the C version of a stack. I'm going to make it a `ValueStack`, specifically to only store `Value`. I could probably make it more generic, but... why? It's not what we need and C doesn't really do generic things. 

First, let's define the struct:

```c
typedef struct
{
    size_t capacity;
    size_t size;
    Value *values;

} ValueStack;
```

We're going to pre-allocate `capacity`. That's how many `Values` the `ValueStack` can currently hold while `size` is the number of `Values` it is *actually* holding. Then `values` is a block of memory to store the values. 

The goal is when we need more `values` than we have `capacity`, `realloc` and increase `capacity` and move the pointer (if necessary). It's more low level memory manipulation than I normally do, but it's certainly interesting. 

Okay, let's init:

```c
#define VS_INITIAL_CAPACITY 8

// Initialize the stack with default capacity
ValueStack *vs_init()
{
    ValueStack *stack = malloc(sizeof(ValueStack));
    Value *values = malloc(sizeof(Value) * VS_INITIAL_CAPACITY);

    if (!stack || !values)
    {
        fprintf(stderr, "Failed to allocate memory for a ValueStack\n");
        exit(1);
    }

    stack->capacity = VS_INITIAL_CAPACITY;
    stack->size = 0;
    stack->values = values;

    return stack;
}
```

Straight forward. Yes, `VS_INITIAL_CAPACITY` is totally arbitrary. :smile:

Next, let's reallocate (when necessary):

```c
// Ensure there's room to push another value onto the stack
void vs_ensure_capacity(ValueStack *stack, size_t new_size)
{
    if (new_size >= stack->capacity)
    {
        size_t new_capacity = stack->capacity * 2;
        Value *new_values = realloc(stack->values, sizeof(Value) * new_capacity);

        if (!new_values)
        {
            fprintf(stderr, "Failed to re-allocate memory for a ValueStack\n");
            exit(1);
        }

        stack->capacity = new_capacity;
        stack->values = new_values;
    }
}
```

I'm going to go ahead and double the size of the stack whenever it needs to expand. This is probably overestimating (significantly), but I have to choose something. I don't expect it will double too many times in general, so it should be fine. 

It really is fascinating to me that that's all that's needed. If `realloc` can just grab the next chunk of memory, it will just return the same pointer. If not, it will copy all of the values for you and free the old memory. Pretty cool. 

Okay, next the basic stack things, `push` and `pop`:

```c
// Push a value onto the stack
void vs_push(ValueStack *stack, Value val)
{
    vs_ensure_capacity(stack, stack->size + 1);
    stack->values[stack->size++] = val;
}

// Pop and return a  value from the stack
Value *vs_pop(ValueStack *stack)
{
    if (stack->size == 0)
    {
        fprintf(stderr, "Attempted to pop from an empty stack\n");
        exit(1);
    }

    return &stack->values[--stack->size];
}
```

Sweet. 

Next, random access (making it a `vec` rather than a [[wiki:linked list]]()):

```c
// Get a value from the stack by index without removing it
Value *vs_get(ValueStack *stack, size_t index)
{
    if (index >= stack->size)
    {
        fprintf(stderr, "Attempted to get a value from the stack at an invalid index (%lu, size is %lu)\n", index, stack->size);
        exit(1);
    }

    return &stack->values[index];
}

// Set a value in the stack at a given index
void vs_set(ValueStack *stack, size_t index, Value value)
{
    if (index >= stack->size)
    {
        fprintf(stderr, "Attempted to get a value from the stack at an invalid index (%lu, size is %lu)\n", index, stack->size);
        exit(1);
    }

    stack->values[index] = value;
}
```

And that's it. A C style `ValueStack`.

### Connecting it to the compiler

First, a bunch of identical blocks in the `compile_expr` block for `Expression::Identifier`:

```rust
"make-stack" => lines.push(
    include_str!("../compile_c_includes/builtins/stack-new.c")
        .to_string(),
),
"stack-ref" => lines.push(
    include_str!("../compile_c_includes/builtins/stack-ref.c")
        .to_string(),
),
...
```

And then each of those generate a small block of C:

```c
// stack-new.c
{
    Value v = {.type = TAG_STACK, .as_stack = vs_init()};
    *(++stack_ptr) = v;
}

// stack-ref.c
{
    Value *i = stack_ptr--;
    Value *s = stack_ptr--;

    assert_type("stack-ref", "stack", TAG_STACK, s, names);
    assert_type("stack-ref", "integer", TAG_NUMBER_INTEGER, i, names);

    ValueStack *stack = s->as_stack;
    Value *v = vs_get(stack, i->as_integer);
    *(++stack_ptr) = *v;
}
```

Other than the new [type assertions](#adding-type-assertions), pretty simple code. 

And that's it. We have stacks!

## Adding type assertions

So what did I do for type assertions? 

Well, I started writing decent error messages that would output something like "Error in stack-ref; expected stack, got ...". But that's a handful of expressions each time (calling `value_write` and `stack_dump`). Instead, we can make it a single function:

```c
void assert_type(char *name, char *type_name, uint8_t type_tag, Value *value, Name *names)
{
    if (value->type != type_tag)
    {
        fprintf(stderr, "Error in %s, expected a %s, got: ", name, type_name);
        value_write(stderr, value);
        fprintf(stderr, " with");
        stack_dump(names);
        exit(1);
    }
}
```

It's a bit ugly to have to pass both the type name and tag, but the tags are numeric. I could probably do something with macros and `#type_tag`, but I couldn't get it to work. Likewise, having to pass `names` because `stack_dump` needs it is a bit weird, but scoping. 

Still, it's much easier to type one long `assert_type` call rather than those ~6 lines. Good times. 

## The proof is in the (Collatz) pudding?

```bash

$ ./target/release/stacklang vm examples/collatz.stack

1 => 0
2 => 1
3 => 7
4 => 2
5 => 5
6 => 8
7 => 16
8 => 3
9 => 19
10 => 6
11 => 14
12 => 9
13 => 9
14 => 17
15 => 17
16 => 4
17 => 12
18 => 20
19 => 20
20 => 7

$ ./target/release/stacklang compile --run examples/collatz.stack

1 => 0
2 => 1
3 => 7
4 => 2
5 => 5
6 => 8
7 => 16
8 => 3
9 => 19
10 => 6
11 => 14
12 => 9
13 => 9
14 => 17
15 => 17
16 => 4
17 => 12
18 => 20
19 => 20
20 => 7
```

That's so cool when something (eventually) just works(tm). 

## Cleaning up the compiler code

While I was working here, one thing that I wanted to do was clean up the compiler code a bit. 

For some reason, I'd been factoring out the generated code into many different files. But that ... doesn't really make sense. I'm always including it. 

So instead, I'm now making a single [template.c file](https://github.com/jpverkamp/stacklang/blob/f52e0a1adb4142bc6ca3898b6ba74afc26471acb/compile_c_includes/template.c) with blocks that look like `/*{BLOCK}*/` that will be replaced with generated code. Much cleaner. 

I did also add VSCode style `// #region` blocks to the template so that both when I'm editing it and when I'm looking at the generated code, I can get folding and outlines. Pretty cool. 

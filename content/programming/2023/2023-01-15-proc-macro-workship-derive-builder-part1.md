---
title: "Proc Macro Workshop: derive(Builder) [Part 1]"
date: 2023-01-15
programming/languages:
- Rust
programming/topics:
- Rust
- Macros
- Compilers
series:
- "Proc Macro Workshop"
- "Proc Macro Workshop: derive(Builder)"
---
While continuing to learn a bit more about macros in Rust ([[Writing a curry! macro for MacroKata|previous post]]()), I really want to move beyond the simple declarative macros and get into something a bit more interesting. Enter [procedural macros](https://doc.rust-lang.org/reference/procedural-macros.html). In a nutshell, procedural macros in Rust, rather than relying entirely on pattern matching and expansion are fully Rust functions. 

They take a specific input (a stream of tokens) and output a specific output (a new stream of tokens), but in between they can do just about anything a full Rust function can do. And what's better yet... they operate at compile time. And because they operate on tokens (rather than a full AST), you can do things that just aren't syntactically valid in normal Rust. Things like... {{<wikipedia "variadic functions">}} (a la `print!` or `var!`) or even crazier things like [embedding Python in Rust](https://docs.rs/inline-python/latest/inline_python/) for ... reasons. 

Today specifically, I've started working through the [prod-macro-workshop](https://github.com/dtolnay/proc-macro-workshop) repo. It's a series of five examples macros with test cases and some guidance set up to help you get up to speed. I'm going to be working through the first of these: `derive(Builder)`. Now don't get me wrong. I really have no idea what I'm doing, so don't take this as an example of *how to write a macro*. But perhaps by writing this out, it will help me learn it better... and if you happen to learn something as well, all the better!

<!--more-->

{{<toc>}}

## Problem statement

So what is `derive(Builder)` anyways? Well, Rust has a small pile of `derive` macros that you've probably seen already. Things like `derive(Clone)` or `derive(Debug)` that you can attach to a struct/enum/trait by putting them directly before the definition. In doing so, the compiler will know that you want to automatically inject some code based on that. So in the case of `derive(Clone)`, you want to implement the `Clone` trait by providing a `clone` method (that in turn calls `Clone` on each member of the struct). Similarly for `Debug`. So how does/should `Builder` work?

Well, we want to implement the {{<wikipedia "builder pattern">}}. Specifically, since as mentioned Rust doesn't have variadic functions, it's common to build structs by calling `::new` and then passing along a number of additional functions that specify initial values. A la:

```rust
#[derive(Builder)]
pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: String,
}

let command = Command::builder()
    .executable("cargo".to_owned())
    .args(vec!["build".to_owned(), "--release".to_owned()])
    .env(vec![])
    .current_dir("..".to_owned())
    .build()
    .unwrap();
```

That'll take a bit to get to, but that's the direction we're going in. 

Specific to this workshop, we have a series of test cases. Each of which will guide us through another part of writing this macro. So let's buckle in and see what we have to do. 

## 1. Parse

Okay. First, we want to do the very minimum thing and set up the necessary crates. Specifically, we'll want:

* [syn](https://docs.rs/syn/latest/syn/) with `extra-traits`: a syntax parsing library for Rust; turns a stream of Rust tokens into a Rust AST; you can do without (manually parsing the token stream), but for now, we don't want to do this; by including `extra-traits` we get `Debug` (most important), `Eq`, `PartialEq`, and `Hash` for anything `syn` can parse
* [quote](https://docs.rs/quote/latest/quote/): a `quote!` macro that can turn Rust syntax trees back into tokens (essentially acts as the inverse of `syn`)
* [proc-macro2](https://docs.rs/proc-macro2/latest/proc_macro2/): an expansion of the built in `proc_macro` crate that can do things that `proc_macro` cannot do stably yet; in addition `proc_macro` can only be used in macros--this sounds weird, but there's at least one big case that doesn't cover: test cases!

So: 

```bash
$ cargo add syn --features extra-traits
$ cargo add quote
$ cargo add proc-macro2
```

Or, in `cargo.toml`:

```toml
[dependencies]
proc-macro2 = "1.0.49"
quote = "1.0.23"
syn = "1.0.107"
```

Let's take that + the initial scaffold provided and parse out an AST (plus pretty print it with `:#?` and the aforementioned `extra-traits`):

```rust
// --- lib.rs ---
use quote::{quote};
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    eprintln!("{ast:#?}");

    todo!()
}

// --- main.rs ---
use derive_builder::Builder;

#[derive(Builder)]
pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: String,
}

fn main() {}
```

A quick `cargo build` (kind of weird to run code that way, but this is compiler level / macro time), and we see what the compiler sees:

```rust
DeriveInput {
    attrs: [],
    vis: Public(
        VisPublic {
            pub_token: Pub,
        },
    ),
    ident: Ident {
        ident: "Command",
        span: #0 bytes(1001..1008),
    },
    generics: Generics {
        lt_token: None,
        params: [],
        gt_token: None,
        where_clause: None,
    },
    data: Struct(
        DataStruct {
            struct_token: Struct,
            fields: Named(
                FieldsNamed {
                    brace_token: Brace,
                    named: [
                        Field {
                            attrs: [],
                            vis: Inherited,
                            ident: Some(
                                Ident {
                                    ident: "executable",
                                    span: #0 bytes(1015..1025),
                                },
                            ),
                            colon_token: Some(
                                Colon,
                            ),
                            ty: Path(
                                TypePath {
                                    qself: None,
                                    path: Path {
                                        leading_colon: None,
                                        segments: [
                                            PathSegment {
                                                ident: Ident {
                                                    ident: "String",
                                                    span: #0 bytes(1027..1033),
                                                },
                                                arguments: None,
                                            },
                                        ],
                                    },
                                },
                            ),
                        },
                        Comma,
                        Field {
                            attrs: [],
                            vis: Inherited,
                            ident: Some(
                                Ident {
                                    ident: "args",
                                    span: #0 bytes(1039..1043),
                                },
                            ),
                            colon_token: Some(
                                Colon,
                            ),
                            ty: Path(
                                TypePath {
                                    qself: None,
                                    path: Path {
                                        leading_colon: None,
                                        segments: [
                                            PathSegment {
                                                ident: Ident {
                                                    ident: "Vec",
                                                    span: #0 bytes(1045..1048),
                                                },
                                                arguments: AngleBracketed(
                                                    AngleBracketedGenericArguments {
                                                        colon2_token: None,
                                                        lt_token: Lt,
                                                        args: [
                                                            Type(
                                                                Path(
                                                                    TypePath {
                                                                        qself: None,
                                                                        path: Path {
                                                                            leading_colon: None,
                                                                            segments: [
                                                                                PathSegment {
                                                                                    ident: Ident {
                                                                                        ident: "String",
                                                                                        span: #0 bytes(1049..1055),
                                                                                    },
                                                                                    arguments: None,
                                                                                },
                                                                            ],
                                                                        },
                                                                    },
                                                                ),
                                                            ),
                                                        ],
                                                        gt_token: Gt,
                                                    },
                                                ),
                                            },
                                        ],
                                    },
                                },
                            ),
                        },
                        Comma,
                        Field {
                            attrs: [],
                            vis: Inherited,
                            ident: Some(
                                Ident {
                                    ident: "env",
                                    span: #0 bytes(1062..1065),
                                },
                            ),
                            colon_token: Some(
                                Colon,
                            ),
                            ty: Path(
                                TypePath {
                                    qself: None,
                                    path: Path {
                                        leading_colon: None,
                                        segments: [
                                            PathSegment {
                                                ident: Ident {
                                                    ident: "Vec",
                                                    span: #0 bytes(1067..1070),
                                                },
                                                arguments: AngleBracketed(
                                                    AngleBracketedGenericArguments {
                                                        colon2_token: None,
                                                        lt_token: Lt,
                                                        args: [
                                                            Type(
                                                                Path(
                                                                    TypePath {
                                                                        qself: None,
                                                                        path: Path {
                                                                            leading_colon: None,
                                                                            segments: [
                                                                                PathSegment {
                                                                                    ident: Ident {
                                                                                        ident: "String",
                                                                                        span: #0 bytes(1071..1077),
                                                                                    },
                                                                                    arguments: None,
                                                                                },
                                                                            ],
                                                                        },
                                                                    },
                                                                ),
                                                            ),
                                                        ],
                                                        gt_token: Gt,
                                                    },
                                                ),
                                            },
                                        ],
                                    },
                                },
                            ),
                        },
                        Comma,
                        Field {
                            attrs: [],
                            vis: Inherited,
                            ident: Some(
                                Ident {
                                    ident: "current_dir",
                                    span: #0 bytes(1084..1095),
                                },
                            ),
                            colon_token: Some(
                                Colon,
                            ),
                            ty: Path(
                                TypePath {
                                    qself: None,
                                    path: Path {
                                        leading_colon: None,
                                        segments: [
                                            PathSegment {
                                                ident: Ident {
                                                    ident: "String",
                                                    span: #0 bytes(1097..1103),
                                                },
                                                arguments: None,
                                            },
                                        ],
                                    },
                                },
                            ),
                        },
                        Comma,
                    ],
                },
            ),
            semi_token: None,
        },
    ),
}
warning: fields `executable`, `args`, `env`, and `current_dir` are never read
  --> main.rs:28:5
   |
27 | pub struct Command {
   |            ------- fields in this struct
28 |     executable: String,
   |     ^^^^^^^^^^
29 |     args: Vec<String>,
   |     ^^^^
30 |     env: Vec<String>,
   |     ^^^
31 |     current_dir: String,
   |     ^^^^^^^^^^^
   |
   = note: `#[warn(dead_code)]` on by default

warning: `proc-macro-workshop` (bin "workshop") generated 1 warning
    Finished dev [unoptimized + debuginfo] target(s) in 0.08s
```

Well that's certainly a lot. But what's import is that we have the nicely nested structure that we're expecting. A few interesting things jump out immediately at me:

* `ast.ident` is the identifier that we're going to want to use in our macro (the name of the `struct` we're doing the `derive` on)
* there are various `span` arguments that represent where in source code each token is (useful for good error messages)
* `data` contains the actual nested data, specifically the `fields` as a `FieldsNamed`; that will be useful to make the necessary functions

So... do we compile?

```bash
$ cargo test

   Compiling derive_builder v0.0.0 (/Users/jp/Projects/proc-macro-workshop/builder)
    Finished test [unoptimized + debuginfo] target(s) in 0.31s
     Running unittests src/lib.rs (/Users/jp/Projects/proc-macro-workshop/target/debug/deps/derive_builder-c665c92efcacdb1a)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/progress.rs (/Users/jp/Projects/proc-macro-workshop/target/debug/deps/tests-0a232a511e2dccbe)

running 1 test
   Compiling derive_builder v0.0.0 (/Users/jp/Projects/proc-macro-workshop/builder)
   Compiling derive_builder-tests v0.0.0 (/Users/jp/Projects/proc-macro-workshop/target/tests/derive_builder)
    Finished dev [unoptimized + debuginfo] target(s) in 0.32s


test tests/01-parse.rs ... ok


test tests ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.63s

   Doc-tests derive_builder

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Sweet.

## 2. Create `builder`

Okay, we don't do anything yet. (Other than parsing an AST). What's next? 

First, we want to write a `builder` function for `Command` (or whatever we're wrapping). As mentioned, to do that, we'll want the `ast.ident`:

```rust
use quote::{quote};
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let ident = ast.ident;

    let output = quote! {
        impl #ident {
            pub fn builder() {
                todo!()
            }
        }
    };

    proc_macro::TokenStream::from(output)
}
```

As I mentioned `quote!` is essentially the opposite of `syn` / `parse_macro_input!`. Given a block of Rust code, it will interpolate any variables (prefixed with `#`, they have to implement `ToTokens`, but anything we get from `syn` will do that) and return a `TokenStream`. That we can in turn return (that sounds funny) from the function. 

For now, we just want to generate the new (almost empty) function. One thing that's pretty cool: we can actually see what we're expanding to by using the `cargo-expand` crate/tool. 


```rust
// $ cargo expand
// 
//     Checking proc-macro-workshop v0.0.0 (/Users/jp/Projects/proc-macro-workshop)
//     Finished dev [unoptimized + debuginfo] target(s) in 0.05s

#![feature(prelude_import)]
#[prelude_import]
use std::prelude::rust_2021::*;
#[macro_use]
extern crate std;
use derive_builder::Builder;
pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: String,
}
impl Command {
    pub fn builder() {
        ::core::panicking::panic("not yet implemented")
    }
}
fn main() {
    let builder = Command::builder();
    let _ = builder;
}
```

That's pretty much exactly what we expectc to see. The initial `pub struct Command` and fields are left alone and then the new `impl Command` with the `panic` (from `todo!`) is included. That's pretty cool. 

What else? 

> Before moving on, have the macro also generate:
> 
> ```rust
> pub struct CommandBuilder {
>     executable: Option<String>,
>     args: Option<Vec<String>>,
>     env: Option<Vec<String>>,
>     current_dir: Option<String>,
> }
> ```
> 
> and in the `builder` function:
> 
> ```rust
> impl Command {
>     pub fn builder() -> CommandBuilder {
>         CommandBuilder {
>             executable: None,
>             args: None,
>             env: None,
>             current_dir: None,
>         }
>     }
> }
> ```

Now that... that is a bit more interesting. From what I see, to do this, we need to be able to do a few things:

* Generate a new `Ident` for `CommandBuilder`, so figure out how to to strings into `Ident`s
* Create a new struct defintion that has the same fields as our object but each made optional
* Modify our currently empty `builder` function to return a new `CommandBuilder` object

Neat. So, first. How can we get a new `Ident`? Well, luckily if you dig a bit in `quote`, there just so happens to be exactly the macro you might need: [format_ident!](https://docs.rs/quote/latest/quote/macro.format_ident.html). Taking the same same form as `format!` and makes an `Ident` out of it. So we have:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let ident = ast.ident;
    let builder_ident = format_ident!("{ident}Builder");

    let output = quote! {
        // ...

        pub struct #builder_ident {
        }
    };

    proc_macro::TokenStream::from(output)
}
```

And expanded:

```rust
// $ cargo expand
// 
//     Checking proc-macro-workshop v0.0.0 (/Users/jp/Projects/proc-macro-workshop)
//     Finished dev [unoptimized + debuginfo] target(s) in 0.05s

// ...
impl Command {
    pub fn builder() {
        ::core::panicking::panic("not yet implemented")
    }
}
pub struct CommandBuilder {}
// ...
```

Well that way easy (how long has it been since the Easy Button?). 

Next though, we want to parse the fields. Remember the giant AST from before? And how I mentioned the `fields` variable? Well, let's write a BMOD (Big Match Of Doom) and pull that field out:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as syn::DeriveInput);
    let ident = ast.ident.clone();
    let builder_ident = format_ident!("{ident}Builder");

    let fields = match ast {
        syn::DeriveInput{
            data: syn::Data::Struct(
                syn::DataStruct{
                    fields: syn::Fields::Named (
                        syn::FieldsNamed{
                            named: fields,
                            ..
                        },
                    ),
                    ..
                },

            ),
            ..
        } => {
            fields
        },
        _ => unimplemented!("derive(Builder) only supports structs with named fields")
    };

    // ...
}
```

So that's a mess. But going through the printed AST from earlier + docs to trace down when we have an enum (`syn::Data` is a `Struct`, `Enum`, or `Union`; `syn::Fields` is `Named`, `Unnamed` or `Unit`) and unpack the fields (heh) we care about makes it... well, if not easy at least understandable. 

One note is that I did add a `clone` to the `ident` line. Taking that fields partially borrows `ast`, which we need later (now) to match against, so `clone` the text and we're good. 

So. We have the fields. How do we output them again with `Option<...>`? Well... that's actually the neat part. Remember how I said that you can safely put anything in a `quote!` that has `ToTokens`? Well, the output of `quote!` does that. And there's even an iterator form. So if we can make an `Iterator` where `Item: ToTokens`, we should be good. Something like this:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    let builder_fields = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let ty = field.ty;

        quote! {
            #id: std::option::Option<#ty>
        }
    });

    let output = quote! {
        impl #ident {
            pub fn builder() {
                todo!()
            }
        }

        pub struct #builder_ident {
            #(#builder_fields)*
        }
    };

    proc_macro::TokenStream::from(output)
}
```

That's the iterated `quote!` syntax I was talking about. The same way that declarative macros work, `#(...)*` signifies that the thing in the parens is something that you can iterate 0 or more times, in this case `#builder_fields`. One step before that, we're making `builder_fields` by taking each field, getting it's `id`entifier and `ty`pe, wrapping it in `Option` and making that into tokens. 

So, what's the output look like?

```rust
// $ cargo expand
// ...

pub struct CommandBuilder {
    executable: std::option::Option<String>,
    args: std::option::Option<Vec<String>>,
    env: std::option::Option<Vec<String>>,
    current_dir: std::option::Option<String>,
}

// ...
```

Not going to lie, that's pretty cool. 

So, as a side note, why did I use `std::option::Option` there? Well, for one, the comments hint that it's probably a good idea. For two, I'm used to the idea of macros having to be more specific than code that you may yourself write. I have no idea why you might want to, but imagine the case where I added a `use std::option`... and then in your code you have something silly like `struct Option { /* do stuff */ }`. Defining your own type. 

If Rust macros were truly hygenic (like Racket macros are, by default), this wouldn't be a problem. But they aren't, so it is. You get things like `Option` leaking through the macro abstraction. So... over specify and things should go well for you. 

Okay, last part, we want to modify our `builder` function to initialize one of these:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    let builder_defaults = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        
        quote! { #id: std::option::Option::None }
    });

    let output = quote! {
        pub struct #builder_ident {
            #(#builder_fields),*
        }

        impl #ident {
            pub fn builder() -> #builder_ident {
                #builder_ident { 
                    #(#builder_defaults),*
                }
            }
        }
    };

    proc_macro::TokenStream::from(output)
}

```

So here, we only care about the `id` for each field and we want to set each field to `None`. That's why we made them `Option` after all. In this case, `#(...),*` means repeat what's in the parens 0 or more times, but this time delimit with `,`. 

So we get:

```rust
// $ cargo expand
// ...

pub struct CommandBuilder {
    executable: std::option::Option<String>,
    args: std::option::Option<Vec<String>>,
    env: std::option::Option<Vec<String>>,
    current_dir: std::option::Option<String>,
}
impl Command {
    pub fn builder() -> CommandBuilder {
        CommandBuilder {
            executable: std::option::Option::None,
            args: std::option::Option::None,
            env: std::option::Option::None,
            current_dir: std::option::Option::None,
        }
    }
}
fn main() {
    let builder = Command::builder();
    let _ = builder;
}
```

That should be what we want... and tests pass. Awesome. Onward!

## 3. Call setters

Next up:

> Generate methods on the builder for setting a value of each of the struct
> fields.
>
> ```rust
> impl CommandBuilder {
>     fn executable(&mut self, executable: String) -> &mut Self {
>         self.executable = Some(executable);
>         self
>     }
>
>     ...
> }
> ```

That's not bad. What we want to do for each of these is:

* for each `field` in `fields`
  * create a new method with the same name as the `field`
  * the method should take a variable of the `type` of the `field`
  * update the `field` in the struct with `Some(value)` (since it's optional)
  * return `&mut self` so these can chain

Sweet. Let's do it:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    let setters = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let ty = field.ty;

        quote! {
            pub fn #id(&mut self, value: #ty) -> &mut Self {
                self.#id = std::option::Option::Some(value);
                self
            }
        }
    });

    let output = quote! {
        pub struct #builder_ident {
            #(#builder_fields),*
        }

        impl #builder_ident {
            #(#setters)*
        }

        impl #ident {
            pub fn builder() -> #builder_ident {
                #builder_ident { 
                    #(#builder_defaults),*
                }
            }
        }
    };

    proc_macro::TokenStream::from(output)
}
```

Make sure that the new `setters` are specifically in the in a new `impl #builder_ident` (and not the `struct` definition) as I did at first and you should be golden:

```rust
// ----- main.rs -----
#[derive(Builder)]
pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: String,
}

fn main() {
    let mut builder = Command::builder();
    builder.executable("cargo".to_owned());
    builder.args(vec!["build".to_owned(), "--release".to_owned()]);
    builder.env(vec![]);
    builder.current_dir("..".to_owned());
}

// $ cargo expand
// ...

impl CommandBuilder {
    pub fn executable(&mut self, value: String) -> &mut Self {
        self.executable = std::option::Option::Some(value);
        self
    }
    pub fn args(&mut self, value: Vec<String>) -> &mut Self {
        self.args = std::option::Option::Some(value);
        self
    }
    pub fn env(&mut self, value: Vec<String>) -> &mut Self {
        self.env = std::option::Option::Some(value);
        self
    }
    pub fn current_dir(&mut self, value: String) -> &mut Self {
        self.current_dir = std::option::Option::Some(value);
        self
    }
}

// ...

fn main() {
    let mut builder = Command::builder();
    builder.executable("cargo".to_owned());
    builder
        .args(
            <[_]>::into_vec(
                #[rustc_box]
                ::alloc::boxed::Box::new(["build".to_owned(), "--release".to_owned()]),
            ),
        );
    builder.env(::alloc::vec::Vec::new());
}
```

We get the new functions and even get an interesting look at what `vec!` expands into. Apparently it takes a `rustc_box` of the values and calls `into_vec` on it. Interesting!

And tests pass. I think I'm getting the hang of this now!

## 4. Call `build`

> Generate a `build` method to go from builder to original struct.
>
> This method should require that every one of the fields has been explicitly
> set; it should return an error if a field is missing. The precise error type
> is not important. Consider using Box<dyn Error>, which you can construct
> using the impl From<String> for Box<dyn Error>.
>
> ```rust
> impl CommandBuilder {
>     pub fn build(&mut self) -> Result<Command, Box<dyn Error>> {
>         ...
>     }
> }
> ```

Okay, that makes sense. We have all of these `Option`s, let's make sure they're set and then output something. I think that doing this in two parts makes the most sense: first will check each variable and second will actually build the `Command`:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    let build_checkers = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let err = format!("{id} was not set");

        quote! {
            if self.#id.is_none() {
                return std::result::Result::Err(#err.to_owned().into());
            }
        }
    });

    let build_fields = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();

        quote! {
            #id: self.#id.clone().unwrap()
        }
    });

    let output = quote! {
        // ...

        impl #builder_ident {
            #(#setters)*

            pub fn build(&mut self) -> std::result::Result<#ident, std::boxed::Box<dyn std::error::Error>> {
                #(#build_checkers);*

                std::result::Result::Ok(#ident {
                    #(#build_fields),*
                })
            }
        }

        // ...
    };

    proc_macro::TokenStream::from(output)
}
```

It's a bit funny looking here, but perhaps more sensible if you see what `cargo expand` is:

```rust
// $ cargo expand
// ...

impl CommandBuilder {
    // ...

    pub fn build(
        &mut self,
    ) -> std::result::Result<Command, std::boxed::Box<dyn std::error::Error>> {
        if self.executable.is_none() {
            return std::result::Result::Err("executable was not set".into());
        }
        if self.args.is_none() {
            return std::result::Result::Err("args was not set".into());
        }
        if self.env.is_none() {
            return std::result::Result::Err("env was not set".into());
        }
        if self.current_dir.is_none() {
            return std::result::Result::Err("current_dir was not set".into());
        }
        std::result::Result::Ok(Command {
            executable: self.executable.clone().unwrap(),
            args: self.args.clone().unwrap(),
            env: self.env.clone().unwrap(),
            current_dir: self.current_dir.clone().unwrap(),
        })
    }
}

// ...
```

Each of the fields will check `is_none` and if it is, return an `Err` constructed from an `&str` (`into` is still a little weird to me...). If all of those pass, we'll created a new `Result::Ok` that wraps the values. One gotcha here is that we need to `clone()` each one, since the `CommandBuilder` still owns the values. Not sure I'm a fan of that, since `clone()` can be expensive. But after that, it's safe to `unwrap()`, since we've already checked that they are `Some`.

Is there another way to do this? Of course! [ok_or](https://doc.rust-lang.org/stable/std/option/enum.Option.html#method.ok_or). Basically, if you have an `Option`, you can turn it into a `Result` that will contain the `Some` or an `Err` if it was `None`. Like this:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    let build_fields = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let err = format!("{id} was not set");

        quote! {
            #id: self.#id.clone().ok_or(#err.into())?
        }
    });

    // ...
}
```

Rust doesn't like that though:

```rust
error[E0283]: type annotations needed
  --> tests/04-call-build.rs:16:10
   |
16 | #[derive(Builder)]
   |          ^^^^^^^ cannot infer type of the type parameter `E` declared on the associated function `ok_or`
   |
   = note: multiple `impl`s satisfying `Box<dyn std::error::Error>: From<_>` found in the following crates: `alloc`, `core`:
           - impl From<String> for Box<(dyn std::error::Error + 'static)>;
           - impl<'a, E> From<E> for Box<(dyn std::error::Error + 'a)>
             where E: std::error::Error, E: 'a;
           - impl<'a> From<Cow<'a, str>> for Box<(dyn std::error::Error + 'static)>;
           - impl<> From<&str> for Box<(dyn std::error::Error + 'static)>;
           - impl<T> From<!> for T;
           - impl<T> From<T> for T;
   = note: required for `Result<Command, Box<dyn std::error::Error>>` to implement `FromResidual<Result<Infallible, _>>`
   = note: this error originates in the derive macro `Builder` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider specifying the generic argument
   |
16 | #[derive(Builder::<E>)]
   |                 +++++
```

And I don't really want to specify the return types right now... so we'll go with the first option for the time being!

All tests pass, let's do part 5!

## 5. Method chaining

This one is actually why we've been return `&mut Self` this whole time. By doing that, we can chain the methods, turning this:

```rust
fn main() {
    let mut builder = Command::builder()
    builder.executable("cargo".to_owned());
    builder.args(vec!["build".to_owned(), "--release".to_owned()]);
    builder.env(vec![]);
    builder.current_dir("..".to_owned());
    let command = builder.build().unwrap();

    assert_eq!(command.executable, "cargo");
}
```

Into this:

```rust
fn main() {
    let command = Command::builder()
        .executable("cargo".to_owned())
        .args(vec!["build".to_owned(), "--release".to_owned()])
        .env(vec![])
        .current_dir("..".to_owned())
        .build()
        .unwrap();

    assert_eq!(command.executable, "cargo");
}
```

I like the second style and... it just works!

Free is good. :smile:

## 6. Optional fields

> Some fields may not always need to be specified. Typically these would be represented as Option<T> in the struct being built. Have your macro identify fields in the macro input whose type is Option and make the corresponding builder method optional for the caller.

Now that's interesting. So how do we know if something is optional? Well, let's look at what the `ast` is for a sample field:

```rust
// ----- main.rs -----
#[derive(Builder)]
pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: Option<String>,
}

// ----- lib.rs -----
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as syn::DeriveInput);
    let ident = ast.ident.clone();
    let builder_ident = format_ident!("{ident}Builder");

    let fields = match ast {
        // ...
    };

    println!("{:#?}", fields.iter().last().unwrap());

    // ...
}

// ----- <stdout> -----
// ...

Field {
    attrs: [],
    vis: Inherited,
    ident: Some(
        Ident {
            ident: "current_dir",
            span: #0 bytes(2871..2882),
        },
    ),
    colon_token: Some(
        Colon,
    ),
    ty: Path(
        TypePath {
            qself: None,
            path: Path {
                leading_colon: None,
                segments: [
                    PathSegment {
                        ident: Ident {
                            ident: "Option",
                            span: #0 bytes(2884..2890),
                        },
                        arguments: AngleBracketed(
                            AngleBracketedGenericArguments {
                                colon2_token: None,
                                lt_token: Lt,
                                args: [
                                    Type(
                                        Path(
                                            TypePath {
                                                qself: None,
                                                path: Path {
                                                    leading_colon: None,
                                                    segments: [
                                                        PathSegment {
                                                            ident: Ident {
                                                                ident: "String",
                                                                span: #0 bytes(2891..2897),
                                                            },
                                                            arguments: None,
                                                        },
                                                    ],
                                                },
                                            },
                                        ),
                                    ),
                                ],
                                gt_token: Gt,
                            },
                        ),
                    },
                ],
            },
        },
    ),
}

// ...
```

That's still so much type. The things to note though are:

* The initial `Type` is a `Path` containing (a few steps down) one `PathSegment` with `ident` of `Ident{ident: "Option"}` and `arguments` that are `AngleBracketed` with its own `args`, which in turn have a single `Type` in them. That's exactly the pattern match, so can we write one BMOD for that?

```rust
fn try_optional(ty: &syn::Type) -> std::option::Option<syn::Type> {
    // Pull out the first path segments (containing just the Option)
    // Verify that there's exactly one value in the path
    let segments = match ty {
        syn::Type::Path(
            syn::TypePath{
                path: syn::Path {
                    segments,
                    ..
                },
                ..
            }
        ) 
        if segments.len() == 1
        => segments.clone(),
        _ => return std::option::Option::None,
    };
    
    // Pull out the first arg segment in the Option
    // Verify that there's exactly one parameter
    let args = match &segments[0] {
        syn::PathSegment{
            ident,
            arguments: syn::PathArguments::AngleBracketed(
                syn::AngleBracketedGenericArguments {
                    args,
                    ..
                }
            )
        }
        if ident == "Option" && args.len() == 1
        => args,
        _ => return std::option::Option::None,
    };
    
    // Extract that single type
    // Verify that there's exactly one
    // TODO: Future case should deal with things like lifetimes etc that could also be in here
    let ty = match &args[0] {
        syn::GenericArgument::Type(t) => t,
        _ => return std::option::Option::None
    };

    Some(ty.clone())
}
```

Not exactly. Because we can't (for whatever reason) match directly against a `Punctuated` that I can tell, instead we have to `iter()` and check each of those (as above). But this function otherwise does exactly what we want. If the type given is an `Option`, return `Some` inner type. If it's not, `None`. 

Now we need to thread this through our existing code a bit:

```rust
#[proc_macro_derive(Builder)]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    // In builder fields, we take either the Option's inner type or the original type
    let builder_fields = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let ty = try_optional(&field.ty).or(std::option::Option::Some(field.ty));
        
        quote! { #id: std::option::Option<#ty> }
    });

    // ...

    // In setters, we always unwrap the type (and ... put the Option right back on :smile:)
    let setters = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let ty = try_optional(&field.ty).or(std::option::Option::Some(field.ty));

        quote! {
            pub fn #id(&mut self, value: #ty) -> &mut Self {
                self.#id = std::option::Option::Some(value);
                self
            }
        }
    });

    // In build checkers, we only check if `try_optional` doesn't return
    // If it doesn't, it's an optional value, so not having it set is expected
    // This does need to return something ToTokens, ergo `quote!{}`
    let build_checkers = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();
        let err = format!("{id} was not set");

        if try_optional(&field.ty).is_none() {
            quote! {
                if self.#id.is_none() {
                    return std::result::Result::Err(#err.into());
                }
            }
        } else {
            quote! {}
        }
    });

    // When we're building the fields, don't unwrap explicitly optional fields, keep the Option
    let build_fields = fields.iter().map(|field| {
        let field = field.clone();
        let id = field.ident.unwrap();

        if try_optional(&field.ty).is_some() {
            quote! {
               #id: self.#id.clone()
            }
        } else {
            quote! {
               #id: self.#id.clone().unwrap()
            }
        }
    });

    // ...
}
```

Okay, so it's a few changes throughout the entire code, but I think it's still relatively reasonable. Pulling that out into a helper function was nice though. The other optional would have been to make something like a list of `optional_fields` during our macro expansion or perhaps to attach the new value to `fields` as we collect them. But I like this well enough. 

And the macro expansion, once all that is written out:

```rust
// $ cargo expand
// ...

pub struct Command {
    executable: String,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: Option<String>,
}
pub struct CommandBuilder {
    executable: std::option::Option<String>,
    args: std::option::Option<Vec<String>>,
    env: std::option::Option<Vec<String>>,
    current_dir: std::option::Option<String>,
}
impl CommandBuilder {
    pub fn executable(&mut self, value: String) -> &mut Self {
        self.executable = std::option::Option::Some(value);
        self
    }
    pub fn args(&mut self, value: Vec<String>) -> &mut Self {
        self.args = std::option::Option::Some(value);
        self
    }
    pub fn env(&mut self, value: Vec<String>) -> &mut Self {
        self.env = std::option::Option::Some(value);
        self
    }
    pub fn current_dir(&mut self, value: String) -> &mut Self {
        self.current_dir = std::option::Option::Some(value);
        self
    }
    pub fn build(
        &mut self,
    ) -> std::result::Result<Command, std::boxed::Box<dyn std::error::Error>> {
        if self.executable.is_none() {
            return std::result::Result::Err("executable was not set".into());
        }
        if self.args.is_none() {
            return std::result::Result::Err("args was not set".into());
        }
        if self.env.is_none() {
            return std::result::Result::Err("env was not set".into());
        }
        std::result::Result::Ok(Command {
            executable: self.executable.clone().unwrap(),
            args: self.args.clone().unwrap(),
            env: self.env.clone().unwrap(),
            current_dir: self.current_dir.clone(),
        })
    }
}
impl Command {
    pub fn builder() -> CommandBuilder {
        CommandBuilder {
            executable: std::option::Option::None,
            args: std::option::Option::None,
            env: std::option::Option::None,
            current_dir: std::option::Option::None,
        }
    }
}
// ...
```

I think the best part is that this really shows the power of macros. The extra error check is *just gone*, since it's either generated (or not) at compile time. Likewise, the new type for `current_dir` and the lack of `unwrap` on the same. Pretty cool. 

## To be continued...

Well, that's about 5000 words so far, so let's go ahead and split this post. I'll finish up the macro either next part or in three and then onwards to the other examples.

It's fun so far!
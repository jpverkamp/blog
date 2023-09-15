---
title: "Proc Macro Workshop: derive(Builder) [Part 2]"
date: 2023-01-17
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
Okay, in [[Proc Macro Workshop: derive(Builder) [Part 1]]]() we created a `derive(Builder)` macro to implement the [[wiki:builder pattern]](). We created a new `*Builder` struct, created methods to set each field in a chain, and allowed some fields to be optional. 

So what's left? (Be sure to start with [[Proc Macro Workshop: derive(Builder) [Part 1]|Part 1]]() if you haven't read that!)

{{<toc>}}

Let's do this!

<!--more-->

## 7. Repeated fields

For this, we want to add support for:

```rust
let command = Command::builder()
    .executable("cargo".to_owned())
    .arg("build".to_owned())
    .arg("--release".to_owned())
    .build()
    .unwrap();
```

Explicitly, to be able to specify the `args` one at a time (if we want). To do that, one option would be to automagically create the singular for plural field names... but that doesn't seem very Rusty. Instead, we'll use `attributes`:

```rust
#[derive(Builder)]
pub struct Command {
    executable: String,
    #[builder(each = "arg")]
    args: Vec<String>,
    #[builder(each = "env")]
    env: Vec<String>,
    current_dir: Option<String>,
}
```

Any time you specify `builder(each = $name)`, you should create a second method that takes the values one at a time. One additional gotcha: if the name is different (a la `args` and `arg`), generate both. If they aren't (a la `env`), only generate the one at a time method. 

That'll be interesting!

So first, we'll need to parse the attributes. To tell the macro library that we're doing this, we actually need to change the first `proc_macro_derive` call with an additional `attributes` parameter. It's macros all the way down!

```rust
#[proc_macro_derive(Builder, attributes(builder))]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...
}
```

Then, let's look at what we're actually getting here. Putting a `println!("{:#?}", ...)` on the first field above (args), we get:

```rust
Some(
    Field {
        attrs: [
            Attribute {
                pound_token: Pound,
                style: Outer,
                bracket_token: Bracket,
                path: Path {
                    leading_colon: None,
                    segments: [
                        PathSegment {
                            ident: Ident {
                                ident: "builder",
                                span: #0 bytes(1468..1475),
                            },
                            arguments: None,
                        },
                    ],
                },
                tokens: TokenStream [
                    Group {
                        delimiter: Parenthesis,
                        stream: TokenStream [
                            Ident {
                                ident: "each",
                                span: #0 bytes(1476..1480),
                            },
                            Punct {
                                ch: '=',
                                spacing: Alone,
                                span: #0 bytes(1481..1482),
                            },
                            Literal {
                                kind: Str,
                                symbol: "arg",
                                suffix: None,
                                span: #0 bytes(1483..1488),
                            },
                        ],
                        span: #0 bytes(1475..1489),
                    },
                ],
            },
        ],
        vis: Inherited,
        ident: Some(
            Ident {
                ident: "args",
                span: #0 bytes(1495..1499),
            },
        ),
        colon_token: Some(
            Colon,
        ),
        ty: Path(
            // ...
        ),
    },
)
```

So. We'll have `attrs`, which is a list of some sort containing the `path` part (`builder`) and the internal `tokens` part (`each = "arg"`). Let's make a function that can pull out a specific attribute as a hash map. 

I feel like we should be able to get a bit more structure out of that though... and thankfully the `syn` maintainers agreed. There's a [parse_meta](https://docs.rs/syn/latest/syn/struct.Attribute.html#method.parse_meta) method on `Attribute` that (if possible) parses the attribute into a `Meta` form:

```rust
Ok(
    List(
        MetaList {
            path: Path {
                leading_colon: None,
                segments: [
                    PathSegment {
                        ident: Ident {
                            ident: "builder",
                            span: #0 bytes(1468..1475),
                        },
                        arguments: None,
                    },
                ],
            },
            paren_token: Paren,
            nested: [
                Meta(
                    NameValue(
                        MetaNameValue {
                            path: Path {
                                leading_colon: None,
                                segments: [
                                    PathSegment {
                                        ident: Ident {
                                            ident: "each",
                                            span: #0 bytes(1476..1480),
                                        },
                                        arguments: None,
                                    },
                                ],
                            },
                            eq_token: Eq,
                            lit: Str(
                                LitStr {
                                    token: "arg",
                                },
                            ),
                        },
                    ),
                ),
            ],
        },
    ),
)
```

So let's see what we can do to parse this:

```rust
fn try_parse_builder_each(field: &syn::Field) -> std::result::Result<std::option::Option<String>, syn::Error> {
    for attr in field.attrs.iter() {
        let err = std::result::Result::Err(syn::Error::new(field.span(), "Unknown attribute form"));

        let nested = match attr.parse_meta() {
            Ok(syn::Meta::List(
                syn::MetaList { 
                    path: syn::Path {
                        segments,
                        ..
                    },
                    nested,
                    .. 
                }
            )) if segments.len() == 1 && segments[0].ident == "builder" && nested.len() == 1
            => nested[0].clone(),
            Ok(_) => return err,
            Err(e) => return std::result::Result::Err(e),
        };

        // TODO: check the eq_token?
        let value = match nested {
            syn::NestedMeta::Meta (
                syn::Meta::NameValue (
                    syn::MetaNameValue {
                        path: syn::Path {
                            segments,
                            ..
                        },
                        eq_token,
                        lit: syn::Lit::Str(str)
                    } 

                )
            ) if segments.len() == 1 && segments[0].ident == "each"
            => str.value(),
            _ => return err,
        };

        return std::result::Result::Ok(std::option::Option::Some(value));
    }

    // If we make it out of the loop, no (matching) attributes; response is Ok but None
    std::result::Result::Ok(std::option::Option::None)
}
```

I'm not sure if I'm happy with this or not. It's a bit weird to have a `Result<Option<String>>`, but I think that's what I want. It's `Ok` if it parses correctly, `Err` if it doesn't. And then it's `Some<String>` if we get back a value and `None` if it parsed correctly but without a value. 

Other than that, we do the same as we did yesterday for `try_optional` and unpack the meta structure, checking it as we go. 

To test it out:

```rust
// ----- lib.rs -----

#[proc_macro_derive(Builder, attributes(builder))]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    for field in fields.iter() {
        let id = field.ident.clone().unwrap();
        let v = try_parse_builder_each(field);
        println!("{id:#}: {v:?}");
    }

    // ...
}

// $ cargo expand
// ...

executable: Ok(None)
args: Ok(Some("arg"))
env: Ok(Some("env"))
current_dir: Ok(None)

// ...
```

That's a good sign!

So we know which ones are optional... and actually which ones have two methods (if the names are different) versus just one (if they're the same). 

But... now we're really getting into the weeds, so I'm going to go back and do something I should have done a while ago... I'm going to replaced `fields` with a custom struct that has exactly what I want:

```rust
#[proc_macro_derive(Builder, attributes(builder))]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as syn::DeriveInput);
    let ident = ast.ident.clone();
    let builder_ident = format_ident!("{ident}Builder");

    // Unwrap the nested fields information
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

    struct FieldData {
        // Main identifier and type for the field
        id: syn::Ident,
        ty: syn::Type,
        // If the type is a simply nested type (a la Option<Thing> or Vec<Thing>), populate these
        nested_ty: std::option::Option<(String, syn::Type)>,
        // If the field has an each id
        each_id: std::option::Option<syn::Ident>,
    }

    // Parse the fields information we actually care about
    let fields = fields.iter().map(|field| {
        let id = field.ident.as_ref().unwrap().clone();
        let ty = field.ty.clone();
        
        let mut nested_ty = std::option::Option::None;
        
        let valid_outer_types = ["Option", "Vec"];
        for target in valid_outer_types {
            if let std::option::Option::Some(ty) = try_nested_type(&ty, target) {
                nested_ty = std::option::Option::Some((target.to_owned(), ty));
                break;
            }
        }

        let each_id = if let std::option::Option::Some(id) = try_parse_builder_each(&field).unwrap() {
            std::option::Option::Some(format_ident!("{}", id))
        } else {
            std::option::Option::None
        };

        FieldData {
            id,
            ty,
            nested_ty,
            each_id,
        }
    }).collect::<Vec<_>>();

    // ...
}
```

Basically, go ahead and keep the `id` and `ty` as we have, but now, we're going to also:

* Parse a few known inner types (`Option` for the previously used intentionally optional fields and `Vec` for the currently only supported `each` type)
* Use the function above to parse the `each` attribute as an identifier (this code could be inlined, since this is now the only place that calls it)

Then... we get to go through and use this in all of the previous methods:

```rust
#[proc_macro_derive(Builder, attributes(builder))]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    // ...

    // Build the fields that will be placed in XBuilder
    // Each fields do not wrap in Option, everything else does
    let builder_fields = fields.iter().map(|field| {
        let FieldData { id, ty, nested_ty, each_id, .. } = field;

        if each_id.is_some() || nested_ty.is_some() && nested_ty.as_ref().unwrap().0 == "Option" {
            quote! { #id: #ty }
        } else {
            quote! { #id: std::option::Option<#ty> }
        }
    });

    // Build the default values for each XBuilder
    // Each fields should be special cased, everything else is None
    let builder_defaults = fields.iter().map(|field| {
        let FieldData { id, nested_ty, each_id, .. } = field;

        if each_id.is_some() {
            if nested_ty.is_some() && nested_ty.as_ref().unwrap().0 == "Vec" {
                quote! { #id: std::vec::Vec::new() }
            } else {
                unimplemented!("The only each fields currently supported must be Vec")
            }
        } else {
            quote! { #id: std::option::Option::None }
        }
    });

    // Generate setters for each field in XBuilder
    // Full setters set the entire value at once
    // Each setters append one value at a time to a field
    let setters = fields.iter().map(|field| {
        let FieldData { id, ty, nested_ty, each_id } = field;
        let mut setters = Vec::new();

        // We have only full setter (no each setter)
        if each_id.is_none() {
            setters.push(
                if nested_ty.is_some() && nested_ty.as_ref().unwrap().0 == "Option" {
                    // It is for an optional value
                    let inner_ty = nested_ty.as_ref().unwrap().1.clone();
                    quote! {
                        pub fn #id(&mut self, value: #inner_ty) -> &mut Self {
                            self.#id = std::option::Option::Some(value);
                            self
                        }
                    }
                } else {
                    // Non-optional value, need to Some it
                    quote! {
                        pub fn #id(&mut self, value: #ty) -> &mut Self {
                            self.#id = std::option::Option::Some(value);
                            self
                        }
                    }
                }
            );
        }

        // We have a full setter and an each setter (the names don't collide)
        if each_id.is_some() && id != each_id.as_ref().unwrap() {
            setters.push(quote! {
                pub fn #id(&mut self, value: #ty) -> &mut Self {
                    self.#id = value;
                    self
                }
            });
        }

        // We have an each setter
        if each_id.is_some() && nested_ty.is_some() {
            if nested_ty.as_ref().unwrap().0 == "Vec" {
                let inner_ty = nested_ty.as_ref().unwrap().1.clone();
                setters.push(quote! {
                    pub fn #each_id(&mut self, value: #inner_ty) -> &mut Self {
                        self.#id.push(value);
                        self
                    }
                });
            } else {
                unimplemented!("Builder each setters only support Vec fields for now")
            }
        }
         
        // Output one or both, depending on if they're set
        quote! { 
            #(#setters)*
        }
    });

    // Any fields that are required should be set to something
    let build_checkers = fields.iter().map(|field| {
        let FieldData { id, nested_ty, .. } = field;
        let err = format!("{id} was not set");
        
        if nested_ty.is_none() || nested_ty.as_ref().unwrap().0 == "Optional" {
            quote! {
                if self.#id.is_none() {
                    return std::result::Result::Err(#err.into());
                }
            }
        } else {
            quote! {}
        }
    });

    // Unpack the values from XBuilder in order to make an X
    let build_fields = fields.iter().map(|field| {
        let FieldData { id, nested_ty, each_id, ..} = field;

        if each_id.is_some() || nested_ty.is_some() && nested_ty.as_ref().unwrap().0 == "Option" {
            quote! {
               #id: self.#id.clone()
            }
        } else {
            quote! {
               #id: self.#id.clone().unwrap()
            }
        }
    });

    // 🎵 All together now 🎵
    let output = quote! {
        pub struct #builder_ident {
            #(#builder_fields),*
        }

        impl #builder_ident {
            #(#setters)*

            pub fn build(&mut self) -> std::result::Result<#ident, std::boxed::Box<dyn std::error::Error>> {
                #(#build_checkers);*

                std::result::Result::Ok(#ident {
                    #(#build_fields),*
                })
            }
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
I'm not 100% sure that is actually cleaner... but I think I like it. 

So what does that actually expand to?

```rust
// $ cargo expand
// ...

pub struct Command {
    executable: String,
    #[builder(each = "arg")]
    args: Vec<String>,
    #[builder(each = "env")]
    env: Vec<String>,
    current_dir: Option<String>,
}
pub struct CommandBuilder {
    executable: std::option::Option<String>,
    args: Vec<String>,
    env: Vec<String>,
    current_dir: Option<String>,
}
impl CommandBuilder {
    pub fn executable(&mut self, value: String) -> &mut Self {
        self.executable = std::option::Option::Some(value);
        self
    }
    pub fn args(&mut self, value: Vec<String>) -> &mut Self {
        self.args = value;
        self
    }
    pub fn arg(&mut self, value: String) -> &mut Self {
        self.args.push(value);
        self
    }
    pub fn env(&mut self, value: String) -> &mut Self {
        self.env.push(value);
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
        std::result::Result::Ok(Command {
            executable: self.executable.clone().unwrap(),
            args: self.args.clone(),
            env: self.env.clone(),
            current_dir: self.current_dir.clone(),
        })
    }
}
impl Command {
    pub fn builder() -> CommandBuilder {
        CommandBuilder {
            executable: std::option::Option::None,
            args: std::vec::Vec::new(),
            env: std::vec::Vec::new(),
            current_dir: std::option::Option::None,
        }
    }
}
fn main() {
    let command = Command::builder()
        .executable("cargo".to_owned())
        .arg("build".to_owned())
        .arg("--release".to_owned())
        .build()
        .unwrap();
    match (&command.executable, &"cargo") {
        (left_val, right_val) => {
            if !(*left_val == *right_val) {
                let kind = ::core::panicking::AssertKind::Eq;
                ::core::panicking::assert_failed(
                    kind,
                    &*left_val,
                    &*right_val,
                    ::core::option::Option::None,
                );
            }
        }
    };
    match (
        &command.args,
        &<[_]>::into_vec(#[rustc_box] ::alloc::boxed::Box::new(["build", "--release"])),
    ) {
        (left_val, right_val) => {
            if !(*left_val == *right_val) {
                let kind = ::core::panicking::AssertKind::Eq;
                ::core::panicking::assert_failed(
                    kind,
                    &*left_val,
                    &*right_val,
                    ::core::option::Option::None,
                );
            }
        }
    };
}
```

You know? That's not bad. 

Tests? 

```bash
$ cargo test

...
test tests/01-parse.rs ... ok
test tests/02-create-builder.rs ... ok
test tests/03-call-setters.rs ... ok
test tests/04-call-build.rs ... ok
test tests/05-method-chaining.rs ... ok
test tests/06-optional-field.rs ... ok
test tests/07-repeated-field.rs ... ok
...
```

Nice. 

## 8. Unrecognized attributes

Part 8. Oh part 8. In a nutshell, if we do something silly like using the attribute as `builder(eac = "arg")`, we should generate better error messages like this:

```text
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
error: expected `builder(each = "...")`
  --> tests/08-unrecognized-attribute.rs:22:7
   |
22 |     #[builder(eac = "arg")]
   |       ^^^^^^^^^^^^^^^^^^^^
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
```

Currently we're generating this:

```text
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
error: proc-macro derive panicked
  --> tests/08-unrecognized-attribute.rs:19:10
   |
19 | #[derive(Builder)]
   |          ^^^^^^^
   |
   = help: message: called `Result::unwrap()` on an `Err` value: Error("Unknown attribute form")
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
```

So first pass, let's collect errors as we go:

```rust

#[proc_macro_derive(Builder, attributes(builder))]
pub fn derive(input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let ast = parse_macro_input!(input as syn::DeriveInput);
    let ident = ast.ident.clone();
    let builder_ident = format_ident!("{ident}Builder");
    let mut errors = Vec::new();
    
    // ...

    // Parse the fields information we actually care about
    let fields = fields.iter().map(|field| {
        // ...
    
        let each_id = match try_parse_builder_each(&field) {
            std::result::Result::Ok(std::option::Option::Some(id)) => std::option::Option::Some(format_ident!("{}", id)),
            std::result::Result::Ok(std::option::Option::None) => std::option::Option::None,
            std::result::Result::Err(err) => {
                errors.push(err.to_compile_error());
                std::option::Option::None
            },
        };

        // ...
    }).collect::<Vec<_>>();

    // ...

    // 🎵 All together now 🎵
    let output = quote! {
        // ...

        #(#errors)*
    };

    proc_macro::TokenStream::from(output)
}
```

Basically, outside of my parsing, keep track of any compiler errors that I get and then at the end, add them to my stream. What's that output? 

```text
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
error: Unknown attribute form
  --> tests/08-unrecognized-attribute.rs:22:5
   |
22 | /     #[builder(eac = "arg")]
23 | |     args: Vec<String>,
   | |_____________________^
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
```

That's closer!

Update `try_parse_builder_each` to:

```rust
fn try_parse_builder_each(field: &syn::Field) -> std::result::Result<std::option::Option<String>, syn::Error> {
    for attr in field.attrs.iter() {
        let err = std::result::Result::Err(syn::Error::new(field.span(), "expected `builder(each = \"...\")`"));

        // ...
    }
    
    // ...
}
```

And one step closer:

```text
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
error: expected `builder(each = "...")`
  --> tests/08-unrecognized-attribute.rs:22:5
   |
22 | /     #[builder(eac = "arg")]
23 | |     args: Vec<String>,
   | |_____________________^
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
```

We just need to get the right span on it. 

```rust
fn try_parse_builder_each(field: &syn::Field) -> std::result::Result<std::option::Option<String>, syn::Error> {
    for attr in field.attrs.iter() {
        let err = std::result::Result::Err(syn::Error::new(attr.span(), "expected `builder(each = \"...\")`"));

        // ...
    }
    
    // ...
}
```

Gives us:

```text
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
error: expected `builder(each = "...")`
  --> tests/08-unrecognized-attribute.rs:22:5
   |
22 |     #[builder(eac = "arg")]
   |     ^^^^^^^^^^^^^^^^^^^^^^^
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
```

Ugh. 

In the end, the actual span that the test case wants is the one that's the `MetaList` variable in the first match. So I have to capture that, which means that I have to sprinkle in some `ref` to make things happy:

```rust
fn try_parse_builder_each(field: &syn::Field) -> std::result::Result<std::option::Option<String>, syn::Error> {
    for attr in field.attrs.iter() {
        let err = |span| std::result::Result::Err(syn::Error::new(span, "expected `builder(each = \"...\")`"));

        let (attr_span, nested) = match attr.parse_meta() {
            Ok(syn::Meta::List(
                ref metalist @ syn::MetaList { 
                    path: syn::Path {
                        ref segments,
                        ..
                    },
                    ref nested,
                    .. 
                }
            )) if segments.len() == 1 && segments[0].ident == "builder" && nested.len() == 1
            => (metalist.span(), nested[0].clone()),
            Ok(thing) => return err(thing.span()),
            Err(e) => return std::result::Result::Err(e),
        };

        // TODO: check the eq_token?
        let value = match nested {
            syn::NestedMeta::Meta (
                syn::Meta::NameValue (
                    syn::MetaNameValue {
                        path: syn::Path {
                            segments,
                            ..
                        },
                        eq_token: _,
                        lit: syn::Lit::Str(str)
                    } 

                )
            ) if segments.len() == 1 && segments[0].ident == "each"
            => str.value(),
            _ => return err(attr_span),
        };

        return std::result::Result::Ok(std::option::Option::Some(value));
    }

    // If we make it out of the loop, no (matching) attributes; response is Ok but None
    std::result::Result::Ok(std::option::Option::None)
}
```

But now that's all in place:


```bash
$ cargo test

...
test tests/01-parse.rs [should pass] ... ok
test tests/02-create-builder.rs [should pass] ... ok
test tests/03-call-setters.rs [should pass] ... ok
test tests/04-call-build.rs [should pass] ... ok
test tests/05-method-chaining.rs [should pass] ... ok
test tests/06-optional-field.rs [should pass] ... ok
test tests/07-repeated-field.rs [should pass] ... ok
test tests/08-unrecognized-attribute.rs [should fail to compile] ... ok
...
```

Nice. 

## 9. Redefined prelude types

Okay, so the last one *should* be a freebie if I've been doing this right. Remember how I said people can do squirrely things with types and you should fully qualify them in macros? Well:

```rust
use derive_builder::Builder;

type Option = ();
type Some = ();
type None = ();
type Result = ();
type Box = ();

#[derive(Builder)]
pub struct Command {
    executable: String,
}

fn main() {}
```

Have I been?

```bash
$ cargo test

...
test tests/01-parse.rs [should pass] ... ok
test tests/02-create-builder.rs [should pass] ... ok
test tests/03-call-setters.rs [should pass] ... ok
test tests/04-call-build.rs [should pass] ... ok
test tests/05-method-chaining.rs [should pass] ... ok
test tests/06-optional-field.rs [should pass] ... ok
test tests/07-repeated-field.rs [should pass] ... ok
test tests/08-unrecognized-attribute.rs [should fail to compile] ... ok
test tests/09-redefined-prelude-types.rs [should pass] ... ok
...
```

You bet!

## What's next?

And that's that. I've finished the first of the proc-macro workshop. That's pretty cool, but there's still so much to do! 

I think at this point, I want to do them in order, so I'll probably do `derive(CustomDebug)` next. Should be fun.

Onward!
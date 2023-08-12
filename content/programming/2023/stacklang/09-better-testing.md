---
title: "StackLang Part IX: Better Testing"
date: '2023-08-12 00:00:00'
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
Two posts in two days? Madness!

{{< taxonomy-list "series" "StackLang" >}}

But really, it got a bit late yesterday so I figured I'd split this into two different posts. 

In this post:

{{<toc>}}

Full source code for StackLang: [github:jpverkamp/stacklang](https://github.com/jpverkamp/stacklang/)

## Generating tests

## Version 1: A simple function

In a nutshell, I have a directory of [examples](https://github.com/jpverkamp/stacklang/tree/main/examples) with what should be consistent output. It would be nice if I could set up tests so that when I changed something, I could just `cargo test` and verify that the output of the examples hasn't changed. Even better, I could also check the `vm` and `compile --run` (and any possible other versions) output and make sure that they're the same!

This actually turned out much easier than I expected:

```rust
// example_tests.rs
#[cfg(test)]
mod test {
    use std::process::Command;
    use std::str;

    fn test(path: &str, target: &str) {
        let vm_output = Command::new("cargo")
            .arg("run")
            .arg("--")
            .arg("vm")
            .arg(path)
            .output()
            .expect("failed to run vm");

        assert_eq!(vm_output.status.success(), true, "vm exit code");
        assert_eq!(
            str::from_utf8(&vm_output.stdout).unwrap(),
            target,
            "vm output"
        );

        let compile_output = Command::new("cargo")
            .arg("run")
            .arg("--")
            .arg("compile")
            .arg(path)
            .arg("--output")
            .arg(format!("output/test-{}.c", path.replace("/", "-")))
            .arg("--run")
            .output()
            .expect("failed to execute process");

        assert_eq!(
            compile_output.status.success(),
            true,
            "c compiler exit code"
        );
        assert_eq!(
            str::from_utf8(&compile_output.stdout).unwrap(),
            target,
            "c compiler output"
        );
    }


    #[test]
    fn test_add2() {
        test("examples/add2.stack", "12\n");
    }

    #[test]
    fn test_basic_math() {
        test("examples/basic-math.stack", "98\n");
    }
    
    ...
}
```

That's really it. I made a helper function `test` that takes the path to the `example/*.stack` file and the expected output. It then uses `Command` to run the `vm` version, check it's status and output and then `compile` with its status and output. If any of these fail, fail the test. Otherwise, all good. 

I think I'd probably rather having a test for vm and one for compile... so let's do that!

### Version 2: Macros!

To split the tests, we need a macro to generate two functions:

```rust
macro_rules! make_tests {
    ($name:ident: $path:expr => $target:expr) => {
        paste! {
            #[test]
            fn [< test_vm_ $name >]() {
                let vm_output = Command::new("cargo")
                    .arg("run")
                    .arg("--")
                    .arg("vm")
                    .arg($path)
                    .output()
                    .expect("failed to run vm");

                assert_eq!(vm_output.status.success(), true, "vm exit code");
                assert_eq!(
                    str::from_utf8(&vm_output.stdout).unwrap(),
                    $target,
                    "vm output"
                );
            }

            #[test]
            fn [< test_compile_ $name >]() {
                let compile_output = Command::new("cargo")
                    .arg("run")
                    .arg("--")
                    .arg("compile")
                    .arg($path)
                    .arg("--output")
                    .arg(format!("output/test-{}.c", $path.replace("/", "-")))
                    .arg("--run")
                    .output()
                    .expect("failed to execute process");

                assert_eq!(
                    compile_output.status.success(),
                    true,
                    "c compiler exit code"
                );
                assert_eq!(
                    str::from_utf8(&compile_output.stdout).unwrap(),
                    $target,
                    "c compiler output"
                );
            }
        }
    };
}
```

That's actually easier than I feared. One gotcha is that Rust `macro_rules!` macros can't (by default) make new identifiers. And we do need to do that, since the functions have to have different names. [paste](https://docs.rs/paste/latest/paste/) to the rescue! (that sounds silly). Basically, add `[< ... >]` syntax that can build new identifiers out of old ones + syntax objects. Pretty straight forward that. 

And to use it:

```rust
make_tests!(add2: "examples/add2.stack" => "12\n");
make_tests!(basic_math: "examples/basic-math.stack" => "98\n");
make_tests!(named_variables: "examples/double-named.stack" => "20\n");
make_tests!(name_2: "examples/name-two.stack" => "3\n");

...
```

I really like that! :smile: And when I add another backend? Just add to the macro and tests for FREE! 

## Test output

Using version 2, so we have `test_vm_*` and `test_compile_*` separate: 

```bash
$  cargo test

   Compiling stacklang v0.1.0 (/Users/jp/Projects/stacklang)
    Finished test [unoptimized + debuginfo] target(s) in 0.31s
     Running unittests src/main.rs (target/debug/deps/stacklang-d83b4a09c025c08b)

running 59 tests
test example_tests::test::test_compile_loop_apply ... FAILED
test example_tests::test::test_compile_arity_in_2 ... ok
test example_tests::test::test_compile_loop ... ok
test example_tests::test::test_compile_add2 ... ok
test example_tests::test::test_compile_if ... ok
test example_tests::test::test_compile_loop_list ... FAILED
test example_tests::test::test_compile_arity_out_2 ... ok
test example_tests::test::test_compile_list ... ok
test example_tests::test::test_compile_basic_math ... ok
test example_tests::test::test_compile_lists_of_lists ... ok
test example_tests::test::test_compile_arity_2_2 ... ok
test example_tests::test::test_compile_cond_recursion ... ok
test example_tests::test::test_vm_basic_math ... ok
test example_tests::test::test_vm_arity_out_2 ... ok
test example_tests::test::test_vm_arity_in_2 ... ok
test example_tests::test::test_vm_if ... ok
test example_tests::test::test_vm_add2 ... ok
test example_tests::test::test_vm_arity_2_2 ... ok
test example_tests::test::test_vm_cond_recursion ... ok
test example_tests::test::test_compile_name_2 ... ok
test example_tests::test::test_compile_named_variables ... ok
test example_tests::test::test_compile_recursion ... ok
test example_tests::test::test_compile_mutual_recursion ... ok
test lexer::test::test_binary ... ok
test lexer::test::test_brackets ... ok
test lexer::test::test_float_scientific ... ok
test lexer::test::test_floats ... ok
test lexer::test::test_hex ... ok
test lexer::test::test_identifiers ... ok
test lexer::test::test_integers ... ok
test lexer::test::test_negative_integers ... ok
test lexer::test::test_prefixed ... ok
test lexer::test::test_rationals ... ok
test lexer::test::test_strings ... ok
test lexer::test::test_symbolic ... ok
test parser::test::test_assignment_bang ... ok
test parser::test::test_boolean_literal ... ok
test parser::test::test_dotted_identifier ... ok
test parser::test::test_factorial ... ok
test parser::test::test_float ... ok
test parser::test::test_identifier ... ok
test parser::test::test_integer ... ok
test parser::test::test_list_naming ... ok
test parser::test::test_naming ... ok
test parser::test::test_simple_addition ... ok
test parser::test::test_simple_block ... ok
test parser::test::test_string_literal ... ok
test parser::test::test_symbolic_identifier ... ok
test example_tests::test::test_compile_recursive_helper ... ok
test example_tests::test::test_vm_recursive_helper ... ok
test example_tests::test::test_vm_recursion ... ok
test example_tests::test::test_vm_loop ... ok
test example_tests::test::test_vm_list ... ok
test example_tests::test::test_vm_named_variables ... ok
test example_tests::test::test_vm_lists_of_lists ... ok
test example_tests::test::test_vm_loop_apply ... ok
test example_tests::test::test_vm_name_2 ... ok
test example_tests::test::test_vm_loop_list ... ok
test example_tests::test::test_vm_mutual_recursion ... ok

failures:

---- example_tests::test::test_compile_loop_apply stdout ----
thread 'example_tests::test::test_compile_loop_apply' panicked at 'assertion failed: `(left == right)`
  left: `false`,
 right: `true`: c compiler exit code', src/example_tests.rs:73:5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

---- example_tests::test::test_compile_loop_list stdout ----
thread 'example_tests::test::test_compile_loop_list' panicked at 'assertion failed: `(left == right)`
  left: `false`,
 right: `true`: c compiler exit code', src/example_tests.rs:85:5


failures:
    example_tests::test::test_compile_loop_apply
    example_tests::test::test_compile_loop_list

test result: FAILED. 57 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.74s

error: test failed, to rerun pass `--bin stacklang`
```

When I first started writing these, I had a couple more failures, mostly because I hadn't actually implemented {{<crosslink text="stacks" title="StackLang Part VIII: Compiler Stacks">}} yet (yes, these posts are out of order). But now, I'm only missing loop lists / apply in the compiler version. Everything else is good to go. 

And now, whenever I do any major refactoring... the tests should show me what I mess up. Pretty cool. 
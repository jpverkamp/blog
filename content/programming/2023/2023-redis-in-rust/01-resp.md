---
title: "Cloning Redis in Rust: RESP [Part 1]"
date: 2023-01-31
programming/languages:
- Rust
programming/topics:
- Redis
- Parsing
- Data Structures
series:
- Cloning Redis in Rust
---
Recently, I read through [[Build Your Own Redis with C/C++]](). C/C++ are ugly, so let's run through it in Rust!

My goal: implement some large subset of [Redis](https://redis.io/) (both server and client) in Rust. For any features I implement, it should be compatible with Redis off the shelf. I should be able to use their client with my server and their server with my client and it should just work. 

No idea if this is going to work out, but it sounds like an interesting problem!

First task: [the REdis Serialization Protocol (RESP)](https://redis.io/docs/reference/protocol-spec/).

<!--more-->

{{<toc>}}

## The struct (and errors)

First step, let's make a basic struct for what we'll be storing. There are 4 basic data types in the Redis protocol:

* Strings 
* Errors (really just strings under the hood)
* Integers (signed, 64 bit)
* Arrays (contain the other types, can be mixed and/or nested)

On top of that, we actually have two different null types: `NullString` and `NullArray`. For historical reasons, Redis can return either of these for different functions, so we'll have to deal with them. In a nutshell, they are represented by a string/array with a negative length. 

```rust
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub enum RedisType {
    NullString,
    NullArray,
    String { value: String },
    Error { value: String },
    Integer { value: i64 },
    Array { value: Vec<RedisType> },
}
```

Next up, we have a few different errors that can come up. Since I'm experimenting with `Result` types, let's make an `Error` type to go with it. 

```rust
#[derive(Copy, Clone, Debug)]
pub enum RedisTypeParseError {
    MissingPrefix,
    InvalidPrefix,
    InvalidSuffix,
    InvalidArrayLength,
    LeftOverData,
}
```

## `From` for a few basic types

Okay, now that we have that, we can just directly implement `From` for a few basic types, which will give us `Into` for 'free'. Basically, if a type is already a string, i64, or array of the same, we can coerce it. I'll add `Option<String>` for those `NullString` types (to distinguish between `""` and `None`). Not sure if it's necessary. 

```rust
impl From<Option<String>> for RedisType {
    fn from(value: Option<String>) -> Self {
        match value {
            Some(value) => RedisType::String {
                value: value.to_owned(),
            },
            None => RedisType::NullString,
        }
    }
}

impl From<String> for RedisType {
    fn from(value: String) -> Self {
        RedisType::String {
            value: value.to_owned(),
        }
    }
}

impl From<i64> for RedisType {
    fn from(value: i64) -> Self {
        RedisType::Integer { value }
    }
}

impl From<Vec<RedisType>> for RedisType {
    fn from(value: Vec<RedisType>) -> Self {
        RedisType::Array { value }
    }
}
```

## `Display`: Turning structs into strings

Now we're getting into the meat of the algorithm. Basically, each of the `Redis` types starts with a single key character and ends with `\r\n`:

* `+` - basic (non-binary) strings, cannot contain newlines or binary data
* `-` - errors, no newlines, the same as `+`
* `:` - integers, represented as the digits in text (not directly as binary)

Then we have the two 'length' types:

* `$` - represents a bulk string / binary data; the first line has the length of remaining data, then the data itself; example: `$11\r\nHello world\r\n` represents the string `Hello world` as a bulk string--"11" characters, a `\r\n`, then those 11 characters, then another `\r\n` (unnecessary, since we know the length; but there anyways)
* `*` - an array, encoded the same way; so the list `[1, 2, 3]` would be `*3\r\n:1\r\n:2\r\n:3\r\n`--array of 3 then each of the values

There are also (as I mentioned) the two special cases:

* `$-1\r\n` is a null bulk string (not an empty bulk string, that is `$0\r\n\r\n`--note the 'extra' `\r\n` even with no actual items, or an empty simple string would be `+\r\n`)
* `*-1\r\n` is a null bulk array (empty array: `*0\r\n\r\n`)

And that's it. So if we want to print those things out:

```rust
impl Display for RedisType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let crlf = "\r\n";

        match self {
            RedisType::NullString => write!(f, "$-1{}", crlf),
            RedisType::NullArray => write!(f, "*-1{}", crlf),
            RedisType::String { value } => {
                if value.len() == 0 {
                    // Empty strings
                    write!(f, "$0{}{}", crlf, crlf)
                } else if value
                    .chars()
                    .any(|c| c.is_control() || c == '\r' || c == '\n')
                {
                    // Bulk strings
                    // TODO: Are there any other interesting cases?
                    write!(f, "${}{}{}{}", value.len(), crlf, value, crlf)
                } else {
                    // Simple strings
                    write!(f, "+{}{}", value, crlf)
                }
            }
            RedisType::Error { value } => write!(f, "-{}{}", value, crlf),
            RedisType::Integer { value } => write!(f, ":{}{}", value, crlf),
            RedisType::Array { value } => {
                write!(f, "*{}{}", value.len(), crlf)?;

                for el in value {
                    write!(f, "{}", el)?;
                }

                Ok(())
            }
        }
    }
}
```

I think it's pretty straight forward. It's pretty cool that `Display` is the same as `to_string`. Makes sense really. 

## `FromStr`: Turning strings into structs

Okay, now the other way around. We want to turn strings into structs. To do that for more of the types is pretty easy, just read a line (until `\r\n`). But unfortunately, arrays really mess with that. 

To make those work, we need a very simple recursive descent parser. Basically, the `parse` inner function below that takes a string, parses one object and then returns what's left of the string + the resulting type. So when parsing an array, you can call this function and once you've parsed enough, continue on where you where. 

```rust
impl FromStr for RedisType {
    type Err = RedisTypeParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        fn parse(s: &str) -> Result<(&str, RedisType), RedisTypeParseError> {
            let bytes = s.as_bytes();

            if s.len() == 0 {
                return Err(RedisTypeParseError::MissingPrefix);
            }

            if !s.contains("\r\n") {
                return Err(RedisTypeParseError::InvalidSuffix);
            }

            let crlf = s.find("\r\n").unwrap();
            let payload = &s[1..crlf];
            let mut rest = &s[crlf + 2..];

            match bytes[0] as char {
                '+' => Ok((
                    rest,
                    RedisType::String {
                        value: String::from(payload),
                    },
                )),
                '-' => Ok((
                    rest,
                    RedisType::Error {
                        value: String::from(payload),
                    },
                )),
                // TODO: Better error handling for failing to parse
                ':' => Ok((
                    rest,
                    RedisType::Integer {
                        value: String::from(payload).parse::<i64>().unwrap(),
                    },
                )), 
                '*' => {
                    // TODO: Validate that array length parsed correctly
                    let len = String::from(payload).parse::<i64>().unwrap(); 

                    // Special case: bulk string with -1 length is actually a 'null' array
                    // This is historical
                    if len < 0 {
                        Ok((rest, RedisType::NullArray))
                    } else {
                        let mut value = Vec::new();

                        for _ in 0..len {
                            let (next, el) = parse(rest)?;
                            value.push(el);
                            rest = next;
                        }

                        Ok((rest, RedisType::Array { value }))
                    }
                }
                '$' => {
                    let len = String::from(payload).parse::<i64>().unwrap(); // TODO: Validate

                    // Special case: bulk string with -1 length is actually a 'null' value
                    // I'm just treating any negative as this case
                    if len < 0 {
                        Ok((rest, RedisType::NullString))
                    } else {
                        let len = len as usize;
                        let value = String::from(&rest[0..len]);
                        rest = &rest[len + 2..];

                        Ok((rest, RedisType::String { value }))
                    }
                }
                _ => Err(RedisTypeParseError::InvalidPrefix),
            }
        }

        match parse(s) {
            Ok((rest, result)) if rest.len() == 0 => Ok(result),
            Ok(_) => Err(RedisTypeParseError::LeftOverData),
            Err(e) => Err(e),
        }
    }
}
```

Pretty cool I think. And it even handles extra data pretty well. 

I don't think I'm using errors quite right... but for the moment, it does work. 

## Tests all around

So I started writing some tests. As one does. 

And I realized that they were *super* repetitive. 

And how do fix repetitive things in programming? 

MACROS!

```rust
macro_rules! make_tests {
    ($name:tt, $string:expr, $redis:expr) => {
        paste::item! {
            #[test]
            fn [< test_ $name _from_str >]() {
                assert_eq!(RedisType::from_str($string).unwrap(), $redis);
            }

            #[test]
            fn [< test_ $name _to_string >]() {
                assert_eq!($redis.to_string(), $string);
            }

            #[test]
            fn [< test_ $name _inverse_to_from  >]() {
                assert_eq!(RedisType::from_str(&$redis.to_string()).unwrap(), $redis);
            }

            #[test]
            fn [< test_ $name _inverse_from_to >]() {
                assert_eq!(RedisType::from_str($string).unwrap().to_string(), $string);
            }
        }
    };
}
```

This uses the [`paste` crate](https://docs.rs/paste/1.0.11/paste/) to build identifiers for each of four test functions that we'll output:

* Using `from_str` to parse a string into a `RedisType`
* Using `to_string` / `Display` to go back to a string
* Round tripping with `to_string` first
* Round tripping the other way

I absolutely did not need those last two, but :shrug: 

Actual test cases:

```rust
make_tests!(null, "$-1\r\n", RedisType::NullString);
make_tests!(null_array, "*-1\r\n", RedisType::NullArray);

make_tests!(
    simple_string,
    "+Hello world\r\n",
    RedisType::String {
        value: "Hello world".to_owned()
    }
);

make_tests!(
    empty_string,
    "$0\r\n\r\n",
    RedisType::String {
        value: "".to_owned()
    }
);

make_tests!(
    bulk_string,
    "$5\r\nYo\0\r\n\r\n",
    RedisType::String {
        value: "Yo\0\r\n".to_owned()
    }
);

make_tests!(
    err,
    "-ERR Goodbye world\r\n",
    RedisType::Error {
        value: "ERR Goodbye world".to_owned()
    }
);

make_tests!(
    positive_integer,
    ":42\r\n",
    RedisType::Integer { value: 42 }
);

make_tests!(
    negative_integer,
    ":-1337\r\n",
    RedisType::Integer { value: -1337 }
);

make_tests!(
    array,
    "*3\r\n+Hello world\r\n:42\r\n-ERR Goodbye world\r\n",
    RedisType::Array {
        value: vec![
            RedisType::String {
                value: "Hello world".to_owned()
            },
            RedisType::Integer { value: 42 },
            RedisType::Error {
                value: "ERR Goodbye world".to_owned()
            },
        ]
    }
);

make_tests!(
    null_in_array,
    "*3\r\n$3\r\nYo\0\r\n$-1\r\n-ERR Goodbye world\r\n",
    RedisType::Array {
        value: vec![
            RedisType::String {
                value: "Yo\0".to_owned()
            },
            RedisType::NullString,
            RedisType::Error {
                value: "ERR Goodbye world".to_owned()
            },
        ]
    }
);

make_tests!(
    nested_array,
    "*4\r\n+Hello world\r\n:42\r\n-ERR Goodbye world\r\n*3\r\n+Hello world\r\n:42\r\n-ERR Goodbye world\r\n",
    RedisType::Array {
        value: vec![
            RedisType::String {
                value: "Hello world".to_owned()
            },
            RedisType::Integer { value: 42 },
            RedisType::Error {
                value: "ERR Goodbye world".to_owned()
            },
            RedisType::Array {
                value: vec![
                    RedisType::String {
                        value: "Hello world".to_owned()
                    },
                    RedisType::Integer { value: 42 },
                    RedisType::Error {
                        value: "ERR Goodbye world".to_owned()
                    },
                ]
            }
        ]
    }
);
```

I think that's a pretty good list. We test each of the main types, both kinds of nulls, positive and negative integers, and both un-nested and nested arrays. I'm sure I'm missing some cases, but it's pretty good for now. 

```bash
$ cargo test

    Finished test [unoptimized + debuginfo] target(s) in 0.08s
     Running unittests src/lib.rs (target/debug/deps/redis_rs-f3cfbacec8e60619)

running 44 tests
test tests::test_bulk_string_to_string ... ok
test tests::test_array_to_string ... ok
test tests::test_array_inverse_to_from ... ok
test tests::test_bulk_string_from_str ... ok
test tests::test_array_from_str ... ok
test tests::test_empty_string_from_str ... ok
test tests::test_bulk_string_inverse_from_to ... ok
test tests::test_bulk_string_inverse_to_from ... ok
test tests::test_array_inverse_from_to ... ok
test tests::test_empty_string_inverse_from_to ... ok
test tests::test_empty_string_inverse_to_from ... ok
test tests::test_empty_string_to_string ... ok
test tests::test_err_from_str ... ok
test tests::test_err_inverse_from_to ... ok
test tests::test_err_inverse_to_from ... ok
test tests::test_err_to_string ... ok
test tests::test_negative_integer_from_str ... ok
test tests::test_negative_integer_inverse_from_to ... ok
test tests::test_negative_integer_inverse_to_from ... ok
test tests::test_negative_integer_to_string ... ok
test tests::test_nested_array_from_str ... ok
test tests::test_nested_array_inverse_from_to ... ok
test tests::test_nested_array_inverse_to_from ... ok
test tests::test_null_array_from_str ... ok
test tests::test_null_array_inverse_from_to ... ok
test tests::test_null_array_inverse_to_from ... ok
test tests::test_null_array_to_string ... ok
test tests::test_null_from_str ... ok
test tests::test_null_in_array_from_str ... ok
test tests::test_nested_array_to_string ... ok
test tests::test_null_in_array_inverse_from_to ... ok
test tests::test_null_in_array_inverse_to_from ... ok
test tests::test_null_in_array_to_string ... ok
test tests::test_null_inverse_to_from ... ok
test tests::test_null_inverse_from_to ... ok
test tests::test_positive_integer_from_str ... ok
test tests::test_positive_integer_inverse_from_to ... ok
test tests::test_null_to_string ... ok
test tests::test_positive_integer_inverse_to_from ... ok
test tests::test_positive_integer_to_string ... ok
test tests::test_simple_string_from_str ... ok
test tests::test_simple_string_inverse_from_to ... ok
test tests::test_simple_string_inverse_to_from ... ok
test tests::test_simple_string_to_string ... ok

test result: ok. 44 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/client.rs (target/debug/deps/client-a8942fb79fdb150b)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/server.rs (target/debug/deps/server-0d5859cce044e451)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests redis-rs

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Yeah, okay. That's a lot

## What's next?

Well, that handles how clients and servers talk to one another... so I think next we should write a very simple server (we can talk to it with {{<wikipedia "telnet">}} / {{<wikipedia "netcat">}}). A simple hash map for just keys/values and maybe number of keys should be good.

Onward!
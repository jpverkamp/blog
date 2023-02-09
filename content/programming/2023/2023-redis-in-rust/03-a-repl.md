---
title: "Redis in Rust: A REPL Client [Part 3]"
date: 2023-02-09 01:00:00
programming/languages:
- Rust
programming/topics:
- Redis
- REPL
- Client
- Parsing
- Networking
- TCP
series:
- Cloning Redis in Rust
---
Okay, we've got a server and we can ping it. Let's actually make a simple client, so I don't have to do funny things with echo any more. Specifically, let's make a {{<wikipedia "REPL">}}!

{{<toc>}}

<!--more-->

## A REPL

In a nutshell:

### The code

```rust

use std::io::{self, BufRead, stdout, Write};
use std::str::FromStr;

use redis_rs::RedisType;

use tokio::net::{TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use tracing_subscriber;

#[tokio::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();

    let addr = "0.0.0.0:6379";
    let mut stream = TcpStream::connect(addr).await?;
    tracing::info!("Connecting to {addr}");

    let stdin = io::stdin();
    let mut stdin_iterator = stdin.lock().lines();
    let mut buf = [0; 1024];

    // To match the protocol, always encode strings as bulk string even when it's not necessary
    // TODO: Do this better :)
    unsafe {
        redis_rs::ALWAYS_USE_BULK_STRING = true;
    }
    
    loop {
        print!("redis-rs> ");
        stdout().flush()?;

        match stdin_iterator.next() {
            Some(Ok(line)) => {
                tracing::debug!("Input read: {line}");

                // Parse the input into a collection of bulk strings
                let mut values = Vec::new();
                for arg in line.split_ascii_whitespace().into_iter() {
                    values.push(RedisType::String { value: String::from(arg) });
                }

                // Bundle into an array
                let array = RedisType::from(values);
                tracing::debug!("Input parsed: {array}");

                // Send them to the server
                stream.write_all(array.to_string().as_bytes()).await?;

                // Wait for an read a response back from the server
                let bytes_read = stream.read(&mut buf).await?;
                if bytes_read == 0 {
                    break;
                }
                tracing::debug!("Received {bytes_read} bytes from server");

                // Parse the response from the server
                let string = String::from_utf8_lossy(&buf[0..bytes_read]);
                let data = match RedisType::from_str(&string) {
                    Ok(data) => data,
                    Err(err) => {
                        tracing::warn!("Error parsing response from server: {err:?}");
                        continue;
                    },
                };
                
                // Print out the response from the server
                // TODO: Do something else with this? 
                println!("{data:?}");
            },
            Some(Err(e)) => {
                tracing::warn!("Error reading from stdin: {e:?}");
            },
            None => {
                tracing::info!("Reached end of stdin");
                break;
            }
        }
    }

    Ok(())
}
```

I'm still using `tracing` and `tokio`, but I don't actually need the async code for this. Instead, I'm going to basically:

* `R`ead a new line of input
* `P`arse that input by splitting on whitespace and pushing each into a string
  * This isn't quite correct, I actually want to read off `"this is a test"` as one String. That can be a problem for tomorrow though. 
* `E`valuate the string... by sending it to the server, letting it parse and echo it back, and printing back what we got
* `L`oop back to the beginning!

A REPL as it were. :smile:

### `unsafe`...

The one *really* ugly bit of code I have at the moment (which I will fix!) is 

```rust
// To match the protocol, always encode strings as bulk string even when it's not necessary
// TODO: Do this better :)
unsafe {
    redis_rs::ALWAYS_USE_BULK_STRING = true;
}
```

This matches a quick update in `lib.rs`, specifically in the `impl Display for RedisType`:

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
                } else if unsafe { ALWAYS_USE_BULK_STRING }
                    || (value
                        .chars()
                        .any(|c| c.is_control() || c == '\r' || c == '\n'))
                {
                    // Bulk strings
                    // TODO: Are there any other interesting cases?
                    write!(f, "${}{}{}{}", value.len(), crlf, value, crlf)
                } else {
                    // Simple strings
                    write!(f, "+{}{}", value, crlf)
                }
            }

            ...
        }

        ...
    }
}
```

If `ALWAYS_USE_BULK_STRING` is set, write it in the `$` bulk string format, since that's apparently how the client is expected to talk to the server. If it's not set, use the previous heuristics. 

Why `unsafe`? Because if you modify this 'static' value between two threads *BAD THINGS COULD HAPPEN*. I'm half kidding, but I get why Rust is trying to protect me from this. 

As I said though, that's a problem for another day. 

For now:

### Server

```bash
$ RUST_LOG=debug cargo run --bin server


    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running `target/debug/server`
2023-02-09T06:16:30.000510Z  INFO server: Listening on 0.0.0.0:6379
2023-02-09T06:16:36.348605Z DEBUG server: Accepted connection from 127.0.0.1:57082
2023-02-09T06:16:36.348686Z  INFO server: [127.0.0.1:57082] Accepted connection
2023-02-09T06:16:44.659516Z DEBUG server: [127.0.0.1:57082] Received 38 bytes
2023-02-09T06:16:44.659635Z DEBUG server: [127.0.0.1:57082 Received Array { value: [String { value: "SET" }, String { value: "the_answer" }, String { value: "42" }] }
2023-02-09T06:16:52.037582Z DEBUG server: [127.0.0.1:57082] Received 37 bytes
2023-02-09T06:16:52.037694Z DEBUG server: [127.0.0.1:57082 Received Array { value: [String { value: "SET" }, String { value: "hello" }, String { value: "\"WORLD\"" }] }
2023-02-09T06:16:54.533763Z DEBUG server: [127.0.0.1:57082] Received 24 bytes
2023-02-09T06:16:54.533879Z DEBUG server: [127.0.0.1:57082 Received Array { value: [String { value: "GET" }, String { value: "hello" }] }
2023-02-09T06:16:56.229537Z  INFO server: [127.0.0.1:57082] Ending connection
^C
```

### Client

```bash
$ RUST_LOG=debug cargo run --bin client

    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running `target/debug/client`
2023-02-09T06:16:36.348568Z  INFO client: Connecting to 0.0.0.0:6379
redis-rs> SET the_answer 42
2023-02-09T06:16:44.659081Z DEBUG client: Input read: SET the_answer 42
2023-02-09T06:16:44.659234Z DEBUG client: Input parsed: *3
$3
SET
$10
the_answer
$2
42

2023-02-09T06:16:44.659788Z DEBUG client: Received 38 bytes from server
Array { value: [String { value: "SET" }, String { value: "the_answer" }, String { value: "42" }] }
redis-rs> SET hello "WORLD"
2023-02-09T06:16:52.037235Z DEBUG client: Input read: SET hello "WORLD"
2023-02-09T06:16:52.037322Z DEBUG client: Input parsed: *3
$3
SET
$5
hello
$7
"WORLD"

2023-02-09T06:16:52.037879Z DEBUG client: Received 37 bytes from server
Array { value: [String { value: "SET" }, String { value: "hello" }, String { value: "\"WORLD\"" }] }
redis-rs> GET hello
2023-02-09T06:16:54.533415Z DEBUG client: Input read: GET hello
2023-02-09T06:16:54.533495Z DEBUG client: Input parsed: *2
$3
GET
$5
hello

2023-02-09T06:16:54.534065Z DEBUG client: Received 24 bytes from server
Array { value: [String { value: "GET" }, String { value: "hello" }] }
redis-rs> ^C
```

That's pretty cool to just see it working! 

## What's next? 

Now, I have a few options for what to do next:

* Actually make the server do something with these values
* Test my client against the 'real' redis server
* Test my server against the 'real' redis client
* Fix the `unsafe` thing

We shall see which one sounds most interesting later this week!


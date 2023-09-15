---
title: "Redis in Rust: Testing redis-cli + GET/SET support"
date: 2023-02-28
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
And I'm back. It's been a busy month with the [Genuary]([Genuary 2023]) series and life in general, but I'm still thinking about Redis in general :smile:.

Up this time, let's see what the official `redis-cli` app does when talking to our client and actually start handling some commands. Specifically, the very basic commands: `SET` and `GET`. With that, we would actually have a (very very basic) keystore up and running!

{{<toc>}}

<!--more-->


## Testing the client

Okay, first things first. I mentioned [[Redis in Rust: A REPL Client [Part 3]|last time]]() that I wanted to see how my server reacted to the official client, so let's do that:

```bash
$ RUST_LOG=debug cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.43s
     Running `target/debug/server`
2023-02-28T22:44:26.820918Z  INFO server: Listening on 0.0.0.0:6379
2023-02-28T22:44:31.563159Z DEBUG server: Accepted connection from 127.0.0.1:57879
2023-02-28T22:44:31.563366Z  INFO server: [127.0.0.1:57879] Accepted connection
2023-02-28T22:44:31.563464Z DEBUG server: [127.0.0.1:57879] Received 27 bytes
2023-02-28T22:44:31.563532Z DEBUG server: [127.0.0.1:57879 Received Array { value: [String { value: "COMMAND" }, String { value: "DOCS" }] }
2023-02-28T22:44:31.563937Z  INFO server: [127.0.0.1:57879] Ending connection

$ redis-cli

Assertion failed: (commandTable->element[i + 1]->type == REDIS_REPLY_MAP || commandTable->element[i + 1]->type == REDIS_REPLY_ARRAY), function cliCountCommands, file redis-cli.c, line 724.
zsh: abort      redis-cli
```

That's a good start. :smile:

It looks like before you even get to run a command, the first thing that `redis-cli` does is ask the server what commands it has, which is an interesting choice. Specifically it sends a `COMMAND DOCS` command to the server. Let's try just responding to that with an empty string:

```rust
# server.rs
async fn handle(mut stream: TcpStream, addr: SocketAddr) -> std::io::Result<()> {
    tracing::info!("[{addr}] Accepted connection");

    let mut buf = [0; 1024];
    let mut state = State::default();

    loop {
        let bytes_read = stream.read(&mut buf).await?;
        if bytes_read == 0 {
            break;
        }
        tracing::debug!("[{addr}] Received {bytes_read} bytes");

        stream.write_all(RedisType::Array { value: vec![] }.to_string().as_bytes()).await?;
    }
}
```

I don't want to actually deal actually sending all of the commands just yet, so let's see if this is enough to get away with for the time being:

```bash
$ RUST_LOG=debug cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.23s
     Running `target/debug/server`
2023-02-28T22:47:29.964696Z  INFO server: Listening on 0.0.0.0:6379
2023-02-28T22:47:32.176521Z DEBUG server: Accepted connection from 127.0.0.1:58089
2023-02-28T22:47:32.176730Z  INFO server: [127.0.0.1:58089] Accepted connection
2023-02-28T22:47:32.176781Z DEBUG server: [127.0.0.1:58089] Received 27 bytes
2023-02-28T22:47:32.176866Z DEBUG server: [127.0.0.1:58089 Received: COMMAND [String { value: "DOCS" }]
2023-02-28T22:47:35.527012Z DEBUG server: [127.0.0.1:58089] Received 24 bytes
2023-02-28T22:47:35.527265Z DEBUG server: [127.0.0.1:58089 Received: GET [String { value: "hello" }]
2023-02-28T22:47:36.623683Z  WARN server: An error occurred: Os { code: 54, kind: ConnectionReset, message: "Connection reset by peer" }

$ redis-cli

127.0.0.1:6379> GET hello
(empty array)
127.0.0.1:6379> EXIT
```

Sweet. We actually get to a REPL in the `redis-cli`. So we don't have to actually send anything interesting back, an empty array is fine. And it turns out that we can send that back to every command the REPL will happily print it out. Now that's progress. 

Let's actually implement something!

## Implementing Commands

Okay, to actually implement commands, let's take a step back and actually decide what a `Command` actually is. I think that we'll need:

1. some state for the server (whatever values we're storing, timeouts for values, ability to serialize to disk for backups)
2. the function(s) to run in specific commands

Eventually we'll probably be able to put a lot more here, like type checking and parsing, but that's for another day. For now:

```rust
#[derive(Debug, Default)]
pub struct State {
    keystore: HashMap<String, String>,
}

#[derive()]
pub struct Command {
    f: Box<fn(&mut State, &[RedisType]) -> Result<RedisType, String>>,
}
```

Specifically, the `State` right now will store just the basic `keystore` which is `String` to `String` (we'll get more types later, the value of this can be various data types. 

`Command` likewise just has the function `f` right now which takes in a mutable reference to a state (we'll need that for `SET` and friends) and a slice of `RedisType` as the arguments (whatever they may be). We'll return either a `RedisType` as the return value or a `String` as an error (which we'll 'promote' to `RedisType::Error`). 

And then we can use {{<doc rust lazy_static>}} to create a `&'static` `HashMap` of `Commands`!

```rust
lazy_static! {
    static ref COMMANDS: HashMap<&'static str, Command> = {
        let mut m = HashMap::new();
        
        m.insert("COMMAND", Command {
            f: Box::new(|_state, _args| {
                // TODO: Assume for now it's run as COMMAND DOCS with no more parameters
                // Eventually we'll want to serialize and send `COMMANDS` back
                Ok(RedisType::Array { value: vec![] })
            })
        });
    }
}
```

Pretty bizarre looking, not going to lie, but for the moment it does what I want. I think that I'll have to figure out a better abstraction for this, but let's see if this works. 

## Parsing and running a `Command`

Assuming we have the above, let's modify the `handle` function to use it. We need to:

1. Verify that we actually got at least one argument from the client (the `Command`)
2. Parse that
3. Verify that it's defined in our `COMMANDS` `HashMap` (or return an error)
4. Run the stored function (which may mutate `State`)
5. Return whatever that function returns to the client *or* if we got an error, return a `RedisType::Error` instead

Like this:

```rust
async fn handle(mut stream: TcpStream, addr: SocketAddr) -> std::io::Result<()> {
    tracing::info!("[{addr}] Accepted connection");

    let mut buf = [0; 1024];
    let mut state = State::default();

    loop {
        let bytes_read = stream.read(&mut buf).await?;
        if bytes_read == 0 {
            break;
        }
        tracing::debug!("[{addr}] Received {bytes_read} bytes");

        let string = String::from_utf8_lossy(&buf[0..bytes_read]);
        let command = match RedisType::from_str(&string) {
            Ok(RedisType::Array { value }) => value,
            Ok(data) => {
                tracing::warn!("[{addr}] Error, input should be array, got: {data:?}");
                continue;
            }
            Err(err) => {
                tracing::warn!("[{addr}] Error parsing input: {err:?}");
                continue;
            }
        };

        if command.len() < 1 {
            tracing::warn!("[{addr}] Input command was empty");
            continue;
        }

        let args = &command[1..];
        let command = match &command[0] {
            RedisType::String { value } => value.to_ascii_uppercase().to_owned(),
            _ => {
                tracing::warn!(
                    "[{addr}] Input command must be a string, got {:?}",
                    command[0]
                );
                continue;
            }
        };
        tracing::debug!("[{addr} Received: {command} {args:?}");

        match COMMANDS.get(command.as_str()) {
            Some(command) => {
                let response = match command.f.as_ref()(&mut state, args) {
                    Ok(value) => value,
                    Err(value) => RedisType::Error { value },
                };
                stream.write_all(response.to_string().as_bytes()).await?;
            }
            None => {
                tracing::warn!("[{addr}] Unimplemented command: {command} {args:?}");
                stream
                    .write_all(
                        RedisType::Error {
                            value: format!("Unimplemented command: {command}").to_owned(),
                        }
                        .to_string()
                        .as_bytes(),
                    )
                    .await?;
                continue;
            }
        }
    }

    tracing::info!("[{addr}] Ending connection");

    Ok(())
}
```

That's actually not bad. More to do the initial parsing than there is in the running the functions even. We do make sure that there's not only at least a first argument but that the first argument has to be a `RedisType::String`, since that's what commands have to do. 

Testing it out... should be no different, since our only command is `COMMAND DOCS`:

```bash
$ RUST_LOG=debug cargo run --bin server

   Compiling redis-rs v0.1.0 (/Users/jp/Projects/redis-rs)
    Finished dev [unoptimized + debuginfo] target(s) in 1.13s
     Running `target/debug/server`
2023-02-28T23:03:59.250735Z  INFO server: Listening on 0.0.0.0:6379
2023-02-28T23:04:02.523925Z DEBUG server: Accepted connection from 127.0.0.1:59537
2023-02-28T23:04:02.524167Z  INFO server: [127.0.0.1:59537] Accepted connection
2023-02-28T23:04:02.524225Z DEBUG server: [127.0.0.1:59537] Received 27 bytes
2023-02-28T23:04:02.524414Z DEBUG server: [127.0.0.1:59537 Received: COMMAND [String { value: "DOCS" }]
2023-02-28T23:04:05.358497Z DEBUG server: [127.0.0.1:59537] Received 24 bytes
2023-02-28T23:04:05.358628Z DEBUG server: [127.0.0.1:59537 Received: GET [String { value: "hello" }]
2023-02-28T23:04:05.358706Z  WARN server: [127.0.0.1:59537] Unimplemented command: GET [String { value: "hello" }]
2023-02-28T23:04:07.477619Z  INFO server: [127.0.0.1:59537] Ending connection

redis-cli

127.0.0.1:6379> GET hello
(error) Unimplemented command: GET
127.0.0.1:6379> EXIT
```

Sweet. It's even happy about sending commands I don't know yet and just sends those back as a `RedisType::Err`. 

## SET and GET

Okay, so we have a server, let's implement our first two commands: `SET` and `GET`. `SET` actually takes far more optional parameters than I even knew... but we can ignore most of them for now. For now, just `SET key value` and `GET key`. 

```rust
m.insert("SET", Command {
    f: Box::new(|state, args| {
        if args.len() < 2 {
            return Err("Expected: SET key value [NX | XX] [GET] [EX seconds | PX milliseconds | EXAT unix-time-seconds | PXAT unix-time-milliseconds | KEEPTTL]".to_string());
        }

        if args.len() > 2 {
            return Err("Expected: SET key value; additional parameters are not yet supported".to_string());
        }

        let key = match &args[0] {
            RedisType::String { value } => value.to_owned(),
            _ => return Err("SET: Unknown key format".to_string())
        };

        let value = match &args[1] {
            RedisType::String { value } => value.to_owned(),
            _ => return Err("SET: Unknown value format".to_string())
        };

        state.keystore.insert(key, value);
        Ok(RedisType::String { value: "OK".to_owned() })
    })
});

m.insert("GET", Command {
    f: Box::new(|state, args| {
        if args.len() != 1 {
            return Err("Expected: GET $key".to_string());
        }

        let key = match &args[0] {
            RedisType::String { value } => value.to_owned(),
            _ => return Err("Expected: GET $key:String".to_string())
        };

        Ok(match state.keystore.get(&key) {
            Some(value) => RedisType::String { value: value.to_owned() },
            None => RedisType::NullString,
        })
    })
});
```

That's not so bad. We do need to do some manual parsing of the `key` / `value` right now. I should probably macro that. But for the moment, it just works. Let's test it:

```bash
$ RUST_LOG=debug cargo run --bin server
    Finished dev [unoptimized + debuginfo] target(s) in 0.03s
     Running `target/debug/server`
...[server]

$ redis-cli
...[client]

[server] 2023-02-28T23:07:29.755427Z  INFO server: Listening on 0.0.0.0:6379
[server] 2023-02-28T23:07:31.825408Z DEBUG server: Accepted connection from 127.0.0.1:60005
[server] 2023-02-28T23:07:31.825627Z  INFO server: [127.0.0.1:60005] Accepted connection
[server] 2023-02-28T23:07:31.825674Z DEBUG server: [127.0.0.1:60005] Received 27 bytes
[server] 2023-02-28T23:07:31.825741Z DEBUG server: [127.0.0.1:60005 Received: COMMAND [String { value: "DOCS" }]

[client] 127.0.0.1:6379> GET hello
[server] 2023-02-28T23:07:33.413137Z DEBUG server: [127.0.0.1:60005] Received 24 bytes
[server] 2023-02-28T23:07:33.413269Z DEBUG server: [127.0.0.1:60005 Received: GET [String { value: "hello" }]
[client] (nil)

[client] 127.0.0.1:6379> SET hello "world"
[server] 2023-02-28T23:07:39.452693Z DEBUG server: [127.0.0.1:60005] Received 35 bytes
[server] 2023-02-28T23:07:39.452771Z DEBUG server: [127.0.0.1:60005 Received: SET [String { value: "hello" }, String { value: "world" }]
[client] "OK"

[client] 127.0.0.1:6379> GET hello
[server] 2023-02-28T23:07:41.571335Z DEBUG server: [127.0.0.1:60005] Received 24 bytes
[server] 2023-02-28T23:07:41.571410Z DEBUG server: [127.0.0.1:60005 Received: GET [String { value: "hello" }]
[client] "world"

[client] 127.0.0.1:6379> EXIT
[server] 2023-02-28T23:07:43.393666Z  INFO server: [127.0.0.1:60005] Ending connection
```

(I'm not sure how to better print those...)

But it's totally working. We can `GET` values that aren't stored yet, `SET` them, and then `GET` them again. 

Not so bad. 

## Testing with our client

What about if we actually use our client? 

```bash
$ cargo run --bin client

redis-rs> GET hello
NullString
redis-rs> SET hello "world"
String { value: "OK" }
redis-rs> GET hello
String { value: "\"world\"" }
```

Well that's actually really close! Except I totally don't parse or handle quotes correctly in my client. That's probably something I really should do... another day. 

## Full source

As always (although I don't know if I've said it), the full source is [on GitHub](https://github.com/jpverkamp/redis-rs/) with [tags available](https://github.com/jpverkamp/redis-rs/tags) for the code at the state of each blog post. 

## Next steps

* Implement the optional parameters of `SET`
  * Implement timing out and eviction of entries
* Implement another data type (sets, hashes, sorted sets, streams, etc)
* Implement persistance to disk / backups
* Improve the client to handle quoted strings
  * Test the improved client against the official server

So much to do. Onward!
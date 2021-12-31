---
title: "AoC 2021 Day 24: Aluinator"
date: 2021-12-24 00:00:03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Optimization
- Lexing
- Parsing
- Data Structures
- Mathematics
---
### Source: [Arithmetic Logic Unit](https://adventofcode.com/2021/day/24)

#### **Part 1:** Simulate an ALU with 4 registers (`w`, `x`, `y`, and `z`) and instructions defined below. Find the largest 14 digit number with no 0 digits which result in `z=0`. 

<!--more-->

> Instructions:
> * `inp a` - read the next input value into register `a`
> * `add a b` - set `a = a + b` (`b` can always be a register or an integer)
> * `mul a b` - set `a = a * b` 
> * `div a b` - set `a = a / b` (using integer division / discarding the remainder)
> * `mod a b` - set `a = a % b` (`%` is the {{< wikipedia "modulo" >}} operator)
> * `eql a b` - set `a = 1` if `a == b`, set `a = 0` otherwise

Fascinating. So there are a number of different ways you can approach this problem. 

First, we can just implement the ALU and try to brute force it:

```python
OPS = {
    'add': lambda a, b: a + b,
    'mul': lambda a, b: a * b,
    'div': lambda a, b: a // b,
    'mod': lambda a, b: a % b,
    'eql': lambda a, b: 1 if a == b else 0,
    'neq': lambda a, b: 1 if a != b else 0,
}


@app.command()
def run(file: typer.FileText, input: str, quiet: bool = False):
    input_digits = [int(c) for c in input]

    registers = {
        'w': 0,
        'x': 0,
        'y': 0,
        'z': 0,
    }

    for i, line in enumerate(file, 1):
        line = line.strip()
        logging.debug(f'[{i:04d} {registers=}] {line}')

        cmd, *args = line.split()

        if cmd == 'inp':
            a = args[0]
            registers[a] = input_digits[0]
            input_digits = input_digits[1:]

        else:
            a = args[0]
            b = args[1]

            a_val = registers[a]
            b_val = registers[b] if b in registers else int(b)

            r_val = OPS[cmd](a_val, b_val)

            registers[a] = r_val

    if quiet:
        return registers['z']
    else:
        print(registers['z'])
    
@app.command()
def part1(file: typer.FileText):
    
    for i in range(99999999999999, 1, -1):
        input = str(i)
        if '0' in input:
            continue

        file.seek(0)

        result = run(file, input, True)
        if result == 0:
            break

        if input.endswith('9999'):
            logging.info(f'{input} -> {result}')


    print(input)
```

Very short/clean code. Will take... forever to run. It can crank through roughly 10,000 values in 2-3 seconds. Given that we have 1 quadrillion to check (ignoring the 0 condition for now), that's... 6000 years to check them all. Even assuming the first two digits are 9, that's still 63 years. 

Yeah, no. 

Disclaimer, this was *not* actually my first solution to the problem. I actually wrote it up so that I could verify solutions obtained other ways, so let's back up and try a few other approaches.

##### Version 1: State with input paths

For my first real attempt, I didn't look at the input code (which would really have helped). Instead, I jumped straight in to a state map sort of like this:

```python

state = {
    'w': {0: {}},
    'x': {0: {}},
    'y': {0: {}},
    'z': {0: {}},
}

input_counter = 0
for i, (cmd, a, b) in enumerate(code, 1):
    logging.info(f'[{i:04d}] {cmd} {a} {b}')

    # Take the current input value and add that to the state to get here
    if cmd == 'inp':
        state[a] = {
            digit: {input_counter: {digit}}
            for digit in ALL_INPUTS
        }
        input_counter += 1

    # Otherwise, try to apply the given operation
    # But only on input states that match
    else:
        op = OPS[cmd]

        # If we have a constant, just apply it (path hasn't changed)
        if isinstance(b, int):
            state[a] = {
                op(key, b): key_path
                for key, key_path in state[a].items()
            }

        # Otherwise, apply all changes if the paths are the same
        else:
            new_output = defaultdict(lambda: defaultdict(set))

            for key, key_path in state[a].items():
                logging.debug(f'{PRE}- {key=}, {key_path=}')

                for value, value_path in state[b].items():
                    result = op(key, value)
                    logging.debug(f'{PRE}-- {value=}, {value_path=}, {result=}')

                    all_indexes = key_path.keys() | value_path.keys()

                    # There are no restrictions on inputs at all
                    if not key_path and not value_path:
                        logging.debug(f'{PRE}--- No restrictions')
                        if result not in new_output:
                            new_output[result] = defaultdict(set)

                    # Key path is known but not value path
                    if not value_path:
                        logging.debug(f'{PRE}--- No restriction on value')
                        for i, inputs in key_path.items():
                            new_output[result][i] |= inputs

                    # Value path is known, but not key
                    elif not key_path:
                        logging.debug(f'{PRE}--- No restriction on key')
                        for i, inputs in value_path.items():
                            new_output[result][i] |= inputs

                    # There are no overlapping indexes, include both
                    #elif not any(
                    #    index in key_path and index in value_path
                    #    for index in all_indexes
                    #):
                    #    logging.debug(f'{PRE}--- No overlapping indexes, combine')
                    #    for index in all_indexes:
                    #        new_output[result][index] = key_path.get(index) or value_path.get(index)

                    # The indexes are compatible
                    elif any(
                        index not in key_path or index not in value_path or key_path[index] == value_path[index]
                        for index in all_indexes
                    ):
                        logging.debug(f'{PRE}--- Compatible indexes, combine')
                        for index in all_indexes:
                            new_output[result][index] = key_path.get(index) or value_path.get(index)

                    else:
                        raise NotImplementedError

            new_output = {
                k1: {
                    k2: s
                    for k2, s in new_output[k1].items()
                    if s != ALL_INPUTS
                }
                for k1 in new_output
            }
            logging.debug(f'{PRE}{new_output=}')
            state[a] = new_output

    #logging.info(f'\n{pformat(state)}')

    # DEBUG
    #if i > 25:
    #    break

print()
#pprint(state)

pprint(state['z'])
```

It's... quite a mess. The basic idea is we have this nutty data structure where each state (of the 4 registers) stores all of the ways we could get to it. That's a dictionary of `{register: {input_key: set(input_value)}}`. This ignores the fact that `w` is the only register written to, it's always written to in input order (which we do know from the problem statement), and was a royal pain to write. So... let's try again.

##### Version 2: Parsing into an Abstract Syntax Tree

For attempt 2, I'm still going to try to solve for 'all values', but this time I'm going to do it by parsing out the eventual {{< wikipedia "abstract syntax tree" >}} for all values. As another way of saying it, if we have this program:

```text
inp w
mul x 0
add x z
mod x 26
```

You will get this sequence of trees:

```text
# inp w
I(0)

# mul x 0
mul
├ I(0)
└ 0

# add x z
add
├ mul
│ ├ I(0)
│ └ 0
└ R(z) # whatever Z previously was

# mod x 26
mod x 26
├ add
│ ├ mul
│ │ ├ I(0)
│ │ └ 0
│ └ R(z) # whatever Z previously was
└ 26
```

Pretty neat. And the code's not bad either:

```python
@dataclass(frozen=True)
class Node:
    pass


@dataclass(frozen=True)
class Literal(Node):
    value: int

    def __call__(self, input: str, depth: int = 0) -> int:
        return self.value


@dataclass(frozen=True)
class Input(Node):
    index: int

    def __call__(self, input: str, depth: int = 0) -> int:
        return int(input[self.index])


@dataclass(frozen=True)
class Operator(Node):
    function: str
    left: Node
    right: Node

    def __call__(self, input: str, depth: int = 0) -> int:
        l_value = self.left(input, depth + 1)
        r_value = self.right(input, depth + 1)
        return OPS[self.function](l_value, r_value)
```

And a parser:

```python
def parse(file: TextIO) -> Node:
    '''Read input into a list of instructions.'''

    registers = {
        'w': Literal(0),
        'x': Literal(0),
        'y': Literal(0),
        'z': Literal(0),
    }

    next_input_index = 0

    for i, line in enumerate(file, 1):
        line = line.strip()
        logging.info(f'[{i:04d}] Parsing {line}')

        cmd, *args = line.strip().split()
        a = args[0]

        if cmd == 'inp':
            registers[a] = Input(next_input_index)
            next_input_index += 1
            continue

        b = args[1]
        if not b.isalpha():
            right = Literal(int(b))
        else:
            right = registers[b]

        registers[a] = Operator(cmd, registers[a], right)

    return registers['z']
```

That will return a callable/function that you can call on every value to get what the result of `z` is. Problem is... these trees are *gigantic*. So I played a neat optimization trick where I can do `partial evaluation`:

```python
@dataclass(frozen=True)
class Node:
    pass

    def partial_eval(self) -> 'Node':
        return self

@dataclass(frozen=True)
class Operator(Node):
    function: str
    left: Node
    right: Node

    @disableable_cache
    def partial_eval(self) -> 'Node':
        l_value = self.left.partial_eval()
        r_value = self.right.partial_eval()

        # Literal evals can be directly simplified
        if isinstance(l_value, Literal) and isinstance(r_value, Literal):
            try:
                result = Literal(OPS[self.function](l_value.value, r_value.value))
            except ZeroDivisionError:
                result = Literal(0)

            logging.info(f'{PRE} Simplifying {self} -> {result}')
            return result

        # additive identity
        elif self.function == 'add' and isinstance(l_value, Literal) and l_value.value == 0:
            logging.info(f'{PRE} Applying 0+a=a')
            return r_value

        elif self.function == 'add' and isinstance(r_value, Literal) and r_value.value == 0:
            logging.info(f'{PRE} Applying a+0=a')
            return l_value

        # multiplicative identity
        elif self.function == 'mul' and isinstance(l_value, Literal) and l_value.value == 1:
            logging.info(f'{PRE} Applying 1*a=a')
            return r_value

        elif self.function == 'mul' and isinstance(r_value, Literal) and r_value.value == 1:
            logging.info(f'{PRE} Applying a*1=a')
            return l_value

        elif self.function == 'mul' and isinstance(l_value, Literal) and l_value.value == 0:
            logging.info(f'{PRE} Applying 0*a=a')
            return Literal(0)

        elif self.function == 'mul' and isinstance(r_value, Literal) and r_value.value == 0:
            logging.info(f'{PRE} Applying a*0=a')
            return Literal(0)

        # division identities
        elif self.function == 'div' and isinstance(r_value, Literal) and r_value.value == 1:
            logging.info(f'{PRE} Applying a/1=a')
            return l_value

        elif self.function == 'div' and l_value == r_value:
            logging.info(f'{PRE} Applying a/a=1')
            return Literal(1)

        # equality identities
        elif self.function == 'eql' and l_value == r_value:
            logging.info(f'{PRE} Applying a == a -> 1')
            return Literal(1)

        elif (
            self.function == 'eql'
            and isinstance(l_value, Operator)
            and l_value.function == 'eql'
            and isinstance(r_value, Literal)
            and r_value.value == 0
        ):
            result = Operator('neq', l_value.left, l_value.right)
            logging.info(f'{PRE} Converting eq to neq')
            return result

        # If we're doing EQL any input to a value not [0, 9], that's always 0
        elif (
            self.function == 'eql'
            and isinstance(l_value, Literal)
            and (l_value.value < 0 or l_value.value > 9)
            and isinstance(r_value, Input)
        ):
            logging.info(f'{PRE} Simplifying impossible {self} -> 0')
            return Literal(0)

        elif (
            self.function == 'eql'
            and isinstance(r_value, Literal)
            and (r_value.value < 0 or r_value.value > 9)
            and isinstance(l_value, Input)
        ):
            logging.info(f'{PRE} Simplifying impossible {self} -> 0')
            return Literal(0)

        elif (
            self.function == 'neq'
            and isinstance(l_value, Literal)
            and (l_value.value < 0 or l_value.value > 9)
            and isinstance(r_value, Input)
        ):
            logging.info(f'{PRE} Simplifying impossible {self} -> 0')
            return Literal(1)

        elif (
            self.function == 'neq'
            and isinstance(r_value, Literal)
            and (r_value.value < 0 or r_value.value > 9)
            and isinstance(r_value, Input)
        ):
            logging.info(f'{PRE} Simplifying impossible {self} -> 0')
            return Literal(1)

        # Base case
        else:
            return self
```

As noted, there are a lot of mathematical operations (like `a*0=0`) that we can apply to cut out huge swatches of the AST. Especially since these are *actually used* in our input to zero out variables, for example. 

And that really does work, it makes the trees quite a bit smaller. But... it's still gigantic and takes much longer than just directly evaluating the answers (in version 0). So... I abandoned this one as well, cool as it was.

##### Version 3: State tree redux + golang

Okay, version 3. This time I was going to more cleanly do the state map that I tried in version 1. This time, the map is `{registers: input string}`. Since I know I'm looking for the largest string, I only have to keep that. 

```python
@dataclass(frozen=True)
class State:
    w: int
    x: int
    y: int
    z: int

    def __getitem__(self, key: Union[str, int]) -> int:
        if key in 'wxyz':
            return getattr(self, key)

        return int(key)

    def set(self, key: str, value: int) -> 'State':
        return State(
            value if key == 'w' else self.w,
            value if key == 'x' else self.x,
            value if key == 'y' else self.y,
            value if key == 'z' else self.z,
        )

    def __repr__(self):
        return f'{{{self.w}, {self.x}, {self.y}, {self.z}}}'
```

And the actual state map:

```python
def read(file: TextIO):
    start = time.perf_counter()
    states = {State(0, 0, 0, 0): ''}

    input_length = 0
    for i, line in enumerate(file, 1):
        line = line.strip()
        logging.info(
            f'[line={i:04d} len={input_length} states={len(states)} time={time.perf_counter() - start:02f}s] {line}')

        cmd, *args = line.split()

        if cmd == 'inp':
            # Now expand again with the new inputs
            a = args[0]
            new_states = {}
            input_length += 1

            for i in ALL_INPUTS:
                for state, input in states.items():
                    new_state = state.set(a, i)
                    new_input = input + str(i)

                    if new_state not in new_states:
                        new_states[new_state] = new_input

                    new_states[new_state] = max(new_states[new_state], new_input)

            states = new_states

        else:
            # Otherwise apply the function to all current states
            a, b = args
            states = {
                state.set(a, OPS[cmd](state[a], state[b])): input
                for state, input in states.items()
            }

    result = None

    logging.info('Scanning for final solution')
    for state, input in states.items():
        if state.z != 0:"""  """
            continue

        if not result or input > result:
            logging.info(f'New maximum found: {input}')
            result = input

    return result
```

Let's see it with debug mode on:

```python
$ python3 aluinator-v3.py --debug part1 input.txt

# It runs pretty fast at first!
11:24:21 INFO [line=0001 len=0 states=1 time=0.000013s] inp w
11:24:21 INFO [line=0002 len=1 states=9 time=0.000126s] mul x 0
11:24:21 INFO [line=0003 len=1 states=9 time=0.000165s] add x z
11:24:21 INFO [line=0004 len=1 states=9 time=0.000194s] mod x 26
11:24:21 INFO [line=0005 len=1 states=9 time=0.000222s] div z 1
11:24:21 INFO [line=0006 len=1 states=9 time=0.000250s] add x 10
...
# But every time there's an inp, we multiple states by 9...
11:24:22 INFO [line=0090 len=5 states=7290 time=0.268895s] add z y
11:24:22 INFO [line=0091 len=5 states=7290 time=0.276940s] inp w
11:24:22 INFO [line=0092 len=6 states=65610 time=0.392064s] mul x 0
...
# We do sometimes simplify a bunch of states (with things like mul y 0, which is basically y = 0)
11:24:22 INFO [line=0098 len=6 states=65610 time=0.945848s] eql x 0
11:24:22 INFO [line=0099 len=6 states=65610 time=1.051166s] mul y 0
11:24:22 INFO [line=0100 len=6 states=11340 time=1.136822s] add y 25
11:24:22 INFO [line=0101 len=6 states=11340 time=1.149788s] mul y x
...
# And even by the 8th input, we're already taking about a second per command
# And we're only around halfway through the program and have 6 more 9x of state counts...
11:24:29 INFO [line=0131 len=8 states=649539 time=7.659318s] div z 26
11:24:30 INFO [line=0132 len=8 states=649539 time=8.575231s] add x -12
...
# Yeah, 20 seconds per iteration isn't great (we're just about to inp again)
11:31:08 INFO [line=0179 len=10 states=5970510 time=406.829251s] mul y x
11:31:29 INFO [line=0180 len=10 states=5970510 time=427.306535s] add z y
...
```

And what's worse, by the time I got to here, I was eating up 32GB of RAM and getting into swap space. So... that didn't help runtime. In any case, I didn't let this run out. I did try to rewrite it in golang though!

```go
package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
)

type state struct {
	w int
	x int
	y int
	z int
}

func (s state) get(r string) int {
	if r == "w" {
		return s.w
	} else if r == "x" {
		return s.w
	} else if r == "y" {
		return s.y
	} else if r == "z" {
		return s.z
	} else {
		result, err := strconv.Atoi(r)
		if err != nil {
			log.Panic(err)
		}
		return result
	}
}

func (s state) set(r string, v int) state {
	result := s
	if r == "w" {
		result.w = v
	} else if r == "x" {
		result.x = v
	} else if r == "y" {
		result.y = v
	} else if r == "z" {
		result.z = v
	}
	return result
}

type input struct {
	min string
	max string
}

func minput(i1 input, i2 input) input {
	result := input{"", ""}

	if i1.min < i2.min { 
		result.min = i1.min
	} else {
		result.min = i2.min
	}

	if i1.max > i2.max { 
		result.max = i1.max
	} else {
		result.max = i2.max
	}

	return result
}

type Op func(int, int) int

func is_reg(s string) bool {
	return s == "w" || s == "x" || s == "y" || s == "z"
}

func main() {
	// Store a list of operators
	operators := make(map[string]Op)
	operators["add"] = func(a int, b int) int { return a + b }
	operators["mul"] = func(a int, b int) int { return a * b }
	operators["div"] = func(a int, b int) int { if b == 0 { return 0 } else { return a / b } }
	operators["mod"] = func(a int, b int) int { if b == 0 { return 0 } else { return a % b } }
	operators["eql"] = func(a int, b int) int { if a == b { return 1 } else { return 0 } }

	// Open the input file
	file, err := os.Open("input.txt")
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	// Initialize the register states
	var states map[state]input
	var new_states map[state]input

	states = make(map[state]input)
	states[state{0, 0, 0, 0}] = input{"", ""}

	// Start scanning through the file line by line
	scanner := bufio.NewScanner(file)
	input_length := 0
	line_number := 0
	for scanner.Scan() {
		line_number += 1
		line := scanner.Text()
		fields := strings.Fields(line)
		log.Printf("[%d len=%d states=%d] %s", line_number, input_length, len(states), line)

		// Build a new set of states from the current set
		new_states = make(map[state]input)
		
		// An input value adds 9 new states for each old state, each possible non-zero input
		if fields[0] == "inp" {
			a := fields[1]
			for i := 1; i <= 9; i++ {
				for old_state, old_input := range states {
					// Update the proper variable in the input string
					new_state := old_state.set(a, i)
					
					// Calculate the new minimum/maximum input string
					new_input := input{fmt.Sprint(old_input.min, i), fmt.Sprint(old_input.max, i)}
						
					// Check if we've already stored that in our new_state, if so keep the min/max
					if prev_new_input, ok := new_states[new_state]; ok {
						new_states[new_state] = minput(prev_new_input, new_input)
					} else {
						new_states[new_state] = new_input
					}
				}
			}

			
		} else {
			// Fetch the proper operator function
			f, ok := operators[fields[0]]
			if !ok {
				log.Fatal("Unknown operator", fields[1])
			}
			a := fields[1]

			// Update all old states
			for old_state, old_input := range states {
				b := fields[2]

				a_val := old_state.get(a)
				b_val := old_state.get(b)
				r_val := f(a_val, b_val)

				new_state := old_state.set(a, r_val)

				// Check if we've already stored that in our new_state, if so keep the min/max
				if prev_new_input, ok := new_states[new_state]; ok {
					new_states[new_state] = minput(prev_new_input, old_input)
				} else {
					new_states[new_state] = old_input
				}
			}
		}

		// Finally, swap new_state to state
		states = new_states
	}

	result := input{"", ""}
	result_set := false

	for state, input := range states {
		if state.z != 0 {
			continue
		}

		if !result_set {
			result = input
			result_set = true
			continue
		}

		result = minput(result, input)
	}

	fmt.Println(result)
}
```

That's not actually that bad! I should write more go. And while it did work faster at first... it had a lot *more* issues with RAM (might be how I wrote it and a lack of successful GC?). When I came back in the morning, my computer had actually rebooted, so... that wasn't great.

Fun to write though?

##### Version 4: Let's just do it by hand

So... let's try something completely different. One you I noticed (finally) was that the input was 14 almost identical blocks that looked like this:

```text
inp w
mul x 0
add x z
mod x 26
div z 1  # zdiv, this can be 1 or 26
add x 10 # cx
eql x w
eql x 0
mul y 0
add y 25
mul y x
add y 1
mul z y
mul y 0
add y w
add y 10 # cy
mul y x
add z y
```

There are 3 constants that change, which I've named `zdiv`, `cx`, and `cy`.

```text
zdiv cx      cy
1    10      10      
1    13      5       
1    15      12      
26   -12     12      
1    14      6       
26   -2      6       
1    13      15      
26   -12     15      
1    15      7       
1    11      11      
26   -3      11      
26   -13     7       
26   -12     5       
26   -13     10      
```

All of the rest of the code is the same. We can actually de-compile it if we want:

```python
def f(z, i, zdiv, cx, cy):
    '''Take the previous z, the input value, and two constants.'''

    # mul x 0
    # add x z
    # mod x 26
    # div z 1 -- zdiv (either 1 or 26)
    # add x 10 -- cx
    # >> x = (z // zdiv) % 26 + cx

    # eql x w
    # eql x 0
    # >> x is 1 if x != i
    x_flag = (i == (z // zdiv) % 26 + cx)

    # mul y 0
    # add y 25
    # mul y x
    # >> because x is 0 or 1 if i == z % 26 + cx
    # >> y == 0 or 25 if i == z % 26 + cx

    # add y 1
    # mul z y
    # >> y == 1 or 26 if i == z % 26 + cx

    # so:
    # >> z *= 26 if i == z % 26 + cx
    # >> z *= 1 (nop) if i != z % 26 + cx
    if x_flag:
        z *= 26

    # mul y 0
    # add y w
    # add y 10 -- cy
    # mul y x
    # add z y
    if x_flag:
        z += i + cy
```

Which ends up with this very compact block:

```python
def f(z, i, zdiv, cx, cy):
    if (i == (z // zdiv) % 26 + cx):
        return z * 26 + i + cy
```

So... what's interesting about that? Well, we're always either multiplying, dividing, or modding `z` by 26. That makes me think of a base 26 number (or a letter)? And that last bit, `zdiv`... that's either `1` (which dividing by 1 is a no-op) or `26`, removing a character from the base26 number. 

Hmm...

Okay. Let's think of `z` as a stack of base-26 numbers (I know, crazy right?). Each successful iteration, we're going to advance the stack (multiplying by 26) and push `i + cy` onto the stack. *But* if we have a `z / 26` step, that means we're essentially going to pop *off* the stack, checking the value against `+ cx`... which makes an equality between two different input values!

```text
zd  cx  cy  stack / equations
1	10	10  i1+10
1	13	5   i1+10, i2+5
1	15	12  i1+10, i2+5, i3+12
26	-12	12  i4 = i3 + 12 - 12 = i3
1	14	6   i1+10, i2+5, i5+6
26	-2	4   i6 = i5 + 6 - 2 = i5 + 4
1	13	15  i1+10, i2+5, i7+15
26	-12	3   i8 = i7 + 15 - 12 = i7 + 3
1	15	7   i1+10, i2+5, i9+7
1	11	11  i1+10, i2+5, i9+7, i10+11
26	-3	2   i11 = i10 + 11 - 3 = i10 + 8
26	-13	12  i12 = i9 + 7 - 13 = i9 - 6
26	-12	4   i13 = i2 + 5 - 12 = i2 - 7
26	-13	11  i14 = i1 + 10 - 13 = i1 - 3
```

So each time `zd=1`, add `i#+cy` to the stack, so we add `i1+10`, then `i2+5`, then `i3+12`. Then we get our first `zd=26`, so we'll pop the `i3+12` off the stack and combine it with `i4` and the current `cx`:

```text
i4 = i3 + 12 - 12 
i4 = i3
```

Interesting. We continue as above, eventually creating a system of 7 equations that relate all 14 variables. That should be enough to generate all possible output values!

```text
i4 = i3
i6 = i5 + 4
i8 = i7 + 3
i11 = i10 + 8
i12 = i9 - 6
i13 = i2 - 7
i14 = i1 - 3
```

But what's more, we know we're looking for the largest. So for each pair, we'll always set (at least) one 9 (the larger value) and then use the question to set the smaller. So `i4 = i3 = 9`, but if `i6 = 9`, then `9 = i5 + 4` so `i5 = 5`. And so on:

```python
---------11111
12345678901234
..99..........
..9959........
..995969......
..995969.19...
..9959699193..
.999596991932.
99995969919326
```

Trying that against our simulator/version 0:

```bash
$ python3 aluinator.py run input.txt 99995969919326

0
```

BAM! And the first 4 digits were all 9, so it wouldn't have taken 63 years... just 30 weeks. Yay 2022 I suppose? 

That is very cool. It's not nearly as 'code' as many of the other solutions, but it's still pretty awesome IMO. 

#### **Part 2:** Find the smallest such 14 digit number with no 0 digits such that `z=0`.

Nothing changes, we already have the equations! We just need to the earlier value to `1`:

```text
---------11111
12345678901234
..11..........
..1115........
..111514......
..111514.19...
..1115147191..
.811151471911.
48111514719111
```

Verify:

```python
$ python3 aluinator.py run input.txt 48111514719111

0
```

BAM!

#### Generating solutions

Okay, now that I see how to solve the problem, I want to actually write a bit more code. Let's write something that can pull out those constants and do the same equations:

```python
@app.command()
def solve(file: typer.FileText):

    blocks = []
    zdiv, cx, cy = 0, 0, 0

    logging.info('Finding block parameters')
    for i, line in enumerate(file, 1):
        line = line.strip()
        last = line.split()[-1]
        logging.debug(f'[{i:04d} {zdiv=} {cx=} {cy=}] {line}')

        if line.startswith('inp'):
            if zdiv:
                logging.info(f'Block found: {zdiv=}, {cx=}, {cy=}')
                blocks.append((zdiv, cx, cy))

        elif line.startswith('div z ') and last not in 'wxyz':
            zdiv = int(line.split()[-1])

        elif line.startswith('add x ') and last not in 'wxyz':
            cx = int(line.split()[-1])

        elif line.startswith('add y ') and last not in 'wxyz':
            cy = int(line.split()[-1])

    logging.info(f'Block found: {zdiv=}, {cx=}, {cy=}')
    blocks.append((zdiv, cx, cy))


    logging.info('----- ----- -----')
    logging.info('Generating equations')
    stack = []
    equations = []

    for i, (zdiv, cx, cy) in enumerate(blocks):
        if zdiv == 1:
            stack.append((i, cy))
            logging.info(f'{zdiv:<4d} {cx:<4d} {cy:<4d}  {stack}')
        else:
            j, cy = stack.pop()
            equations.append((i, j, cx + cy))
            logging.info(f'{zdiv:<4d} {cx:<4d} {cy:<4d}  i{i} = i{j} + {cx} + {cy} = i{j} + {cx+cy}')

    logging.info('----- ----- -----')
    logging.info('Solving for minimum/maximum')

    part1 = ['?'] * 14
    part2 = ['?'] * 14

    for i, j, delta in equations:
        i, j = min(i, j), max(i, j)

        if delta <= 0:
            part1[i], part1[j] = '9', str(9 + delta)
            part2[i], part2[j] = str(1 + abs(delta)), '1'

        else:
            part1[i], part1[j] = str(9 - delta), '9'
            part2[i], part2[j] = '1', str(1 + delta)

        equation = f'i{i} = i{j} + {delta}'
        logging.info(f'{equation:<15s} {"".join(part1)} {"".join(part2)}')

    print('part1:', ''.join(part1))
    print('part2:', ''.join(part2))
```

It's the same idea, but with nice logging output:

```bash
$ python3 aluinator.py --debug solve input.txt

Finding block parameters
Block found: zdiv=1, cx=10, cy=10
Block found: zdiv=1, cx=13, cy=5
Block found: zdiv=1, cx=15, cy=12
Block found: zdiv=26, cx=-12, cy=12
Block found: zdiv=1, cx=14, cy=6
Block found: zdiv=26, cx=-2, cy=4
Block found: zdiv=1, cx=13, cy=15
Block found: zdiv=26, cx=-12, cy=3
Block found: zdiv=1, cx=15, cy=7
Block found: zdiv=1, cx=11, cy=11
Block found: zdiv=26, cx=-3, cy=2
Block found: zdiv=26, cx=-13, cy=12
Block found: zdiv=26, cx=-12, cy=4
Block found: zdiv=26, cx=-13, cy=11
----- ----- -----
Generating equations
1    10   10    [(0, 10)]
1    13   5     [(0, 10), (1, 5)]
1    15   12    [(0, 10), (1, 5), (2, 12)]
26   -12  12    i3 = i2 + -12 + 12 = i2 + 0
1    14   6     [(0, 10), (1, 5), (4, 6)]
26   -2   6     i5 = i4 + -2 + 6 = i4 + 4
1    13   15    [(0, 10), (1, 5), (6, 15)]
26   -12  15    i7 = i6 + -12 + 15 = i6 + 3
1    15   7     [(0, 10), (1, 5), (8, 7)]
1    11   11    [(0, 10), (1, 5), (8, 7), (9, 11)]
26   -3   11    i10 = i9 + -3 + 11 = i9 + 8
26   -13  7     i11 = i8 + -13 + 7 = i8 + -6
26   -12  5     i12 = i1 + -12 + 5 = i1 + -7
26   -13  10    i13 = i0 + -13 + 10 = i0 + -3
----- ----- -----
Solving for minimum/maximum
i2 = i3 + 0     ??99?????????? ??11??????????
i4 = i5 + 4     ??9959???????? ??1115????????
i6 = i7 + 3     ??995969?????? ??111514??????
i9 = i10 + 8    ??995969?19??? ??111514?19???
i8 = i11 + -6   ??9959699193?? ??1115147191??
i1 = i12 + -7   ?999596991932? ?811151471911?
i0 = i13 + -3   99995969919326 48111514719111

part1: 99995969919326
part2: 48111514719111
```

Fast too! (As it should be):

```bash
--- Day 24: Arithmetic Logic Uni ---

$ python3 aluinator.py solve input.txt
part1: 99995969919326
part2: 48111514719111
# time 50759375ns / 0.05s
```

A bit better than 30 weeks. :D

Anyways. That was weird and fun. A neat change of pace. Onward and lastward!
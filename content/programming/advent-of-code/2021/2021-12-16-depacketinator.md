---
title: "AoC 2021 Day 16: Depacketinator"
date: 2021-12-16
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Data Structures
- Network
- Parsing
---
### Source: [Packet Decoder](https://adventofcode.com/2021/day/16)

#### **Part 1:** Given a recursive binary packet definition (see below), parse the given packet. Return the sum of each packet's `version`.

<!--more-->

All packet fields are in bits. Possible packet formats:

| Name | Structure |
|------|-----------|
| Literal Value | `AAA 010 [1CCCC]* [1CCCC]` |
| Type 0 Operator | `AAA BBB 0 DDDDDDDDDDDDDDD (children)` |
| Type 1 Operator | `AAA BBB 1 EEEEEEEEEEE (children)` |

In all packets:
* `AAA` - 3 bits representing the `version` of the packet
* `BBB` - 3 bits representing the `type_id` of the packet

In literal packets--where `type_id` = 4 (`010`)--the value is an integer encoded in a value similar to [[wiki:UTF-8 encoding]](). There will be a sequence of 0 or more 5 bit values `1CCCC` (with the `1` indicating the number continues, followed by a single `0CCCC` segment, ending the value. These `C*`s will be concatenated and treated as a single unsigned binary value and converted to an integer. 

In Type 0 Operator packets, the next 15 bits (`D{15}`) should be interpreted as an unsigned integer containing the number of following bits that encode 'child' packets. Parse the following `D` bits as child packets (perhaps recursively) and attach those to the Type 0 Operator as children. 

In Type 1 Operator packets, the next 11 bits (`E{11}`) should be interpreted as an unsigned integer containing the number of child packets (instead of their length). Parse that many child packets (perhaps recursively, only top level children count towards this number `E`) and attach those to the Type 1 Operator as children. 

Yeah, that's a mouthful. But it's a pretty awesome excuse to use a few techniques that are common in parsing binary encodings, such as network packets. 

First things first, I want to make a `BitStream` class that can take in the data that's going to make up our packets and keep track of where we are. That way, we can read out an arbitrary number of bits (3, 1, 4, 15, and 11 bits in this case, depending on the structure) as whatever types we need:

```python
@dataclass
class BitStream:
    index: int
    data: str

    @staticmethod
    def from_hex(hex_data: str) -> 'BitStream':
        return BitStream(0, ''.join(
            '{:04b}'.format(int(c, 16)) for c in hex_data
        ))

    def read_bits(self, n: int) -> str:
        '''Read n bits from the current position in the bitsting as a string of 0/1'''

        value = self.data[self.index:self.index+n]
        self.index += n

        if self.index > len(self.data):
            raise BitStreamException('Attempted to read past the end of bitstream')

        return value

    def read_int(self, n: int) -> int:
        '''Read n bits from the current position and convert to an integer'''

        return int(self.read_bits(n), 2)

    def read_bool(self) -> bool:
        '''Read the next bit from the current position as True/False'''

        return self.read_bits(1) == '1'

    def __str__(self):
        if self.index + 8 < len(self.data):
            return f'<{self.index}/{len(self.data)}, {self.data[self.index:self.index+8]}...>'
        else:
            return f'<{self.index}/{len(self.data)}, {self.data[self.index:]}>'
```

That's actually not that bad, I don't think. It's a bit interesting that we're mostly reading in `from_hex`, but that just means take each single hex character, turn it into an integer with `int(c, 16)` and then print that as a fixed four bits with `{:04b}.format(...)`. Other than that, `read_bits` will read n bits and advance the current pointer into the stream, and `read_int` / `read_bool` will wrap that to read a specific kind of value. 

With all that, we should be ready to parse the packets:

```python
@dataclass
class Packet:
    version: int
    type_id: int

    value: int
    children: List['Packet']

    length: int

    @staticmethod
    def from_hex(hex: str) -> 'Packet':
        return Packet.from_bitstream(BitStream.from_hex(hex))

    @staticmethod
    def from_bitstream(bits: BitStream, _depth: int = 0) -> 'Packet':
        logging.info(f'{" " * _depth}Parsing new packet at {bits}')

        version = bits.read_int(3)
        type_id = bits.read_int(3)
        length = 6

        value = 0
        children = []

        logging.info(f'{" " * _depth} - {version=}, {type_id=}')

        # Literal values
        if type_id == 4:
            logging.info(f'{" " * _depth} - Mode=literal')

            keep_reading = True
            while keep_reading:
                keep_reading = bits.read_bool()
                byte = bits.read_int(4)
                logging.info(f'{" " * _depth} - Read byte {byte}, will continue: {keep_reading}')

                value = value * 16 + byte
                length += 5

        # Any other operator value
        else:
            # The next bit is the length_type_id
            # If it's set, read the number of bits in subpackets
            length += 1
            if bits.read_bool():
                length += 11
                number_of_children = bits.read_int(11)
                logging.info(f'{" " * _depth} - Mode=operator, length_type=1 ({number_of_children} children)')

                for _ in range(number_of_children):
                    child = Packet.from_bitstream(bits, _depth + 1)
                    children.append(child)

                    length += child.length

            # If it's not, read the number of subpackets
            else:
                length += 15
                body_length = bits.read_int(15)
                logging.info(f'{" " * _depth} - Mode=operator, length_type=0 ({body_length} bits)')
                logging.info(f'{" " * _depth} - {len(bits.data)-bits.index} of {len(bits.data)} remaining')

                while body_length:
                    child = Packet.from_bitstream(bits, _depth + 1)
                    children.append(child)

                    body_length -= child.length
                    length += child.length

                    logging.info(f'{" " * _depth} - New child used {child.length} bits, {body_length} remaining')

                    if body_length < 0:
                        raise PacketParseException('Could not parse packet, too many bits used by children')

        p = Packet(version, type_id, value, children, length)
        logging.info(f'{" " * _depth} \ Packet parsed: {p}')
        return p
```

There's a fair amount of debugging code in there... because this took a bit to get right. And all for a relatively simple mistake. Essentially, we start by taking the bit stream and reading the `value` and `type_id`. That is always 6 bits. After that, there's a special case for `type_id = 4`: literals. That's the first half of the `if`. In there, we're going to read 1 + 4 bits at a time until the first bit is 0, adding the other 4 bits as an ever growing base 16 literal. Pretty cool!

The other two cases depend on the next bit read with `bits.read_bool()`. If it's 0, we're parsing a specific number of children. That one's not so bad, because we can just read off `Packet.from_bitstream` at the current point for that many children. But we absolutely have to update the length because of the next case: 

If the `bits.read_bool()` was 1. In this case, we only know how many bits the child packets are made of. This is actually the more common method in network and other binary formats I've found, because it lets you skip parsing if you don't actually care about the children. You can just jump ahead that many bits. In the above case with a number of children, you have no idea how large those children actually are, so you have to parse them. 

In any case, we now have perfectly functional parsing of packets. It's pretty cool to see it work too:

```python
>>> Packet.from_hex('D2FE28')
Packet(version=6, type_id=4, value=2021, children=[], length=21)

>>> Packet.from_hex('38006F45291200')
Packet(version=1, type_id=6, value=0, children=[
    Packet(version=6, type_id=4, value=10, children=[], length=11),
    Packet(version=2, type_id=4, value=20, children=[], length=16)
], length=49)

>>> Packet.from_hex('EE00D40C823060')
Packet(version=7, type_id=3, value=0, children=[
    Packet(version=2, type_id=4, value=1, children=[], length=11), 
    Packet(version=4, type_id=4, value=2, children=[], length=11), 
    Packet(version=1, type_id=4, value=3, children=[], length=11)
], length=51)
```

I like reading the debug view as well (which is good, since I spent a while staring at it...)

```python
>>> Packet.from_hex('EE00D40C823060')
INFO Parsing new packet at <0/56, 11101110...>
INFO  - version=7, type_id=3
INFO  - Mode=operator, length_type=1 (3 children)
INFO  Parsing new packet at <18/56, 01010000...>
INFO   - version=2, type_id=4
INFO   - Mode=literal
INFO   - Read byte 1, will continue: False
INFO   \ Packet parsed: Packet(version=2, type_id=4, value=1, children=[], length=11)
INFO  Parsing new packet at <29/56, 10010000...>
INFO   - version=4, type_id=4
INFO   - Mode=literal
INFO   - Read byte 2, will continue: False
INFO   \ Packet parsed: Packet(version=4, type_id=4, value=2, children=[], length=11)
INFO  Parsing new packet at <40/56, 00110000...>
INFO   - version=1, type_id=4
INFO   - Mode=literal
INFO   - Read byte 3, will continue: False
INFO   \ Packet parsed: Packet(version=1, type_id=4, value=3, children=[], length=11)
INFO  \ Packet parsed: Packet(version=7, type_id=3, value=0, children=[Packet(version=2, type_id=4, value=1, children=[], length=11), Packet(version=4, type_id=4, value=2, children=[], length=11), Packet(version=1, type_id=4, value=3, children=[], length=11)], length=51)

Packet(version=7, type_id=3, value=0, children=[
    Packet(version=2, type_id=4, value=1, children=[], length=11), 
    Packet(version=4, type_id=4, value=2, children=[], length=11), 
    Packet(version=1, type_id=4, value=3, children=[], length=11)
], length=51)
```

Neat!

Wrap it to actually satisfy the actual prompt (sum all `versions`):

```python
def part1(file: typer.FileText):

    def sum_versions(p: Packet) -> int:
        return p.version + sum(sum_versions(child) for child in p.children)

    p = Packet.from_hex(file.read().strip())
    logging.info(p)
    print(f'{sum_versions(p):-16} {line}')
```

And that's it. A nice recursive `sum_versions` that looks into `children` if there are any, summing as it goes. Nice. So... how does it work on the given input?

```python
$ python3 depacketinator.py part1 input.txt
             981 0055....C000
# time 63753417ns / 0.06s
```

Nice. Quick too. 

So... while we're here, what was the error that took me forever to figure out? Originally, my `else` block (the type 0/1 operators) looked like this:

```python
        ...
        # Any other operator value
        else:
            # The next bit is the length_type_id
            # If it's set, read the number of bits in subpackets
            if bits.read_bool():
                number_of_children = bits.read_int(11)
                logging.info(f'{" " * _depth} - Mode=operator, length_type=1 ({number_of_children} children)')

                for _ in range(number_of_children):
                    child = Packet.from_bitstream(bits, _depth + 1)
                    children.append(child)

                    length += child.length

            # If it's not, read the number of subpackets
            else:
                body_length = bits.read_int(15)
                logging.info(f'{" " * _depth} - Mode=operator, length_type=0 ({body_length} bits)')
                logging.info(f'{" " * _depth} - {len(bits.data)-bits.index} of {len(bits.data)} remaining')

                while body_length:
                    child = Packet.from_bitstream(bits, _depth + 1)
                    children.append(child)

                    body_length -= child.length
                    length += child.length

                    logging.info(f'{" " * _depth} - New child used {child.length} bits, {body_length} remaining')

                    if body_length < 0:
                        raise PacketParseException('Could not parse packet, too many bits used by children')

        p = Packet(version, type_id, value, children, length)
        logging.info(f'{" " * _depth} \ Packet parsed: {p}')
        return p
```

Pretty much the same, no?

Well, actually there are three very important lines missing. Three lines that, because of how the test packet lengths worked out, led to a number of hard to debug errors, but only in *some* of the test cases. 

Any guesses? Look back and compare? 

Turns out, you absolutely need to have the correct lengths for nested operator packets. So 1 bit for the type and either 15 or 11 for the count. It only matters if you have a Type 1 packet with non-literals inside of it (so at least two levels of nesting), otherwise the lengths work well enough, but in that case, it certainly got tricky. It kept looking for more information when there just weren't any more bits to be had. 

Oh, debuggging. 

I really should be writing better test cases, but in this case, that wouldn't have necessarily helped. I *knew* which test was failing, I just didn't know (at first) *why*. Live and learn. 

#### **Part 2:** Given the following `type_id` to function mappings, evaluate the packet. 

* `0`: `sum` of the values of child packets
* `1`: `product` of the values of child packets
* `2`: `minimum` of the values of child packets
* `3`: `maximum` of the values of child packets
* `4`: `literal` values (see above)
* `5`: will have exactly two child packets, `1` if `a > b` else `0`
* `6`: will have exactly two child packets, `1` if `a < b` else `0`
* `7`: will have exactly two child packets, `1` if `a = b` else `0`

Well, we did the hard part. We just have to change the recursive function. Instead of summing values, we need to evaluate the children then apply the given function:

```python
@app.command()
def part2(file: typer.FileText):
    def prod(ls):
        result = 1
        for el in ls:
            result *= el
        return result

    operators: Mapping[int, Callable[[List[int]], int]] = {
        0: sum,
        1: prod,
        2: min,
        3: max,
        5: lambda ab: 1 if ab[0] > ab[1] else 0,
        6: lambda ab: 1 if ab[0] < ab[1] else 0,
        7: lambda ab: 1 if ab[0] == ab[1] else 0,
    }

    def a_better_eval(p: Packet) -> int:
        # Literal values first
        if p.type_id == 4:
            result = p.value

        # Otherwise, parse children
        else:
            values = [a_better_eval(child) for child in p.children]
            f = operators[p.type_id]
            result = f(values)

        logging.info(f'a_better_eval({p}) = {result}')
        return result

    p = Packet.from_hex(line.read().strip())
    print(f'{a_better_eval(p):-16} {line}')
```

And of course, this one worked first try:

```bash
$ python3 depacketinator.py part2 input.txt
    299227024091 0055...C000
# time 40238833ns / 0.04s
```

Pretty fun.

I've really enjoyed the last few days of these puzzles! In the world of the more common web apps, where space isn't really an issue and everything is sent in something as verbose as JSON, it's kind of fun to actually get down into really compact formats where the equivalent of a single 8-bit character can store 3+ fields.
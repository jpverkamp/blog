---
title: "AoC 2021 Day 25: Cucumbinator"
date: 2021-12-25 00:00:03
programming/languages:
- Python
programming/sources:
- Advent of Code
series:
- Advent of Code 2021
programming/topics:
- Cellular Automata
- Data Structures
- Generative Art
- Mathematics
---
### Source: [Sea Cucumber](https://adventofcode.com/2021/day/25)

#### **Part 1:** Load a grid of empty cells (`.`), east movers (`>`), and south movers (`v`). Each step, move all east movers than all south movers (only if they can this iteration). Wrap east/west and north/south. How many steps does it take the movers to get stuck?

<!--more-->

Let's just do it!

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __repr__(self):
        return f'<{self.x}, {self.y}>'

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    def __mod__(self, bound: 'Point') -> 'Point':
        return Point(self.x % bound.x, self.y % bound.y)


EAST = Point(1, 0)
SOUTH = Point(0, 1)


@dataclass(frozen=True)
class State:
    bounds: Point
    east_movers: FrozenSet[Point]
    south_movers: FrozenSet[Point]

    @staticmethod
    def read(file: TextIO) -> 'State':
        east_movers = set()
        south_movers = set()

        for y, line in enumerate(file):
            for x, c in enumerate(line.strip()):
                if c == '>':
                    east_movers.add(Point(x, y))
                elif c == 'v':
                    south_movers.add(Point(x, y))

        return State(Point(x + 1, y + 1), east_movers, south_movers)

    def step(self) -> 'State':
        new_east_movers = {
            (p + EAST) % self.bounds if (
                (p + EAST) % self.bounds not in self.east_movers
                and (p + EAST) % self.bounds not in self.south_movers
            ) else p
            for p in self.east_movers
        }

        new_south_movers = {
            (p + SOUTH) % self.bounds if(
                (p + SOUTH) % self.bounds not in new_east_movers
                and (p + SOUTH) % self.bounds not in self.south_movers
            ) else p
            for p in self.south_movers

        }

        return State(self.bounds, new_east_movers, new_south_movers)
```

I particularly like how `p + p` and `p % p` work and also how you can step them all pretty much in two lines. Pretty cool!

And to solve:

```python
@app.command()
def solve(file: typer.FileText):
    s = State.read(file)

    for i in itertools.count(1):
        logging.info(f'{i}\n{s}')

        sp = s.step()
        if s == sp:
            break
        else:
            s = sp

    logging.info('\n{s}\n')
    print(f'{i} steps')
```

Quick enough:

```python
--- Day 25: Sea Cucumber ---

$ python3 cucumbinator.py solve input.txt
419 steps
# time 14198676792ns / 14.20s
```


I did take some time to render it as a gif though!

```bash
$ python3 cucumbinator.py render input.txt 'aoc2021-25-input.gif' 556x548
```

{{< figure src="/embeds/2021/aoc2021-25-input.gif" >}}

Merry Christmas. :D

#### 'All' solutions

As always with Advent of Code, there's no part 2 on the last day. So instead, for better or for worse, here's the current timing of all my answers this year!

```bash
$ python3 all.py

--- Day 1: Sonar Sweep ---

$ python3 depth-finder.py part1 input.txt
1393
# time 44893792ns / 0.04s

$ python3 depth-finder.py part2 input.txt 3
1359
# time 34075167ns / 0.03s

$ python3 depth-finder.py part2-simple input.txt 3
1359
# time 33592209ns / 0.03s

--- Day 2: Dive! ---

$ python3 submarine-simulator.py part1 input.txt
position=2007, depth=747, position*depth=1499229
# time 33215792ns / 0.03s

$ python3 submarine-simulator.py part2 input.txt
position=2007, depth=668080, position*depth=1340836560
# time 32647917ns / 0.03s

--- Day 3: Binary Diagnostic ---

$ python3 binary-contraption.py part1 input.txt
gamma='100100101010'=2346, epsilon='011011010101'=1749, product=4103154
# time 34595542ns / 0.03s

$ python3 binary-contraption.py part2 input.txt
potential_generators=['110101000111']=3399, potential_scrubbers=['010011100001']=1249, product=4245351
# time 33425041ns / 0.03s

--- Day 4: Giant Squid ---

$ python3 his-name-oh.py part1 input.txt
remaining_numbers=[99, 19, 9, 59, 92, 82, 69, 72, 2, 45, 93, 27], sum(remaining_numbers)=668, number=66, product=44088
# time 46472333ns / 0.05s

$ python3 his-name-oh.py part2 input.txt
remaining_numbers=[3, 78, 23, 79, 80], sum(remaining_numbers)=263, number=90, product=23670
# time 64237667ns / 0.06s

--- Day 5: Hydrothermal Venture ---

$ python3 linear-avoidinator.py part1 input.txt
5632
# time 160036875ns / 0.16s

$ python3 linear-avoidinator.py part2 input.txt
22213
# time 289326791ns / 0.29s

--- Day 6: Lanternfish ---

$ python3 we-all-glow-down-here.py 80 input.txt
395627
3.95e6
# time 32692042ns / 0.03s

$ python3 we-all-glow-down-here.py 256 input.txt
1767323539209
1.76e13
# time 32836333ns / 0.03s

--- Day 7: The Treachery of Whales ---

$ python3 brachyura-aligner.py part1 input.txt
target=323, fuel=336040
# time 134097542ns / 0.13s

$ python3 brachyura-aligner.py part2 input.txt
target=463, fuel=94813675
# time 265068000ns / 0.27s

--- Day 8: Seven Segment Search ---

$ python3 seven-segment-demystifier.py part1 input.txt
349
# time 704037791ns / 0.70s

$ python3 seven-segment-demystifier.py part2 input.txt
1070957
# time 722054125ns / 0.72s

$ python3 seven-segment-demystifier.py --fast part1 input.txt
349
# time 50202125ns / 0.05s

$ python3 seven-segment-demystifier.py --fast part2 input.txt
1070957
# time 50484291ns / 0.05s

--- Day 9: Smoke Basin ---

$ python3 local-minimum-deminifier.py part1 input.txt
total_risk=491
# time 41001958ns / 0.04s

$ python3 local-minimum-deminifier.py part2 input.txt
The largest basins are [112, 99, 97] with a size product of 1075536
# time 44843709ns / 0.04s

--- Day 10: Syntax Scoring ---

$ python3 chunkinator.py part1 input.txt
167379
# time 34562209ns / 0.03s

$ python3 chunkinator.py part2 input.txt
2776842859
# time 34596333ns / 0.03s

--- Day 11: Dumbo Octopus ---

$ python3 octopus-flashinator.py part1 input.txt
1679
# time 43026125ns / 0.04s

$ python3 octopus-flashinator.py part2 input.txt
519
# time 79435000ns / 0.08s

--- Day 12: Passage Passing ---

$ python3 submarine-spider.py part1 input.txt
4749
# time 69497166ns / 0.07s

$ python3 submarine-spider.py part2 input.txt
123054
# time 1182472583ns / 1.18s

$ python3 submarine-spider.py part2-fast input.txt
123054
# time 516106250ns / 0.52s

--- Day 13: Transparent Origami ---

$ python3 foldinator.py part1 input.txt
706
# time 35915167ns / 0.04s

$ python3 foldinator.py part2 input.txt
*    ***  ****   ** ***    ** **** *  *
*    *  * *       * *  *    * *    *  *
*    *  * ***     * ***     * ***  ****
*    ***  *       * *  *    * *    *  *
*    * *  *    *  * *  * *  * *    *  *
**** *  * *     **  ***   **  **** *  *

# time 37279250ns / 0.04s

--- Day 14: Extended Polymerization ---

$ python3 polymerizationinator.py direct input.txt 10
2797
# time 54387334ns / 0.05s

$ python3 polymerizationinator.py recursive input.txt 10
2797
# time 100416792ns / 0.10s

$ python3 polymerizationinator.py direct input.txt 15
85972
# time 795572458ns / 0.80s

$ python3 polymerizationinator.py recursive input.txt 15
85972
# time 2112865750ns / 2.11s

$ python3 polymerizationinator.py --cache recursive input.txt 15
85972
# time 39737625ns / 0.04s

$ python3 polymerizationinator.py --cache recursive input.txt 40
2926813379532
# time 48990125ns / 0.05s

--- Day 15: Chiton ---

$ python3 low-ceiling-simulator.py part1 input.txt
best_score=687
# time 1697947292ns / 1.70s

$ python3 low-ceiling-simulator.py --version 2 part1 input.txt
best_score=687
# time 88316334ns / 0.09s

$ python3 low-ceiling-simulator.py --version 3 part1 input.txt
best_score=687
# time 269650750ns / 0.27s

$ python3 low-ceiling-simulator.py --version 4 part1 input.txt
best_score=687
# time 93736375ns / 0.09s

$ python3 low-ceiling-simulator.py --version 4 part2 input.txt
best_score=2957
# time 1704585750ns / 1.70s

--- Day 16: Packet Decoder ---

$ python3 depacketinator.py part1 input.txt
             981 005532447836402684AC7AB3801A800021F0961146B1007A1147C89440294D005C12D2A7BC992D3F4E50C72CDF29EECFD0ACD5CC016962099194002CE31C5D3005F401296CAF4B656A46B2DE5588015C913D8653A3A001B9C3C93D7AC672F4FF78C136532E6E0007FCDFA975A3004B002E69EC4FD2D32CDF3FFDDAF01C91FCA7B41700263818025A00B48DEF3DFB89D26C3281A200F4C5AF57582527BC1890042DE00B4B324DBA4FAFCE473EF7CC0802B59DA28580212B3BD99A78C8004EC300761DC128EE40086C4F8E50F0C01882D0FE29900A01C01C2C96F38FCBB3E18C96F38FCBB3E1BCC57E2AA0154EDEC45096712A64A2520C6401A9E80213D98562653D98562612A06C0143CB03C529B5D9FD87CBA64F88CA439EC5BB299718023800D3CE7A935F9EA884F5EFAE9E10079125AF39E80212330F93EC7DAD7A9D5C4002A24A806A0062019B6600730173640575A0147C60070011FCA005000F7080385800CBEE006800A30C023520077A401840004BAC00D7A001FB31AAD10CC016923DA00686769E019DA780D0022394854167C2A56FB75200D33801F696D5B922F98B68B64E02460054CAE900949401BB80021D0562344E00042A16C6B8253000600B78020200E44386B068401E8391661C4E14B804D3B6B27CFE98E73BCF55B65762C402768803F09620419100661EC2A8CE0008741A83917CC024970D9E718DD341640259D80200008444D8F713C401D88310E2EC9F20F3330E059009118019A8803F12A0FC6E1006E3744183D27312200D4AC01693F5A131C93F5A131C970D6008867379CD3221289B13D402492EE377917CACEDB3695AD61C939C7C10082597E3740E857396499EA31980293F4FD206B40123CEE27CFB64D5E57B9ACC7F993D9495444001C998E66B50896B0B90050D34DF3295289128E73070E00A4E7A389224323005E801049351952694C000
# time 43134500ns / 0.04s

$ python3 depacketinator.py part2 input.txt
    299227024091 005532447836402684AC7AB3801A800021F0961146B1007A1147C89440294D005C12D2A7BC992D3F4E50C72CDF29EECFD0ACD5CC016962099194002CE31C5D3005F401296CAF4B656A46B2DE5588015C913D8653A3A001B9C3C93D7AC672F4FF78C136532E6E0007FCDFA975A3004B002E69EC4FD2D32CDF3FFDDAF01C91FCA7B41700263818025A00B48DEF3DFB89D26C3281A200F4C5AF57582527BC1890042DE00B4B324DBA4FAFCE473EF7CC0802B59DA28580212B3BD99A78C8004EC300761DC128EE40086C4F8E50F0C01882D0FE29900A01C01C2C96F38FCBB3E18C96F38FCBB3E1BCC57E2AA0154EDEC45096712A64A2520C6401A9E80213D98562653D98562612A06C0143CB03C529B5D9FD87CBA64F88CA439EC5BB299718023800D3CE7A935F9EA884F5EFAE9E10079125AF39E80212330F93EC7DAD7A9D5C4002A24A806A0062019B6600730173640575A0147C60070011FCA005000F7080385800CBEE006800A30C023520077A401840004BAC00D7A001FB31AAD10CC016923DA00686769E019DA780D0022394854167C2A56FB75200D33801F696D5B922F98B68B64E02460054CAE900949401BB80021D0562344E00042A16C6B8253000600B78020200E44386B068401E8391661C4E14B804D3B6B27CFE98E73BCF55B65762C402768803F09620419100661EC2A8CE0008741A83917CC024970D9E718DD341640259D80200008444D8F713C401D88310E2EC9F20F3330E059009118019A8803F12A0FC6E1006E3744183D27312200D4AC01693F5A131C93F5A131C970D6008867379CD3221289B13D402492EE377917CACEDB3695AD61C939C7C10082597E3740E857396499EA31980293F4FD206B40123CEE27CFB64D5E57B9ACC7F993D9495444001C998E66B50896B0B90050D34DF3295289128E73070E00A4E7A389224323005E801049351952694C000
# time 41857292ns / 0.04s

--- Day 17: Trick Shot ---

$ python3 pew-pewinator.py part1 input.txt
2850
# time 728209708ns / 0.73s

$ python3 pew-pewinator.py part2 input.txt
1117
# time 34003049541ns / 34.00s

--- Day 18: Snailfish ---

$ python3 pairs-of-pairs.py part1 input.txt
4433
# time 412309834ns / 0.41s

$ python3 pairs-of-pairs.py part2 input.txt
4559
# time 5496543584ns / 5.50s

--- Day 19: Beacon Scanner ---

$ python3 point-matchinator.py part1 input.txt
313
# time 420895747958ns / 420.90s

$ python3 point-matchinator.py part2 input.txt
10656
# time 403475587666ns / 403.48s

--- Day 20: Trench Map ---

$ python3 enhancinator.py part1 input.txt
5057
# time 288085792ns / 0.29s

$ python3 enhancinator.py part2 input.txt
18502
# time 10353347750ns / 10.35s

--- Day 21: Dirac Dice ---

$ python3 dicinator.py part1 input.txt
1 wins, 752247
# time 37687791ns / 0.04s

$ python3 dicinator.py part2 input.txt
221109915584112
# time 170310291ns / 0.17s

--- Day 22: Reactor Reboot ---

$ python3 cubinator.py part1 input.txt
590467
# time 32701100500ns / 32.70s

$ python3 cubinator.py part2 input.txt
1225064738333321
# time 9419514983155ns / 9419.51s

--- Day 23: Amphipods ---

$ python3 amphipodinator.py main input1.txt goal1.txt
Final solution:
State<13x5>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #########
}
states examined: 896123
11608
# time 105522400083ns / 105.52s

$ python3 amphipodinator.py main input1.txt goal1.txt --heuristic
Final solution:
State<13x5>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #########
}
states examined: 156876
11608
# time 18701982625ns / 18.70s

$ python3 amphipodinator.py main input2.txt goal2.txt --heuristic
Final solution:
State<13x7>{
#############
#           #
###A#B#C#D###
  #A#B#C#D#
  #A#B#C#D#
  #A#B#C#D#
  #########
}
states examined: 784637
46754
# time 162205732958ns / 162.21s

--- Day 24: Arithmetic Logic Unit ---

$ python3 aluinator.py solve input.txt
part1: 99995969919326
part2: 48111514719111
# time 64456917ns / 0.06s

--- Day 25: Sea Cucumber ---

$ python3 cucumbinator.py solve input.txt
419 steps
# time 14853312250ns / 14.85s
```

There are some that could certainly be better... but overall, I'm pretty happy with it. Now, to go back and do the years I missed!
---
title: "A quick ruby DSL for creating L-Systems"
date: 2021-03-24
programming/topics:
- Generative Art
- Procedural Content
programming/languages:
- Ruby
---
{{< wikipedia "L-Systems" >}} are pretty awesome. With only a bare few rules, you can turn something like this:

```ruby
LSystem.new("Barnsley Fern") do
    start "+++X"

    rule "X", "F+[[X]-X]-F[-FX]+X" 
    rule "F", "FF"

    terminal "F" do forward end
    terminal "[" do push end
    terminal "]" do pop end
    terminal "-" do rotate -25 end
    terminal "+" do rotate +25 end
end
```
Into this: 

<div style="width: 400px">
{{< include "output/barnsley-fern.svg" >}}
</div>

<!--more-->

I'll be the first to admit, this is not a particularly complicated bit of code. Mostly, I'm using it to continue to wrap my head around Ruby's `instance_eval` and using that to make DSLs. So here's what we have:

{{< source ruby "lsystem.rb" >}}

In particular, this is the entirety of the parsing code:

```ruby
def initialize(name, &block)
    @name = name
    @start = nil
    @alphabet = Set[]
    @terminals = Set[]
    @rules = {}
    @terminals = {}

    self.instance_eval(&block)
end

def start(key)
    @start = key
end

def rule(key, value)
    raise "duplicate key #{key}" if @rules.include? key

    @rules[key] = value
    @alphabet.add key
    value.chars.each { |k| @alphabet.add k }
end

def terminal(key, &block)
    raise "duplicate terminal #{key}" if @terminals.include? key
    
    @terminals[key] = block
end
```

Where it gets rather more interesting is in the `to_svg` function that actually turns an L-System into something we can look at:

```ruby
def to_svg(n, debug = false)
    @bounds = [0, 0, 0, 0]
    @x = 0
    @y = 0
    @r = 0
    @stack = []
    @output = []
    @debug = debug

    # Slow mode (calculate first)
    if SLOW_MODE
        # Expansion step
        state = @start
        n.times do
            state = state.chars.map { |c| @rules[c] or c }.join
        end

        # Evaluation step
        state.chars.each { |c| self.instance_eval(&@terminals[c]) if @terminals.include?(c) }

    # Fast mode (calculate as we go)
    else
        def recur(c, depth)
            if depth == 0
                self.instance_eval(&@terminals[c]) if @terminals.include?(c)
            else
                (@rules[c] or c).chars.each do
                    |c| recur(c, depth - 1)
                end
            end
        end
        recur(@start, n)
    end


    viewport = "#{@bounds[0]} #{@bounds[1]} #{@bounds[2]-@bounds[0]} #{@bounds[3]-@bounds[1]}"
    return %{<?xml version="1.0" standalone="no"?>
<svg viewBox="#{viewport}" version="1.1" xmlns="http://www.w3.org/2000/svg">
<!--
#{self} 
#{n} iterations: #{state}
-->
\t<g stroke="black" fill="transparent" stroke-width="5">
\t\t#{@output.join("\n\t\t")}
\t</g>
</svg>
}
end
```

We're going to have a number of helper functions (do those next), but essentially, we're going to stake the single `@start` character (although it can totally be a starting string) and expand it a number of times:

```ruby
# Expansion step
state = @start
n.times do
    state = state.chars.map { |c| @rules[c] or c }.join
end

# Evaluation step
state.chars.each { |c| self.instance_eval(&@terminals[c]) if @terminals.include?(c) }
```

The problem with doing it this way though is that it can be rather memory intensive as it has to keep the entire string in memory--and some of these systems get very very large very quickly. So I made a quicker version that solves it recursively:

```ruby
def recur(c, depth)
    if depth == 0
        self.instance_eval(&@terminals[c]) if @terminals.include?(c)
    else
        (@rules[c] or c).chars.each do
            |c| recur(c, depth - 1)
        end
    end
end
recur(@start, n)
```

It's fairly similar, but this one uses the stack to track only the parts of the string we're working on, rather than the whole thing. This wouldn't work nearly as well for doing contextual translations (a TODO for next time) where you need to have the surrounding characters as well, but I think it could still be made to work. We'll see!

And then finally, we have to add a handful more helpers that can actually be used to generate the systems:

```ruby
def forward(distance=1.0)
    emit "<!-- forward(#{distance}) -->" if @debug
    emit "<!-- x = #{@x}, y = #{@y}, r = #{@r} -->" if @debug

    # Intentionally reversed to rotate
    x1, y1 = @x, @y
    x2 = (x1 - 100.0 * distance * Math.sin(@r)).round(2)
    y2 = (y1 - 100.0 * distance * Math.cos(@r)).round(2)

    emit "<line x1=\"#{x1}\" y1=\"#{y1}\" x2=\"#{x2}\" y2=\"#{y2}\" />"

    @x, @y = x2, y2
    update_bounds
end

def push
    emit "<!-- push(#{[@x, @y, @r]}) on to #{@stack} -->" if @debug
    @stack.push([@x, @y, @r])
end

def pop
    emit "<!-- pop from #{@stack} -->" if @debug
    @x, @y, @r = @stack.pop
end

def rotate(angle, radians=false)
    emit "<!-- rotate(#{angle}, #{radians}) -->" if @debug

    angle = Math::PI * angle / 180.0 unless radians
    @r += angle
end

def emit(svg)
    @output.append svg
end

def update_bounds
    @bounds = [
        [@bounds[0], @x].min,
        [@bounds[1], @y].min,
        [@bounds[2], @x].max,
        [@bounds[3], @y].max,
    ]
end
```

It's kind of funny that I made `emit` a function, since we're not actually emitting SVG (only debug) other than in the `forward` function, but that could change if we do other sorts of things (circles or arcs or whatever). It's half a remnant of an earlier structure (where I was using `g` elements with `transform` attributes for everything) and half future proofing. We could easily add those as functions though!

And that's about it!

Here are a few of the examples from the Wikipedia page:

```fish
$ begin
      ruby examples/barnsley-fern.rb 5 > output/barnsley-fern.svg
      ruby examples/binary-tree.rb 8 > output/binary-tree.svg
      ruby examples/dragon-curve.rb 8 > output/dragon-curve.svg
      ruby examples/sierpinski-arrowhead.rb 8 > output/sierpinski-arrowhead.svg
  end
```

{{< tabs >}}
    {{< sourcetab ruby "examples/barnsley-fern.rb" >}}
    {{< tab "barnsley-fern.svg" >}}
        {{< include "output/barnsley-fern.svg" >}}
    {{< /tab >}}

    {{< sourcetab ruby "examples/binary-tree.rb" >}}
    {{< tab "binary-tree.svg" >}}
        {{< include "output/binary-tree.svg" >}}
    {{< /tab >}}

    {{< sourcetab ruby "examples/dragon-curve.rb" >}}
    {{< tab "dragon-curve.svg" >}}
        {{< include "output/dragon-curve.svg" >}}
    {{< /tab >}}

    {{< sourcetab ruby "examples/sierpinski-arrowhead.rb" >}}
    {{< tab "sierpinski-arrowhead.svg" >}}
        {{< include "output/sierpinski-arrowhead.svg" >}}
    {{< /tab >}}  
{{< /tabs >}}

There are a pile of things more I could do with this, including probabalistic rules (choose one of many randomly based on pre-set chances) and contextual rules (see what's around a character before expanding it). We'll have to see how it goes!
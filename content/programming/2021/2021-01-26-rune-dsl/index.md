---
title: "A DSL for rendering magic circles and runes"
date: 2021-01-26
programming/topics:
- Generative Art
- Procedural Content
programming/languages:
- Ruby
---
Let's make magic circles/runes!

Turn this:

{{< source ruby "examples/astrology-and-moons.rune" >}}

Into this: 

<div style="width: 400px">
{{< include "output/astrology-and-moons.svg" >}}
</div>

<!--more-->

All through the magic of RUBY!

{{< tabs >}}
    {{< sourcetab ruby "rune.rb" >}}

    {{< sourcetab ruby "components/_core.rb" >}}
    {{< sourcetab ruby "components/children.rb" >}}
    {{< sourcetab ruby "components/circles.rb" >}}
    {{< sourcetab ruby "components/control.rb" >}}
    {{< sourcetab ruby "components/lines.rb" >}}
    {{< sourcetab ruby "components/stars.rb" >}}
    {{< sourcetab ruby "components/text.rb" >}}
{{< /tabs >}}

My goal here was to design a series of functions that each automatically generate parts of an SVG as they're going, all scaled to a 100.0 unit radius circle (chosen arbitrarily) centered as 0,0. That way, you can do transformations/scaling/etc and it will always work. You can take a large, complicated rune and make it a small subset of another and it will just work(tm). 

How? 

The core of this code revolves around Ruby's block syntax. If you aren't familiar (well, really either way), blocks are a neat little way of passing a bit of code to a function without going so far as to sending around first class functions everywhere (you can do this, but it's not as elegant). So every time you see `do`/`end` or `{...}`, you can think of that as an inline function call being passed to another function which can do with it what it wants. For example, `double` is defined as:

```ruby
Node.class_eval do
    def double(width, &block)
        run(&block)
        scale(1-width) { run(&block) }
        self
    end
end
```

It takes in the `width` as a normal parameter and (in this case) explicitly takes a `block`. It actually uses another function that I defined (`scale`) and calls `run` on the `&block` twice. Now... that's a lot of words, most of which is my custom functionality. Let's take a look at the whole `Node` class (in `components/_core.rb`), which has a few very powerful functions:

First, how do we create a new Node explicitly:

```ruby
class Node
    def initialize(name, children=nil, **attributes)
        @name = name
        @attributes = attributes
        @children = children || []

        @attributes['vector-effect'] = 'non-scaling-stroke' if $NON_SCALING_ELEMENTS.include?(@name) or $NON_SCALING_ELEMENTS.include?(@name.to_s)
    end
end
```

Most of the time, you won't explicitly add the `children` (nodes contained by this node), but you can always set attributes. This is way of assigning arbitrary `xml` attributes to the generated `svg`. For example:

```ruby
irb(main):008:0> Node.new(:g, width: 5).to_s
=> "Node<g {:width=>5}>"

irb(main):006:0> Node.new(:g, width: 5).to_xml
=> "<g width=\"5\" />\n"
```

Speaking of which, I have functions that can render Node to either a more explicit string or directly `to_xml`:

```ruby
class Node
    def to_s
        parts = []
        parts.append @name
        parts.append @attributes unless @attributes.empty?
        parts.append "[" + @children.map{ |n| n.to_s }.join(", ") + "]" unless @children.empty?
        return "Node<#{parts.join(" ")}>"
    end

    def to_xml(depth: 0)
        xml = %(#{'  ' * depth}<#{@name})
        xml += " " + @attributes.map { |k, v| "#{k}=\"#{v}\"" }.join(" ") unless @attributes.empty?
        if @children.empty?
            xml += " />\n"
        else
            xml += ">\n"
            @children.map do |child| 
                if child.is_a? Node
                    xml += child.to_xml(depth: depth + 1) 
                else
                    xml += "#{'  ' * (depth + 1)}#{child.to_s}\n"
                end
            end
            xml += "#{'  ' * depth}</#{@name}>\n"
        end
        return xml
    end
end
```

`to_xml` is a recursive function that always expects `children` to be an array of either nodes or text elements. Other things are possible, but will just get `to_s`ed, so strange things can happen. Essentially, it's generating 'nice' XML for this limited subset of elements. First, the `@attributes` map, then (if no children) a closing tag or recursively do the children one level deeper. I like that it properly indents and newlines the output. It makes debugging easier.

Finally, still in Node, we have two more useful functions:

```ruby
class Node
    def run(*args, **kwargs, &block)
        self.instance_exec(*args, **kwargs, &block)
        self
    end

    def <<(child)
        @children.push(child)
        self
    end
end
```

`run` we saw before. It looks bizarre, but all it really means is that you're going to run the given `&block` in the context of the current `Node` object. This allows you to do things like access the `@children` attribute within the block, which is exactly how the basic elements work:

```ruby
Node.class_eval do
    def circle
        @children.push(Node.new(:circle, cx: 0, cy: 0, r: 100))
        self
    end
end
```

Create a new `svg` `circle` element as a `Node` with a few default attributes and add it to the `Node` who is calling this function's `@children` attribute. It's always centered at the current origin and always 100 units in radius. Anyone using this DSL should never have to worry about explitic radii, instead making everything relative. 

Originally, I didn't use the `@children` attribute and instead had the elements implicitly being returned. But that only works for the last element. In a previous version of this work (in Racket), you could return lists of elements and automatically collect them, but that doesn't work as well in Ruby. But this version works and the end user's view is the same--even if implementation is a bit more complicated. 

The last function (back in Node) is the `<<` 'add child' function. It allows you to more easily nest nodes when writing helper functions. For example, the `children` constructor:

```ruby


Node.class_eval do
    def children(ls, scale: 1, offset: 0, &block)
        ls = *(0..ls-1) if ls.is_a? Integer

        group = Node.new(:g)
        
        ls.each_with_index do |el, i|
            group << Node.new(:g, transform: %(
                rotate(#{i*360.0/ls.length})
                translate(0 #{100*offset.to_f})
                scale(#{scale.to_f})
            ).squish).run(el, &block)
        end

        @children.push(group)
        self
    end
end
```

This is one of the core functions of a 'magic circle' generator. You can either give it a number of children or a list of elements and it will evenly space them around a circle, applying a `scale` or `offset` (from the center) for each. So if you want a series of 1/4 scale circles in a circle themselves:

```ruby
irb(main):033:2* puts(rune do
irb(main):034:3*   children(4, scale: 1/4r, offset: 3/4r) do
irb(main):035:3*     circle
irb(main):036:2*   end
irb(main):037:0> end.to_xml)
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200">
  <g transform="rotate(180)" stroke="black" fill="white">
    <g>
      <g transform="rotate(0.0) translate(0 75.0) scale(0.25)">
        <circle cx="0" cy="0" r="100" vector-effect="non-scaling-stroke" />
      </g>
      <g transform="rotate(90.0) translate(0 75.0) scale(0.25)">
        <circle cx="0" cy="0" r="100" vector-effect="non-scaling-stroke" />
      </g>
      <g transform="rotate(180.0) translate(0 75.0) scale(0.25)">
        <circle cx="0" cy="0" r="100" vector-effect="non-scaling-stroke" />
      </g>
      <g transform="rotate(270.0) translate(0 75.0) scale(0.25)">
        <circle cx="0" cy="0" r="100" vector-effect="non-scaling-stroke" />
      </g>
    </g>
  </g>
</svg>
```

Each one is rotated a different degree automatically, then translated out 3/4 of the default radius (100), and scaled to 1/4. The `1/4r` is a Ruby way of specifying rational constants rather than `1/4` which is integer division and equals `0`. That took a bit to discover. :)

And that's just about it. I've already gone through and done a number of basic functions that can be used to create some pretty awesome examples. 

A few more examples:

{{< tabs >}}
    {{< sourcetab ruby "examples/art-station.rune" >}}
    {{< tab "art-station.svg" >}}
        {{< include "output/art-station.svg" >}}
    {{< /tab >}}

    {{< sourcetab ruby "examples/astrology-and-moons.rune" >}}
    {{< tab "astrology-and-moons.svg" >}}
        {{< include "output/astrology-and-moons.svg" >}}
    {{< /tab >}}

    {{< sourcetab ruby "examples/text-circle.rune" >}}
    {{< tab "text-circle.svg" >}}

        {{< include "output/text-circle.svg" >}}
    {{< /tab >}}
{{< /tabs >}}

It's wonderful. :D 

Next up: 

* Add rules to make 'runes', such as Vegvisir: {{< figure src="/embeds/2021/vegvisir.jpg" >}}

* Add a system to automatically generate runes that follow certain rules

Onward!
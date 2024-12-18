---
title: PyMint - A Python Multi-Interpreter
date: 2007-10-20 04:55:08
programming/languages:
- Python
---
During the computer architecture class I took at <a title="Rose-Hulman Institute of Technology" href="http://www.rose-hulman.edu/">Rose-Hulman</a>, we were working with a simple assembly language that we had to compile by hand down to [[wiki:MIPS architecture|MIPS bytecode]]() and that's no fun (also there's nothing not worth over doing :smile:). So I decided to write a program that would allow for modular XML definitions of a language or translation and run it on pretty much any given code.

<!--more-->

Basically, the XML files have a specific structure to run before, during, and after seeing a specifically structured line in the input (the parser is pretty dump, parsing something like Java would be well beyond it at this point) and run some Python code on that output, transforming it in a number of ways.

At the moment, I have definitions that can do any of the following:

* [assemble](/embeds/2007/rhij-assemble.xml) the given code into bytecode
* [write out those bytes](/embeds/2007/rhij-mif.xml) in a structure we can load directly into the simulator
* [even run a virtual machine](/embeds/2007/rhij-run.xml) over the given code.

As an example, consider the following implementation of a GCD algorithm in RHIJ:

```asm
BIPUSH 		10
BIPUSH 		5
INVOKEVIRTUAL 	gcd
OUTPUT
HALT

gcd 2 1

BIPUSH 		10
BIPUSH 		5
INVOKEVIRTUAL	mod
OUTPUT
HALT

gcd 2 1:

gcd_loop:
ILOAD		1
IFEQ		gcd_done
ILOAD		1
ISTORE		2
ILOAD		0
ILOAD		1
INVOKEVIRTUAL	mod
ISTORE		1
ILOAD		2
ISTORE		0
GOTO		gcd_loop

gcd_done:
ILOAD		0
IRETURN

mod 2 0

mod_loop:
ILOAD		0
IFLT		mod_done
ILOAD		0
ILOAD		1
ISUB
ISTORE		0
GOTO		mod_loop

mod_done:
ILOAD		0
ILOAD		1
IADD
IRETURN
```

If we were to the assembly over it, we would get something like this:

```asm
Assembled code:
0x40 0x0a
0x40 0x05
0x80 0x00 0x01
0x31
0xFF
0x00 0x02 0x00 0x01
0x40 0x0a
0x40 0x05
0x80 0x00 0x01
0x31
0xFF
0x00 0x02 0x00 0x01
0x60 0x01
0x51 0x00 0x17
0x60 0x01
0x61 0x02
0x60 0x00
0x60 0x01
0x80 0x00 0x01
0x61 0x01
0x60 0x02
0x61 0x00
0x58 0xff 0xea
0x60 0x00
0x20
0x00 0x02 0x00 0x00
0x60 0x00
0x50 0x00 0x0d
0x60 0x00
0x60 0x01
0x01
0x61 0x00
0x58 0xff 0xf4
0x60 0x00
0x60 0x01
0x00
0x20

Constant pool:
0x00 0x16
0x00 0x36
```

If we were to turn that into the actual bytes we could put in the simulator, we'd get this lovely mess:

```asm
00000116000001367777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
77777777777777777777777777777777
05400a4031010080000200FF400a4001
010080050200FF310160010060170051
60026101800160000161010000610260
60eaff580200200000600000600d0050
01016000ff580061600060f4FF200001
```

(That big old block of 7s is the constant pool. Since we only have two constants (used for jump targets), most of it is set to 7s. I'm sure there's a reason. :smile:)

And then finally, if we were to run it on the virtual machine:

```asm
0x40 0x0a
0x40 0x05
0x80 {{{INVOKEVIRTUAL|GCD}}}
0x31
0xFF
0x00 0x02 0x00 0x01
0x40 0x0a
0x40 0x05
0x80 {{{INVOKEVIRTUAL|MOD}}}
0x31
0xFF
0x00 0x02 0x00 0x01
0x60 0x01
0x51 {{{GOTO|28|GCD_DONE}}}
0x60 0x01
0x61 0x02
0x60 0x00
0x60 0x01
0x80 {{{INVOKEVIRTUAL|MOD}}}
0x61 0x01
0x60 0x02
0x61 0x00
0x58 {{{GOTO|48|GCD_LOOP}}}
0x60 0x00
0x20
0x00 0x02 0x00 0x00
0x60 0x00
0x50 {{{GOTO|60|MOD_DONE}}}
0x60 0x00
0x60 0x01
0x01
0x61 0x00
0x58 {{{GOTO|70|MOD_LOOP}}}
0x60 0x00
0x60 0x01
0x00
0x20
```

(Yes, that is exactly what it's supposed to output.)

I'm not sure if there's anyone out there that this would actually be useful for, but it was definitely an interesting experiment to write. That and it gave me a taste for just how deep the rabbit hole of compilers goes. Perhaps I'll look a bit deeper in the future.

Anyways, if you'd like to download and run the code, you can find a link below. You'll need <a title="Python" href="http://www.python.org/">Python </a>and <a title="wxPython" href="http://wxpython.org/">wxPython</a> for the GUI (side note: working with wxPython? Very straight forward.)

**Download**: [PyMint.zip](/embeds/2007/PyMint.zip)

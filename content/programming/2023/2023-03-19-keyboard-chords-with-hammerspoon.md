---
title: "Keyboard Chords with Hammerspoon"
date: '2023-03-19 23:00:00'
programming/languages:
- Lua
programming/topics:
- Dotfiles
- Window Managers
- Productivity
---
I love keyboard shortcuts. The less I have to switch between keyboard and mouse, the more efficient I (at least feel I) can be!

{{<toc>}}

## Problem statement

But there are only so many unique combinations of keys on a standard keyboard. Assume 26 letters, 10 digits, and (for now) 20 other characters, along with 4 'modifier' keys (⌘ ⌃ ⌥ ⇧) that you can use in any combination of one or more. So {{<inline-latex "26 * 10 * 20 * (2^4 - 1) = 78,000">}}. Like I said. Limited. :smile:

But we can do better!

Enter the [Hammerspoon hs.hotkey.modal](https://www.hammerspoon.org/docs/hs.hotkey.modal.html) module!

<!--more-->

In a nutshell, you can define {{<wikipedia "modal">}} hotkeys: enter one combination and you'll be in the context of another function. Within that context, you can hit one of multiple keys (or even enter a nested modal!). 

## Hammerspoon chords

So say I want to bind a few common Hammerspoon functions to a chord:

```lua
hammerspoonMode = hs.hotkey.modal.new('⌘⌃', 'h')

hammerspoonMode:bind('', 'r', function()
    hs.alert.show('Reloading Hammerspoon')
    hs.reload()
    hammerspoonMode:exit()
end)

hammerspoonMode:bind('', 'l', function()
    hs.alert.show('Running init_layout')
    init_layout()
    hammerspoonMode:exit()
end)
```

Create a new `mode` for `⌘⌃+h` (for Hammerspoon), then you can hit `r` to reload or `l` to run my layout scripts (see [[Once Again, to Hammerspoon]]()). In both cases, I use `hammerspoonMode:exit()` to get back out of the context of the modal. If you don't do that, it won't think you're don, so any `r` you hit will reload Hammerspoon again... ask me how I know. :smile:

## Capture chords

Another thing I have set up is `⌘⌃+c` defined as my '[Capture](https://www.dropbox.com/capture)'[^disclosure] modal, and then I can hit `s` for a screenshot, `r` to capture a screen recording or `g` to capture a gif. Three keyboard shortcuts only taking one of those ~78,000 keyboard shortcuts. How's that for efficiency! 

Implementation wise, it's pretty straight forward:

```lua
captureMode = hs.hotkey.modal.new('⌘⌃', 'c')

captureMode:bind('', 's', function()
    hs.eventtap.keyStroke('⌘⌃⇧', '1')
    captureMode:exit()
end)

captureMode:bind('', 'r', function()
    hs.eventtap.keyStroke('⌘⌃⇧', '2')
    hs.eventtap.keyStroke('⌘⌃⇧', '4') -- mute
    captureMode:exit()
end)

captureMode:bind('', 'g', function()
    hs.eventtap.keyStroke('⌘⌃⇧', '3');
    captureMode:exit()
end)

captureMode:bind('', 'SPACE', function()
    hs.eventtap.keyStroke('⌘⌃⇧', '9');
    captureMode:exit()
end)
```

So this looks a bit funny. Basically, what we're doing is capturing the chord (`⌘⌃+c, s` for example) and then immediately turning around and firing off another keyboard shortcut (`⌘⌃⇧+1`)... that--doesn't help at all to save those ~78k... but that's a lot anyways. What that does do though is let me send a non-chord keyboard shortcut to Capture:

{{<figure src="/embeds/2023/capture-shortcuts.png">}}

Something out of the way. And it works great! Albeit not for taking screenshots of itself.  

## Running programs

Last but not least, I have another chord for running programs specifically with additional parameters (so Spotlight or [Dash](https://www.dropbox.com/dash) wouldn't pick them up):

```lua
runMode = hs.hotkey.modal.new('⌘⌃', 'r')

runMode:bind('', 't', function()
    hs.execute("code ~/Dropbox/todo.code-workspace", true)
    runMode:exit()
end)

runMode:bind('', 'b', function()
    hs.execute("code ~/Projects/blog", true)
    runMode:exit()
end)
```

Specifically, open a [VSCode workspace](https://code.visualstudio.com/docs/editor/workspaces) (a collection of folders I want to open at the same time) or my blog in VSCode with a chord. Works great. I can see myself adding more to this. 

## Wrapping it up

So one thing extra that I've done, I'm not directly running the code blocks above. Instead, I have something more like this:

```lua
register_key_chord('Run ⌘⌃r', function() 
    runMode = hs.hotkey.modal.new('⌘⌃', 'r')

    ...
end)
```

That way in my `keys.lua` file, I can do this:

```lua
key_chords = {}

function register_key_chord(name, f) 
    key_chords[name] = f
end

function init_keys()
    print('[debug] init_keys()')

    ...

    -- run any registered functions
    for name, f in pairs(key_chords) do
        print('[debug] Running key function: ' .. name)
        f()
    end
end
```

So instead of having to register each of them, I just have to import them and use the one `init_keys` function to reload them all. Good times. 

## Next steps

So what's next? 

1. Well, one thing I want to try is multiple levels of Chords. So instead of `⌘⌃+c, s` for screenshots, I could have `⌥+g, c, s` for `G`o `C`apture `S` screenshot. Since I have Caps Lock bound to Option (⌥), this fits. I already have my terminal on `⌥-a` and [Dropbox Dash](https://www.dropbox.com/dash) (formerly [Command E](https://getcommande.com/)) on `⌥-s`. 

2. Next? Perhaps my window movement. Perhaps (to keep things on my left hand), I could use a Chord with `wasd` for moving windows around? And because it's within a chord, I can actually hit more than one key. So things like `w,d` to move to top+right. Or `w,e,d` to move to top+right third instead of half. 

3. {{<wikipedia "Debouncing">}} for chords. Rather than immediately ending the modal, I can set it so that after 100ms (for example) without hitting a key that does something, it stops listening. That works well with the above for essentially typing in a subcommand. 

4. And of course, bind all the things! There's so many more things I could automate!

[^disclosure]: Full disclosure: I work for Dropbox. But I still do think that Capture is a surprisingly good screenshot tool, worth trying out. 